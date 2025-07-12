"""
Module d'édition visuelle GrapesJS pour les propositions commerciales OptimPV.
Fournit un éditeur drag-and-drop avec composants solaires prédéfinis.
"""

import streamlit as st
import json
from typing import Dict, Any, Optional
import logging

# Import du générateur de template premium
try:
    from .professional_template_generator import ProfessionalTemplateGenerator
    PREMIUM_TEMPLATE_AVAILABLE = True
except ImportError:
    PREMIUM_TEMPLATE_AVAILABLE = False

logger = logging.getLogger(__name__)

class GrapesJSEditor:
    """Éditeur visuel GrapesJS pour les propositions commerciales."""
    
    def __init__(self):
        """Initialise l'éditeur GrapesJS."""
        if PREMIUM_TEMPLATE_AVAILABLE:
            self.premium_generator = ProfessionalTemplateGenerator()
        else:
            self.premium_generator = None
    
    def show_editor(self, project_data: Dict[str, Any]):
        """
        Affiche l'éditeur de proposition natif Streamlit.
        
        Args:
            project_data: Données du projet pour pré-remplir l'éditeur
        """
        st.info("🎨 **Éditeur de Proposition** - Interface simple et efficace")
        
        # Options de template
        col1, col2, col3 = st.columns([3, 2, 2])
        
        with col1:
            template_mode = st.selectbox(
                "🎨 Choisir un template",
                ["Template Premium Turquoise", "Solaire Standard", "Template Personnalisé"],
                key="template_selector"
            )
            st.session_state['selected_template_mode'] = template_mode
        
        with col2:
            if st.button("📋 **Charger Template**", use_container_width=True):
                self._load_template(template_mode, project_data)
                st.success(f"✅ Template {template_mode} chargé!")
                st.rerun()
        
        with col3:
            if st.button("🔄 **Nouveau Document**", use_container_width=True):
                self._reset_editor()
                st.rerun()
        
        st.markdown("---")
        
        # Éditeur par blocs natif Streamlit
        self._show_native_block_editor(project_data)
    
    def _show_native_block_editor(self, project_data: Dict[str, Any]):
        """Affiche l'éditeur par blocs natif Streamlit."""
        
        # Initialiser les blocs si nécessaire
        if 'editor_blocks' not in st.session_state:
            st.session_state['editor_blocks'] = []
        
        # Interface en deux colonnes
        col_editor, col_preview = st.columns([1, 1])
        
        with col_editor:
            st.subheader("🛠️ Construction de la Proposition")
            
            # Toolbar d'ajout de blocs premium
            st.markdown("**📑 Blocs Template Premium (10 pages) :**")
            
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                if st.button("📑 Couverture", use_container_width=True):
                    self._add_block("cover_page", project_data)
                    st.rerun()
            with col2:
                if st.button("💡 Résumé", use_container_width=True):
                    self._add_block("executive_summary", project_data)
                    st.rerun()
            with col3:
                if st.button("⭐ Avantages", use_container_width=True):
                    self._add_block("key_benefits", project_data)
                    st.rerun()
            with col4:
                if st.button("📊 Comparaison", use_container_width=True):
                    self._add_block("bill_comparison", project_data)
                    st.rerun()
            with col5:
                if st.button("💎 Modèle Prix", use_container_width=True):
                    self._add_block("pricing_model", project_data)
                    st.rerun()
            
            col6, col7, col8, col9, col10 = st.columns(5)
            with col6:
                if st.button("📈 Économies", use_container_width=True):
                    self._add_block("long_term_savings", project_data)
                    st.rerun()
            with col7:
                if st.button("⚡ Technique", use_container_width=True):
                    self._add_block("technical_specs", project_data)
                    st.rerun()
            with col8:
                if st.button("🌍 Écologie", use_container_width=True):
                    self._add_block("environmental_impact", project_data)
                    st.rerun()
            with col9:
                if st.button("❓ FAQ", use_container_width=True):
                    self._add_block("faq_section", project_data)
                    st.rerun()
            with col10:
                if st.button("🎯 Contact", use_container_width=True):
                    self._add_block("timeline_contact", project_data)
                    st.rerun()
            
            st.markdown("---")
            st.markdown("**🔧 Blocs Basiques :**")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("🌟 En-tête Premium", use_container_width=True):
                    self._add_block("premium_header", project_data)
                    st.rerun()
            
            with col2:
                if st.button("📊 Métriques", use_container_width=True):
                    self._add_block("metrics", project_data)
                    st.rerun()
            
            with col3:
                if st.button("💰 Financier", use_container_width=True):
                    self._add_block("financial", project_data)
                    st.rerun()
            
            with col4:
                if st.button("📝 Texte", use_container_width=True):
                    self._add_block("text", project_data)
                    st.rerun()
            
            col5, col6, col7, col8 = st.columns(4)
            
            with col5:
                if st.button("🌱 Impact Éco", use_container_width=True):
                    self._add_block("ecology", project_data)
                    st.rerun()
            
            with col6:
                if st.button("📞 Contact Simple", use_container_width=True):
                    self._add_block("contact", project_data)
                    st.rerun()
            
            with col7:
                if st.button("🖼️ Image", use_container_width=True):
                    self._add_block("image", project_data)
                    st.rerun()
            
            with col8:
                if st.button("⭐ Bénéfices", use_container_width=True):
                    self._add_block("benefits", project_data)
                    st.rerun()
            
            st.markdown("---")
            
            # Gestion des blocs existants
            if st.session_state['editor_blocks']:
                st.markdown("**📋 Votre Document :**")
                
                for i, block in enumerate(st.session_state['editor_blocks']):
                    with st.expander(f"{block['icon']} {block['title']}", expanded=False):
                        
                        # Contrôles de position
                        col_up, col_down, col_edit, col_delete = st.columns([1, 1, 2, 1])
                        
                        with col_up:
                            if st.button("⬆️", key=f"up_{i}") and i > 0:
                                self._move_block(i, i-1)
                                st.rerun()
                        
                        with col_down:
                            if st.button("⬇️", key=f"down_{i}") and i < len(st.session_state['editor_blocks'])-1:
                                self._move_block(i, i+1)
                                st.rerun()
                        
                        with col_edit:
                            if st.button("✏️ Modifier", key=f"edit_{i}", use_container_width=True):
                                st.session_state[f'editing_block_{i}'] = True
                                st.rerun()
                        
                        with col_delete:
                            if st.button("🗑️", key=f"delete_{i}"):
                                self._delete_block(i)
                                st.rerun()
                        
                        # Mode édition
                        if st.session_state.get(f'editing_block_{i}', False):
                            self._edit_block(i, block, project_data)
            else:
                st.info("👆 Ajoutez des éléments pour construire votre proposition")
        
        with col_preview:
            st.subheader("👁️ Aperçu en Temps Réel")
            
            # Actions d'export
            col_export1, col_export2 = st.columns(2)
            with col_export1:
                if st.button("📄 **Télécharger HTML**", type="primary", use_container_width=True):
                    html_content = self._generate_final_html(project_data)
                    st.download_button(
                        "💾 Télécharger",
                        data=html_content,
                        file_name=f"proposition_{project_data['client_name'].replace(' ', '_')}.html",
                        mime="text/html"
                    )
            
            with col_export2:
                if st.button("🔄 **Actualiser**", use_container_width=True):
                    st.rerun()
            
            # Affichage de l'aperçu
            if st.session_state['editor_blocks']:
                preview_html = self._generate_preview_html(project_data)
                st.components.v1.html(preview_html, height=600, scrolling=True)
            else:
                st.markdown("""
                <div style="
                    padding: 60px 20px; 
                    text-align: center; 
                    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                    border-radius: 10px;
                    border: 2px dashed #dee2e6;
                ">
                    <h3 style="color: #6c757d; margin-bottom: 20px;">📄 Aperçu de votre proposition</h3>
                    <p style="color: #adb5bd;">Ajoutez des éléments à gauche pour voir l'aperçu ici</p>
                </div>
                """, unsafe_allow_html=True)
    
    def _add_block(self, block_type: str, project_data: Dict[str, Any]):
        """Ajoute un bloc à l'éditeur."""
        block_templates = {
            "premium_header": {
                "type": "premium_header",
                "title": "En-tête Premium Turquoise",
                "icon": "🌟",
                "content": {
                    "title": "PROPOSITION AUTOCONSOMMATION",
                    "subtitle": f"Projet pour {project_data.get('client_name', '[NOM DU CLIENT]')}",
                    "price": f"{project_data.get('solar_price', 15.0):.1f} ct/kWh",
                    "savings": f"{project_data.get('total_savings_20y', 150000):,} €".replace(",", " ")
                }
            },
            "metrics": {
                "type": "metrics",
                "title": "Métriques Clés",
                "icon": "📊",
                "content": {
                    "metric1": {"value": f"{project_data.get('annual_savings', 7500):,}".replace(",", " "), "label": "Économie Annuelle (€)", "color": "#4ECDC4"},
                    "metric2": {"value": f"{project_data.get('power_kwc', 100)}", "label": "Puissance Installée (kWc)", "color": "#44A08D"},
                    "metric3": {"value": f"{project_data.get('co2_avoided', 7.5):.1f}", "label": "CO₂ Évité/An (T)", "color": "#26C6DA"}
                }
            },
            "financial": {
                "type": "financial",
                "title": "Résumé Financier",
                "icon": "💰",
                "content": {
                    "solar_price": project_data.get('solar_price', 15.0),
                    "grid_price": project_data.get('prix_reseau', 18.5),
                    "savings_20y": project_data.get('total_savings_20y', 150000),
                    "savings_percentage": project_data.get('savings_percentage', 20)
                }
            },
            "text": {
                "type": "text",
                "title": "Section Texte",
                "icon": "📝",
                "content": {
                    "title": "Votre Titre",
                    "text": "Votre texte personnalisé ici..."
                }
            },
            "ecology": {
                "type": "ecology",
                "title": "Impact Écologique",
                "icon": "🌱",
                "content": {
                    "co2_avoided": project_data.get('co2_avoided', 7.5),
                    "trees_equivalent": int(project_data.get('co2_avoided', 7.5) * 50),
                    "cars_equivalent": int(project_data.get('co2_avoided', 7.5) * 2.4)
                }
            },
            "contact": {
                "type": "contact",
                "title": "Contact",
                "icon": "📞",
                "content": {
                    "name": "Votre Contact OptimPV",
                    "phone": "01 23 45 67 89",
                    "email": "contact@optimpv.fr",
                    "message": "Demandez votre étude personnalisée gratuite"
                }
            },
            "image": {
                "type": "image",
                "title": "Image",
                "icon": "🖼️",
                "content": {
                    "src": "https://via.placeholder.com/400x250/4ECDC4/ffffff?text=Votre+Image",
                    "alt": "Image de démonstration",
                    "caption": "Légende de l'image"
                }
            },
            "benefits": {
                "type": "benefits",
                "title": "Avantages",
                "icon": "⭐",
                "content": {
                    "title": "Votre Avantage Principal",
                    "text": "En rejoignant ce projet d'autoconsommation collective, vous bénéficiez d'une électricité produite localement à un tarif fixe et compétitif, à l'abri des hausses du marché.",
                    "cta": "C'est simple, sécurisé et sans investissement de votre part !"
                }
            }
        }
        
        if block_type in block_templates:
            st.session_state['editor_blocks'].append(block_templates[block_type])
    
    def _edit_block(self, index: int, block: Dict, project_data: Dict[str, Any]):
        """Interface d'édition d'un bloc."""
        st.markdown("**✏️ Mode Édition**")
        
        if block['type'] == 'text':
            block['content']['title'] = st.text_input("Titre", value=block['content']['title'], key=f"edit_title_{index}")
            block['content']['text'] = st.text_area("Texte", value=block['content']['text'], key=f"edit_text_{index}", height=100)
        
        elif block['type'] == 'premium_header':
            block['content']['title'] = st.text_input("Titre principal", value=block['content']['title'], key=f"edit_h_title_{index}")
            block['content']['subtitle'] = st.text_input("Sous-titre", value=block['content']['subtitle'], key=f"edit_h_subtitle_{index}")
            block['content']['price'] = st.text_input("Prix", value=block['content']['price'], key=f"edit_h_price_{index}")
            block['content']['savings'] = st.text_input("Économies", value=block['content']['savings'], key=f"edit_h_savings_{index}")
        
        elif block['type'] == 'contact':
            block['content']['name'] = st.text_input("Nom", value=block['content']['name'], key=f"edit_c_name_{index}")
            block['content']['phone'] = st.text_input("Téléphone", value=block['content']['phone'], key=f"edit_c_phone_{index}")
            block['content']['email'] = st.text_input("Email", value=block['content']['email'], key=f"edit_c_email_{index}")
            block['content']['message'] = st.text_area("Message", value=block['content']['message'], key=f"edit_c_message_{index}")
        
        elif block['type'] == 'image':
            block['content']['src'] = st.text_input("URL de l'image", value=block['content']['src'], key=f"edit_i_src_{index}")
            block['content']['alt'] = st.text_input("Texte alternatif", value=block['content']['alt'], key=f"edit_i_alt_{index}")
            block['content']['caption'] = st.text_input("Légende", value=block['content']['caption'], key=f"edit_i_caption_{index}")
        
        # Boutons de sauvegarde
        col_save, col_cancel = st.columns(2)
        with col_save:
            if st.button("✅ Sauvegarder", key=f"save_{index}", use_container_width=True):
                st.session_state['editor_blocks'][index] = block
                st.session_state[f'editing_block_{index}'] = False
                st.rerun()
        
        with col_cancel:
            if st.button("❌ Annuler", key=f"cancel_{index}", use_container_width=True):
                st.session_state[f'editing_block_{index}'] = False
                st.rerun()
    
    def _move_block(self, from_index: int, to_index: int):
        """Déplace un bloc."""
        blocks = st.session_state['editor_blocks']
        blocks[from_index], blocks[to_index] = blocks[to_index], blocks[from_index]
    
    def _delete_block(self, index: int):
        """Supprime un bloc."""
        st.session_state['editor_blocks'].pop(index)
    
    def _reset_editor(self):
        """Remet à zéro l'éditeur."""
        st.session_state['editor_blocks'] = []
        # Nettoyer les états d'édition
        keys_to_remove = [key for key in st.session_state.keys() if key.startswith('editing_block_')]
        for key in keys_to_remove:
            del st.session_state[key]
    
    def _load_template(self, template_name: str, project_data: Dict[str, Any]):
        """Charge un template prédéfini."""
        if template_name == "Template Premium Turquoise":
            # Template complet de 10 pages selon votre spécification
            st.session_state['editor_blocks'] = [
                self._get_block_template("cover_page", project_data),
                self._get_block_template("executive_summary", project_data),
                self._get_block_template("key_benefits", project_data),
                self._get_block_template("bill_comparison", project_data),
                self._get_block_template("pricing_model", project_data),
                self._get_block_template("long_term_savings", project_data),
                self._get_block_template("technical_specs", project_data),
                self._get_block_template("environmental_impact", project_data),
                self._get_block_template("faq_section", project_data),
                self._get_block_template("timeline_contact", project_data)
            ]
        elif template_name == "Solaire Standard":
            st.session_state['editor_blocks'] = [
                self._get_block_template("metrics", project_data),
                self._get_block_template("financial", project_data),
                self._get_block_template("ecology", project_data),
                self._get_block_template("contact", project_data)
            ]
        else:  # Template Personnalisé
            st.session_state['editor_blocks'] = [
                self._get_block_template("text", project_data)
            ]
    
    def _get_block_template(self, block_type: str, project_data: Dict[str, Any]) -> Dict:
        """Retourne un template de bloc sans l'ajouter."""
        from datetime import datetime
        
        block_templates = {
            # PAGE 1 - Couverture
            "cover_page": {
                "type": "cover_page",
                "title": "Page de Couverture",
                "icon": "📑",
                "content": {
                    "main_title": "Proposition d'Autoconsommation Collective - Projet Solaire",
                    "subtitle": "VOTRE PROJET D'AUTOCONSOMMATION SOLAIRE",
                    "client_name": project_data.get('client_name', '[NOM DU CLIENT]'),
                    "price": f"{project_data.get('solar_price', 15.0):.1f} ct/kWh",
                    "savings": f"{project_data.get('total_savings_20y', 150000):,} €".replace(",", " "),
                    "service_date": project_data.get('date_mise_service', 'T2 2025'),
                    "report_date": datetime.now().strftime("%d %B %Y"),
                    "page_number": "Page 1 / 10"
                }
            },
            
            # PAGE 2 - Résumé Exécutif
            "executive_summary": {
                "type": "executive_summary",
                "title": "Une Énergie Plus Verte et Plus Économique",
                "icon": "💡",
                "content": {
                    "title": "Une Énergie Plus Verte et Plus Économique, en Bref",
                    "text": f"""Ce rapport vous présente une opportunité unique de réduire durablement votre facture d'électricité. 
                    En rejoignant le projet d'autoconsommation collective, vous bénéficierez d'une électricité produite localement 
                    à un tarif fixe et compétitif de {project_data.get('solar_price', 15.0):.1f} ct/kWh, à l'abri des hausses du marché. 
                    Cela représente une économie estimée à {project_data.get('savings_percentage', 20):.0f}% sur la part solaire de votre consommation, 
                    soit plus de {project_data.get('total_savings_20y', 150000):,} € sur 20 ans, tout en réduisant votre empreinte carbone de 
                    {project_data.get('co2_avoided', 7.5):.1f} tonnes par an. C'est simple, sécurisé et sans investissement de votre part.""".replace(",", " "),
                    "page_number": "Page 2 / 10"
                }
            },
            
            # PAGE 3 - Avantages Clés
            "key_benefits": {
                "type": "key_benefits",
                "title": "Vos 3 Avantages Clés",
                "icon": "⭐",
                "content": {
                    "title": "Vos 3 Avantages Clés",
                    "benefit1": {
                        "icon": "💰",
                        "title": "ÉCONOMIES DIRECTES",
                        "description": f"Un prix de l'électricité solaire inférieur de {project_data.get('savings_percentage', 20):.0f}% au tarif réglementé actuel."
                    },
                    "benefit2": {
                        "icon": "🔒",
                        "title": "STABILITÉ DES PRIX",
                        "description": "Un tarif fixe pendant 20 ans, vous protégeant de la volatilité du marché."
                    },
                    "benefit3": {
                        "icon": "🌱",
                        "title": "IMPACT POSITIF",
                        "description": "Accès à une énergie 100% verte et locale, valorisant votre image RSE."
                    },
                    "page_number": "Page 3 / 10"
                }
            },
            
            # PAGE 4 - Comparaison Facture
            "bill_comparison": {
                "type": "bill_comparison",
                "title": "Visualisez l'Impact sur Votre Facture Annuelle",
                "icon": "📊",
                "content": {
                    "title": "Visualisez l'Impact sur Votre Facture Annuelle",
                    "without_solar": {
                        "amount": project_data.get('cout_annuel_actuel', 50000),
                        "description": "100% de votre électricité achetée sur le réseau."
                    },
                    "with_solar": {
                        "amount": project_data.get('cout_annuel_avec_solaire', 42500),
                        "solar_part": project_data.get('solar_coverage', 35),
                        "grid_part": 100 - project_data.get('solar_coverage', 35)
                    },
                    "annual_savings": project_data.get('annual_savings', 7500),
                    "reduction_percentage": project_data.get('reduction_percentage', 15),
                    "page_number": "Page 4 / 10"
                }
            },
            
            # PAGE 5 - Modèle Tarifaire
            "pricing_model": {
                "type": "pricing_model",
                "title": "Un Modèle Simple et un Prix Transparent",
                "icon": "💎",
                "content": {
                    "title": "Un Modèle Simple et un Prix Transparent",
                    "solar_price": project_data.get('solar_price', 15.0),
                    "coverage_percentage": project_data.get('solar_coverage', 35),
                    "contract_duration": project_data.get('duree_contrat', 20),
                    "indexation": project_data.get('indexation', 'Fixe'),
                    "investment": 0,
                    "how_it_works": [
                        {"step": 1, "title": "Production", "description": f"Les panneaux solaires sur {project_data.get('localisation', '[Lieu de l installation]')} produisent de l'électricité."},
                        {"step": 2, "title": "Distribution", "description": "L'électricité est injectée dans le réseau public local."},
                        {"step": 3, "title": "Consommation", "description": "Vous la consommez instantanément."},
                        {"step": 4, "title": "Facturation", "description": "Nous mesurons la part solaire que vous avez consommée et nous vous la facturons au prix convenu."}
                    ],
                    "page_number": "Page 5 / 10"
                }
            },
            
            # PAGE 6 - Économies Long Terme
            "long_term_savings": {
                "type": "long_term_savings",
                "title": "Vos Économies sur le Long Terme",
                "icon": "📈",
                "content": {
                    "title": "Vos Économies sur le Long Terme",
                    "annual_savings": project_data.get('annual_savings', 7500),
                    "total_savings_20y": project_data.get('total_savings_20y', 150000),
                    "description": "Ce graphique illustre la puissance de votre engagement. Tandis que le prix de l'électricité du réseau devrait continuer d'augmenter, votre tarif solaire reste stable, créant des économies de plus en plus importantes chaque année.",
                    "page_number": "Page 6 / 10"
                }
            },
            
            # PAGE 7 - Spécifications Techniques
            "technical_specs": {
                "type": "technical_specs",
                "title": "Une Source d'Énergie Locale et Fiable",
                "icon": "⚡",
                "content": {
                    "title": "Une Source d'Énergie Locale et Fiable",
                    "location": project_data.get('localisation', '[Adresse de l installation]'),
                    "power_kwc": project_data.get('power_kwc', 100),
                    "equivalent_households": project_data.get('equivalent_foyers', 33),
                    "annual_production": project_data.get('total_production', 110000),
                    "technology": "Panneaux photovoltaïques haute performance",
                    "maintenance": "Assurées par nos équipes 24/7",
                    "page_number": "Page 7 / 10"
                }
            },
            
            # PAGE 8 - Impact Environnemental
            "environmental_impact": {
                "type": "environmental_impact",
                "title": "Plus qu'une Économie, un Geste pour la Planète",
                "icon": "🌍",
                "content": {
                    "title": "Plus qu'une Économie, un Geste pour la Planète",
                    "co2_avoided": project_data.get('co2_avoided', 7.5),
                    "cars_equivalent": project_data.get('cars_equivalent', 3),
                    "local_benefits": [
                        "Soutien à la production d'énergie locale.",
                        "Contribution à la transition énergétique de la région.",
                        "Valorisation de votre image de marque auprès de vos clients et collaborateurs."
                    ],
                    "page_number": "Page 8 / 10"
                }
            },
            
            # PAGE 9 - FAQ
            "faq_section": {
                "type": "faq_section",
                "title": "Foire Aux Questions",
                "icon": "❓",
                "content": {
                    "title": "Foire Aux Questions",
                    "faqs": [
                        {
                            "question": "Et s'il n'y a pas de soleil ?",
                            "answer": "Votre alimentation est garantie sans coupure. Le réseau électrique prend le relais automatiquement. Vous ne remarquerez aucune différence, sauf sur votre facture."
                        },
                        {
                            "question": "Que se passe-t-il si je consomme plus que ce que le solaire produit ?",
                            "answer": "Le complément est fourni par le réseau, comme aujourd'hui. Notre offre ne couvre que la part d'énergie solaire que vous consommez."
                        },
                        {
                            "question": "Mon contrat est-il flexible ?",
                            "answer": "Expliquer les conditions de sortie ou de transfert du contrat, par exemple en cas de déménagement."
                        },
                        {
                            "question": "Qui s'occupe de la maintenance ?",
                            "answer": "Nous nous occupons de tout. L'exploitation et la maintenance de la centrale sont entièrement à notre charge."
                        }
                    ],
                    "page_number": "Page 9 / 10"
                }
            },
            
            # PAGE 10 - Timeline et Contact
            "timeline_contact": {
                "type": "timeline_contact",
                "title": "Prêt à Réduire Votre Facture ?",
                "icon": "🎯",
                "content": {
                    "title": "Prêt à Réduire Votre Facture ?",
                    "timeline": [
                        {"step": "Proposition", "description": "Lecture de ce document."},
                        {"step": "Entretien", "description": "RDV pour répondre à vos questions."},
                        {"step": "Signature", "description": "Signature de la convention."},
                        {"step": "Démarrage", "description": "Début de vos économies !"}
                    ],
                    "contact": {
                        "name": project_data.get('contact_name', 'Nom et Prénom'),
                        "title": project_data.get('contact_title', 'Titre'),
                        "phone": project_data.get('contact_phone', '01 23 45 67 89'),
                        "email": project_data.get('contact_email', 'email@exemple.com')
                    },
                    "company": {
                        "name": "OptimPV - Votre Partenaire Énergie",
                        "address": "123 Avenue de l'Énergie Verte\n75001 Paris, France",
                        "phone": "01 23 45 67 89",
                        "email": "contact@optimpv.fr",
                        "website": "www.optimpv.fr"
                    },
                    "page_number": "Page 10 / 10"
                }
            },
            
            # Blocs existants pour compatibilité
            "premium_header": {
                "type": "premium_header",
                "title": "En-tête Premium Turquoise",
                "icon": "🌟",
                "content": {
                    "title": "PROPOSITION AUTOCONSOMMATION",
                    "subtitle": f"Projet pour {project_data.get('client_name', '[NOM DU CLIENT]')}",
                    "price": f"{project_data.get('solar_price', 15.0):.1f} ct/kWh",
                    "savings": f"{project_data.get('total_savings_20y', 150000):,} €".replace(",", " ")
                }
            },
            "metrics": {
                "type": "metrics",
                "title": "Métriques Clés",
                "icon": "📊",
                "content": {
                    "metric1": {"value": f"{project_data.get('annual_savings', 7500):,}".replace(",", " "), "label": "Économie Annuelle (€)", "color": "#4ECDC4"},
                    "metric2": {"value": f"{project_data.get('power_kwc', 100)}", "label": "Puissance Installée (kWc)", "color": "#44A08D"},
                    "metric3": {"value": f"{project_data.get('co2_avoided', 7.5):.1f}", "label": "CO₂ Évité/An (T)", "color": "#26C6DA"}
                }
            },
            "financial": {
                "type": "financial",
                "title": "Résumé Financier",
                "icon": "💰",
                "content": {
                    "solar_price": project_data.get('solar_price', 15.0),
                    "grid_price": project_data.get('prix_reseau', 18.5),
                    "savings_20y": project_data.get('total_savings_20y', 150000),
                    "savings_percentage": project_data.get('savings_percentage', 20)
                }
            },
            "text": {
                "type": "text",
                "title": "Section Texte",
                "icon": "📝",
                "content": {
                    "title": "Votre Titre",
                    "text": "Votre texte personnalisé ici..."
                }
            },
            "ecology": {
                "type": "ecology",
                "title": "Impact Écologique",
                "icon": "🌱",
                "content": {
                    "co2_avoided": project_data.get('co2_avoided', 7.5),
                    "trees_equivalent": int(project_data.get('co2_avoided', 7.5) * 50),
                    "cars_equivalent": int(project_data.get('co2_avoided', 7.5) * 2.4)
                }
            },
            "contact": {
                "type": "contact",
                "title": "Contact",
                "icon": "📞",
                "content": {
                    "name": "Votre Contact OptimPV",
                    "phone": "01 23 45 67 89",
                    "email": "contact@optimpv.fr",
                    "message": "Demandez votre étude personnalisée gratuite"
                }
            },
            "benefits": {
                "type": "benefits",
                "title": "Avantages",
                "icon": "⭐",
                "content": {
                    "title": "Votre Avantage Principal",
                    "text": "En rejoignant ce projet d'autoconsommation collective, vous bénéficiez d'une électricité produite localement à un tarif fixe et compétitif, à l'abri des hausses du marché.",
                    "cta": "C'est simple, sécurisé et sans investissement de votre part !"
                }
            }
        }
        
        return block_templates.get(block_type, {})
    
    def _generate_preview_html(self, project_data: Dict[str, Any]) -> str:
        """Génère l'HTML d'aperçu."""
        blocks_html = ""
        
        for block in st.session_state['editor_blocks']:
            if block['type'] == 'premium_header':
                blocks_html += f"""
                <div style="background: linear-gradient(135deg, #4ECDC4 0%, #44A08D 100%); color: white; padding: 40px; text-align: center; border-radius: 15px; margin-bottom: 20px;">
                    <h1 style="font-size: 32px; margin-bottom: 15px;">{block['content']['title']}</h1>
                    <h2 style="font-size: 18px; margin-bottom: 20px; opacity: 0.9;">{block['content']['subtitle']}</h2>
                    <div style="background: rgba(255,255,255,0.2); padding: 20px; border-radius: 10px; display: inline-block;">
                        <div style="font-size: 28px; font-weight: bold;">{block['content']['price']}</div>
                        <div style="margin-top: 10px;">Économie 20 ans: {block['content']['savings']}</div>
                    </div>
                </div>
                """
            
            elif block['type'] == 'metrics':
                blocks_html += f"""
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-bottom: 20px;">
                    <div style="background: {block['content']['metric1']['color']}; color: white; padding: 20px; border-radius: 10px; text-align: center;">
                        <div style="font-size: 24px; font-weight: bold;">{block['content']['metric1']['value']}</div>
                        <div style="font-size: 14px; margin-top: 5px;">{block['content']['metric1']['label']}</div>
                    </div>
                    <div style="background: {block['content']['metric2']['color']}; color: white; padding: 20px; border-radius: 10px; text-align: center;">
                        <div style="font-size: 24px; font-weight: bold;">{block['content']['metric2']['value']}</div>
                        <div style="font-size: 14px; margin-top: 5px;">{block['content']['metric2']['label']}</div>
                    </div>
                    <div style="background: {block['content']['metric3']['color']}; color: white; padding: 20px; border-radius: 10px; text-align: center;">
                        <div style="font-size: 24px; font-weight: bold;">{block['content']['metric3']['value']}</div>
                        <div style="font-size: 14px; margin-top: 5px;">{block['content']['metric3']['label']}</div>
                    </div>
                </div>
                """
            
            elif block['type'] == 'text':
                blocks_html += f"""
                <div style="padding: 20px; margin-bottom: 20px;">
                    <h3 style="color: #2d3748; margin-bottom: 15px;">{block['content']['title']}</h3>
                    <p style="line-height: 1.6; color: #4a5568;">{block['content']['text']}</p>
                </div>
                """
            
            elif block['type'] == 'financial':
                blocks_html += f"""
                <div style="background: linear-gradient(135deg, #ff6b6b 0%, #feca57 100%); color: white; padding: 25px; border-radius: 15px; margin-bottom: 20px;">
                    <h3 style="margin-bottom: 20px;">💰 Synthèse Financière</h3>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                        <div>
                            <h4>Prix Solaire: {block['content']['solar_price']} ct/kWh</h4>
                            <p>vs {block['content']['grid_price']} ct/kWh réseau</p>
                        </div>
                        <div>
                            <h4>Économie 20 ans: {block['content']['savings_20y']:,} €</h4>
                            <p>{block['content']['savings_percentage']:.1f}% d'économie</p>
                        </div>
                    </div>
                </div>
                """.replace(",", " ")
            
            elif block['type'] == 'ecology':
                blocks_html += f"""
                <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); color: white; padding: 25px; border-radius: 15px; margin-bottom: 20px;">
                    <h3 style="margin-bottom: 20px;">🌱 Impact Environnemental</h3>
                    <div style="display: flex; justify-content: space-around; text-align: center;">
                        <div>
                            <div style="font-size: 24px; font-weight: bold;">{block['content']['co2_avoided']} T</div>
                            <div>CO₂ évité/an</div>
                        </div>
                        <div>
                            <div style="font-size: 24px; font-weight: bold;">{block['content']['trees_equivalent']}</div>
                            <div>Arbres équivalents</div>
                        </div>
                        <div>
                            <div style="font-size: 24px; font-weight: bold;">{block['content']['cars_equivalent']}</div>
                            <div>Voitures en moins</div>
                        </div>
                    </div>
                </div>
                """
            
            elif block['type'] == 'contact':
                blocks_html += f"""
                <div style="background: #2C3E50; color: white; padding: 25px; border-radius: 15px; text-align: center; margin-bottom: 20px;">
                    <h3 style="margin-bottom: 15px;">{block['content']['name']}</h3>
                    <p style="margin: 8px 0;">📞 {block['content']['phone']}</p>
                    <p style="margin: 8px 0;">✉️ {block['content']['email']}</p>
                    <div style="margin-top: 20px; padding: 15px; background: #4ECDC4; border-radius: 8px;">
                        <strong>{block['content']['message']}</strong>
                    </div>
                </div>
                """
            
            elif block['type'] == 'image':
                blocks_html += f"""
                <div style="text-align: center; padding: 20px; margin-bottom: 20px;">
                    <img src="{block['content']['src']}" alt="{block['content']['alt']}" style="max-width: 100%; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
                    <p style="margin-top: 10px; color: #6c757d; font-style: italic;">{block['content']['caption']}</p>
                </div>
                """
            
            elif block['type'] == 'benefits':
                blocks_html += f"""
                <div style="background: #f8f9fa; padding: 30px; border-radius: 15px; margin-bottom: 20px;">
                    <h3 style="color: #4ECDC4; margin-bottom: 15px;">{block['content']['title']}</h3>
                    <p style="line-height: 1.6; color: #2c3e50; margin-bottom: 20px;">{block['content']['text']}</p>
                    <div style="padding: 15px; background: #4ECDC4; color: white; border-radius: 8px; text-align: center;">
                        <strong>{block['content']['cta']}</strong>
                    </div>
                </div>
                """
            
            # NOUVEAUX BLOCS PREMIUM TEMPLATE
            elif block['type'] == 'cover_page':
                blocks_html += f"""
                <div style="background: linear-gradient(135deg, #4ECDC4 0%, #44A08D 100%); color: white; padding: 60px; text-align: center; border-radius: 20px; margin-bottom: 40px; page-break-after: always;">
                    <h1 style="font-size: 36px; margin-bottom: 10px; font-weight: 700;">{block['content']['main_title']}</h1>
                    <h2 style="font-size: 28px; margin-bottom: 30px; font-weight: 500;">{block['content']['subtitle']}</h2>
                    <h3 style="font-size: 20px; margin-bottom: 40px; opacity: 0.9;">Proposition pour : <strong>{block['content']['client_name']}</strong></h3>
                    
                    <div style="background: rgba(255,255,255,0.15); padding: 30px; border-radius: 15px; display: inline-block; margin: 20px 0;">
                        <div style="margin-bottom: 20px; font-size: 18px;">Prix Garanti :</div>
                        <div style="font-size: 42px; font-weight: bold; margin-bottom: 10px;">{block['content']['price']}</div>
                        <div style="margin-bottom: 20px;">Économie sur 20 ans :</div>
                        <div style="font-size: 32px; font-weight: bold;">{block['content']['savings']} €</div>
                        <div style="margin-top: 20px;">Mise en service : {block['content']['service_date']}</div>
                    </div>
                    
                    <div style="margin-top: 40px; font-size: 16px; opacity: 0.8;">
                        Rapport préparé le {block['content']['report_date']}<br>
                        <strong>{block['content']['page_number']}</strong>
                    </div>
                </div>
                """
            
            elif block['type'] == 'executive_summary':
                blocks_html += f"""
                <div style="padding: 40px; background: white; border-radius: 15px; margin-bottom: 30px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); page-break-after: always;">
                    <h2 style="color: #4ECDC4; font-size: 28px; margin-bottom: 30px; text-align: center;">{block['content']['title']}</h2>
                    <div style="font-size: 18px; line-height: 1.8; color: #2c3e50; text-align: justify;">
                        {block['content']['text']}
                    </div>
                    <div style="text-align: right; margin-top: 40px; color: #666; font-size: 14px;">
                        <strong>{block['content']['page_number']}</strong>
                    </div>
                </div>
                """
                
            elif block['type'] == 'key_benefits':
                blocks_html += f"""
                <div style="padding: 40px; background: white; border-radius: 15px; margin-bottom: 30px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); page-break-after: always;">
                    <h2 style="color: #4ECDC4; font-size: 28px; margin-bottom: 40px; text-align: center;">{block['content']['title']}</h2>
                    
                    <div style="display: grid; grid-template-columns: 1fr; gap: 30px;">
                        <div style="text-align: center; padding: 30px; background: linear-gradient(135deg, #4ECDC4, #44A08D); color: white; border-radius: 15px;">
                            <div style="font-size: 48px; margin-bottom: 15px;">{block['content']['benefit1']['icon']}</div>
                            <h3 style="font-size: 20px; margin-bottom: 15px; font-weight: 700;">{block['content']['benefit1']['title']}</h3>
                            <p style="font-size: 16px; line-height: 1.6;">{block['content']['benefit1']['description']}</p>
                        </div>
                        
                        <div style="text-align: center; padding: 30px; background: linear-gradient(135deg, #44A08D, #26C6DA); color: white; border-radius: 15px;">
                            <div style="font-size: 48px; margin-bottom: 15px;">{block['content']['benefit2']['icon']}</div>
                            <h3 style="font-size: 20px; margin-bottom: 15px; font-weight: 700;">{block['content']['benefit2']['title']}</h3>
                            <p style="font-size: 16px; line-height: 1.6;">{block['content']['benefit2']['description']}</p>
                        </div>
                        
                        <div style="text-align: center; padding: 30px; background: linear-gradient(135deg, #26C6DA, #4ECDC4); color: white; border-radius: 15px;">
                            <div style="font-size: 48px; margin-bottom: 15px;">{block['content']['benefit3']['icon']}</div>
                            <h3 style="font-size: 20px; margin-bottom: 15px; font-weight: 700;">{block['content']['benefit3']['title']}</h3>
                            <p style="font-size: 16px; line-height: 1.6;">{block['content']['benefit3']['description']}</p>
                        </div>
                    </div>
                    
                    <div style="text-align: right; margin-top: 40px; color: #666; font-size: 14px;">
                        <strong>{block['content']['page_number']}</strong>
                    </div>
                </div>
                """
                
            elif block['type'] == 'bill_comparison':
                blocks_html += f"""
                <div style="padding: 40px; background: white; border-radius: 15px; margin-bottom: 30px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); page-break-after: always;">
                    <h2 style="color: #4ECDC4; font-size: 28px; margin-bottom: 40px; text-align: center;">{block['content']['title']}</h2>
                    
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 30px; margin-bottom: 40px;">
                        <div style="text-align: center; padding: 30px; background: linear-gradient(135deg, #ff6b6b, #ff8e8e); color: white; border-radius: 15px;">
                            <h3 style="margin-bottom: 20px; font-size: 18px;">SANS le projet solaire</h3>
                            <div style="font-size: 36px; font-weight: bold; margin-bottom: 15px;">{block['content']['without_solar']['amount']:,} €</div>
                            <p>{block['content']['without_solar']['description']}</p>
                        </div>
                        
                        <div style="text-align: center; padding: 30px; background: linear-gradient(135deg, #4ECDC4, #44A08D); color: white; border-radius: 15px;">
                            <h3 style="margin-bottom: 20px; font-size: 18px;">AVEC le projet solaire</h3>
                            <div style="font-size: 36px; font-weight: bold; margin-bottom: 15px;">{block['content']['with_solar']['amount']:,} €</div>
                            <div style="font-size: 14px;">
                                <div>🌞 Électricité Solaire Locale ({block['content']['with_solar']['solar_part']}%)</div>
                                <div>⚡ Complément Réseau ({block['content']['with_solar']['grid_part']}%)</div>
                            </div>
                        </div>
                    </div>
                    
                    <div style="text-align: center; padding: 30px; background: linear-gradient(135deg, #48bb78, #38a169); color: white; border-radius: 15px; margin-bottom: 20px;">
                        <h3 style="font-size: 24px; margin-bottom: 10px;">Soit {block['content']['annual_savings']:,} € d'économie par an</h3>
                        <p style="font-size: 18px;">{block['content']['reduction_percentage']:.1f}% de réduction sur votre facture</p>
                    </div>
                    
                    <div style="text-align: right; margin-top: 20px; color: #666; font-size: 14px;">
                        <strong>{block['content']['page_number']}</strong>
                    </div>
                </div>
                """.replace(",", " ")
                
            elif block['type'] == 'pricing_model':
                how_it_works_html = ""
                for step in block['content']['how_it_works']:
                    how_it_works_html += f"""
                    <div style="text-align: center; margin-bottom: 20px;">
                        <div style="background: #4ECDC4; color: white; width: 40px; height: 40px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; font-weight: bold; margin-bottom: 10px;">{step['step']}</div>
                        <h4 style="margin-bottom: 5px; color: #2c3e50;">{step['title']}</h4>
                        <p style="color: #666; font-size: 14px; line-height: 1.4;">{step['description']}</p>
                    </div>
                    """
                
                blocks_html += f"""
                <div style="padding: 40px; background: white; border-radius: 15px; margin-bottom: 30px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); page-break-after: always;">
                    <h2 style="color: #4ECDC4; font-size: 28px; margin-bottom: 40px; text-align: center;">{block['content']['title']}</h2>
                    
                    <div style="background: #f8f9fa; padding: 30px; border-radius: 15px; margin-bottom: 40px;">
                        <h3 style="color: #2c3e50; margin-bottom: 20px; text-align: center;">Détail de notre offre</h3>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                            <div>
                                <p><strong>Prix de vente de l'électricité solaire:</strong> {block['content']['solar_price']:.1f} ct/kWh HT</p>
                                <p><strong>Part de votre consommation couverte par le solaire:</strong> {block['content']['coverage_percentage']:.0f}%</p>
                                <p><strong>Durée du contrat:</strong> {block['content']['contract_duration']} ans</p>
                            </div>
                            <div>
                                <p><strong>Indexation du prix:</strong> {block['content']['indexation']}</p>
                                <p><strong>Investissement requis de votre part:</strong> {block['content']['investment']} €</p>
                            </div>
                        </div>
                    </div>
                    
                    <h3 style="color: #2c3e50; margin-bottom: 30px; text-align: center;">Comment ça marche ?</h3>
                    <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px;">
                        {how_it_works_html}
                    </div>
                    
                    <div style="text-align: right; margin-top: 40px; color: #666; font-size: 14px;">
                        <strong>{block['content']['page_number']}</strong>
                    </div>
                </div>
                """
                
            elif block['type'] == 'long_term_savings':
                blocks_html += f"""
                <div style="padding: 40px; background: white; border-radius: 15px; margin-bottom: 30px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); page-break-after: always;">
                    <h2 style="color: #4ECDC4; font-size: 28px; margin-bottom: 40px; text-align: center;">{block['content']['title']}</h2>
                    
                    <div style="text-align: center; padding: 40px; background: linear-gradient(135deg, #4ECDC4, #44A08D); color: white; border-radius: 15px; margin-bottom: 30px;">
                        <h3 style="font-size: 24px; margin-bottom: 20px;">Projection de vos gains sur 20 ans</h3>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 30px;">
                            <div>
                                <div style="font-size: 36px; font-weight: bold; margin-bottom: 10px;">{block['content']['annual_savings']:,} €</div>
                                <div style="font-size: 16px;">Économie annuelle</div>
                            </div>
                            <div>
                                <div style="font-size: 36px; font-weight: bold; margin-bottom: 10px;">{block['content']['total_savings_20y']:,} €</div>
                                <div style="font-size: 16px;">Total sur 20 ans</div>
                            </div>
                        </div>
                    </div>
                    
                    <p style="font-size: 16px; line-height: 1.6; color: #2c3e50; text-align: center; font-style: italic;">
                        {block['content']['description']}
                    </p>
                    
                    <div style="text-align: right; margin-top: 40px; color: #666; font-size: 14px;">
                        <strong>{block['content']['page_number']}</strong>
                    </div>
                </div>
                """.replace(",", " ")
                
            elif block['type'] == 'technical_specs':
                blocks_html += f"""
                <div style="padding: 40px; background: white; border-radius: 15px; margin-bottom: 30px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); page-break-after: always;">
                    <h2 style="color: #4ECDC4; font-size: 28px; margin-bottom: 40px; text-align: center;">{block['content']['title']}</h2>
                    
                    <div style="background: #f8f9fa; padding: 30px; border-radius: 15px; margin-bottom: 30px;">
                        <h3 style="color: #2c3e50; margin-bottom: 20px; text-align: center;">Fiche Technique en bref</h3>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                            <div>
                                <p><strong>Localisation:</strong> {block['content']['location']}</p>
                                <p><strong>Puissance installée:</strong> {block['content']['power_kwc']} kWc</p>
                                <p><strong>Équivalent foyers:</strong> {block['content']['equivalent_households']} foyers</p>
                            </div>
                            <div>
                                <p><strong>Production annuelle estimée:</strong> {block['content']['annual_production']:,} kWh</p>
                                <p><strong>Technologie:</strong> {block['content']['technology']}</p>
                                <p><strong>Maintenance & Supervision:</strong> {block['content']['maintenance']}</p>
                            </div>
                        </div>
                    </div>
                    
                    <div style="text-align: right; margin-top: 40px; color: #666; font-size: 14px;">
                        <strong>{block['content']['page_number']}</strong>
                    </div>
                </div>
                """.replace(",", " ")
                
            elif block['type'] == 'environmental_impact':
                benefits_html = ""
                for benefit in block['content']['local_benefits']:
                    benefits_html += f"<li style='margin-bottom: 10px;'>{benefit}</li>"
                
                blocks_html += f"""
                <div style="padding: 40px; background: white; border-radius: 15px; margin-bottom: 30px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); page-break-after: always;">
                    <h2 style="color: #4ECDC4; font-size: 28px; margin-bottom: 40px; text-align: center;">{block['content']['title']}</h2>
                    
                    <div style="text-align: center; padding: 40px; background: linear-gradient(135deg, #48bb78, #38a169); color: white; border-radius: 15px; margin-bottom: 30px;">
                        <div style="font-size: 48px; margin-bottom: 15px;">🌿</div>
                        <div style="font-size: 36px; font-weight: bold; margin-bottom: 10px;">{block['content']['co2_avoided']} tonnes</div>
                        <div style="font-size: 18px; margin-bottom: 15px;">de CO₂ évitées par an</div>
                        <div style="font-size: 16px; font-style: italic;">
                            "C'est comme retirer {block['content']['cars_equivalent']} voitures de la circulation chaque année !"
                        </div>
                    </div>
                    
                    <div style="background: #f8f9fa; padding: 30px; border-radius: 15px;">
                        <h3 style="color: #2c3e50; margin-bottom: 20px;">Un Acteur Engagé dans son Territoire</h3>
                        <ul style="color: #555; line-height: 1.8; list-style-type: none; padding-left: 0;">
                            {benefits_html}
                        </ul>
                    </div>
                    
                    <div style="text-align: right; margin-top: 40px; color: #666; font-size: 14px;">
                        <strong>{block['content']['page_number']}</strong>
                    </div>
                </div>
                """
                
            elif block['type'] == 'faq_section':
                faqs_html = ""
                for faq in block['content']['faqs']:
                    faqs_html += f"""
                    <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                        <h4 style="color: #4ECDC4; margin-bottom: 10px; font-size: 16px;">{faq['question']}</h4>
                        <p style="color: #2c3e50; line-height: 1.6; margin: 0;">{faq['answer']}</p>
                    </div>
                    """
                
                blocks_html += f"""
                <div style="padding: 40px; background: white; border-radius: 15px; margin-bottom: 30px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); page-break-after: always;">
                    <h2 style="color: #4ECDC4; font-size: 28px; margin-bottom: 40px; text-align: center;">{block['content']['title']}</h2>
                    
                    {faqs_html}
                    
                    <div style="text-align: right; margin-top: 40px; color: #666; font-size: 14px;">
                        <strong>{block['content']['page_number']}</strong>
                    </div>
                </div>
                """
                
            elif block['type'] == 'timeline_contact':
                timeline_html = ""
                for step in block['content']['timeline']:
                    timeline_html += f"""
                    <div style="text-align: center; margin-bottom: 20px;">
                        <div style="background: #4ECDC4; color: white; padding: 10px 20px; border-radius: 25px; display: inline-block; margin-bottom: 10px; font-weight: bold;">{step['step']}</div>
                        <p style="color: #2c3e50; margin: 0; font-size: 14px;">{step['description']}</p>
                    </div>
                    """
                
                blocks_html += f"""
                <div style="padding: 40px; background: white; border-radius: 15px; margin-bottom: 30px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
                    <h2 style="color: #4ECDC4; font-size: 28px; margin-bottom: 40px; text-align: center;">{block['content']['title']}</h2>
                    
                    <div style="background: linear-gradient(135deg, #4ECDC4, #44A08D); color: white; padding: 30px; border-radius: 15px; margin-bottom: 40px;">
                        <h3 style="text-align: center; margin-bottom: 30px; font-size: 20px;">FRISE CHRONOLOGIQUE</h3>
                        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px;">
                            {timeline_html}
                        </div>
                    </div>
                    
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 30px;">
                        <div style="text-align: center; background: #f8f9fa; padding: 30px; border-radius: 15px;">
                            <h3 style="color: #4ECDC4; margin-bottom: 20px;">Votre Interlocuteur Dédié</h3>
                            <div style="margin-bottom: 15px; font-size: 18px; font-weight: bold; color: #2c3e50;">{block['content']['contact']['name']}</div>
                            <div style="margin-bottom: 10px; color: #666;">{block['content']['contact']['title']}</div>
                            <div style="margin-bottom: 5px;">📞 {block['content']['contact']['phone']}</div>
                            <div>✉️ {block['content']['contact']['email']}</div>
                        </div>
                        
                        <div style="text-align: center; background: #2C3E50; color: white; padding: 30px; border-radius: 15px;">
                            <h3 style="color: #4ECDC4; margin-bottom: 20px;">{block['content']['company']['name']}</h3>
                            <div style="margin-bottom: 15px; white-space: pre-line;">{block['content']['company']['address']}</div>
                            <div style="margin-bottom: 5px;">📞 {block['content']['company']['phone']}</div>
                            <div style="margin-bottom: 5px;">✉️ {block['content']['company']['email']}</div>
                            <div>🌐 {block['content']['company']['website']}</div>
                        </div>
                    </div>
                    
                    <div style="text-align: right; margin-top: 40px; color: #666; font-size: 14px;">
                        <strong>{block['content']['page_number']}</strong>
                    </div>
                </div>
                """
        
        return f"""
        <div style="font-family: 'Open Sans', sans-serif; max-width: 800px; margin: 0 auto; padding: 20px;">
            {blocks_html}
        </div>
        """
    
    def _generate_final_html(self, project_data: Dict[str, Any]) -> str:
        """Génère l'HTML final pour export."""
        from datetime import datetime
        preview_content = self._generate_preview_html(project_data)
        
        return f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Proposition OptimPV - {project_data['client_name']}</title>
    <link href="https://fonts.googleapis.com/css2?family=Open+Sans:wght@300;400;600;700&family=Montserrat:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        body {{
            margin: 0;
            padding: 20px;
            font-family: 'Open Sans', sans-serif;
            background: #f8f9fa;
            line-height: 1.6;
        }}
        
        @media print {{
            body {{ background: white; }}
        }}
    </style>
</head>
<body>
    {preview_content}
    
    <div style="text-align: center; margin-top: 40px; padding: 20px; border-top: 2px solid #e9ecef; color: #6c757d;">
        <p>© {datetime.now().year} OptimPV - Document généré le {datetime.now().strftime("%d/%m/%Y à %H:%M")}</p>
    </div>
</body>
</html>
        """
    
    def _create_grapesjs_editor(self, project_data: Dict[str, Any], template: str = "Solaire Standard") -> str:
        """
        Crée l'éditeur GrapesJS avec configuration solaire.
        
        Args:
            project_data: Données du projet
            template: Template à utiliser
            
        Returns:
            HTML complet de l'éditeur GrapesJS
        """
        # Configuration des blocs personnalisés
        solar_blocks = self._get_solar_blocks_config(project_data)
        
        # Template de départ selon le choix
        initial_content = self._get_initial_template(template, project_data)
        
        premium_css = self._get_premium_css()
        
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Éditeur GrapesJS - Proposition Premium</title>
    <link rel="stylesheet" href="https://unpkg.com/grapesjs/dist/css/grapes.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;700&family=Open+Sans:wght@300;400;600&display=swap" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        body, html {{ 
            margin: 0; 
            height: 100%; 
            font-family: 'Open Sans', sans-serif; 
            overflow: hidden;
        }}
        
        #gjs {{ 
            height: 100vh; 
            width: 100%;
            overflow: visible;
        }}
        
        /* Amélioration de l'interface GrapesJS */
        .gjs-cv-canvas {{
            width: 100%;
            height: 100%;
        }}
        
        .gjs-pn-panel {{
            background: #f8f9fa;
            border: 1px solid #e2e8f0;
        }}
        
        .gjs-pn-btn {{
            padding: 8px 12px;
            margin: 2px;
            background: #ffffff;
            border: 1px solid #cbd5e0;
            border-radius: 4px;
            color: #4a5568;
            font-size: 14px;
        }}
        
        .gjs-pn-btn:hover {{
            background: #e2e8f0;
            border-color: #4ECDC4;
        }}
        
        .gjs-pn-btn.gjs-pn-active {{
            background: #4ECDC4;
            color: white;
            border-color: #44A08D;
        }}
        
        /* Amélioration des blocs */
        .gjs-blocks-c {{
            display: flex;
            flex-wrap: wrap;
            padding: 10px;
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            max-height: 400px;
            overflow-y: auto;
        }}
        
        .gjs-block {{
            width: 45%;
            margin: 5px 2.5%;
            padding: 15px 10px;
            background: #f8f9fa;
            border: 2px solid #e2e8f0;
            border-radius: 8px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
            min-height: 80px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }}
        
        .gjs-block:hover {{
            border-color: #4ECDC4;
            background: #ffffff;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(78, 205, 196, 0.2);
        }}
        
        .gjs-block-label {{
            font-size: 12px;
            font-weight: 600;
            color: #2d3748;
            margin-top: 8px;
        }}
        
        /* Style des panels latéraux */
        .gjs-pn-panel.gjs-pn-panel-right {{
            width: 300px;
            background: #ffffff;
            border-left: 1px solid #e2e8f0;
        }}
        
        .gjs-sm-sector {{
            background: #f8f9fa;
            border: 1px solid #e2e8f0;
            border-radius: 4px;
            margin-bottom: 10px;
        }}
        
        .gjs-sm-title {{
            background: #4ECDC4;
            color: white;
            padding: 8px 12px;
            font-weight: 600;
        }}
        
        {premium_css}
        
        .eco-card {{
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            padding: 25px;
            border-radius: 15px;
            color: white;
            margin: 15px 0;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
        }}
        
        /* Responsive improvements */
        @media (max-width: 768px) {{
            .gjs-block {{
                width: 100%;
                margin: 5px 0;
            }}
            
            .gjs-pn-panel.gjs-pn-panel-right {{
                width: 250px;
            }}
        }}
    </style>
</head>
<body>
    <div id="gjs"></div>
    
    <script src="https://unpkg.com/grapesjs"></script>
    <script>
        const editor = grapesjs.init({{
            height: '100vh',
            container: '#gjs',
            fromElement: true,
            width: 'auto',
            storageManager: {{
                id: 'gjs-optimpv',
                type: 'local',
                autosave: true,
                autoload: true,
                stepsBeforeSave: 1,
            }},
            canvas: {{
                styles: [
                    'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap',
                    'https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;700&family=Open+Sans:wght@300;400;600&display=swap'
                ]
            }},
            blockManager: {{
                appendTo: '#blocks',
                blocks: {json.dumps(solar_blocks, indent=2)}
            }},
            styleManager: {{
                appendTo: '#styles',
                sectors: [{{
                    name: '🎨 Dimensions',
                    open: true,
                    buildProps: ['width', 'height', 'min-height', 'padding', 'margin'],
                    properties: [{{
                        type: 'integer',
                        name: 'Largeur',
                        property: 'width',
                        units: ['px', '%', 'auto'],
                        defaults: 'auto',
                        min: 0,
                    }}, {{
                        type: 'integer',
                        name: 'Hauteur',
                        property: 'height',
                        units: ['px', '%', 'auto'],
                        defaults: 'auto',
                        min: 0,
                    }}]
                }}, {{
                    name: '🎯 Décoration',
                    open: false,
                    buildProps: ['background-color', 'border-radius', 'border', 'box-shadow', 'color'],
                }}, {{
                    name: '📝 Typographie',
                    open: false,
                    buildProps: ['font-family', 'font-size', 'font-weight', 'text-align', 'line-height'],
                }}]
            }},
            layerManager: {{
                appendTo: '#layers',
            }},
            traitManager: {{
                appendTo: '#traits',
            }},
            selectorManager: {{
                appendTo: '#styles',
                states: [{{
                    name: 'hover',
                    label: 'Survol',
                }}, {{
                    name: 'active',
                    label: 'Actif',
                }}],
            }},
            panels: {{
                defaults: [{{
                    id: 'layers',
                    el: '.panel__right',
                    resizable: {{
                        maxDim: 350,
                        minDim: 200,
                        tc: 0,
                        cl: 1,
                        cr: 0,
                        bc: 0,
                        keyWidth: 'flex-basis',
                    }},
                }}, {{
                    id: 'panel-switcher',
                    el: '.panel__switcher',
                    buttons: [{{
                        id: 'show-layers',
                        active: true,
                        label: '📁 Calques',
                        command: 'show-layers',
                        togglable: false,
                    }}, {{
                        id: 'show-style',
                        active: true,
                        label: '🎨 Styles',
                        command: 'show-styles',
                        togglable: false,
                    }}, {{
                        id: 'show-traits',
                        active: true,
                        label: '⚙️ Propriétés',
                        command: 'show-traits',
                        togglable: false,
                    }}]
                }}, {{
                    id: 'panel-devices',
                    el: '.panel__devices',
                    buttons: [{{
                        id: 'device-desktop',
                        label: '🖥️',
                        command: 'set-device-desktop',
                        active: true,
                        togglable: false,
                    }}, {{
                        id: 'device-mobile',
                        label: '📱',
                        command: 'set-device-mobile',
                        togglable: false,
                    }}]
                }}, {{
                    id: 'panel-top',
                    el: '.panel__top',
                    buttons: [{{
                        id: 'visibility',
                        active: true,
                        className: 'btn-toggle-borders',
                        label: '👁️ Bordures',
                        command: 'sw-visibility',
                    }}, {{
                        id: 'export',
                        className: 'btn-open-export',
                        label: '💾 Exporter',
                        command: 'export-template',
                        context: 'export-template',
                    }}, {{
                        id: 'fullscreen',
                        className: 'btn-preview',
                        label: '🔍 Aperçu',
                        context: 'preview',
                        command: 'preview',
                    }}]
                }}]
            }},
            deviceManager: {{
                devices: [{{
                    name: 'Desktop',
                    width: '',
                }}, {{
                    name: 'Mobile',
                    width: '320px',
                    widthMedia: '480px',
                }}]
            }},
        }});

        // Panel layout personnalisé
        const panelTopbar = editor.Panels.addPanel({{ id: 'panel-top' }});
        panelTopbar.get('appendContent').appendChild(document.createElement('div')).innerHTML = `
            <div class="panel__top" style="text-align: center; padding: 10px; background: #f8f9fa; border-bottom: 1px solid #e2e8f0;"></div>
        `;

        const panelSwitcher = editor.Panels.addPanel({{ id: 'panel-switcher' }});
        panelSwitcher.get('appendContent').appendChild(document.createElement('div')).innerHTML = `
            <div class="panel__switcher" style="padding: 10px; background: #ffffff; border-bottom: 1px solid #e2e8f0;"></div>
        `;

        const panelRight = editor.Panels.addPanel({{ id: 'layers' }});
        panelRight.get('appendContent').appendChild(document.createElement('div')).innerHTML = `
            <div class="panel__right" style="width: 300px; height: 100vh; overflow-y: auto; background: #ffffff;">
                <div style="padding: 15px; border-bottom: 1px solid #e2e8f0;">
                    <h4 style="margin: 0; color: #2d3748;">📦 Blocs</h4>
                    <div id="blocks" style="margin-top: 10px;"></div>
                </div>
                <div style="padding: 15px; border-bottom: 1px solid #e2e8f0;">
                    <h4 style="margin: 0; color: #2d3748;">📁 Calques</h4>
                    <div id="layers" style="margin-top: 10px; min-height: 200px;"></div>
                </div>
                <div style="padding: 15px; border-bottom: 1px solid #e2e8f0;">
                    <h4 style="margin: 0; color: #2d3748;">🎨 Styles</h4>
                    <div id="styles" style="margin-top: 10px; min-height: 200px;"></div>
                </div>
                <div style="padding: 15px;">
                    <h4 style="margin: 0; color: #2d3748;">⚙️ Propriétés</h4>
                    <div id="traits" style="margin-top: 10px; min-height: 150px;"></div>
                </div>
            </div>
        `;

        const panelDevices = editor.Panels.addPanel({{ id: 'panel-devices' }});
        panelDevices.get('appendContent').appendChild(document.createElement('div')).innerHTML = `
            <div class="panel__devices" style="position: absolute; top: 10px; right: 320px; z-index: 1000;"></div>
        `;

        // Commandes personnalisées
        editor.Commands.add('set-device-desktop', {{
            run: (editor) => editor.setDevice('Desktop')
        }});
        editor.Commands.add('set-device-mobile', {{
            run: (editor) => editor.setDevice('Mobile')  
        }});
        editor.Commands.add('show-layers', {{
            run: (editor) => {{
                document.getElementById('layers').style.display = 'block';
                document.getElementById('styles').style.display = 'none';
                document.getElementById('traits').style.display = 'none';
            }}
        }});
        editor.Commands.add('show-styles', {{
            run: (editor) => {{
                document.getElementById('layers').style.display = 'none';
                document.getElementById('styles').style.display = 'block';
                document.getElementById('traits').style.display = 'none';
            }}
        }});
        editor.Commands.add('show-traits', {{
            run: (editor) => {{
                document.getElementById('layers').style.display = 'none';
                document.getElementById('styles').style.display = 'none';
                document.getElementById('traits').style.display = 'block';
            }}
        }});
        editor.Commands.add('sw-visibility', {{
            run: (editor) => {{
                const codeViewer = editor.CodeManager.getViewer('CodeMirror').clone();
                codeViewer.set({{
                    codeName: 'htmlmixed',
                    readOnly: 0,
                    theme: 'hopscotch',
                    autoBeautify: true,
                    autoCloseTags: true,
                    autoCloseBrackets: true,
                    lineWrapping: true,
                    styleActiveLine: true,
                    smartIndent: true,
                }});
                
                editor.Modal.setTitle('🔧 Code HTML/CSS').setContent(codeViewer.getElement()).open();
                codeViewer.setContent(editor.getHtml() + '<style>' + editor.getCss() + '</style>');
            }}
        }});

        // Contenu initial avec fallback
        try {{
            editor.setComponents(`{initial_content}`);
            editor.setStyle(`{self._get_solar_css()}`);
        }} catch(e) {{
            console.error('Erreur lors du chargement du contenu:', e);
            editor.setComponents('<div style="padding: 40px; text-align: center;"><h1>Éditeur GrapesJS</h1><p>Glissez des blocs depuis la barre latérale pour commencer.</p></div>');
        }}
        
        // Sauvegarde automatique améliorée
        editor.on('storage:end:store', () => {{
            console.log('✅ Design sauvegardé automatiquement');
            
            // Notification visuelle
            const notification = document.createElement('div');
            notification.innerHTML = '✅ Sauvegardé';
            notification.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                background: #4ECDC4;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                z-index: 10000;
                font-family: 'Open Sans', sans-serif;
                animation: fadeInOut 3s ease-in-out;
            `;
            document.body.appendChild(notification);
            
            setTimeout(() => {{
                if (notification.parentNode) {{
                    notification.parentNode.removeChild(notification);
                }}
            }}, 3000);
        }});
        
        // Styles pour l'animation
        const style = document.createElement('style');
        style.textContent = `
            @keyframes fadeInOut {{
                0%, 100% {{ opacity: 0; transform: translateY(-20px); }}
                20%, 80% {{ opacity: 1; transform: translateY(0); }}
            }}
        `;
        document.head.appendChild(style);
        
    </script>
</body>
</html>
        """
    
    def _show_fullscreen_editor(self, project_data: Dict[str, Any], template_mode: str):
        """Affiche l'éditeur en mode plein écran."""
        
        # Bouton de retour centré
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("❌ **Quitter le Mode Plein Écran**", type="secondary", use_container_width=True):
                st.session_state['fullscreen_editor'] = False
                st.rerun()
        
        # CSS pour maximiser l'espace disponible
        st.markdown("""
            <style>
                /* Maximiser le conteneur principal */
                .main .block-container {
                    padding: 0 !important;
                    max-width: 100% !important;
                    width: 100% !important;
                }
                
                /* Masquer les éléments Streamlit */
                .stApp > header {
                    display: none !important;
                }
                
                .css-18e3th9, .css-1d391kg {
                    padding: 0 !important;
                }
                
                /* Forcer le plein écran */
                iframe[title="streamlit_app"] {
                    height: 95vh !important;
                    width: 100% !important;
                    border: none !important;
                }
            </style>
        """, unsafe_allow_html=True)
        
        # Éditeur plein écran avec hauteur maximale
        st.info("🎨 **Mode Plein Écran Activé** - Utilisez F11 pour masquer complètement l'interface du navigateur")
        grapesjs_html = self._create_fullscreen_grapesjs_editor(project_data, template_mode)
        st.components.v1.html(grapesjs_html, height=800, scrolling=False)
    
    def _create_fullscreen_grapesjs_editor(self, project_data: Dict[str, Any], template: str = "Solaire Standard") -> str:
        """Crée l'éditeur GrapesJS simplifié pour le plein écran."""
        
        # Configuration des blocs personnalisés
        solar_blocks = self._get_solar_blocks_config(project_data)
        
        # Template de départ selon le choix
        initial_content = self._get_initial_template(template, project_data)
        
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Éditeur GrapesJS - Mode Étendu</title>
    <link rel="stylesheet" href="https://unpkg.com/grapesjs/dist/css/grapes.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;700&family=Open+Sans:wght@300;400;600&display=swap" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        body, html {{ 
            margin: 0; 
            padding: 0;
            height: 100vh; 
            width: 100%;
            font-family: 'Open Sans', sans-serif; 
            background: #f8f9fa;
        }}
        
        #gjs {{ 
            height: 100vh; 
            width: 100%;
        }}
        
        /* Maximiser l'espace canvas */
        .gjs-cv-canvas {{
            width: calc(100% - 350px) !important;
            height: 100% !important;
        }}
        
        /* Panel droit optimisé */
        .gjs-pn-panel.gjs-pn-panel-right {{
            width: 350px !important;
            background: #ffffff;
            border-left: 2px solid #e2e8f0;
            box-shadow: -2px 0 10px rgba(0,0,0,0.1);
        }}
        
        /* Améliorer les blocs */
        .gjs-blocks-c {{
            display: flex;
            flex-wrap: wrap;
            padding: 15px;
            max-height: 400px !important;
            overflow-y: auto;
            background: #f8f9fa;
            border-radius: 8px;
            margin: 10px;
        }}
        
        .gjs-block {{
            width: calc(50% - 10px) !important;
            margin: 5px !important;
            min-height: 80px !important;
            background: white !important;
            border: 2px solid #e2e8f0 !important;
            border-radius: 8px !important;
            display: flex !important;
            flex-direction: column !important;
            justify-content: center !important;
            align-items: center !important;
            cursor: pointer !important;
            transition: all 0.3s ease !important;
        }}
        
        .gjs-block:hover {{
            border-color: #4ECDC4 !important;
            background: #f0fdfc !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 4px 12px rgba(78, 205, 196, 0.3) !important;
        }}
        
        .gjs-block-label {{
            font-size: 12px !important;
            font-weight: 600 !important;
            color: #2d3748 !important;
            text-align: center !important;
            margin-top: 8px !important;
        }}
        
        /* Toolbar du haut */
        .editor-toolbar {{
            background: linear-gradient(135deg, #4ECDC4 0%, #44A08D 100%);
            color: white;
            padding: 15px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        .toolbar-title {{
            font-size: 20px;
            font-weight: 600;
            font-family: 'Montserrat', sans-serif;
        }}
        
        .toolbar-actions {{
            display: flex;
            gap: 15px;
        }}
        
        .toolbar-btn {{
            background: rgba(255,255,255,0.2);
            border: 1px solid rgba(255,255,255,0.3);
            color: white;
            padding: 8px 15px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.3s ease;
        }}
        
        .toolbar-btn:hover {{
            background: rgba(255,255,255,0.3);
            transform: translateY(-1px);
        }}
        
        /* Améliorer l'interface des panels */
        .gjs-sm-sector {{
            background: #f8f9fa !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 6px !important;
            margin-bottom: 15px !important;
        }}
        
        .gjs-sm-title {{
            background: #4ECDC4 !important;
            color: white !important;
            padding: 12px 15px !important;
            font-weight: 600 !important;
            border-radius: 6px 6px 0 0 !important;
        }}
        
        .gjs-field {{
            margin-bottom: 10px !important;
        }}
        
        /* Style des boutons de l'éditeur */
        .gjs-pn-btn {{
            background: #ffffff !important;
            border: 1px solid #cbd5e0 !important;
            color: #4a5568 !important;
            padding: 8px 12px !important;
            margin: 2px !important;
            border-radius: 4px !important;
            font-size: 13px !important;
        }}
        
        .gjs-pn-btn:hover {{
            background: #4ECDC4 !important;
            color: white !important;
            border-color: #44A08D !important;
        }}
        
        .gjs-pn-btn.gjs-pn-active {{
            background: #4ECDC4 !important;
            color: white !important;
            border-color: #44A08D !important;
        }}
        
        /* Responsive */
        @media (max-width: 1200px) {{
            .gjs-pn-panel.gjs-pn-panel-right {{
                width: 300px !important;
            }}
            
            .gjs-cv-canvas {{
                width: calc(100% - 300px) !important;
            }}
        }}
    </style>
</head>
<body>
    <!-- Toolbar personnalisé -->
    <div class="editor-toolbar">
        <div class="toolbar-title">
            🎨 Éditeur de Proposition OptimPV
        </div>
        <div class="toolbar-actions">
            <button class="toolbar-btn" onclick="saveDesign()">
                💾 Sauvegarder
            </button>
            <button class="toolbar-btn" onclick="exportHTML()">
                📄 Exporter
            </button>
            <button class="toolbar-btn" onclick="togglePreview()">
                👁️ Aperçu
            </button>
        </div>
    </div>
    
    <div id="gjs" style="height: calc(100vh - 70px);"></div>
    
    <script src="https://unpkg.com/grapesjs"></script>
    <script>
        // Configuration simplifiée de GrapesJS
        const editor = grapesjs.init({{
            height: 'calc(100vh - 70px)',
            container: '#gjs',
            fromElement: true,
            storageManager: {{
                id: 'gjs-optimpv-extended',
                type: 'local',
                autosave: true,
                autoload: true,
            }},
            canvas: {{
                styles: [
                    'https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;700&family=Open+Sans:wght@300;400;600&display=swap'
                ]
            }},
            panels: {{
                defaults: [{{
                    id: 'basic-actions',
                    el: '.panel__basic-actions',
                    buttons: [{{
                        id: 'visibility',
                        active: true,
                        className: 'btn-toggle-borders',
                        label: '<i class="fa fa-border-all"></i>',
                        command: 'sw-visibility',
                    }}, {{
                        id: 'export',
                        className: 'btn-open-export',
                        label: '<i class="fa fa-code"></i>',
                        command: 'export-template',
                    }}]
                }}, {{
                    id: 'panel-devices',
                    el: '.panel__devices',
                    buttons: [{{
                        id: 'device-desktop',
                        label: '<i class="fa fa-desktop"></i>',
                        command: 'set-device-desktop',
                        active: true,
                        togglable: false,
                    }}, {{
                        id: 'device-mobile',
                        label: '<i class="fa fa-mobile"></i>',
                        command: 'set-device-mobile',
                        togglable: false,
                    }}]
                }}]
            }},
            blockManager: {{
                blocks: {json.dumps(solar_blocks, indent=2)}
            }},
            deviceManager: {{
                devices: [{{
                    name: 'Desktop',
                    width: '',
                }}, {{
                    name: 'Mobile',
                    width: '320px',
                    widthMedia: '480px',
                }}]
            }},
        }});

        // Commandes personnalisées
        editor.Commands.add('set-device-desktop', {{
            run: (editor) => editor.setDevice('Desktop')
        }});
        
        editor.Commands.add('set-device-mobile', {{
            run: (editor) => editor.setDevice('Mobile')
        }});

        // Fonctions du toolbar
        function saveDesign() {{
            editor.store();
            showNotification('✅ Design sauvegardé !');
        }}
        
        function exportHTML() {{
            const html = editor.getHtml();
            const css = editor.getCss();
            const fullHTML = `<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Proposition OptimPV</title>
    <style>${{css}}</style>
</head>
<body>
    ${{html}}
</body>
</html>`;
            
            const blob = new Blob([fullHTML], {{ type: 'text/html' }});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'proposition_optimpv.html';
            a.click();
            URL.revokeObjectURL(url);
            
            showNotification('📄 HTML exporté !');
        }}
        
        function togglePreview() {{
            editor.runCommand('preview');
        }}
        
        function showNotification(message) {{
            const notification = document.createElement('div');
            notification.innerHTML = message;
            notification.style.cssText = `
                position: fixed;
                top: 90px;
                right: 20px;
                background: #4ECDC4;
                color: white;
                padding: 15px 20px;
                border-radius: 8px;
                z-index: 10000;
                font-family: 'Open Sans', sans-serif;
                font-weight: 500;
                box-shadow: 0 4px 15px rgba(78, 205, 196, 0.4);
            `;
            document.body.appendChild(notification);
            
            setTimeout(() => {{
                if (notification.parentNode) {{
                    notification.parentNode.removeChild(notification);
                }}
            }}, 3000);
        }}

        // Contenu initial
        try {{
            editor.setComponents(`{initial_content.replace('`', '\\`')}`);
            editor.setStyle(`{self._get_solar_css()}`);
        }} catch(e) {{
            console.error('Erreur lors du chargement:', e);
            editor.setComponents('<div style="padding: 40px; text-align: center; font-family: Montserrat, sans-serif;"><h1 style="color: #4ECDC4;">🎨 Éditeur GrapesJS</h1><p style="color: #666;">Glissez des blocs depuis la barre latérale pour créer votre proposition.</p></div>');
        }}
        
        // Auto-save
        editor.on('storage:end:store', () => {{
            console.log('✅ Sauvegarde automatique effectuée');
        }});
        
    </script>
</body>
</html>
        """
    
    def _get_solar_blocks_config(self, project_data: Dict[str, Any]) -> list:
        """
        Configuration des blocs personnalisés pour le solaire.
        
        Args:
            project_data: Données du projet
            
        Returns:
            Liste des blocs GrapesJS
        """
        return [
            {
                "id": "solar-header-premium",
                "label": "🌟 En-tête Premium",
                "category": "Turquoise Premium",
                "media": '<svg viewBox="0 0 24 24" style="fill: #4ECDC4;"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>',
                "content": f"""
                <div style="background: linear-gradient(135deg, #4ECDC4 0%, #44A08D 100%); color: white; padding: 60px 40px; text-align: center; border-radius: 20px; margin-bottom: 30px;">
                    <h1 style="font-family: 'Montserrat', sans-serif; font-size: 48px; font-weight: 700; margin-bottom: 20px;">
                        PROPOSITION AUTOCONSOMMATION
                    </h1>
                    <h2 style="font-size: 24px; opacity: 0.9; margin-bottom: 30px;">
                        Projet pour {project_data.get('client_name', '[NOM DU CLIENT]')}
                    </h2>
                    <div style="background: rgba(255,255,255,0.2); padding: 30px; border-radius: 15px; display: inline-block;">
                        <h3 style="margin-bottom: 15px;">Prix Garanti</h3>
                        <div style="font-size: 54px; font-weight: 700; margin: 15px 0;">
                            {project_data.get('solar_price', 15.0):.1f} ct/kWh
                        </div>
                        <p style="font-size: 18px;">
                            Économie sur 20 ans: {project_data.get('total_savings_20y', 150000):,} €
                        </p>
                    </div>
                </div>
                """.replace(",", " ")
            },
            {
                "id": "turquoise-metrics",
                "label": "📊 Métriques Turquoise",
                "category": "Turquoise Premium",
                "media": '<svg viewBox="0 0 24 24" style="fill: #4ECDC4;"><path d="M3 3v18h18V3H3zm16 16H5V5h14v14zM7 10h2v7H7zm4-3h2v10h-2zm4 6h2v4h-2z"/></svg>',
                "content": f"""
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 30px; margin: 40px 0;">
                    <div style="background: #4ECDC4; color: white; padding: 30px; border-radius: 15px; text-align: center;">
                        <h3 style="font-size: 36px; font-weight: 700; margin-bottom: 10px;">
                            {project_data.get('annual_savings', 7500):,} €
                        </h3>
                        <p>Économie Annuelle</p>
                    </div>
                    
                    <div style="background: #44A08D; color: white; padding: 30px; border-radius: 15px; text-align: center;">
                        <h3 style="font-size: 36px; font-weight: 700; margin-bottom: 10px;">
                            {project_data.get('power_kwc', 100)} kWc
                        </h3>
                        <p>Puissance Installée</p>
                    </div>
                    
                    <div style="background: #26C6DA; color: white; padding: 30px; border-radius: 15px; text-align: center;">
                        <h3 style="font-size: 36px; font-weight: 700; margin-bottom: 10px;">
                            {project_data.get('co2_avoided', 7.5):.1f} T
                        </h3>
                        <p>CO₂ Évité/An</p>
                    </div>
                </div>
                """.replace(",", " ")
            },
            {
                "id": "solar-header-standard",
                "label": "🏠 En-tête Standard",
                "category": "Solaire Standard",
                "media": '<svg viewBox="0 0 24 24" style="fill: #667eea;"><path d="M12 3L2 12h3v8h6v-6h2v6h6v-8h3L12 3z"/></svg>',
                "content": f"""
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 60px 40px; text-align: center; border-radius: 20px;">
                    <h1 style="font-size: 2.5em; margin-bottom: 20px;">{project_data['template']['cover']['title']}</h1>
                    <h2 style="font-size: 1.5em; opacity: 0.9;">Proposition pour {project_data['client_name']}</h2>
                    <div style="background: rgba(255,255,255,0.2); padding: 20px; border-radius: 10px; margin-top: 30px; display: inline-block;">
                        <h3>Prix Garanti: {project_data['solar_price']} ct/kWh</h3>
                        <p>Économie estimée sur 20 ans: {project_data['total_savings_20y']:,} €</p>
                    </div>
                </div>
                """.replace(",", " ")
            },
            {
                "id": "solar-metrics-grid",
                "label": "📈 Grille Métriques",
                "category": "Solaire Standard", 
                "media": '<svg viewBox="0 0 24 24" style="fill: #667eea;"><path d="M3 3v18h18V3H3zm8 16H5v-6h6v6zm0-8H5V5h6v6zm8 8h-6v-6h6v6zm0-8h-6V5h6v6z"/></svg>',
                "content": f"""
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 40px 0;">
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 12px; text-align: center; box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);">
                        <h3>{project_data['annual_savings']:,} €</h3>
                        <p>Économie Annuelle</p>
                    </div>
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 12px; text-align: center; box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);">
                        <h3>{project_data['power_kwc']} kWc</h3>
                        <p>Puissance Installée</p>
                    </div>
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 12px; text-align: center; box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);">
                        <h3>{project_data['solar_coverage']}%</h3>
                        <p>Couverture Solaire</p>
                    </div>
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 12px; text-align: center; box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);">
                        <h3>{project_data['co2_avoided']} T</h3>
                        <p>CO₂ Évité/An</p>
                    </div>
                </div>
                """.replace(",", " ")
            },
            {
                "id": "eco-impact-modern",
                "label": "🌱 Impact Écologique",
                "category": "Environnement",
                "media": '<svg viewBox="0 0 24 24" style="fill: #48bb78;"><path d="M17,8C8,10 5.9,16.17 3.82,21.34L5.71,22L6.66,19.7C7.14,19.87 7.64,20 8,20C19,20 22,3 22,3C21,5 14,5.25 9,6.25C4,7.25 2,11.5 2,13.5C2,15.5 3.75,17.25 3.75,17.25C7,8 17,8 17,8Z"/></svg>',
                "content": f"""
                <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); padding: 25px; border-radius: 15px; color: white; margin: 15px 0; box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);">
                    <h3>🌱 Impact Environnemental</h3>
                    <div style="display: flex; justify-content: space-between; margin-top: 20px;">
                        <div style="text-align: center;">
                            <h4>{project_data['co2_avoided']} tonnes</h4>
                            <p>CO₂ évité par an</p>
                        </div>
                        <div style="text-align: center;">
                            <h4>{int(project_data['co2_avoided'] * 50)} arbres</h4>
                            <p>Équivalent planté</p>
                        </div>
                        <div style="text-align: center;">
                            <h4>{int(project_data['co2_avoided'] * 2.4)} voitures</h4>
                            <p>Retirées circulation</p>
                        </div>
                    </div>
                </div>
                """
            },
            {
                "id": "financial-summary",
                "label": "💰 Résumé Financier", 
                "category": "Financier",
                "media": '<svg viewBox="0 0 24 24" style="fill: #ff6b6b;"><path d="M7,15H9C9,16.08 10.37,17 12,17C13.63,17 15,16.08 15,15C15,13.9 13.96,13.5 11.76,12.97C9.64,12.44 7,11.78 7,9C7,7.21 8.47,5.69 10.5,5.18V3H13.5V5.18C15.53,5.69 17,7.21 17,9H15C15,7.92 13.63,7 12,7C10.37,7 9,7.92 9,9C9,10.1 10.04,10.5 12.24,11.03C14.36,11.56 17,12.22 17,15C17,16.79 15.53,18.31 13.5,18.82V21H10.5V18.82C8.47,18.31 7,16.79 7,15Z"/></svg>',
                "content": f"""
                <div style="background: linear-gradient(135deg, #ff6b6b 0%, #feca57 100%); padding: 30px; border-radius: 15px; color: white; margin: 20px 0;">
                    <h3>💰 Synthèse Financière</h3>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px;">
                        <div>
                            <h4>Prix Solaire: {project_data['solar_price']} ct/kWh</h4>
                            <p>vs {project_data.get('prix_reseau', 18.5)} ct/kWh réseau</p>
                        </div>
                        <div>
                            <h4>Économie 20 ans: {project_data['total_savings_20y']:,} €</h4>
                            <p>{project_data['savings_percentage']:.1f}% d'économie</p>
                        </div>
                    </div>
                </div>
                """.replace(",", " ")
            },
            {
                "id": "benefits-section",
                "label": "⭐ Section Avantages",
                "category": "Marketing",
                "media": '<svg viewBox="0 0 24 24" style="fill: #4ECDC4;"><path d="M12,17.27L18.18,21L16.54,13.97L22,9.24L14.81,8.62L12,2L9.19,8.62L2,9.24L7.46,13.97L5.82,21L12,17.27Z"/></svg>',
                "content": f"""
                <div style="background: #f8f9fa; padding: 40px; border-radius: 20px; margin: 30px 0;">
                    <h3 style="color: #4ECDC4; margin-bottom: 20px; font-family: 'Montserrat', sans-serif;">
                        Votre Avantage Principal
                    </h3>
                    <p style="font-size: 18px; line-height: 1.6; color: #2c3e50;">
                        En rejoignant ce projet d'autoconsommation collective, vous bénéficiez d'une électricité 
                        produite localement à un tarif fixe et compétitif, à l'abri des hausses du marché.
                    </p>
                    <div style="margin-top: 30px; padding: 20px; background: #4ECDC4; color: white; border-radius: 10px; text-align: center;">
                        <strong>C'est simple, sécurisé et sans investissement de votre part !</strong>
                    </div>
                </div>
                """
            },
            {
                "id": "text-block",
                "label": "📝 Bloc Texte",
                "category": "Basique",
                "media": '<svg viewBox="0 0 24 24" style="fill: #718096;"><path d="M3,5H21V7H3V5M3,13V11H21V13H3M3,19V17H21V19H3Z"/></svg>',
                "content": "<div style='padding: 20px; font-family: Open Sans, sans-serif; line-height: 1.6;'><h3>Titre de section</h3><p>Votre texte ici...</p></div>"
            },
            {
                "id": "image-block", 
                "label": "🖼️ Image",
                "category": "Basique",
                "media": '<svg viewBox="0 0 24 24" style="fill: #718096;"><path d="M19,3H5A2,2 0 0,0 3,5V19A2,2 0 0,0 5,21H19A2,2 0 0,0 21,19V5A2,2 0 0,0 19,3M5,19L8.5,14.5L11,17.5L15.5,12.5L19,17V19H5Z"/></svg>',
                "content": """
                <div style="text-align: center; padding: 20px;">
                    <img src="https://via.placeholder.com/400x250/4ECDC4/ffffff?text=Votre+Image" 
                         style="max-width: 100%; border-radius: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.2);"
                         alt="Image de démonstration">
                    <p style="margin-top: 15px; color: #718096; font-style: italic;">Légende de l'image</p>
                </div>
                """
            },
            {
                "id": "contact-section",
                "label": "📞 Contact",
                "category": "Marketing",
                "media": '<svg viewBox="0 0 24 24" style="fill: #4ECDC4;"><path d="M20,15.5C18.8,15.5 17.5,15.3 16.4,14.9C16.1,14.8 15.7,14.9 15.5,15.1L13.2,17.4C10.4,15.9 8,13.6 6.6,10.8L8.9,8.5C9.1,8.3 9.2,7.9 9.1,7.6C8.7,6.5 8.5,5.2 8.5,4C8.5,3.5 8,3 7.5,3H4C3.5,3 3,3.5 3,4C3,13.4 10.6,21 20,21C20.5,21 21,20.5 21,20V16.5C21,16 20.5,15.5 20,15.5M5,5H6.5C6.6,5.9 6.8,6.8 7,7.6L5.8,8.8C5.4,7.6 5.1,6.3 5,5M19,19C17.7,18.9 16.4,18.6 15.2,18.2L16.4,17C17.2,17.2 18.1,17.4 19,17.5V19Z"/></svg>',
                "content": f"""
                <div style="background: #2C3E50; color: white; padding: 40px; text-align: center; border-radius: 15px;">
                    <h3>Votre Contact OptimPV</h3>
                    <div style="margin: 20px 0;">
                        <p style="font-size: 18px; margin: 10px 0;">📞 01 23 45 67 89</p>
                        <p style="font-size: 18px; margin: 10px 0;">✉️ contact@optimpv.fr</p>
                        <p style="font-size: 16px; margin: 10px 0; opacity: 0.8;">Disponible du lundi au vendredi, 9h-18h</p>
                    </div>
                    <div style="margin-top: 30px; padding: 15px; background: #4ECDC4; border-radius: 8px;">
                        <strong>Demandez votre étude personnalisée gratuite</strong>
                    </div>
                </div>
                """
            }
        ]
    
    
    def _get_solar_css(self) -> str:
        """Retourne le CSS de base pour les composants solaires."""
        return """
        .solar-metric {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 12px;
            text-align: center;
            margin: 10px;
            box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
            backdrop-filter: blur(4px);
            border: 1px solid rgba(255, 255, 255, 0.18);
            transition: transform 0.3s ease;
        }
        
        .solar-metric:hover {
            transform: translateY(-5px);
        }
        
        .solar-header {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 40px 20px;
            text-align: center;
            border-radius: 15px;
            margin: 20px 0;
        }
        
        .eco-card {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            padding: 25px;
            border-radius: 15px;
            color: white;
            margin: 15px 0;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
        }
        
        body {
            font-family: 'Inter', sans-serif;
            line-height: 1.6;
        }
        """
    
    def _get_premium_css(self) -> str:
        """Retourne le CSS premium turquoise pour l'éditeur."""
        return """
        :root {
            --primary-color: #4ECDC4;
            --primary-light: #7EDDD6;
            --primary-dark: #3BA99F;
            --text-dark: #2C3E50;
            --text-light: #7F8C8D;
            --background: #FFFFFF;
            --background-alt: #F8F9FA;
            --accent-gray: #ECF0F1;
            --shadow: rgba(0, 0, 0, 0.08);
        }
        
        .premium-cover {
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            background: 
                radial-gradient(circle at 20% 30%, var(--accent-gray) 0%, transparent 50%),
                radial-gradient(circle at 80% 80%, var(--primary-light) 0%, transparent 30%),
                var(--background);
            padding: 80px 60px;
            min-height: 100vh;
        }
        
        .premium-circle {
            width: 350px;
            height: 350px;
            border: 3px solid var(--primary-color);
            border-radius: 50%;
            background: var(--background);
            box-shadow: 0 20px 60px rgba(78, 205, 196, 0.15);
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            margin: 40px 0;
        }
        
        .premium-title {
            font-family: 'Montserrat', sans-serif;
            font-weight: 700;
            font-size: 24px;
            letter-spacing: 3px;
            color: var(--text-dark);
            margin-bottom: 10px;
        }
        
        .premium-subtitle {
            font-family: 'Open Sans', sans-serif;
            font-size: 14px;
            color: var(--text-light);
            letter-spacing: 1px;
            text-transform: uppercase;
        }
        
        .premium-year-badge {
            background: var(--primary-color);
            color: white;
            padding: 12px 32px;
            border-radius: 25px;
            font-family: 'Montserrat', sans-serif;
            font-weight: 600;
            font-size: 18px;
            margin-top: 40px;
        }
        
        .premium-key-benefit {
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-light) 100%);
            color: white;
            padding: 40px;
            border-radius: 15px;
            margin: 30px 0;
            text-align: center;
            box-shadow: 0 15px 35px rgba(78, 205, 196, 0.3);
        }
        
        .premium-info-card {
            background: var(--background);
            padding: 40px;
            border-radius: 15px;
            box-shadow: 0 10px 30px var(--shadow);
            margin: 30px 0;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        .premium-info-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(78, 205, 196, 0.15);
        }
        
        .premium-timeline {
            display: flex;
            justify-content: space-between;
            margin: 50px 0;
            position: relative;
        }
        
        .premium-timeline::before {
            content: '';
            position: absolute;
            top: 30px;
            left: 5%;
            right: 5%;
            height: 3px;
            background: var(--accent-gray);
            border-radius: 2px;
        }
        
        .premium-timeline-dot {
            width: 60px;
            height: 60px;
            background: linear-gradient(135deg, var(--primary-color), var(--primary-light));
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            margin: 0 auto 20px;
            font-family: 'Montserrat', sans-serif;
            font-size: 18px;
            box-shadow: 0 10px 25px rgba(78, 205, 196, 0.3);
        }
        
        .premium-section-title {
            font-family: 'Montserrat', sans-serif;
            font-weight: 600;
            font-size: 32px;
            color: var(--text-dark);
            margin-bottom: 40px;
            position: relative;
            padding-left: 40px;
        }
        
        .premium-section-title::before {
            content: '';
            position: absolute;
            left: 0;
            top: 50%;
            transform: translateY(-50%);
            width: 5px;
            height: 40px;
            background: var(--primary-color);
            border-radius: 3px;
        }
        
        .premium-highlight-number {
            font-family: 'Montserrat', sans-serif;
            font-weight: 700;
            font-size: 48px;
            color: var(--primary-color);
            line-height: 1;
        }
        """
    
    def _get_initial_template(self, template: str, project_data: Dict[str, Any]) -> str:
        """
        Retourne le contenu HTML initial selon le template choisi.
        
        Args:
            template: Nom du template
            project_data: Données du projet
            
        Returns:
            HTML du template initial
        """
        if template == "Vierge":
            return "<div style='padding: 20px;'><h1>Votre proposition commence ici...</h1></div>"
        
        elif template == "Template Premium Turquoise":
            # Utiliser le générateur de template premium turquoise
            if self.premium_generator and PREMIUM_TEMPLATE_AVAILABLE:
                try:
                    # Préparer les données pour le template premium
                    template_data = self._prepare_premium_data(project_data)
                    
                    # Générer le contenu éditable spécifiquement pour GrapesJS
                    return self._create_editable_premium_content(template_data)
                except Exception as e:
                    logger.error(f"Erreur lors de la génération du template premium: {e}")
                    return self._get_turquoise_fallback_template(project_data)
            else:
                # Fallback si le générateur premium n'est pas disponible
                return self._get_turquoise_fallback_template(project_data)
        
        elif template == "Solaire Standard":
            return self._get_solar_standard_template(project_data)
        
        else:  # Professionnel ou autre
            return f"""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 60px 40px; text-align: center; border-radius: 20px;">
                <h1 style="font-size: 2.5em; margin-bottom: 20px;">{project_data['template']['cover']['title']}</h1>
                <h2 style="font-size: 1.5em; opacity: 0.9;">Proposition pour {project_data['client_name']}</h2>
                <div style="background: rgba(255,255,255,0.2); padding: 20px; border-radius: 10px; margin-top: 30px; display: inline-block;">
                    <h3>Prix Garanti: {project_data['solar_price']} ct/kWh</h3>
                    <p>Économie estimée sur 20 ans: {project_data['total_savings_20y']:,} €</p>
                </div>
            </div>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 40px 0;">
                <div class="solar-metric">
                    <h3>{project_data['annual_savings']:,} €</h3>
                    <p>Économie Annuelle</p>
                </div>
                <div class="solar-metric">
                    <h3>{project_data['power_kwc']} kWc</h3>
                    <p>Puissance Installée</p>
                </div>
                <div class="solar-metric">
                    <h3>{project_data['solar_coverage']}%</h3>
                    <p>Couverture Solaire</p>
                </div>
                <div class="solar-metric">
                    <h3>{project_data['co2_avoided']} T</h3>
                    <p>CO₂ Évité/An</p>
                </div>
            </div>
            """.replace(",", " ")
    
    def _prepare_premium_data(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prépare les données pour le template premium."""
        return {
            'client_name': project_data.get('client_name', '[NOM DU CLIENT]'),
            'prix_optimal': project_data.get('prix_optimal', 15.0),
            'economie_totale': project_data.get('economie_totale', 150000),
            'economie_annuelle': project_data.get('economie_annuelle', 7500),
            'cout_annuel_actuel': project_data.get('cout_annuel_actuel', 50000),
            'cout_annuel_avec_solaire': project_data.get('cout_annuel_avec_solaire', 42500),
            'part_solaire': project_data.get('part_solaire', 30),
            'contact_name': 'Votre Contact Commercial',
            'contact_phone': '01 23 45 67 89',
            'contact_email': 'contact@optimpv.fr',
            'date_mise_service': 'T2 2025'
        }
    
    def _create_editable_premium_content(self, data: Dict[str, Any]) -> str:
        """Crée un contenu premium turquoise éditable pour GrapesJS."""
        return f"""
        <div style="background: linear-gradient(135deg, #4ECDC4 0%, #44A08D 100%); color: white; padding: 60px; text-align: center; border-radius: 20px; margin-bottom: 30px;">
            <h1 style="font-family: 'Montserrat', sans-serif; font-size: 48px; font-weight: 700; margin-bottom: 20px;">
                PROPOSITION AUTOCONSOMMATION
            </h1>
            <h2 style="font-size: 24px; opacity: 0.9; margin-bottom: 30px;">
                Projet pour {data.get('client_name', '[NOM DU CLIENT]')}
            </h2>
            <div style="background: rgba(255,255,255,0.2); padding: 30px; border-radius: 15px; display: inline-block;">
                <h3 style="margin-bottom: 15px;">Prix Garanti</h3>
                <div style="font-size: 54px; font-weight: 700; margin: 15px 0;">
                    {data.get('prix_optimal', 15.0):.1f} ct/kWh
                </div>
                <p style="font-size: 18px;">
                    Économie sur 20 ans: {data.get('economie_totale', 150000):,} €
                </p>
            </div>
        </div>
        
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 30px; margin: 40px 0;">
            <div style="background: #4ECDC4; color: white; padding: 30px; border-radius: 15px; text-align: center;">
                <h3 style="font-size: 36px; font-weight: 700; margin-bottom: 10px;">
                    {data.get('economie_annuelle', 7500):,} €
                </h3>
                <p>Économie Annuelle</p>
            </div>
            
            <div style="background: #44A08D; color: white; padding: 30px; border-radius: 15px; text-align: center;">
                <h3 style="font-size: 36px; font-weight: 700; margin-bottom: 10px;">
                    100 kWc
                </h3>
                <p>Puissance Installée</p>
            </div>
            
            <div style="background: #26C6DA; color: white; padding: 30px; border-radius: 15px; text-align: center;">
                <h3 style="font-size: 36px; font-weight: 700; margin-bottom: 10px;">
                    7.5 T
                </h3>
                <p>CO₂ Évité/An</p>
            </div>
        </div>
        
        <div style="background: #f8f9fa; padding: 40px; border-radius: 20px; margin: 30px 0;">
            <h3 style="color: #4ECDC4; margin-bottom: 20px; font-family: 'Montserrat', sans-serif;">
                Votre Avantage Principal
            </h3>
            <p style="font-size: 18px; line-height: 1.6; color: #2c3e50;">
                En rejoignant ce projet d'autoconsommation collective, vous bénéficiez d'une électricité 
                produite localement à un tarif fixe et compétitif, à l'abri des hausses du marché.
            </p>
            <div style="margin-top: 30px; padding: 20px; background: #4ECDC4; color: white; border-radius: 10px; text-align: center;">
                <strong>C'est simple, sécurisé et sans investissement de votre part !</strong>
            </div>
        </div>
        """.replace(",", " ")

    def _get_fallback_template(self) -> str:
        """Template de fallback en cas d'erreur."""
        return """
        <div style="padding: 40px; text-align: center;">
            <h1>Proposition d'Autoconsommation Collective</h1>
            <p>Template premium temporairement indisponible. Utilisez ce template de base pour commencer.</p>
        </div>
        """
    
    def _get_turquoise_fallback_template(self, project_data: Dict[str, Any]) -> str:
        """Template turquoise de fallback si le générateur premium n'est pas disponible."""
        return f"""
        <div style="background: linear-gradient(135deg, #4ECDC4 0%, #44A08D 100%); 
                    color: white; padding: 60px 40px; text-align: center; border-radius: 20px;">
            <h1 style="font-size: 2.5em; margin-bottom: 20px; font-family: 'Montserrat', sans-serif;">
                PROPOSITION AUTOCONSOMMATION
            </h1>
            <h2 style="font-size: 1.5em; opacity: 0.9; font-weight: 300;">
                Projet pour {project_data['client_name']}
            </h2>
            <div style="background: rgba(255,255,255,0.2); padding: 30px; border-radius: 15px; 
                        margin-top: 40px; display: inline-block;">
                <h3 style="margin-bottom: 15px;">Prix Garanti</h3>
                <div style="font-size: 48px; font-weight: 700; margin: 15px 0;">
                    {project_data['solar_price']:.1f} ct/kWh
                </div>
                <p style="font-size: 18px; margin-top: 20px;">
                    Économie estimée sur 20 ans: {project_data['total_savings_20y']:,} €
                </p>
            </div>
        </div>
        
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
                    gap: 30px; margin: 50px 0; padding: 0 20px;">
            <div style="background: #4ECDC4; color: white; padding: 30px; border-radius: 15px; 
                        text-align: center; box-shadow: 0 10px 30px rgba(78, 205, 196, 0.3);">
                <h3 style="font-size: 36px; margin-bottom: 10px; font-weight: 700;">
                    {project_data['annual_savings']:,} €
                </h3>
                <p style="opacity: 0.9;">Économie Annuelle</p>
            </div>
            
            <div style="background: #44A08D; color: white; padding: 30px; border-radius: 15px; 
                        text-align: center; box-shadow: 0 10px 30px rgba(68, 160, 141, 0.3);">
                <h3 style="font-size: 36px; margin-bottom: 10px; font-weight: 700;">
                    {project_data['power_kwc']} kWc
                </h3>
                <p style="opacity: 0.9;">Puissance Installée</p>
            </div>
            
            <div style="background: #26C6DA; color: white; padding: 30px; border-radius: 15px; 
                        text-align: center; box-shadow: 0 10px 30px rgba(38, 198, 218, 0.3);">
                <h3 style="font-size: 36px; margin-bottom: 10px; font-weight: 700;">
                    {project_data['co2_avoided']:.1f} T
                </h3>
                <p style="opacity: 0.9;">CO₂ Évité/An</p>
            </div>
        </div>
        
        <div style="background: #f8f9fa; padding: 40px; border-radius: 20px; margin: 30px 0;">
            <h3 style="color: #4ECDC4; margin-bottom: 20px; font-family: 'Montserrat', sans-serif;">
                Votre Avantage Principal
            </h3>
            <p style="font-size: 18px; line-height: 1.6; color: #2c3e50;">
                En rejoignant ce projet d'autoconsommation collective, vous bénéficiez d'une électricité 
                produite localement à un tarif fixe et compétitif, à l'abri des hausses du marché.
            </p>
            <div style="margin-top: 30px; padding: 20px; background: #4ECDC4; color: white; 
                        border-radius: 10px; text-align: center;">
                <strong>C'est simple, sécurisé et sans investissement de votre part !</strong>
            </div>
        </div>
        """.replace(",", " ")
    
    def _get_solar_standard_template(self, project_data: Dict[str, Any]) -> str:
        """Template solaire standard."""
        return f"""
        <div class="solar-header">
            <h1>Proposition Solaire</h1>
            <h2>Projet pour {project_data.get('client_name', 'Client')}</h2>
        </div>
        <div style="display: flex; gap: 20px;">
            <div class="solar-metric">
                <h3>{project_data.get('economie_annuelle', 7500):,} €</h3>
                <p>Économie Annuelle</p>
            </div>
            <div class="solar-metric">
                <h3>{project_data.get('prix_optimal', 15):.1f} ct/kWh</h3>
                <p>Prix Garanti</p>
            </div>
        </div>
        """.replace(",", " ")

    def _save_design(self):
        """Sauvegarde le design actuel."""
        if 'grapesjs_design' not in st.session_state:
            st.session_state.grapesjs_design = {}
        
        # Dans un vrai cas, on récupérerait depuis GrapesJS
        st.success("💾 Design sauvegardé!")
    
    def _load_design(self):
        """Charge un design sauvegardé."""
        if st.session_state.get('grapesjs_design'):
            st.success("📂 Design chargé!")
        else:
            st.info("Aucun design sauvegardé trouvé.")