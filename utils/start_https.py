#!/usr/bin/env python
"""
Lanceur HTTPS simple pour OptimPV
"""
import subprocess
import sys
import time
import os

def main():
    print("="*50)
    print("   Lancement OptimPV avec HTTPS")
    print("="*50)
    
    # Lancer Streamlit
    print("\n[1/2] Demarrage de Streamlit...")
    streamlit_process = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "app.py", 
         "--server.address", "0.0.0.0",
         "--server.port", "8501"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Attendre que Streamlit démarre
    print("    Attente du demarrage...")
    time.sleep(5)
    
    # Lancer le proxy HTTPS
    print("\n[2/2] Demarrage du proxy HTTPS...")
    https_process = subprocess.Popen(
        [sys.executable, "utils/https_simple.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    print("\n" + "="*50)
    print("OptimPV est maintenant accessible :")
    print("  HTTP  : http://localhost:8501")
    print("  HTTPS : https://localhost:8443")
    print("="*50)
    print("\nCtrl+C pour arreter")
    
    try:
        # Attendre indéfiniment
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nArret en cours...")
        streamlit_process.terminate()
        https_process.terminate()
        print("Termine.")

if __name__ == "__main__":
    main()