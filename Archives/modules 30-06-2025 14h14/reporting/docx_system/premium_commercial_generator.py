"""
Générateur de Propositions Commerciales Ultra-Professionnelles OptimPV
Niveau de qualité : Agence de design premium - Effet "WOW" garanti
"""

import io
import tempfile
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
import traceback

try:
    from docx import Document
    from docx.shared import Inches, RGBColor, Pt, Cm
    from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
    from docx.enum.table import WD_TABLE_ALIGNMENT
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    # Créer des classes mock pour éviter NameError
    class Document:
        def __init__(self, *args, **kwargs):
            raise ImportError("python-docx n'est pas installé")
    
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
    WD_BREAK = None
    WD_TABLE_ALIGNMENT = None

try:
    from .professional_template_engine import ProfessionalTemplateEngine
    from .visual_components import VisualComponents
    from .commercial_chart_generator import CommercialChartGenerator
    PREMIUM_MODULES_AVAILABLE = True
except ImportError:
    PREMIUM_MODULES_AVAILABLE = False


class PremiumCommercialGenerator:
    """
    Générateur de propositions commerciales ultra-professionnelles
    
    Transforme les données OptimPV en documents Word de niveau agence de design
    avec un impact visuel immédiat et une présentation premium.
    """
    
    def __init__(self):
        """Initialise le générateur premium avec tous les composants avancés"""
        
        if not PREMIUM_MODULES_AVAILABLE:
            raise ImportError("Modules premium non disponibles")
        
        # 🎨 Moteurs de design
        self.template_engine = ProfessionalTemplateEngine()
        self.visual_components = VisualComponents()
        self.chart_generator = CommercialChartGenerator()
        
        # 🎯 Configuration premium
        self.colors = self.template_engine.colors
        self.output_dir = tempfile.mkdtemp()
    
    def generate_ultra_professional_proposal(self, client_name: str = None, 
                                           project_name: str = None) -> Optional[io.BytesIO]:
        """
        Génère une proposition commerciale ultra-professionnelle
        
        Niveau de qualité : Document digne d'une agence de design internationale
        Impact visuel : Effet "WOW" immédiat
        
        Args:
            client_name: Nom du client (optionnel)
            project_name: Nom du projet (optionnel)
            
        Returns:
            Buffer DOCX premium ou None si erreur
        """
        
        if not DOCX_AVAILABLE:
            print("❌ python-docx non disponible")
            return None
        
        try:
            print("🎨 Génération proposition commerciale ULTRA-PROFESSIONNELLE...")
            
            # 📊 EXTRACTION DES DONNÉES
            from .data_extractor import OptimPVDataExtractor
            extractor = OptimPVDataExtractor()
            data = extractor.extract_all_data()
            
            if 'error' in data:
                print(f"❌ Erreur extraction données: {data['error']}")
                return None
            
            # 📈 GÉNÉRATION DES GRAPHIQUES PREMIUM
            print("📊 Génération des graphiques commerciaux haute résolution...")
            charts = self.chart_generator.generate_all_commercial_charts(data)
            print(f"✅ {len(charts)} graphiques premium générés")
            
            # 📄 CRÉATION DU DOCUMENT PREMIUM
            doc = self.template_engine.create_premium_document("executive")
            
            # 🏗️ CONSTRUCTION DE LA PROPOSITION ULTRA-PROFESSIONNELLE
            
            # 1. PAGE DE GARDE IMMERSIVE
            self._create_immersive_cover_page(doc, data, client_name, project_name)
            
            # 2. RÉSUMÉ EXÉCUTIF MAGAZINE-STYLE  
            self._create_executive_summary_layout(doc, data, charts)
            
            # 3. SITUATION ACTUELLE - CRÉER L'URGENCE
            self._create_current_situation_showcase(doc, data)
            
            # 4. NOTRE SOLUTION - DESIGN IMMERSIF
            self._create_solution_showcase(doc, data, charts)
            
            # 5. BÉNÉFICES FINANCIERS - DASHBOARD VISUEL
            self._create_financial_benefits_dashboard(doc, data, charts)
            
            # 6. AVANTAGE CONCURRENTIEL - COMPARAISON VISUELLE
            self._create_competitive_advantage_visual(doc, data, charts)
            
            # 7. PROCESSUS ET TIMELINE - FLOW MODERNE
            self._create_process_timeline_visual(doc, data)
            
            # 8. GARANTIES ET CRÉDIBILITÉ - BADGES PREMIUM
            self._create_credibility_showcase(doc, data)
            
            # 9. CALL-TO-ACTION FINAL - IMPACT MAXIMUM
            self._create_final_cta_premium(doc, data)
            
            # 🧹 NETTOYAGE DES GRAPHIQUES TEMPORAIRES
            self.chart_generator.cleanup_charts()
            
            # 💾 SAUVEGARDE EN MÉMOIRE
            buffer = io.BytesIO()
            doc.save(buffer)
            buffer.seek(0)
            
            print("✅ Proposition commerciale ULTRA-PROFESSIONNELLE générée avec succès!")
            print("🎯 Niveau de qualité : Agence de design premium")
            
            return buffer
            
        except Exception as e:
            print(f"❌ Erreur génération proposition premium: {e}")
            print(traceback.format_exc())
            return None
    
    def _create_immersive_cover_page(self, doc: Document, data: Dict[str, Any],
                                   client_name: str = None, project_name: str = None):
        """
        Crée une page de garde immersive avec impact visuel maximum
        
        Design: Grande zone colorée immersive + métriques clés + design moderne
        """
        
        # 🎨 TITRE PREMIUM DYNAMIQUE
        economie_annuelle = data.get('economie_annuelle_calculee', 2500)
        autonomie = data.get('autonomy_rate', 40)
        
        main_title = "🌱 VOTRE PROJET SOLAIRE"
        dynamic_subtitle = f"Économisez {economie_annuelle:,.0f}€/an avec {autonomie:.0f}% d'autonomie".replace(',', ' ')
        
        # Utilisation du moteur premium pour la page de garde
        self.template_engine.create_premium_cover_page(
            doc, 
            main_title, 
            dynamic_subtitle,
            client_name, 
            project_name
        )
        
        # 🏆 MÉTRIQUES HERO EN BAS DE PAGE (avant saut de page)
        # Retirer le saut de page ajouté automatiquement
        doc.paragraphs[-1].clear()
        
        # Ajouter les métriques hero
        hero_metrics = {
            "autonomie": f"{autonomie:.0f}%",
            "economie_20ans": f"{data.get('economies_cumulees_20ans', 50000)/1000:.0f}K€",
            "autoconso": f"{data.get('autoconsumption_rate', 78):.0f}%",
            "prix": f"{data.get('prix_optimal', 0.16):.3f}€/kWh"
        }
        
        self._create_hero_metrics_bar(doc, hero_metrics)
        
        # Maintenant le saut de page
        doc.add_page_break()
    
    def _create_executive_summary_layout(self, doc: Document, data: Dict[str, Any], 
                                       charts: Dict[str, str]):
        """
        Crée un résumé exécutif avec layout magazine professionnel
        """
        
        # 📊 POINTS CLÉS DYNAMIQUES
        economie_annuelle = data.get('economie_annuelle_calculee', 2500)
        puissance = data.get('puissance_kwc_total', 25)
        autonomie = data.get('autonomy_rate', 40)
        economies_20ans = data.get('economies_cumulees_20ans', 50000)
        
        key_points = [
            f"Installation de {puissance:.0f} kWc pour une autonomie de {autonomie:.0f}%",
            f"Économies immédiates de {economie_annuelle:,.0f}€ dès la première année".replace(',', ' '),
            f"ROI attractif avec {economies_20ans/1000:.0f}K€ économisés sur 20 ans",
            "0€ d'investissement initial avec maintenance incluse 20 ans"
        ]
        
        # 📈 MÉTRIQUES VISUELLES
        exec_metrics = {
            "Économie Annuelle": f"{economie_annuelle:,.0f}€".replace(',', ' '),
            "Autonomie": f"{autonomie:.0f}%",
            "ROI 20 ans": f"{economies_20ans/1000:.0f}K€",
            "Prix Solaire": f"{data.get('prix_optimal', 0.16):.3f}€/kWh"
        }
        
        # Utilisation du composant visuel magazine
        self.visual_components.create_executive_summary_layout(
            doc, 
            "RÉSUMÉ EXÉCUTIF - VOTRE OPPORTUNITÉ", 
            key_points, 
            exec_metrics
        )
        
        # 🎨 INSERTION DU DASHBOARD HÉRO SI DISPONIBLE
        if 'hero_dashboard' in charts:
            try:
                # Titre du graphique
                chart_title = doc.add_paragraph()
                chart_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
                title_run = chart_title.add_run("📊 VOTRE PROJET EN UN COUP D'ŒIL")
                title_run.font.size = Pt(14)
                title_run.font.bold = True
                title_run.font.color.rgb = self.colors['primary']
                
                # Insertion de l'image avec cadre
                self._insert_chart_with_premium_frame(doc, charts['hero_dashboard'], 
                                                    "Dashboard de Performance")
                
            except Exception as e:
                print(f"⚠️ Erreur insertion dashboard héro: {e}")
        
        # 🚀 CALL-TO-ACTION INTERMÉDIAIRE
        self.template_engine.add_decorative_separator(doc, 'modern')
        
        cta_text = "Découvrez comment OptimPV va transformer votre consommation énergétique et maximiser vos économies sur les pages suivantes."
        self.template_engine.create_call_to_action_box(doc, cta_text, "Continuons ensemble !")
    
    def _create_current_situation_showcase(self, doc: Document, data: Dict[str, Any]):
        """
        Présentation de la situation actuelle avec impact visuel
        """
        
        # 💰 DONNÉES FINANCIÈRES ACTUELLES
        cout_sans_pv = data.get('cout_sans_pv', 9000)
        consommation = data.get('total_consumption', 45)
        tarif_edf = data.get('tarif_edf_reference', 0.20)
        
        # 📊 COMPARAISON AVANT/APRÈS VISUELLE
        before_data = {
            "Coût énergétique annuel": f"{cout_sans_pv:,.0f}€".replace(',', ' '),
            "Dépendance au réseau": "100%",
            "Protection inflation": "Aucune",
            "Contrôle des coûts": "Limité"
        }
        
        after_data = {
            "Coût énergétique annuel": f"{data.get('cout_avec_pv_total', 6500):,.0f}€".replace(',', ' '),
            "Dépendance au réseau": f"{100 - data.get('autonomy_rate', 40):.0f}%",
            "Protection inflation": "20 ans garantie",
            "Contrôle des coûts": "Total"
        }
        
        savings_highlight = f"{data.get('economie_annuelle_calculee', 2500):,.0f}€/an".replace(',', ' ')
        
        # Utilisation du composant de comparaison premium
        self.visual_components.create_comparison_showcase(
            doc,
            "VOTRE SITUATION ÉNERGÉTIQUE",
            before_data,
            after_data,
            savings_highlight
        )
        
        # 📈 ENCADRÉ TENDANCES DU MARCHÉ
        self.template_engine.create_info_box(
            doc,
            f"Les prix de l'électricité augmentent de 2% par an. Sans action, votre facture de {cout_sans_pv:,.0f}€ atteindra {cout_sans_pv * 1.22:,.0f}€ dans 10 ans. Chaque mois de retard vous coûte {cout_sans_pv/12:,.0f}€ supplémentaires !".replace(',', ' '),
            "warning",
            "⏰ URGENCE D'AGIR"
        )
    
    def _create_solution_showcase(self, doc: Document, data: Dict[str, Any], 
                                charts: Dict[str, str]):
        """
        Présentation de la solution OptimPV avec design immersif
        """
        
        # 🎯 NOTRE SOLUTION TITRE PREMIUM
        self.template_engine.create_section_header(doc, "🎯", "NOTRE SOLUTION OPTIMISÉE", "✨")
        
        # 🏗️ CARACTÉRISTIQUES TECHNIQUES EN CARDS
        tech_metrics = {
            "Puissance": {
                "value": f"{data.get('puissance_kwc_total', 25):.0f} kWc",
                "label": "Installation",
                "icon": "⚡"
            },
            "Production": {
                "value": f"{data.get('total_production', 23.7):.1f} MWh/an",
                "label": "Énergie Produite",
                "icon": "🌞"
            },
            "Autoconsommation": {
                "value": f"{data.get('autoconsumption_rate', 78):.0f}%",
                "label": "Taux d'Usage",
                "icon": "🔄"
            },
            "Prix Négocié": {
                "value": f"{data.get('prix_optimal', 0.16):.3f}€/kWh",
                "label": "Tarif Garanti",
                "icon": "💰"
            }
        }
        
        self.visual_components.create_metrics_dashboard(
            doc,
            "CARACTÉRISTIQUES TECHNIQUES",
            tech_metrics
        )
        
        # 🏆 AVANTAGES OPTIMPV EN BADGES
        advantages = [
            {
                "icon": "💰",
                "title": "0€ Investissement",
                "description": "Nous finançons tout"
            },
            {
                "icon": "🛡",
                "title": "Maintenance 20 ans",
                "description": "Tout inclus"
            },
            {
                "icon": "🔒",
                "title": "Prix Fixe",
                "description": "20 ans garantis"
            }
        ]
        
        self.visual_components.create_guarantee_badges(doc, advantages)
        
        # 📊 EFFET VISUEL AVEC GRADIENT
        self.template_engine.create_gradient_effect(
            doc, 
            self.colors['primary_light'], 
            self.colors['primary_dark'], 
            steps=12,
            height=Cm(0.5)
        )
    
    def _create_financial_benefits_dashboard(self, doc: Document, data: Dict[str, Any], 
                                          charts: Dict[str, str]):
        """
        Dashboard des bénéfices financiers avec visualisations premium
        """
        
        # 💰 TITRE SECTION FINANCIÈRE
        self.template_engine.create_section_header(doc, "💰", "VOS BÉNÉFICES FINANCIERS", "📈")
        
        # 📊 INSERTION ROI TIMELINE SI DISPONIBLE
        if 'roi_timeline' in charts:
            try:
                self._insert_chart_with_premium_frame(doc, charts['roi_timeline'], 
                                                    "Évolution de vos Économies sur 20 ans")
            except Exception as e:
                print(f"⚠️ Erreur insertion ROI timeline: {e}")
        
        # 📋 TABLEAU FINANCIER PREMIUM
        financial_data = [
            [f"{data.get('cout_sans_pv', 9000):,.0f}€".replace(',', ' '), 
             f"{data.get('cout_avec_pv_total', 6500):,.0f}€".replace(',', ' ')],
            ["-", f"{data.get('economie_annuelle_calculee', 2500):,.0f}€".replace(',', ' ')],
            ["-", f"{data.get('economie_annuelle_calculee', 2500) * 10:,.0f}€".replace(',', ' ')],
            ["-", f"{data.get('economies_cumulees_20ans', 50000):,.0f}€".replace(',', ' ')]
        ]
        
        headers = ["SANS Solaire", "AVEC OptimPV"]
        
        self.template_engine.create_professional_table(
            doc, financial_data, headers, style='dashboard'
        )
        
        # 🎯 SYNTHÈSE FINANCIÈRE EN ENCADRÉ PREMIUM
        economie_annuelle = data.get('economie_annuelle_calculee', 2500)
        cout_sans_pv = data.get('cout_sans_pv', 9000)
        pourcentage = (economie_annuelle / cout_sans_pv * 100) if cout_sans_pv > 0 else 0
        
        synthesis_text = f"""
✅ Économies immédiates dès la première année : {economie_annuelle:,.0f}€
✅ {pourcentage:.0f}% de réduction sur votre facture énergétique  
✅ {data.get('economies_cumulees_20ans', 50000)/1000:.0f}K€ économisés sur 20 ans
✅ Protection garantie contre l'inflation énergétique
✅ Valorisation de votre patrimoine immobilier
        """.strip().replace(',', ' ')
        
        self.template_engine.create_info_box(
            doc, synthesis_text, "success", "🎯 SYNTHÈSE FINANCIÈRE"
        )
    
    def _create_competitive_advantage_visual(self, doc: Document, data: Dict[str, Any], 
                                           charts: Dict[str, str]):
        """
        Présentation de l'avantage concurrentiel avec visualisations
        """
        
        # 🏆 TITRE AVANTAGE CONCURRENTIEL
        self.template_engine.create_section_header(doc, "🏆", "POURQUOI OPTIMPV EST LE MEILLEUR CHOIX", "🌟")
        
        # 📊 INSERTION GRAPHIQUE CONCURRENTIEL SI DISPONIBLE
        if 'competitive_advantage' in charts:
            try:
                self._insert_chart_with_premium_frame(doc, charts['competitive_advantage'], 
                                                    "Comparaison OptimPV vs Concurrence")
            except Exception as e:
                print(f"⚠️ Erreur insertion graphique concurrentiel: {e}")
        
        # 📋 TABLEAU DE COMPARAISON DÉTAILLÉE
        cout_sans_pv = data.get('cout_sans_pv', 9000)
        cout_avec_pv = data.get('cout_avec_pv_total', 6500)
        
        comparison_data = [
            [f"{cout_sans_pv:,.0f}€".replace(',', ' '), 
             f"{cout_sans_pv * 0.85:,.0f}€".replace(',', ' '),
             f"{cout_avec_pv:,.0f}€".replace(',', ' ')],
            ["0€", "50 000€+", "0€"],
            ["Non applicable", "À votre charge", "Incluse 20 ans"],
            ["Aucune", "2-5 ans", "20 ans"],
            ["Non applicable", "Optionnel", "Temps réel inclus"]
        ]
        
        headers = ["Sans Solution", "Concurrence", "OptimPV"]
        
        self.template_engine.create_professional_table(
            doc, comparison_data, headers, style='accent'
        )
        
        # 🌟 DIFFÉRENCIATEURS CLÉS
        differentiators_text = """
🚀 Déploiement rapide : installation en 4-6 semaines
🔒 Sécurité financière : prix fixe garanti sur 20 ans  
🎯 Optimisation continue : ajustements en temps réel
🤝 Accompagnement dédié : expert attitré pour votre projet
📊 Transparence totale : accès complet à vos données
        """.strip()
        
        self.template_engine.create_info_box(
            doc, differentiators_text, "highlight", "🌟 NOS DIFFÉRENCIATEURS CLÉS"
        )
    
    def _create_process_timeline_visual(self, doc: Document, data: Dict[str, Any]):
        """
        Processus et timeline avec design flow moderne
        """
        
        # 🚀 PROCESSUS EN FLOW VISUEL
        process_steps = [
            {
                "number": "1",
                "title": "Validation",
                "description": "Signature contrat\nÉtudes réglementaires"
            },
            {
                "number": "2", 
                "title": "Conception",
                "description": "Plans détaillés\nDemandes admin"
            },
            {
                "number": "3",
                "title": "Installation", 
                "description": "Montage équipements\nRaccordement réseau"
            },
            {
                "number": "4",
                "title": "Mise en service",
                "description": "Validation Enedis\nDémarrage production"
            }
        ]
        
        self.visual_components.create_process_flow(
            doc, "PROCESSUS DE RÉALISATION", process_steps
        )
        
        # 📅 TIMELINE DÉTAILLÉE
        timeline_items = [
            {
                "step": "1",
                "title": "Validation du Projet",
                "description": "Signature du contrat et lancement des études réglementaires",
                "duration": "1 semaine"
            },
            {
                "step": "2",
                "title": "Conception Détaillée", 
                "description": "Réalisation des plans techniques et démarches administratives",
                "duration": "2 semaines"
            },
            {
                "step": "3",
                "title": "Installation Terrain",
                "description": "Montage des équipements et raccordement au réseau électrique",
                "duration": "2-3 semaines"
            },
            {
                "step": "4",
                "title": "Mise en Production",
                "description": "Validation Enedis et démarrage officiel de la production",
                "duration": "1 semaine"
            }
        ]
        
        self.visual_components.create_timeline_visual(
            doc, "TIMELINE DE VOTRE PROJET", timeline_items
        )
    
    def _create_credibility_showcase(self, doc: Document, data: Dict[str, Any]):
        """
        Showcase de crédibilité avec garanties et témoignages
        """
        
        # 🛡 GARANTIES PREMIUM
        guarantees = [
            {
                "icon": "🛡",
                "title": "Garantie 20 ans",
                "description": "Performance garantie sur toute la durée"
            },
            {
                "icon": "⚡",
                "title": "Production Minimum",
                "description": "Compensation si objectifs non atteints"
            },
            {
                "icon": "🛠",
                "title": "Maintenance Incluse",
                "description": "Préventive et corrective 24/7"
            }
        ]
        
        self.visual_components.create_guarantee_badges(doc, guarantees)
        
        # 💬 TÉMOIGNAGES CLIENTS
        testimonials = [
            {
                "quote": "Grâce à OptimPV, nous économisons 3 500€/an sur nos factures. L'installation s'est déroulée parfaitement et le suivi est excellent !",
                "author": "Marie Dubois",
                "company": "Commune de Sainville",
                "rating": "5"
            },
            {
                "quote": "Un partenaire de confiance qui tient ses promesses. Production conforme aux prévisions et économies au rendez-vous depuis 3 ans.",
                "author": "Jean Martin",  
                "company": "ZAC Eco-Quartier Lyon",
                "rating": "5"
            }
        ]
        
        self.visual_components.create_testimonial_showcase(doc, testimonials)
        
        # 📊 NOTRE EXPERTISE EN CHIFFRES
        expertise_metrics = {
            "Expérience": {
                "value": "5+",
                "label": "Années d'expertise",
                "icon": "🎓"
            },
            "Projets": {
                "value": "100+", 
                "label": "Réalisations",
                "icon": "🏗"
            },
            "Satisfaction": {
                "value": "98%",
                "label": "Clients satisfaits", 
                "icon": "😊"
            },
            "Garanties": {
                "value": "20",
                "label": "Ans de couverture",
                "icon": "🛡"
            }
        }
        
        self.visual_components.create_metrics_dashboard(
            doc, "NOTRE EXPERTISE EN CHIFFRES", expertise_metrics
        )
    
    def _create_final_cta_premium(self, doc: Document, data: Dict[str, Any]):
        """
        Call-to-action final avec impact maximum
        """
        
        # 🚀 CTA PRINCIPAL PREMIUM
        cta_text = f"""
Votre projet d'autoconsommation collective présente des bénéfices exceptionnels :
• {data.get('economie_annuelle_calculee', 2500):,.0f}€ d'économies annuelles garanties
• {data.get('autonomy_rate', 40):.0f}% d'autonomie énergétique immédiate  
• {data.get('economies_cumulees_20ans', 50000)/1000:.0f}K€ économisés sur 20 ans

Le moment est venu de concrétiser cette opportunité !
        """.strip().replace(',', ' ')
        
        self.template_engine.create_call_to_action_box(
            doc, cta_text, "🚀 DÉMARRONS VOTRE PROJET"
        )
        
        # 📞 COORDONNÉES FINALES PREMIUM
        contact_table = doc.add_table(rows=1, cols=1)
        contact_table.alignment = WD_TABLE_ALIGNMENT.CENTER
        
        contact_cell = contact_table.cell(0, 0)
        contact_cell.width = Cm(16)
        self.template_engine._set_cell_background(contact_cell, self.colors['primary_dark'])
        self.template_engine._set_cell_margins(contact_cell, Pt(24), Pt(24), Pt(32), Pt(32))
        
        contact_para = contact_cell.paragraphs[0]
        contact_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Titre contact
        title_run = contact_para.add_run("📞 CONTACTEZ NOTRE ÉQUIPE COMMERCIALE\n\n")
        title_run.font.size = Pt(16)
        title_run.font.bold = True
        title_run.font.color.rgb = self.colors['white']
        
        # Coordonnées
        coords_run = contact_para.add_run("📧 commercial@optimpv.fr\n🌐 www.optimpv.fr\n📱 01 XX XX XX XX")
        coords_run.font.size = Pt(14)
        coords_run.font.bold = True
        coords_run.font.color.rgb = self.colors['primary_light']
        
        # Signature finale
        doc.add_paragraph()
        signature_para = doc.add_paragraph()
        signature_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        signature_run = signature_para.add_run("🌱 OptimPV - Votre Partenaire Solaire de Confiance")
        signature_run.font.size = Pt(12)
        signature_run.font.bold = True
        signature_run.font.color.rgb = self.colors['primary']
    
    # ===============================
    # MÉTHODES UTILITAIRES PREMIUM
    # ===============================
    
    def _create_hero_metrics_bar(self, doc: Document, metrics: Dict[str, str]):
        """Crée une barre de métriques hero en bas de page de garde"""
        
        # Séparateur décoratif
        self.template_engine.add_decorative_separator(doc, 'diamond')
        
        # Table des métriques
        metrics_table = doc.add_table(rows=1, cols=len(metrics))
        metrics_table.alignment = WD_TABLE_ALIGNMENT.CENTER
        
        for i, (key, value) in enumerate(metrics.items()):
            cell = metrics_table.cell(0, i)
            cell.width = Cm(16 / len(metrics))
            
            # Style de la cellule
            color = self.colors['primary'] if i % 2 == 0 else self.colors['accent']
            self.template_engine._set_cell_background(cell, color)
            self.template_engine._set_cell_margins(cell, Pt(16), Pt(16), Pt(12), Pt(12))
            
            # Contenu
            para = cell.paragraphs[0]
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            
            value_run = para.add_run(f"{value}\n")
            value_run.font.size = Pt(16)
            value_run.font.bold = True
            value_run.font.color.rgb = self.colors['white']
            
            label_run = para.add_run(key.upper())
            label_run.font.size = Pt(9)
            label_run.font.bold = True
            label_run.font.color.rgb = self.colors['white']
    
    def _insert_chart_with_premium_frame(self, doc: Document, chart_path: str, 
                                       title: str = None):
        """Insère un graphique avec cadre premium"""
        
        if not os.path.exists(chart_path):
            return
        
        try:
            # Titre du graphique si fourni
            if title:
                title_para = doc.add_paragraph()
                title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                title_run = title_para.add_run(title)
                title_run.font.size = Pt(12)
                title_run.font.bold = True
                title_run.font.color.rgb = self.colors['neutral_700']
                
                doc.add_paragraph()  # Espacement
            
            # Table pour le cadre
            frame_table = doc.add_table(rows=1, cols=1)
            frame_table.alignment = WD_TABLE_ALIGNMENT.CENTER
            
            frame_cell = frame_table.cell(0, 0)
            self.template_engine._add_cell_border(frame_cell, self.colors['neutral_300'])
            self.template_engine._set_cell_margins(frame_cell, Pt(12), Pt(12), Pt(12), Pt(12))
            
            # Insertion de l'image
            frame_para = frame_cell.paragraphs[0]
            frame_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            
            # Ajout de l'image avec taille optimisée
            run = frame_para.add_run()
            run.add_picture(chart_path, width=Cm(14))
            
            doc.add_paragraph()  # Espacement après
            
        except Exception as e:
            print(f"⚠️ Erreur insertion graphique {chart_path}: {e}")
    
    def cleanup_charts(self):
        """Nettoie les fichiers temporaires"""
        try:
            import shutil
            if os.path.exists(self.output_dir):
                shutil.rmtree(self.output_dir)
        except Exception as e:
            print(f"⚠️ Erreur nettoyage: {e}")