"""
Gestionnaire de dépendances pour le système DOCX OptimPV
Installe automatiquement les dépendances manquantes et fournit des alternatives
"""

import subprocess
import sys
import os
import importlib
from typing import Dict, List, Tuple, Optional


class DocxDependencyManager:
    """
    Gestionnaire de dépendances pour le système DOCX
    Vérifie, installe et gère les dépendances requises
    """
    
    def __init__(self):
        """Initialise le gestionnaire de dépendances"""
        self.required_packages = {
            'python-docx': {
                'import_name': 'docx',
                'description': 'Manipulation de documents Word DOCX',
                'required': True
            },
            'matplotlib': {
                'import_name': 'matplotlib',
                'description': 'Génération de graphiques',
                'required': True
            },
            'pillow': {
                'import_name': 'PIL',
                'description': 'Traitement d\'images',
                'required': True
            },
            'numpy': {
                'import_name': 'numpy',
                'description': 'Calculs numériques',
                'required': False
            }
        }
        
        self.installation_status = {}
        self.check_all_dependencies()
    
    def check_all_dependencies(self) -> Dict[str, bool]:
        """
        Vérifie toutes les dépendances requises
        
        Returns:
            dict: Status de chaque dépendance {package: is_available}
        """
        self.installation_status = {}
        
        for package_name, package_info in self.required_packages.items():
            import_name = package_info['import_name']
            
            try:
                importlib.import_module(import_name)
                self.installation_status[package_name] = True
            except ImportError:
                self.installation_status[package_name] = False
        
        return self.installation_status
    
    def get_missing_dependencies(self) -> List[str]:
        """Retourne la liste des dépendances manquantes"""
        missing = []
        for package_name, is_installed in self.installation_status.items():
            package_info = self.required_packages[package_name]
            if package_info['required'] and not is_installed:
                missing.append(package_name)
        return missing
    
    def get_dependency_status(self) -> Dict[str, Dict[str, any]]:
        """
        Retourne le statut détaillé de toutes les dépendances
        
        Returns:
            dict: Informations détaillées sur chaque dépendance
        """
        status = {}
        
        for package_name, package_info in self.required_packages.items():
            is_installed = self.installation_status.get(package_name, False)
            
            status[package_name] = {
                'installed': is_installed,
                'required': package_info['required'],
                'description': package_info['description'],
                'import_name': package_info['import_name']
            }
        
        return status
    
    def install_package(self, package_name: str) -> Tuple[bool, str]:
        """
        Installe un package spécifique
        
        Args:
            package_name: Nom du package à installer
            
        Returns:
            tuple: (succès, message)
        """
        if package_name not in self.required_packages:
            return False, f"Package inconnu: {package_name}"
        
        try:
            # Essayer différentes commandes d'installation
            install_commands = [
                [sys.executable, '-m', 'pip', 'install', package_name],
                ['pip3', 'install', package_name],
                ['pip', 'install', package_name]
            ]
            
            for cmd in install_commands:
                try:
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=300  # 5 minutes timeout
                    )
                    
                    if result.returncode == 0:
                        # Vérifier que l'installation a réussi
                        import_name = self.required_packages[package_name]['import_name']
                        try:
                            importlib.import_module(import_name)
                            self.installation_status[package_name] = True
                            return True, f"✅ {package_name} installé avec succès"
                        except ImportError:
                            continue
                    
                except FileNotFoundError:
                    continue
                except subprocess.TimeoutExpired:
                    return False, f"❌ Timeout lors de l'installation de {package_name}"
            
            return False, f"❌ Impossible d'installer {package_name}. Installez manuellement: pip install {package_name}"
            
        except Exception as e:
            return False, f"❌ Erreur lors de l'installation de {package_name}: {str(e)}"
    
    def install_all_missing(self) -> Dict[str, Tuple[bool, str]]:
        """
        Installe toutes les dépendances manquantes
        
        Returns:
            dict: Résultats d'installation {package: (succès, message)}
        """
        missing = self.get_missing_dependencies()
        results = {}
        
        for package_name in missing:
            success, message = self.install_package(package_name)
            results[package_name] = (success, message)
        
        # Recheck après installation
        self.check_all_dependencies()
        
        return results
    
    def generate_installation_script(self) -> str:
        """
        Génère un script d'installation manuel
        
        Returns:
            str: Script bash pour installation manuelle
        """
        missing = self.get_missing_dependencies()
        
        if not missing:
            return "# Toutes les dépendances sont déjà installées !"
        
        script = """#!/bin/bash
# Script d'installation des dépendances DOCX OptimPV
# Exécutez ce script pour installer les packages manquants

echo "🚀 Installation des dépendances DOCX OptimPV..."

"""
        
        for package_name in missing:
            description = self.required_packages[package_name]['description']
            script += f"""
echo "📦 Installation de {package_name} ({description})..."
if command -v pip3 &> /dev/null; then
    pip3 install {package_name}
elif command -v pip &> /dev/null; then
    pip install {package_name}
else
    python3 -m pip install {package_name}
fi

"""
        
        script += """
echo "✅ Installation terminée !"
echo "Redémarrez OptimPV pour utiliser le système DOCX."
"""
        
        return script
    
    def is_system_ready(self) -> bool:
        """Vérifie si le système DOCX est prêt à être utilisé"""
        missing = self.get_missing_dependencies()
        return len(missing) == 0
    
    def get_alternative_formats(self) -> List[str]:
        """
        Retourne les formats alternatifs disponibles si DOCX n'est pas disponible
        
        Returns:
            list: Formats disponibles
        """
        alternatives = ["HTML"]
        
        # Vérifier si d'autres formats sont disponibles
        try:
            import weasyprint
            alternatives.append("PDF (WeasyPrint)")
        except ImportError:
            pass
        
        try:
            import reportlab
            alternatives.append("PDF (ReportLab)")
        except ImportError:
            pass
        
        return alternatives
    
    def create_fallback_report(self, data: Dict, report_type: str = "commercial") -> str:
        """
        Crée un rapport de fallback en HTML si DOCX n'est pas disponible
        
        Args:
            data: Données du rapport
            report_type: Type de rapport
            
        Returns:
            str: HTML du rapport de fallback
        """
        html = f"""
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Rapport {report_type.title()} OptimPV</title>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
                h1 {{ color: #27ae60; text-align: center; }}
                .warning {{ background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                .data-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                .data-table th, .data-table td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                .data-table th {{ background-color: #f8f9fa; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📄 Rapport {report_type.title()} OptimPV</h1>
                
                <div class="warning">
                    <strong>⚠️ Mode Dégradé</strong><br>
                    Ce rapport est généré en mode HTML car les dépendances DOCX ne sont pas installées.
                    Pour des rapports Word professionnels, installez les dépendances requises.
                </div>
                
                <h2>📊 Données du Projet</h2>
                <table class="data-table">
                    <tr><th>Paramètre</th><th>Valeur</th></tr>
                    <tr><td>Nom du projet</td><td>{data.get('project_name', 'N/A')}</td></tr>
                    <tr><td>Client</td><td>{data.get('client_name', 'N/A')}</td></tr>
                    <tr><td>Puissance totale</td><td>{data.get('puissance_kwc_total', 0):.1f} kWc</td></tr>
                    <tr><td>Prix optimal</td><td>{data.get('prix_optimal', 0):.4f} €/kWh</td></tr>
                    <tr><td>Économie totale</td><td>{data.get('economie_totale_finale', 0):,.0f} €</td></tr>
                    <tr><td>Durée du projet</td><td>{data.get('duree_projet', 20)} ans</td></tr>
                </table>
                
                <p><em>Généré le {data.get('generated_datetime', 'N/A')} par OptimPV</em></p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def get_installation_instructions(self) -> str:
        """
        Retourne les instructions d'installation détaillées
        
        Returns:
            str: Instructions formatées en markdown
        """
        missing = self.get_missing_dependencies()
        
        if not missing:
            return "✅ **Toutes les dépendances sont installées !**"
        
        instructions = f"""
## 📦 Installation des Dépendances DOCX

Pour utiliser la génération de rapports Word, installez les packages suivants :

### Méthode 1 : Installation automatique
1. Utilisez le bouton "🔧 Installer Automatiquement" dans l'interface
2. Redémarrez OptimPV

### Méthode 2 : Installation manuelle

```bash
# Installer toutes les dépendances en une fois
pip install python-docx matplotlib pillow

# Ou individuellement :
{chr(10).join([f'pip install {pkg}  # {self.required_packages[pkg]["description"]}' for pkg in missing])}
```

### Méthode 3 : Si pip n'est pas disponible

```bash
# Avec python -m pip
python -m pip install python-docx matplotlib pillow

# Ou avec python3
python3 -m pip install python-docx matplotlib pillow
```

### Dépendances manquantes :
{chr(10).join([f'- **{pkg}** : {self.required_packages[pkg]["description"]}' for pkg in missing])}

Une fois installées, redémarrez l'application OptimPV pour activer le système DOCX.
        """
        
        return instructions