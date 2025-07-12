"""
Générateur de propositions commerciales basé sur une vraie template Word
Utilise la template professionnelle fournie pour créer des documents de qualité
"""

import os
import io
import tempfile
from datetime import datetime
from typing import Dict, Any, Optional
import traceback
import shutil

try:
    from docx import Document
    from docx.shared import Inches, RGBColor, Pt, Cm
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    # Créer des classes mock pour éviter NameError
    class Document:
        def __init__(self, *args, **kwargs):
            raise ImportError("python-docx n'est pas installé. Installez-le avec: pip install python-docx")
    
    class RGBColor:
        def __init__(self, *args, **kwargs):
            raise ImportError("python-docx n'est pas installé")
    
    class Inches:
        def __init__(self, *args, **kwargs):
            raise ImportError("python-docx n'est pas installé")
    
    class Pt:
        def __init__(self, *args, **kwargs):
            raise ImportError("python-docx n'est pas installé")
    
    class Cm:
        def __init__(self, *args, **kwargs):
            raise ImportError("python-docx n'est pas installé")
    
    # Mock pour les enums
    WD_ALIGN_PARAGRAPH = None

try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False


class TemplateBasedGenerator:
    """
    Générateur de propositions basé sur votre template Word professionnelle
    Remplace les placeholders dans la template avec les vraies données
    """
    
    def __init__(self):
        """Initialise le générateur avec le chemin de la template"""
        # Chemin de la template
        self.template_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "templates",
            "Business-Proposal-Template.docx"
        )
        
        # Vérifier que la template existe
        if not os.path.exists(self.template_path):
            raise FileNotFoundError(f"Template non trouvée: {self.template_path}")
    
    def generate_from_template(self, client_name: str = None, 
                              project_name: str = None) -> Optional[io.BytesIO]:
        """
        Génère une proposition commerciale à partir de la template
        
        Args:
            client_name: Nom du client
            project_name: Nom du projet
            
        Returns:
            Buffer DOCX ou None si erreur
        """
        
        if not DOCX_AVAILABLE:
            if STREAMLIT_AVAILABLE:
                st.error("❌ python-docx non disponible")
            else:
                print("❌ python-docx non disponible")
            return None
        
        try:
            print(f"📄 Utilisation de la template: {self.template_path}")
            
            # Charger la template
            doc = Document(self.template_path)
            
            # Extraire les données OptimPV
            from .data_extractor import OptimPVDataExtractor
            extractor = OptimPVDataExtractor()
            data = extractor.extract_all_data()
            
            if 'error' in data:
                if STREAMLIT_AVAILABLE:
                    st.error(f"❌ Erreur extraction données: {data['error']}")
                else:
                    print(f"❌ Erreur extraction données: {data['error']}")
                return None
            
            # Définir les placeholders et leurs valeurs
            replacements = self._prepare_replacements(data, client_name, project_name)
            
            # Remplacer dans tous les paragraphes
            self._replace_in_paragraphs(doc, replacements)
            
            # Remplacer dans tous les tableaux
            self._replace_in_tables(doc, replacements)
            
            # Remplacer dans les en-têtes et pieds de page
            self._replace_in_headers_footers(doc, replacements)
            
            # Ajouter les graphiques si nécessaire
            self._insert_charts_if_needed(doc, data)
            
            # Sauvegarder en mémoire
            buffer = io.BytesIO()
            doc.save(buffer)
            buffer.seek(0)
            
            print("✅ Proposition générée avec succès depuis la template!")
            return buffer
            
        except Exception as e:
            print(f"❌ Erreur génération depuis template: {e}")
            print(traceback.format_exc())
            return None
    
    def _prepare_replacements(self, data: Dict[str, Any], 
                            client_name: str, project_name: str) -> Dict[str, str]:
        """
        Prépare le dictionnaire de remplacement des placeholders
        
        Adapte les placeholders selon ce qui est dans votre template
        """
        
        # Date du jour
        today = datetime.now()
        
        # Calculs financiers
        economie_annuelle = data.get('economie_annuelle_calculee', 2500)
        economies_20ans = data.get('economies_cumulees_20ans', 50000)
        autonomie = data.get('autonomy_rate', 40)
        puissance = data.get('puissance_kwc_total', 25)
        prix_solaire = data.get('prix_optimal', 0.16)
        
        # Dictionnaire de remplacement
        # IMPORTANT: Adaptez ces placeholders selon ceux utilisés dans votre template
        replacements = {
            # Informations client/projet
            '[CLIENT_NAME]': client_name or 'Votre Entreprise',
            '[PROJECT_NAME]': project_name or 'Projet Autoconsommation Collective',
            '[DATE]': today.strftime('%d/%m/%Y'),
            '[YEAR]': str(today.year),
            
            # Données techniques
            '[PUISSANCE_KWC]': f"{puissance:.0f}",
            '[PUISSANCE]': f"{puissance:.0f} kWc",
            '[AUTONOMIE]': f"{autonomie:.0f}%",
            '[TAUX_AUTONOMIE]': f"{autonomie:.0f}",
            '[PRIX_SOLAIRE]': f"{prix_solaire:.3f}",
            '[PRIX_KWH]': f"{prix_solaire:.3f}€/kWh",
            
            # Données financières  
            '[ECONOMIE_ANNUELLE]': f"{economie_annuelle:,.0f}€".replace(',', ' '),
            '[ECONOMIE_AN]': f"{economie_annuelle:,.0f}".replace(',', ' '),
            '[ECONOMIE_20ANS]': f"{economies_20ans:,.0f}€".replace(',', ' '),
            '[ECONOMIE_TOTALE]': f"{economies_20ans:,.0f}".replace(',', ' '),
            '[ROI]': f"{economies_20ans/1000:.0f}K€",
            
            # Autres placeholders communs
            '[COMPANY]': 'OptimPV',
            '[CONTACT_EMAIL]': 'commercial@optimpv.fr',
            '[CONTACT_PHONE]': '01 XX XX XX XX',
            '[WEBSITE]': 'www.optimpv.fr',
            
            # Placeholders supplémentaires selon votre template
            '{{CLIENT_NAME}}': client_name or 'Votre Entreprise',
            '{{PROJECT_NAME}}': project_name or 'Projet Autoconsommation Collective',
            '{{DATE}}': today.strftime('%d/%m/%Y'),
            '{{ECONOMIE_ANNUELLE}}': f"{economie_annuelle:,.0f}€".replace(',', ' '),
            '{{AUTONOMIE}}': f"{autonomie:.0f}%",
            '{{PUISSANCE}}': f"{puissance:.0f} kWc",
            '{{PRIX_SOLAIRE}}': f"{prix_solaire:.3f}€/kWh",
        }
        
        return replacements
    
    def _replace_in_paragraphs(self, doc: Document, replacements: Dict[str, str]):
        """Remplace les placeholders dans tous les paragraphes"""
        
        for paragraph in doc.paragraphs:
            for key, value in replacements.items():
                if key in paragraph.text:
                    # Remplacer en préservant le formatage
                    for run in paragraph.runs:
                        if key in run.text:
                            run.text = run.text.replace(key, value)
    
    def _replace_in_tables(self, doc: Document, replacements: Dict[str, str]):
        """Remplace les placeholders dans tous les tableaux"""
        
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        for key, value in replacements.items():
                            if key in paragraph.text:
                                for run in paragraph.runs:
                                    if key in run.text:
                                        run.text = run.text.replace(key, value)
    
    def _replace_in_headers_footers(self, doc: Document, replacements: Dict[str, str]):
        """Remplace les placeholders dans les en-têtes et pieds de page"""
        
        for section in doc.sections:
            # En-têtes
            for paragraph in section.header.paragraphs:
                for key, value in replacements.items():
                    if key in paragraph.text:
                        for run in paragraph.runs:
                            if key in run.text:
                                run.text = run.text.replace(key, value)
            
            # Pieds de page
            for paragraph in section.footer.paragraphs:
                for key, value in replacements.items():
                    if key in paragraph.text:
                        for run in paragraph.runs:
                            if key in run.text:
                                run.text = run.text.replace(key, value)
    
    def _insert_charts_if_needed(self, doc: Document, data: Dict[str, Any]):
        """
        Insère les graphiques si la template contient des placeholders spéciaux
        
        Recherche des placeholders comme [CHART_DASHBOARD], [CHART_ROI], etc.
        """
        
        # Vérifier si on a des placeholders de graphiques
        chart_placeholders = {
            '[CHART_DASHBOARD]': 'hero_dashboard',
            '[CHART_ROI]': 'roi_timeline',
            '[CHART_COMPETITIVE]': 'competitive_advantage',
            '{{CHART_DASHBOARD}}': 'hero_dashboard',
            '{{CHART_ROI}}': 'roi_timeline',
        }
        
        # Générer les graphiques si nécessaire
        charts_needed = False
        for paragraph in doc.paragraphs:
            for placeholder in chart_placeholders.keys():
                if placeholder in paragraph.text:
                    charts_needed = True
                    break
        
        if charts_needed:
            try:
                from .commercial_chart_generator import CommercialChartGenerator
                chart_gen = CommercialChartGenerator()
                charts = chart_gen.generate_all_commercial_charts(data)
                
                # Remplacer les placeholders par les images
                for paragraph in doc.paragraphs:
                    for placeholder, chart_key in chart_placeholders.items():
                        if placeholder in paragraph.text and chart_key in charts:
                            # Remplacer le texte par une image
                            paragraph.text = ""
                            run = paragraph.add_run()
                            run.add_picture(charts[chart_key], width=Inches(6))
                            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                
                # Nettoyer les graphiques temporaires
                chart_gen.cleanup_charts()
                
            except Exception as e:
                print(f"⚠️ Erreur insertion graphiques: {e}")
    
    def list_template_placeholders(self) -> list:
        """
        Liste tous les placeholders trouvés dans la template
        Utile pour savoir quels placeholders utiliser
        """
        
        try:
            doc = Document(self.template_path)
            placeholders = set()
            
            # Patterns de placeholders communs
            import re
            patterns = [
                r'\[([A-Z_]+)\]',           # [PLACEHOLDER]
                r'\{\{([A-Z_]+)\}\}',       # {{PLACEHOLDER}}
                r'\$\{([A-Z_]+)\}',         # ${PLACEHOLDER}
                r'<<([A-Z_]+)>>',           # <<PLACEHOLDER>>
            ]
            
            # Chercher dans les paragraphes
            for paragraph in doc.paragraphs:
                for pattern in patterns:
                    matches = re.findall(pattern, paragraph.text)
                    placeholders.update(matches)
            
            # Chercher dans les tableaux
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        for paragraph in cell.paragraphs:
                            for pattern in patterns:
                                matches = re.findall(pattern, paragraph.text)
                                placeholders.update(matches)
            
            return sorted(list(placeholders))
            
        except Exception as e:
            print(f"Erreur analyse template: {e}")
            return []


def analyze_template():
    """Analyse la template pour identifier les placeholders"""
    
    print("🔍 ANALYSE DE LA TEMPLATE WORD")
    print("="*50)
    
    try:
        generator = TemplateBasedGenerator()
        
        print(f"📄 Template: {generator.template_path}")
        print(f"✅ Template trouvée et accessible")
        
        # Lister les placeholders
        placeholders = generator.list_template_placeholders()
        
        if placeholders:
            print(f"\n📝 Placeholders trouvés ({len(placeholders)}):")
            for ph in placeholders:
                print(f"   - {ph}")
        else:
            print("\n⚠️ Aucun placeholder détecté dans la template")
            print("   La template utilise peut-être un format différent")
        
        print("\n💡 Pour utiliser cette template:")
        print("   1. Identifiez les placeholders dans votre template Word")
        print("   2. Adaptez le dictionnaire 'replacements' dans _prepare_replacements()")
        print("   3. La template sera automatiquement remplie avec les données OptimPV")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        print(traceback.format_exc())


if __name__ == "__main__":
    # Analyser la template si exécuté directement
    analyze_template()