"""
Serveur HTTPS minimaliste pour OptimPV
"""
import http.server
import ssl
import os

# Configuration
HTTPS_PORT = 8443
STREAMLIT_URL = "http://localhost:8501"

class ProxyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        """Redirige vers Streamlit"""
        self.send_response(301)
        self.send_header('Location', STREAMLIT_URL + self.path)
        self.end_headers()
    
    def do_POST(self):
        """Redirige vers Streamlit"""
        self.do_GET()

def create_cert():
    """Créer un certificat auto-signé basique"""
    cert_file = "utils/cert.pem"
    key_file = "utils/key.pem"
    
    if not os.path.exists(cert_file):
        print("Creation du certificat SSL...")
        try:
            # Utiliser cryptography au lieu d'OpenSSL
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
                datetime.datetime.now(datetime.timezone.utc)
            ).not_valid_after(
                datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=365)
            ).add_extension(
                x509.SubjectAlternativeName([
                    x509.DNSName("localhost"),
                    x509.DNSName("127.0.0.1"),
                ]),
                critical=False,
            ).sign(key, hashes.SHA256())
            
            # Sauvegarder la clé
            with open(key_file, "wb") as f:
                f.write(key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.TraditionalOpenSSL,
                    encryption_algorithm=serialization.NoEncryption()
                ))
            
            # Sauvegarder le certificat
            with open(cert_file, "wb") as f:
                f.write(cert.public_bytes(serialization.Encoding.PEM))
            
            print("[OK] Certificat cree avec succes")
        except ImportError:
            print("[!] Module cryptography non installe")
            print("    Installez avec : pip install cryptography")
            return None, None
        except Exception as e:
            print(f"[!] Erreur creation certificat : {e}")
            return None, None
    
    return cert_file, key_file

def main():
    print("="*50)
    print("   Serveur HTTPS pour OptimPV")
    print("="*50)
    
    # Créer/vérifier certificats
    cert_file, key_file = create_cert()
    if not cert_file:
        return
    
    # Créer serveur HTTPS
    httpd = http.server.HTTPServer(('0.0.0.0', HTTPS_PORT), ProxyHandler)
    
    # Ajouter SSL
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(cert_file, key_file)
    httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
    
    print(f"\n[OK] Serveur HTTPS actif sur le port {HTTPS_PORT}")
    print(f"     Acces : https://localhost:{HTTPS_PORT}")
    print("\nNote: Ce serveur redirige vers Streamlit (HTTP)")
    print("      Pour un vrai proxy, utilisez nginx ou Apache")
    print("\nCtrl+C pour arreter\n")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nArret du serveur...")

if __name__ == "__main__":
    main()