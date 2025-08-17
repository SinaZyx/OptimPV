"""
Serveur HTTPS simple pour OptimPV
Lance un proxy HTTPS vers Streamlit
"""

import ssl
import urllib.request
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
import os
import sys

class HTTPSProxy(BaseHTTPRequestHandler):
    def do_GET(self):
        self.proxy_request()
    
    def do_POST(self):
        self.proxy_request()
    
    def proxy_request(self):
        # URL Streamlit cible
        streamlit_url = f"http://localhost:8501{self.path}"
        
        try:
            # Lire le body si POST
            content_length = self.headers.get('Content-Length')
            body = None
            if content_length:
                body = self.rfile.read(int(content_length))
            
            # Créer la requête vers Streamlit
            req = urllib.request.Request(streamlit_url, data=body)
            
            # Copier les headers importants
            for header, value in self.headers.items():
                if header.lower() not in ['host', 'connection']:
                    req.add_header(header, value)
            
            # Faire la requête
            with urllib.request.urlopen(req) as response:
                # Envoyer la réponse
                self.send_response(response.getcode())
                
                # Copier les headers de réponse
                for header, value in response.headers.items():
                    if header.lower() not in ['connection', 'content-encoding']:
                        self.send_header(header, value)
                self.end_headers()
                
                # Copier le contenu
                self.wfile.write(response.read())
                
        except urllib.error.HTTPError as e:
            self.send_error(e.code, e.reason)
        except Exception as e:
            self.send_error(502, f"Erreur proxy: {str(e)}")
    
    def log_message(self, format, *args):
        # Logs simplifiés
        return

def create_self_signed_cert():
    """Créer un certificat auto-signé si nécessaire"""
    cert_dir = "utils/ssl"
    cert_file = os.path.join(cert_dir, "cert.pem")
    key_file = os.path.join(cert_dir, "key.pem")
    
    if os.path.exists(cert_file) and os.path.exists(key_file):
        print("[OK] Certificats SSL trouves")
        return cert_file, key_file
    
    print("Creation des certificats auto-signes...")
    os.makedirs(cert_dir, exist_ok=True)
    
    try:
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        import datetime
        
        # Générer clé privée
        key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        
        # Créer certificat
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
        ])
        
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.datetime.utcnow()
        ).not_valid_after(
            datetime.datetime.utcnow() + datetime.timedelta(days=365)
        ).add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName("localhost"),
                x509.DNSName("127.0.0.1"),
            ]),
            critical=False,
        ).sign(key, hashes.SHA256())
        
        # Sauvegarder
        with open(key_file, "wb") as f:
            f.write(key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        with open(cert_file, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        
        print("[OK] Certificats crees avec succes")
        return cert_file, key_file
        
    except ImportError:
        print("[ERREUR] Module cryptography non installe")
        print("Installez avec : pip install cryptography")
        sys.exit(1)

def main():
    print("="*50)
    print("   Serveur HTTPS pour OptimPV")
    print("="*50)
    
    # Vérifier que Streamlit tourne
    try:
        urllib.request.urlopen("http://localhost:8501", timeout=2)
        print("[OK] OptimPV detecte sur http://localhost:8501")
    except:
        print("[!] ATTENTION: OptimPV n'est pas accessible sur localhost:8501")
        print("  Lancez d'abord : streamlit run app.py")
        print()
    
    # Créer certificats
    cert_file, key_file = create_self_signed_cert()
    
    # Configurer SSL
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(cert_file, key_file)
    
    # Démarrer serveur (port 8443 pour éviter les droits admin)
    port = 8443
    server = HTTPServer(('0.0.0.0', port), HTTPSProxy)
    server.socket = context.wrap_socket(server.socket, server_side=True)
    
    print()
    print("[OK] Serveur HTTPS demarre sur le port", port, "!")
    print()
    print("Accedez a OptimPV via :")
    print(f"  -> https://localhost:{port}")
    print(f"  -> https://VOTRE_IP:{port}")
    print()
    print("Note: Acceptez l'avertissement du certificat auto-signe")
    print("Ctrl+C pour arreter")
    print()
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nArrêt du serveur...")
        server.shutdown()

if __name__ == "__main__":
    main()