#!/bin/bash

# Script d'installation HTTPS pour OptimPV
# À exécuter dans WSL Ubuntu

echo "======================================"
echo "Installation HTTPS pour OptimPV"
echo "======================================"

# Variables à personnaliser
DOMAIN="votre-domaine.com"  # CHANGEZ CECI
EMAIL="votre-email@example.com"  # CHANGEZ CECI

# 1. Mise à jour système
echo "[1/6] Mise à jour du système..."
sudo apt update

# 2. Installation Nginx
echo "[2/6] Installation de Nginx..."
sudo apt install -y nginx

# 3. Installation Certbot (Let's Encrypt)
echo "[3/6] Installation de Certbot..."
sudo apt install -y certbot python3-certbot-nginx

# 4. Création configuration Nginx pour OptimPV
echo "[4/6] Configuration de Nginx..."
sudo tee /etc/nginx/sites-available/optimpv > /dev/null <<EOF
server {
    listen 80;
    server_name $DOMAIN;
    
    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 86400;
    }
    
    location /_stcore/stream {
        proxy_pass http://localhost:8501/_stcore/stream;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }
}
EOF

# 5. Activer le site
echo "[5/6] Activation du site..."
sudo ln -sf /etc/nginx/sites-available/optimpv /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

# 6. Obtenir certificat SSL
echo "[6/6] Obtention du certificat SSL..."
sudo certbot --nginx -d $DOMAIN --non-interactive --agree-tos -m $EMAIL

echo "======================================"
echo "Installation terminée !"
echo "======================================"
echo ""
echo "IMPORTANT :"
echo "1. Modifiez DOMAIN et EMAIL dans ce script"
echo "2. Assurez-vous que le port 80 et 443 sont ouverts"
echo "3. Le DNS doit pointer vers votre serveur"
echo "4. Lancez OptimPV : streamlit run app.py"
echo "5. Accédez à : https://$DOMAIN"