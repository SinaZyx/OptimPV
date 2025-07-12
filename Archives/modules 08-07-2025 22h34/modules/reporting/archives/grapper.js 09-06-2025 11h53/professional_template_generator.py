"""
Générateur de rapport professionnel pour proposition d'autoconsommation collective.
Ce module génère un rapport structuré suivant un template professionnel prédéfini.
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import base64
import io
import logging
from typing import Dict, Any, Optional, List, Tuple

logger = logging.getLogger(__name__)

class ProfessionalTemplateGenerator:
    """Générateur de rapport suivant un template professionnel structuré."""
    
    def __init__(self):
        """Initialise le générateur de template professionnel."""
        self.template_structure = self._define_template_structure()
        
    def _define_template_structure(self) -> List[Dict[str, Any]]:
        """Définit la structure du template professionnel."""
        return [
            {
                "page": 1,
                "title": "Proposition d'Autoconsommation Collective - Projet Solaire",
                "sections": [
                    {"type": "main_title", "content": "VOTRE PROJET D'AUTOCONSOMMATION SOLAIRE"},
                    {"type": "client_info", "field": "client_name"},
                    {"type": "image", "content": "solar_panels", "description": "Panneaux solaires"},
                    {"type": "key_benefits", "fields": ["prix_garanti", "economie_20ans", "mise_service"]},
                    {"type": "footer", "content": "Rapport préparé le {date}"}
                ]
            },
            {
                "page": 2,
                "title": "Une Énergie Plus Verte et Plus Économique, en Bref",
                "sections": [
                    {"type": "intro_text", "content": "introduction_text"},
                    {"type": "three_advantages", "fields": ["economies", "stabilite", "impact"]}
                ]
            },
            {
                "page": 3,
                "title": "Visualisez l'Impact sur Votre Facture Annuelle",
                "sections": [
                    {"type": "cost_comparison_chart"},
                    {"type": "savings_highlight", "fields": ["economie_annuelle", "reduction_percentage"]}
                ]
            },
            {
                "page": 4,
                "title": "Un Modèle Simple et un Prix Transparent",
                "sections": [
                    {"type": "offer_details", "fields": ["prix_vente", "couverture", "duree", "indexation", "investissement"]},
                    {"type": "how_it_works", "steps": ["production", "distribution", "consommation", "facturation"]}
                ]
            },
            {
                "page": 5,
                "title": "Vos Économies sur le Long Terme",
                "sections": [
                    {"type": "savings_projection_chart"},
                    {"type": "explanation_text"}
                ]
            },
            {
                "page": 6,
                "title": "Une Source d'Énergie Locale et Fiable",
                "sections": [
                    {"type": "installation_image"},
                    {"type": "technical_sheet", "fields": ["localisation", "puissance", "production", "technologie", "maintenance"]}
                ]
            },
            {
                "page": 7,
                "title": "Plus qu'une Économie, un Geste pour la Planète",
                "sections": [
                    {"type": "environmental_impact", "fields": ["co2_avoided", "equivalent_cars"]},
                    {"type": "territorial_engagement"}
                ]
            },
            {
                "page": 8,
                "title": "Foire Aux Questions",
                "sections": [
                    {"type": "faq", "questions": ["no_sun", "consumption_excess", "flexibility", "maintenance"]}
                ]
            },
            {
                "page": 9,
                "title": "Prêt à Réduire Votre Facture ?",
                "sections": [
                    {"type": "timeline", "steps": ["proposition", "entretien", "signature", "demarrage"]},
                    {"type": "contact_person", "fields": ["name", "title", "phone", "email"]}
                ]
            },
            {
                "page": 10,
                "title": "Informations Détaillées et Contact",
                "sections": [
                    {"type": "technical_assumptions"},
                    {"type": "company_info", "fields": ["logo", "address", "phone", "email", "website"]},
                    {"type": "qr_code"}
                ]
            }
        ]
    
    def generate_report(self, project_data: Dict[str, Any]) -> str:
        """
        Génère le rapport HTML complet basé sur le template professionnel.
        
        Args:
            project_data: Dictionnaire contenant toutes les données du projet
            
        Returns:
            str: HTML du rapport complet
        """
        html_content = self._generate_html_header()
        
        # Générer chaque page du rapport
        for page_config in self.template_structure:
            if page_config["page"] == 1:
                html_content += self._generate_cover_page(project_data)
            else:
                html_content += self._generate_page(page_config, project_data)
        
        html_content += self._generate_html_footer()
        
        return html_content
    
    def _generate_html_header(self) -> str:
        """Génère l'en-tête HTML avec les styles CSS premium turquoise."""
        return """
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Proposition d'Autoconsommation Collective</title>
            <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;700&family=Open+Sans:wght@300;400;600&display=swap" rel="stylesheet">
            <style>
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
                
                * {
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }
                
                body {
                    font-family: 'Open Sans', sans-serif;
                    color: var(--text-dark);
                    line-height: 1.8;
                    background-color: var(--background-alt);
                }
                
                .document-container {
                    width: 210mm;
                    margin: 0 auto;
                }
                
                .page {
                    width: 210mm;
                    min-height: 297mm;
                    padding: 60px 60px 80px 60px;
                    margin-bottom: 2px;
                    background: var(--background);
                    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
                    position: relative;
                    page-break-after: always;
                }
                
                .page-number {
                    position: absolute;
                    bottom: 30px;
                    right: 60px;
                    color: var(--text-light);
                    font-size: 11px;
                    font-family: 'Montserrat', sans-serif;
                    font-weight: 300;
                }
                
                /* TYPOGRAPHIE PREMIUM */
                h1 {
                    font-family: 'Montserrat', sans-serif;
                    font-weight: 700;
                    font-size: 48px;
                    letter-spacing: 2px;
                    color: var(--text-dark);
                    text-align: center;
                    margin-bottom: 40px;
                }
                
                h2 {
                    font-family: 'Montserrat', sans-serif;
                    font-weight: 600;
                    font-size: 32px;
                    color: var(--text-dark);
                    margin-bottom: 40px;
                    position: relative;
                    padding-left: 40px;
                }
                
                h2::before {
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
                
                h3 {
                    font-family: 'Montserrat', sans-serif;
                    font-weight: 600;
                    font-size: 20px;
                    color: var(--text-dark);
                    margin-bottom: 20px;
                }
                
                h4 {
                    font-family: 'Montserrat', sans-serif;
                    font-weight: 600;
                    font-size: 16px;
                    color: var(--text-dark);
                    margin-bottom: 15px;
                }
                
                p {
                    font-family: 'Open Sans', sans-serif;
                    font-size: 16px;
                    line-height: 1.8;
                    color: var(--text-light);
                    margin-bottom: 20px;
                }
                
                /* PAGE DE COUVERTURE */
                .cover-page {
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
                }
                
                .cover-circle {
                    width: 350px;
                    height: 350px;
                    border: 3px solid var(--primary-color);
                    border-radius: 50%;
                    position: relative;
                    background: var(--background);
                    box-shadow: 0 20px 60px rgba(78, 205, 196, 0.15);
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    align-items: center;
                    margin: 40px 0;
                }
                
                .cover-title {
                    font-family: 'Montserrat', sans-serif;
                    font-weight: 700;
                    font-size: 24px;
                    letter-spacing: 3px;
                    color: var(--text-dark);
                    margin-bottom: 10px;
                }
                
                .cover-subtitle {
                    font-family: 'Open Sans', sans-serif;
                    font-size: 14px;
                    color: var(--text-light);
                    letter-spacing: 1px;
                    text-transform: uppercase;
                }
                
                .year-badge {
                    background: var(--primary-color);
                    color: white;
                    padding: 12px 32px;
                    border-radius: 25px;
                    font-family: 'Montserrat', sans-serif;
                    font-weight: 600;
                    font-size: 18px;
                    margin-top: 40px;
                }
                
                /* CARTES D'INFORMATION PREMIUM */
                .info-card {
                    background: var(--background);
                    padding: 40px;
                    border-radius: 15px;
                    box-shadow: 0 10px 30px var(--shadow);
                    margin: 30px 0;
                    transition: transform 0.3s ease, box-shadow 0.3s ease;
                }
                
                .info-card:hover {
                    transform: translateY(-5px);
                    box-shadow: 0 15px 40px rgba(78, 205, 196, 0.15);
                }
                
                .key-benefit {
                    background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-light) 100%);
                    color: white;
                    padding: 40px;
                    border-radius: 15px;
                    margin: 30px 0;
                    text-align: center;
                    box-shadow: 0 15px 35px rgba(78, 205, 196, 0.3);
                }
                
                .key-benefit h3 {
                    color: white;
                    font-size: 18px;
                    margin-bottom: 15px;
                    font-weight: 600;
                }
                
                .key-benefit .value {
                    font-size: 42px;
                    font-weight: 700;
                    margin: 15px 0;
                    font-family: 'Montserrat', sans-serif;
                }
                
                /* AVANTAGES AVEC STYLE PREMIUM */
                .advantage-box {
                    background: var(--background);
                    border-left: 5px solid var(--primary-color);
                    padding: 30px;
                    margin: 25px 0;
                    border-radius: 10px;
                    box-shadow: 0 5px 15px var(--shadow);
                    transition: all 0.3s ease;
                }
                
                .advantage-box:hover {
                    transform: translateX(5px);
                    box-shadow: 0 8px 25px rgba(78, 205, 196, 0.1);
                }
                
                .advantage-box h4 {
                    color: var(--primary-dark);
                    margin-bottom: 15px;
                }
                
                /* ICÔNES MODERNES */
                .icon {
                    width: 60px;
                    height: 60px;
                    background: linear-gradient(135deg, var(--primary-color), var(--primary-light));
                    border-radius: 50%;
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    margin-right: 20px;
                    vertical-align: middle;
                    box-shadow: 0 8px 20px rgba(78, 205, 196, 0.3);
                    color: white;
                    font-weight: bold;
                    font-size: 18px;
                }
                
                /* TIMELINE PREMIUM */
                .timeline {
                    display: flex;
                    justify-content: space-between;
                    margin: 50px 0;
                    position: relative;
                }
                
                .timeline::before {
                    content: '';
                    position: absolute;
                    top: 30px;
                    left: 5%;
                    right: 5%;
                    height: 3px;
                    background: var(--accent-gray);
                    border-radius: 2px;
                }
                
                .timeline-item {
                    text-align: center;
                    flex: 1;
                    position: relative;
                    z-index: 1;
                }
                
                .timeline-dot {
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
                
                /* GRAPHIQUES ET CHARTS */
                .chart-container {
                    margin: 40px 0;
                    padding: 40px;
                    background: var(--background);
                    border-radius: 15px;
                    box-shadow: 0 10px 30px var(--shadow);
                }
                
                .chart-container h3 {
                    text-align: center;
                    margin-bottom: 30px;
                    color: var(--text-dark);
                }
                
                /* FAQ MODERNE */
                .faq-item {
                    margin: 25px 0;
                    padding: 30px;
                    background: var(--background);
                    border-radius: 12px;
                    border-left: 4px solid var(--primary-color);
                    box-shadow: 0 5px 15px var(--shadow);
                }
                
                .faq-item h4 {
                    color: var(--primary-dark);
                    margin-bottom: 15px;
                }
                
                /* CONTACT CARD PREMIUM */
                .contact-card {
                    background: linear-gradient(135deg, var(--background-alt), var(--background));
                    padding: 40px;
                    border-radius: 20px;
                    text-align: center;
                    margin: 40px 0;
                    border: 2px solid var(--accent-gray);
                    position: relative;
                    overflow: hidden;
                }
                
                .contact-card::before {
                    content: '';
                    position: absolute;
                    top: 0;
                    left: 0;
                    right: 0;
                    height: 5px;
                    background: linear-gradient(90deg, var(--primary-color), var(--primary-light));
                }
                
                /* GRID LAYOUTS */
                .two-column {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 40px;
                    align-items: center;
                }
                
                .three-column {
                    display: grid;
                    grid-template-columns: repeat(3, 1fr);
                    gap: 30px;
                }
                
                /* EFFETS ET ANIMATIONS */
                .fade-in {
                    opacity: 0;
                    transform: translateY(20px);
                    animation: fadeIn 0.8s ease forwards;
                }
                
                @keyframes fadeIn {
                    to {
                        opacity: 1;
                        transform: translateY(0);
                    }
                }
                
                .hoverable {
                    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                }
                
                /* RESPONSIVE ET PRINT */
                @media print {
                    body {
                        background: white;
                    }
                    .page {
                        margin: 0;
                        box-shadow: none;
                        page-break-after: always;
                    }
                    .cover-page {
                        background: white;
                    }
                }
                
                /* ÉLÉMENTS SPÉCIAUX */
                .highlight-number {
                    font-family: 'Montserrat', sans-serif;
                    font-weight: 700;
                    font-size: 48px;
                    color: var(--primary-color);
                    line-height: 1;
                }
                
                .section-divider {
                    width: 60px;
                    height: 4px;
                    background: var(--primary-color);
                    margin: 30px auto;
                    border-radius: 2px;
                }
                
                .quote-text {
                    font-style: italic;
                    font-size: 18px;
                    color: var(--text-dark);
                    text-align: center;
                    margin: 40px 0;
                    position: relative;
                }
                
                .quote-text::before {
                    content: '"';
                    font-size: 60px;
                    color: var(--primary-color);
                    position: absolute;
                    left: -20px;
                    top: -10px;
                }
            </style>
        </head>
        <body>
        <div class="document-container">
        """
    
    def _generate_page(self, page_config: Dict[str, Any], project_data: Dict[str, Any]) -> str:
        """Génère une page du rapport."""
        page_html = f'<div class="page">\n'
        
        # Titre de la page si présent
        if "title" in page_config and page_config["page"] == 1:
            page_html += f'<h1>{page_config["title"]}</h1>\n'
        elif "title" in page_config:
            page_html += f'<h2>{page_config["title"]}</h2>\n'
        
        # Générer chaque section
        for section in page_config["sections"]:
            page_html += self._generate_section(section, project_data)
        
        # Numéro de page
        page_html += f'<div class="page-number">Page {page_config["page"]} / 10</div>\n'
        page_html += '</div>\n'
        
        return page_html
    
    def _generate_section(self, section: Dict[str, Any], project_data: Dict[str, Any]) -> str:
        """Génère une section spécifique basée sur son type."""
        section_type = section.get("type")
        
        if section_type == "main_title":
            return f'<h1 style="margin-top: 50px;">{section["content"]}</h1>\n'
        
        elif section_type == "client_info":
            client_name = project_data.get("client_name", "[NOM DU CLIENT]")
            return f'<h3 style="text-align: center; margin: 30px 0;">Proposition pour : {client_name}</h3>\n'
        
        elif section_type == "image":
            return self._generate_image_placeholder(section.get("description", "Image"))
        
        elif section_type == "key_benefits":
            return self._generate_key_benefits(section["fields"], project_data)
        
        elif section_type == "footer":
            date_str = datetime.now().strftime("%d %B %Y")
            content = section["content"].format(date=date_str)
            return f'<p style="text-align: center; margin-top: 50px; color: #666;">{content}</p>\n'
        
        elif section_type == "intro_text":
            return self._generate_intro_text(project_data)
        
        elif section_type == "three_advantages":
            return self._generate_advantages(section["fields"], project_data)
        
        elif section_type == "cost_comparison_chart":
            return self._generate_cost_comparison(project_data)
        
        elif section_type == "savings_highlight":
            return self._generate_savings_highlight(section["fields"], project_data)
        
        elif section_type == "offer_details":
            return self._generate_offer_details(section["fields"], project_data)
        
        elif section_type == "how_it_works":
            return self._generate_how_it_works(section["steps"])
        
        elif section_type == "savings_projection_chart":
            return self._generate_savings_projection(project_data)
        
        elif section_type == "technical_sheet":
            return self._generate_technical_sheet(section["fields"], project_data)
        
        elif section_type == "environmental_impact":
            return self._generate_environmental_impact(section["fields"], project_data)
        
        elif section_type == "faq":
            return self._generate_faq(section["questions"])
        
        elif section_type == "timeline":
            return self._generate_timeline(section["steps"])
        
        elif section_type == "contact_person":
            return self._generate_contact_person(section["fields"], project_data)
        
        elif section_type == "company_info":
            return self._generate_company_info(section["fields"], project_data)
        
        else:
            return ""
    
    def _generate_image_placeholder(self, description: str) -> str:
        """Génère un placeholder pour une image."""
        return f"""
        <div style="background: #e0e0e0; height: 300px; display: flex; align-items: center; 
                    justify-content: center; border-radius: 10px; margin: 30px 0;">
            <p style="color: #666; font-size: 18px;">[IMAGE : {description}]</p>
        </div>
        """
    
    def _generate_key_benefits(self, fields: List[str], project_data: Dict[str, Any]) -> str:
        """Génère la section des bénéfices clés avec design premium."""
        html = '<div style="margin: 60px 0;">\n'
        html += '<h2 style="text-align: center; margin-bottom: 50px; padding-left: 0;">VOTRE BÉNÉFICE PRINCIPAL</h2>\n'
        html += '<div class="section-divider"></div>\n'
        html += '<div class="three-column" style="margin-top: 40px;">\n'
        
        benefits = {
            "prix_garanti": {
                "label": "Prix Garanti",
                "value": f"{project_data.get('prix_optimal', 15.0):.1f}",
                "unit": "ct/kWh",
                "icon": "€"
            },
            "economie_20ans": {
                "label": "Économie sur 20 ans",
                "value": f"{project_data.get('economie_totale', 150000)/1000:.0f}",
                "unit": "K€",
                "icon": "💰"
            },
            "mise_service": {
                "label": "Mise en service",
                "value": project_data.get('date_mise_service', "T2 2025"),
                "unit": "",
                "icon": "📅"
            }
        }
        
        for field in fields:
            if field in benefits:
                benefit = benefits[field]
                html += f"""
                <div class="key-benefit info-card">
                    <div class="icon" style="margin: 0 auto 20px; display: flex;">{benefit['icon']}</div>
                    <h3 style="color: white; margin-bottom: 20px;">{benefit['label']}</h3>
                    <div class="highlight-number" style="color: white; font-size: 48px; margin: 15px 0;">
                        {benefit['value']}
                    </div>
                    <div style="color: rgba(255,255,255,0.9); font-size: 16px; font-weight: 500;">
                        {benefit['unit']}
                    </div>
                </div>
                """
        
        html += '</div>\n</div>\n'
        return html
    
    def _generate_intro_text(self, project_data: Dict[str, Any]) -> str:
        """Génère le texte d'introduction."""
        project_name = project_data.get('project_name', '[Nom du projet]')
        prix_optimal = project_data.get('prix_optimal', 15.0)
        economie_percentage = project_data.get('economie_percentage', 15)
        economie_totale = project_data.get('economie_totale', 150000)
        co2_annual = project_data.get('co2_avoided_annual', 50)
        
        text = f"""
        <p style="font-size: 16px; line-height: 1.8; text-align: justify;">
        Ce rapport vous présente une opportunité unique de réduire durablement votre facture d'électricité. 
        En rejoignant le projet d'autoconsommation collective de <strong>{project_name}</strong>, vous bénéficierez 
        d'une électricité produite localement à un tarif fixe et compétitif de <strong>{prix_optimal:.1f} ct/kWh</strong>, 
        à l'abri des hausses du marché. Cela représente une économie estimée à <strong>{economie_percentage}%</strong> 
        sur la part solaire de votre consommation, soit plus de <strong>{economie_totale:,.0f} €</strong> sur 20 ans, 
        tout en réduisant votre empreinte carbone de <strong>{co2_annual:.0f}</strong> tonnes par an. 
        C'est simple, sécurisé et sans investissement de votre part.
        </p>
        """.replace(",", " ")
        
        return text
    
    def _generate_advantages(self, fields: List[str], project_data: Dict[str, Any]) -> str:
        """Génère les trois avantages clés."""
        html = '<h3 style="text-align: center; margin: 30px 0;">Vos 3 Avantages Clés</h3>\n'
        html += '<div style="margin: 20px 0;">\n'
        
        advantages = {
            "economies": {
                "title": "ÉCONOMIES DIRECTES",
                "description": f"Un prix de l'électricité solaire inférieur de {project_data.get('economie_percentage', 15)}% au tarif réglementé actuel."
            },
            "stabilite": {
                "title": "STABILITÉ DES PRIX",
                "description": f"Un tarif fixe pendant {project_data.get('duree_contrat', 20)} ans, vous protégeant de la volatilité du marché."
            },
            "impact": {
                "title": "IMPACT POSITIF",
                "description": "Accès à une énergie 100% verte et locale, valorisant votre image RSE."
            }
        }
        
        for field in fields:
            if field in advantages:
                adv = advantages[field]
                html += f"""
                <div class="advantage-box">
                    <div style="display: flex; align-items: center;">
                        <div class="icon"></div>
                        <div>
                            <h4>{adv['title']}</h4>
                            <p>{adv['description']}</p>
                        </div>
                    </div>
                </div>
                """
        
        html += '</div>\n'
        return html
    
    def _generate_cost_comparison(self, project_data: Dict[str, Any]) -> str:
        """Génère le graphique de comparaison des coûts avec design premium."""
        cout_actuel = project_data.get('cout_annuel_actuel', 50000)
        cout_avec_solaire = project_data.get('cout_annuel_avec_solaire', 42500)
        part_solaire = project_data.get('part_solaire', 30)
        economie = cout_actuel - cout_avec_solaire
        
        html = f"""
        <div class="chart-container">
            <h3>Comparatif du Coût Annuel de l'Électricité</h3>
            <div class="two-column" style="margin-top: 40px;">
                
                <!-- SANS projet solaire -->
                <div class="info-card" style="text-align: center; border: 2px solid #e74c3c;">
                    <h4 style="color: #e74c3c; margin-bottom: 25px;">SITUATION ACTUELLE</h4>
                    <div class="highlight-number" style="color: #e74c3c; margin: 20px 0;">
                        {cout_actuel:,.0f}
                    </div>
                    <div style="color: var(--text-light); font-size: 18px; margin-bottom: 20px;">€ / an</div>
                    <p style="color: var(--text-light);">100% de votre électricité achetée sur le réseau public.</p>
                </div>
                
                <!-- AVEC projet solaire -->
                <div class="info-card" style="text-align: center; border: 2px solid var(--primary-color);">
                    <h4 style="color: var(--primary-dark); margin-bottom: 25px;">AVEC AUTOCONSOMMATION</h4>
                    <div class="highlight-number" style="color: var(--primary-color); margin: 20px 0;">
                        {cout_avec_solaire:,.0f}
                    </div>
                    <div style="color: var(--text-light); font-size: 18px; margin-bottom: 20px;">€ / an</div>
                    <div style="display: flex; justify-content: space-between; margin: 20px 0;">
                        <div style="flex: 1; padding: 10px; background: var(--primary-color); color: white; border-radius: 8px; margin-right: 10px;">
                            <div style="font-weight: bold;">{part_solaire}%</div>
                            <div style="font-size: 12px;">Solaire Local</div>
                        </div>
                        <div style="flex: 1; padding: 10px; background: var(--accent-gray); color: var(--text-dark); border-radius: 8px;">
                            <div style="font-weight: bold;">{100-part_solaire}%</div>
                            <div style="font-size: 12px;">Réseau</div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Économie mise en évidence -->
            <div style="text-align: center; margin-top: 40px; padding: 30px; 
                        background: linear-gradient(135deg, var(--primary-color), var(--primary-light)); 
                        border-radius: 15px; color: white;">
                <h3 style="color: white; margin-bottom: 15px;">VOTRE ÉCONOMIE ANNUELLE</h3>
                <div style="font-family: 'Montserrat', sans-serif; font-weight: 700; font-size: 42px; margin: 15px 0;">
                    {economie:,.0f} €
                </div>
                <div style="color: rgba(255,255,255,0.9);">
                    Soit {((economie/cout_actuel)*100):.1f}% de réduction sur votre facture
                </div>
            </div>
        </div>
        """.replace(",", " ")
        
        return html
    
    def _generate_savings_highlight(self, fields: List[str], project_data: Dict[str, Any]) -> str:
        """Génère la mise en évidence des économies."""
        economie_annuelle = project_data.get('economie_annuelle', 7500)
        reduction_percentage = project_data.get('reduction_percentage', 15)
        
        html = f"""
        <div style="background: #f0f8ff; border: 2px solid #2c5aa0; padding: 30px; 
                    border-radius: 10px; text-align: center; margin: 30px 0;">
            <h3 style="color: #2c5aa0; margin-bottom: 20px;">CHIFFRE CLÉ</h3>
            <div style="font-size: 36px; font-weight: bold; color: #2c5aa0;">
                Soit {economie_annuelle:,.0f} € d'économie par an
            </div>
            <div style="font-size: 24px; color: #666; margin-top: 10px;">
                {reduction_percentage}% de réduction sur votre facture
            </div>
        </div>
        """.replace(",", " ")
        
        html += """
        <p style="text-align: center; margin-top: 20px;">
        Grâce à l'énergie solaire locale, une part significative de votre consommation vous coûtera moins cher. 
        Le reste de vos besoins est toujours assuré par le réseau, garantissant une alimentation sans coupure.
        </p>
        """
        
        return html
    
    def _generate_offer_details(self, fields: List[str], project_data: Dict[str, Any]) -> str:
        """Génère les détails de l'offre."""
        html = '<h3>Détail de notre offre</h3>\n'
        html += '<div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin: 20px 0;">\n'
        
        offer_details = {
            "prix_vente": f"Prix de vente de l'électricité solaire: <strong>{project_data.get('prix_optimal', 15.0):.1f} ct/kWh HT</strong>",
            "couverture": f"Part de votre consommation couverte par le solaire: <strong>{project_data.get('taux_couverture', 30)}%</strong>",
            "duree": f"Durée du contrat: <strong>{project_data.get('duree_contrat', 20)} ans</strong>",
            "indexation": f"Indexation du prix: <strong>{project_data.get('indexation', 'Fixe')}</strong>",
            "investissement": "Investissement requis de votre part: <strong>0 €</strong>"
        }
        
        html += '<ul style="list-style: none; padding: 0;">\n'
        for field in fields:
            if field in offer_details:
                html += f'<li style="padding: 8px 0;">{offer_details[field]}</li>\n'
        html += '</ul>\n</div>\n'
        
        return html
    
    def _generate_how_it_works(self, steps: List[str]) -> str:
        """Génère la section 'Comment ça marche'."""
        html = '<h3>Comment ça marche ?</h3>\n'
        html += '<div style="display: flex; justify-content: space-between; margin: 30px 0;">\n'
        
        step_details = {
            "production": {
                "number": "1",
                "title": "Production",
                "description": "Les panneaux solaires produisent de l'électricité."
            },
            "distribution": {
                "number": "2",
                "title": "Distribution",
                "description": "L'électricité est injectée dans le réseau public local."
            },
            "consommation": {
                "number": "3",
                "title": "Consommation",
                "description": "Vous la consommez instantanément."
            },
            "facturation": {
                "number": "4",
                "title": "Facturation",
                "description": "Nous mesurons la part solaire consommée et vous la facturons au prix convenu."
            }
        }
        
        for step in steps:
            if step in step_details:
                detail = step_details[step]
                html += f"""
                <div style="flex: 1; text-align: center; padding: 0 10px;">
                    <div class="timeline-item">
                        <div class="circle">{detail['number']}</div>
                        <h4>{detail['title']}</h4>
                        <p style="font-size: 14px;">{detail['description']}</p>
                    </div>
                </div>
                """
        
        html += '</div>\n'
        return html
    
    def _generate_savings_projection(self, project_data: Dict[str, Any]) -> str:
        """Génère le graphique de projection des économies."""
        html = """
        <div class="chart-container">
            <h3 style="text-align: center; margin-bottom: 20px;">Projection de vos gains sur 20 ans</h3>
            <div style="height: 300px; background: #f0f4f8; display: flex; align-items: center; 
                        justify-content: center; border-radius: 10px;">
                <p style="color: #666;">[GRAPHIQUE : Courbe d'évolution des économies cumulées]</p>
            </div>
        </div>
        <p style="margin-top: 20px; text-align: justify;">
        Ce graphique illustre la puissance de votre engagement. Tandis que le prix de l'électricité 
        du réseau devrait continuer d'augmenter, votre tarif solaire reste stable, créant des économies 
        de plus en plus importantes chaque année.
        </p>
        """
        return html
    
    def _generate_technical_sheet(self, fields: List[str], project_data: Dict[str, Any]) -> str:
        """Génère la fiche technique."""
        html = self._generate_image_placeholder("Photo ou plan de l'installation")
        html += '<h3>Fiche Technique en bref</h3>\n'
        html += '<div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin: 20px 0;">\n'
        
        tech_details = {
            "localisation": f"Localisation: <strong>{project_data.get('localisation', '[Adresse de l\'installation]')}</strong>",
            "puissance": f"Puissance installée: <strong>{project_data.get('puissance_kwc', 100)} kWc</strong> (l'équivalent de la consommation de {project_data.get('equivalent_foyers', 40)} foyers)",
            "production": f"Production annuelle estimée: <strong>{project_data.get('production_annuelle', 110000):,.0f} kWh</strong>".replace(",", " "),
            "technologie": "Technologie: <strong>Panneaux photovoltaïques haute performance</strong>",
            "maintenance": "Maintenance & Supervision: <strong>Assurées par nos équipes 24/7</strong>"
        }
        
        html += '<ul style="list-style: none; padding: 0;">\n'
        for field in fields:
            if field in tech_details:
                html += f'<li style="padding: 8px 0;">{tech_details[field]}</li>\n'
        html += '</ul>\n</div>\n'
        
        return html
    
    def _generate_environmental_impact(self, fields: List[str], project_data: Dict[str, Any]) -> str:
        """Génère la section impact environnemental."""
        co2_annual = project_data.get('co2_avoided_annual', 50)
        cars_equivalent = project_data.get('cars_equivalent', 10)
        
        html = f"""
        <div style="text-align: center; margin: 40px 0;">
            <div class="icon" style="width: 100px; height: 100px; margin: 0 auto 20px;"></div>
            <h3>{co2_annual:.0f} tonnes de CO₂ évitées par an</h3>
            <p style="font-style: italic; color: #666;">
                "C'est comme retirer {cars_equivalent} voitures de la circulation chaque année !"
            </p>
        </div>
        
        <div style="background: #e8f5e9; padding: 30px; border-radius: 10px; margin: 30px 0;">
            <h3 style="text-align: center; margin-bottom: 20px;">Un Acteur Engagé dans son Territoire</h3>
            <ul style="list-style: none; padding: 0; text-align: center;">
                <li style="padding: 5px 0;">✓ Soutien à la production d'énergie locale.</li>
                <li style="padding: 5px 0;">✓ Contribution à la transition énergétique de la région.</li>
                <li style="padding: 5px 0;">✓ Valorisation de votre image de marque auprès de vos clients et collaborateurs.</li>
            </ul>
        </div>
        """
        
        return html
    
    def _generate_faq(self, questions: List[str]) -> str:
        """Génère la section FAQ."""
        html = ''
        
        faq_content = {
            "no_sun": {
                "question": "Et s'il n'y a pas de soleil ?",
                "answer": "Votre alimentation est garantie sans coupure. Le réseau électrique prend le relais automatiquement. Vous ne remarquerez aucune différence, sauf sur votre facture."
            },
            "consumption_excess": {
                "question": "Que se passe-t-il si je consomme plus que ce que le solaire produit ?",
                "answer": "Le complément est fourni par le réseau, comme aujourd'hui. Notre offre ne couvre que la part d'énergie solaire que vous consommez."
            },
            "flexibility": {
                "question": "Mon contrat est-il flexible ?",
                "answer": "Oui, votre contrat inclut des conditions de sortie ou de transfert adaptées, par exemple en cas de déménagement."
            },
            "maintenance": {
                "question": "Qui s'occupe de la maintenance ?",
                "answer": "Nous nous occupons de tout. L'exploitation et la maintenance de la centrale sont entièrement à notre charge."
            }
        }
        
        for question_key in questions:
            if question_key in faq_content:
                faq = faq_content[question_key]
                html += f"""
                <div class="faq-item">
                    <h4>{faq['question']}</h4>
                    <p>{faq['answer']}</p>
                </div>
                """
        
        return html
    
    def _generate_timeline(self, steps: List[str]) -> str:
        """Génère la timeline avec le design premium."""
        html = '<h2 style="text-align: center; margin: 40px 0; padding-left: 0;">Votre Parcours vers l\'Autoconsommation</h2>\n'
        html += '<div class="section-divider"></div>\n'
        html += '<div class="timeline">\n'
        
        timeline_content = {
            "proposition": {
                "number": "1", 
                "title": "Proposition", 
                "description": "Étude de votre profil de consommation et présentation de notre offre personnalisée."
            },
            "entretien": {
                "number": "2", 
                "title": "Entretien", 
                "description": "Rendez-vous personnalisé pour répondre à toutes vos questions techniques et commerciales."
            },
            "signature": {
                "number": "3", 
                "title": "Signature", 
                "description": "Finalisation et signature de la convention d'autoconsommation collective."
            },
            "demarrage": {
                "number": "4", 
                "title": "Démarrage", 
                "description": "Mise en service de votre alimentation solaire et début immédiat de vos économies !"
            }
        }
        
        for step in steps:
            if step in timeline_content:
                content = timeline_content[step]
                html += f"""
                <div class="timeline-item">
                    <div class="timeline-dot">{content['number']}</div>
                    <h4 style="font-family: 'Montserrat', sans-serif; color: var(--text-dark); margin-bottom: 15px;">
                        {content['title']}
                    </h4>
                    <p style="color: var(--text-light); text-align: center; font-size: 14px; line-height: 1.6;">
                        {content['description']}
                    </p>
                </div>
                """
        
        html += '</div>\n'
        
        # Ajouter une citation inspirante
        html += '''
        <div class="quote-text" style="margin-top: 60px;">
            Rejoignez la transition énergétique locale et profitez d'une électricité plus verte et plus économique
        </div>
        '''
        
        return html
    
    def _generate_contact_person(self, fields: List[str], project_data: Dict[str, Any]) -> str:
        """Génère la carte de contact."""
        html = """
        <div class="contact-card">
            <h3>Votre Interlocuteur Dédié</h3>
            <div style="width: 100px; height: 100px; background: #ddd; border-radius: 50%; 
                        margin: 20px auto;"></div>
        """
        
        contact_info = {
            "name": project_data.get('contact_name', 'Nom et Prénom'),
            "title": project_data.get('contact_title', 'Titre'),
            "phone": project_data.get('contact_phone', '01 23 45 67 89'),
            "email": project_data.get('contact_email', 'email@exemple.com')
        }
        
        html += f"""
            <h4>{contact_info['name']}</h4>
            <p>{contact_info['title']}</p>
            <p>📞 {contact_info['phone']}</p>
            <p>✉️ {contact_info['email']}</p>
        </div>
        """
        
        return html
    
    def _generate_company_info(self, fields: List[str], project_data: Dict[str, Any]) -> str:
        """Génère les informations de l'entreprise."""
        html = '<h3>Hypothèses et Données Techniques</h3>\n'
        html += """
        <p style="margin-bottom: 30px;">
        Ce rapport a été généré sur la base de données d'ensoleillement et de consommation 
        spécifiques à votre localisation. Les projections financières incluent une marge de sécurité.
        </p>
        """
        
        company_info = project_data.get('company_info', {
            'name': 'OptimPV - Votre Partenaire Énergie',
            'address': '123 Avenue de l\'Énergie Verte\n75001 Paris, France',
            'phone': '01 23 45 67 89',
            'email': 'contact@optimpv.fr',
            'website': 'www.optimpv.fr'
        })
        
        html += f"""
        <div style="text-align: center; margin-top: 40px;">
            <div style="width: 150px; height: 60px; background: #ddd; margin: 0 auto 20px;"></div>
            <h4>{company_info['name']}</h4>
            <p>{company_info['address'].replace('\n', '<br>')}</p>
            <p>📞 {company_info['phone']}</p>
            <p>✉️ {company_info['email']}</p>
            <p>🌐 {company_info['website']}</p>
            
            <div style="width: 100px; height: 100px; background: #ddd; margin: 30px auto;">
                <p style="line-height: 100px; color: #666;">[QR CODE]</p>
            </div>
        </div>
        """
        
        return html
    
    def _generate_cover_page(self, project_data: Dict[str, Any]) -> str:
        """Génère la page de couverture avec le design premium."""
        client_name = project_data.get('client_name', '[NOM DU CLIENT]')
        current_year = datetime.now().year
        
        html = f'''
        <div class="page cover-page">
            <!-- Logo placeholder en haut -->
            <div style="width: 120px; height: 60px; background: var(--accent-gray); 
                        border-radius: 8px; margin-bottom: 60px; display: flex; 
                        align-items: center; justify-content: center; color: var(--text-light);">
                [LOGO]
            </div>
            
            <!-- Cercle central avec contenu -->
            <div class="cover-circle">
                <div class="cover-title">PROPOSITION</div>
                <div class="cover-title">AUTOCONSOMMATION</div>
                <div class="cover-subtitle">Énergie Solaire Collective</div>
            </div>
            
            <!-- Badge année -->
            <div class="year-badge">{current_year}</div>
            
            <!-- Informations client et préparation -->
            <div style="margin-top: 60px; display: flex; justify-content: space-between; 
                        width: 100%; font-family: 'Open Sans', sans-serif; font-size: 14px; 
                        color: var(--text-light);">
                <div style="text-align: left;">
                    <div style="border-bottom: 1px solid var(--accent-gray); padding-bottom: 5px; margin-bottom: 10px;">
                        <strong>PRÉPARÉ POUR</strong>
                    </div>
                    <div style="color: var(--text-dark); font-weight: 600;">{client_name}</div>
                </div>
                <div style="text-align: right;">
                    <div style="border-bottom: 1px solid var(--accent-gray); padding-bottom: 5px; margin-bottom: 10px;">
                        <strong>PRÉPARÉ PAR</strong>
                    </div>
                    <div style="color: var(--text-dark); font-weight: 600;">OptimPV</div>
                </div>
            </div>
            
            <div class="page-number">Page 1 / 10</div>
        </div>
        '''
        
        return html
    
    def _generate_html_footer(self) -> str:
        """Génère le pied de page HTML."""
        return """
        </div>
        </body>
        </html>
        """
    
    def get_required_data_fields(self) -> Dict[str, str]:
        """
        Retourne la liste des champs de données requis pour générer le rapport.
        
        Returns:
            Dict[str, str]: Dictionnaire avec les noms des champs et leur description
        """
        return {
            # Informations client
            "client_name": "Nom du client",
            "project_name": "Nom du projet d'autoconsommation",
            
            # Données financières
            "prix_optimal": "Prix de vente optimal (ct/kWh)",
            "economie_totale": "Économie totale sur 20 ans (€)",
            "economie_annuelle": "Économie annuelle (€)",
            "economie_percentage": "Pourcentage d'économie (%)",
            "cout_annuel_actuel": "Coût annuel actuel de l'électricité (€)",
            "cout_annuel_avec_solaire": "Coût annuel avec solaire (€)",
            "reduction_percentage": "Pourcentage de réduction sur la facture (%)",
            
            # Données techniques
            "date_mise_service": "Date de mise en service prévue",
            "puissance_kwc": "Puissance installée (kWc)",
            "production_annuelle": "Production annuelle (kWh)",
            "taux_couverture": "Taux de couverture solaire (%)",
            "part_solaire": "Part solaire de la consommation (%)",
            "localisation": "Localisation de l'installation",
            "equivalent_foyers": "Équivalent en nombre de foyers",
            
            # Données environnementales
            "co2_avoided_annual": "CO2 évité par an (tonnes)",
            "cars_equivalent": "Équivalent en voitures retirées",
            
            # Conditions contractuelles
            "duree_contrat": "Durée du contrat (années)",
            "indexation": "Type d'indexation du prix",
            
            # Informations de contact
            "contact_name": "Nom du contact commercial",
            "contact_title": "Titre du contact",
            "contact_phone": "Téléphone du contact",
            "contact_email": "Email du contact",
            
            # Informations entreprise
            "company_info": "Informations de l'entreprise (dict)"
        }