"""
Module de génération HTML pour les propositions commerciales OptimPV.
Génère des documents HTML complets avec styles et animations.
"""

import streamlit as st
from typing import Dict, Any, List
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

class HTMLGenerator:
    """Générateur de documents HTML pour les propositions commerciales."""
    
    def __init__(self):
        """Initialise le générateur HTML."""
        pass
    
    def generate_complete_proposal(self, project_data: Dict[str, Any]) -> str:
        """
        Génère une proposition complète au format HTML.
        
        Args:
            project_data: Données complètes du projet
            
        Returns:
            HTML complet de la proposition
        """
        try:
            html_content = f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Proposition Solaire - {project_data['client_name']}</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    
    <style>
        {self._get_complete_css()}
    </style>
</head>
<body>
    <div class="container">
        {self._generate_cover_section(project_data)}
        {self._generate_executive_summary(project_data)}
        {self._generate_metrics_section(project_data)}
        {self._generate_financial_analysis(project_data)}
        {self._generate_environmental_impact(project_data)}
        {self._generate_charts_section(project_data)}
        {self._generate_faq_section(project_data)}
        {self._generate_footer_section(project_data)}
    </div>
    
    <script>
        {self._get_complete_javascript(project_data)}
    </script>
</body>
</html>
            """
            
            logger.info(f"Proposition HTML générée pour {project_data['client_name']}")
            return html_content
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération HTML: {e}")
            return self._get_error_template(str(e))
    
    def generate_premium_turquoise_proposal(self, project_data: Dict[str, Any]) -> str:
        """
        Génère une proposition premium avec le design turquoise.
        
        Args:
            project_data: Données complètes du projet
            
        Returns:
            HTML complet de la proposition turquoise premium
        """
        try:
            html_content = f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Proposition Autoconsommation - {project_data['client_name']}</title>
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;700&family=Open+Sans:wght@300;400;600&display=swap" rel="stylesheet">
    
    <style>
        {self._get_premium_turquoise_css()}
    </style>
</head>
<body>
    <div class="turquoise-container">
        {self._generate_turquoise_header(project_data)}
        {self._generate_turquoise_metrics(project_data)}
        {self._generate_turquoise_benefits(project_data)}
        {self._generate_turquoise_footer(project_data)}
    </div>
</body>
</html>
            """
            
            logger.info(f"Proposition turquoise premium générée pour {project_data['client_name']}")
            return html_content
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération turquoise: {e}")
            return self._get_error_template(str(e))
    
    def _generate_cover_section(self, project_data: Dict[str, Any]) -> str:
        """Génère la section de couverture."""
        return f"""
        <section class="cover-section">
            <div class="cover-content">
                <div class="cover-badge">
                    <i class="fas fa-solar-panel"></i>
                    OPTIMPV
                </div>
                
                <h1 class="cover-title animate-slide-up">
                    {project_data['template']['cover']['title']}
                </h1>
                
                <h2 class="cover-subtitle animate-slide-up">
                    Proposition personnalisée pour <strong>{project_data['client_name']}</strong>
                </h2>
                
                <div class="cover-metrics">
                    <div class="cover-metric animate-fade-in">
                        <div class="metric-value">{project_data['solar_price']}</div>
                        <div class="metric-unit">ct/kWh</div>
                        <div class="metric-label">Prix Garanti</div>
                    </div>
                    
                    <div class="cover-metric animate-fade-in" style="animation-delay: 0.2s;">
                        <div class="metric-value">{project_data['total_savings_20y']:,}</div>
                        <div class="metric-unit">€</div>
                        <div class="metric-label">Économie 20 ans</div>
                    </div>
                    
                    <div class="cover-metric animate-fade-in" style="animation-delay: 0.4s;">
                        <div class="metric-value">{project_data['power_kwc']}</div>
                        <div class="metric-unit">kWc</div>
                        <div class="metric-label">Puissance</div>
                    </div>
                </div>
                
                <div class="cover-date">
                    Rapport généré le {datetime.now().strftime("%d %B %Y")}
                </div>
            </div>
            
            <div class="wave-divider">
                <svg viewBox="0 0 1200 120" preserveAspectRatio="none">
                    <path d="M0,0V46.29c47.79,22.2,103.59,32.17,158,28,70.36-5.37,136.33-33.31,206.8-37.5C438.64,32.43,512.34,53.67,583,72.05c69.27,18,138.3,24.88,209.4,13.08,36.15-6,69.85-17.84,104.45-29.34C989.49,25,1113-14.29,1200,52.47V0Z" opacity=".25" class="shape-fill"></path>
                    <path d="M0,0V15.81C13,36.92,27.64,56.86,47.69,72.05,99.41,111.27,165,111,224.58,91.58c31.15-10.15,60.09-26.07,89.67-39.8,40.92-19,84.73-46,130.83-49.67,36.26-2.85,70.9,9.42,98.6,31.56,31.77,25.39,62.32,62,103.63,73,40.44,10.79,81.35-6.69,119.13-24.28s75.16-39,116.92-43.05c59.73-5.85,113.28,22.88,168.9,38.84,30.2,8.66,59,6.17,87.09-7.5,22.43-10.89,48-26.93,60.65-49.24V0Z" opacity=".5" class="shape-fill"></path>
                    <path d="M0,0V5.63C149.93,59,314.09,71.32,475.83,42.57c43-7.64,84.23-20.12,127.61-26.46,59-8.63,112.48,12.24,165.56,35.4C827.93,77.22,886,95.24,951.2,90c86.53-7,172.46-45.71,248.8-84.81V0Z" class="shape-fill"></path>
                </svg>
            </div>
        </section>
        """.replace(",", " ")
    
    def _generate_executive_summary(self, project_data: Dict[str, Any]) -> str:
        """Génère le résumé exécutif."""
        return f"""
        <section class="summary-section">
            <div class="section-content">
                <h2 class="section-title">
                    <i class="fas fa-lightbulb"></i>
                    Résumé Exécutif
                </h2>
                
                <div class="summary-content">
                    {project_data['template']['executive_summary']}
                    
                    <div class="highlight-box">
                        <i class="fas fa-star"></i>
                        <strong>Votre avantage immédiat :</strong> 
                        Réduction de {project_data['savings_percentage']}% sur la part solaire de votre facture
                    </div>
                </div>
            </div>
        </section>
        """
    
    def _generate_metrics_section(self, project_data: Dict[str, Any]) -> str:
        """Génère la section des métriques principales."""
        return f"""
        <section class="metrics-section">
            <div class="section-content">
                <h2 class="section-title">
                    <i class="fas fa-chart-line"></i>
                    Indicateurs Clés
                </h2>
                
                <div class="metrics-grid">
                    <div class="metric-card economic">
                        <div class="metric-icon">
                            <i class="fas fa-euro-sign"></i>
                        </div>
                        <div class="metric-details">
                            <div class="metric-value" data-value="{project_data['annual_savings']}">{project_data['annual_savings']:,}</div>
                            <div class="metric-label">Économie Annuelle (€)</div>
                            <div class="metric-trend positive">
                                <i class="fas fa-arrow-up"></i>
                                +{project_data['savings_percentage']}% vs réseau
                            </div>
                        </div>
                    </div>
                    
                    <div class="metric-card energy">
                        <div class="metric-icon">
                            <i class="fas fa-bolt"></i>
                        </div>
                        <div class="metric-details">
                            <div class="metric-value" data-value="{project_data['total_production']}">{project_data['total_production']:,}</div>
                            <div class="metric-label">Production Annuelle (kWh)</div>
                            <div class="metric-info">
                                {project_data['solar_coverage']}% de couverture solaire
                            </div>
                        </div>
                    </div>
                    
                    <div class="metric-card environmental">
                        <div class="metric-icon">
                            <i class="fas fa-leaf"></i>
                        </div>
                        <div class="metric-details">
                            <div class="metric-value" data-value="{project_data['co2_avoided']}">{project_data['co2_avoided']}</div>
                            <div class="metric-label">CO₂ Évité/An (tonnes)</div>
                            <div class="metric-info">
                                ≈ {int(project_data['co2_avoided'] * 50)} arbres plantés
                            </div>
                        </div>
                    </div>
                    
                    <div class="metric-card technical">
                        <div class="metric-icon">
                            <i class="fas fa-solar-panel"></i>
                        </div>
                        <div class="metric-details">
                            <div class="metric-value" data-value="{project_data['power_kwc']}">{project_data['power_kwc']}</div>
                            <div class="metric-label">Puissance Installée (kWc)</div>
                            <div class="metric-info">
                                Installation optimisée
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </section>
        """.replace(",", " ")
    
    def _generate_financial_analysis(self, project_data: Dict[str, Any]) -> str:
        """Génère l'analyse financière détaillée."""
        return f"""
        <section class="financial-section">
            <div class="section-content">
                <h2 class="section-title">
                    <i class="fas fa-calculator"></i>
                    Analyse Financière
                </h2>
                
                <div class="financial-grid">
                    <div class="financial-card">
                        <h3>Comparaison Tarifaire</h3>
                        <div class="price-comparison">
                            <div class="price-item solar">
                                <div class="price-label">Prix Solaire OptimPV</div>
                                <div class="price-value">{project_data['solar_price']} ct/kWh</div>
                                <div class="price-badge">Fixe 20 ans</div>
                            </div>
                            <div class="vs-divider">VS</div>
                            <div class="price-item grid">
                                <div class="price-label">Prix Réseau Actuel</div>
                                <div class="price-value">{project_data.get('grid_price', 16.8)} ct/kWh</div>
                                <div class="price-badge variable">Variable</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="financial-card">
                        <h3>Projection sur 20 ans</h3>
                        <div class="projection-timeline">
                            <div class="timeline-item">
                                <div class="timeline-year">Année 1</div>
                                <div class="timeline-value">{project_data['annual_savings']:,} €</div>
                            </div>
                            <div class="timeline-connector"></div>
                            <div class="timeline-item">
                                <div class="timeline-year">Année 10</div>
                                <div class="timeline-value">{project_data['annual_savings'] * 10:,} €</div>
                            </div>
                            <div class="timeline-connector"></div>
                            <div class="timeline-item highlighted">
                                <div class="timeline-year">Année 20</div>
                                <div class="timeline-value">{project_data['total_savings_20y']:,} €</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </section>
        """.replace(",", " ")
    
    def _generate_environmental_impact(self, project_data: Dict[str, Any]) -> str:
        """Génère la section impact environnemental."""
        trees_equivalent = int(project_data['co2_avoided'] * 50)
        cars_equivalent = int(project_data['co2_avoided'] * 2.4)
        
        return f"""
        <section class="environmental-section">
            <div class="section-content">
                <h2 class="section-title">
                    <i class="fas fa-globe-americas"></i>
                    Impact Environnemental
                </h2>
                
                <div class="environmental-grid">
                    <div class="environmental-card co2">
                        <div class="env-icon">🌿</div>
                        <div class="env-value">{project_data['co2_avoided']} tonnes</div>
                        <div class="env-label">CO₂ évité par an</div>
                    </div>
                    
                    <div class="environmental-card trees">
                        <div class="env-icon">🌳</div>
                        <div class="env-value">{trees_equivalent} arbres</div>
                        <div class="env-label">Équivalent plantation</div>
                    </div>
                    
                    <div class="environmental-card cars">
                        <div class="env-icon">🚗</div>
                        <div class="env-value">{cars_equivalent} voitures</div>
                        <div class="env-label">Retirées de la circulation</div>
                    </div>
                    
                    <div class="environmental-card energy">
                        <div class="env-icon">⚡</div>
                        <div class="env-value">{project_data['total_production']//1000} MWh</div>
                        <div class="env-label">Énergie verte produite</div>
                    </div>
                </div>
                
                <div class="sustainability-message">
                    <i class="fas fa-heart"></i>
                    <p>En choisissant OptimPV, vous participez activement à la transition énergétique 
                    et contribuez à un avenir plus durable pour les générations futures.</p>
                </div>
            </div>
        </section>
        """
    
    def _generate_charts_section(self, project_data: Dict[str, Any]) -> str:
        """Génère la section avec les graphiques."""
        return f"""
        <section class="charts-section">
            <div class="section-content">
                <h2 class="section-title">
                    <i class="fas fa-chart-bar"></i>
                    Analyse Graphique
                </h2>
                
                <div class="charts-grid">
                    <div class="chart-container">
                        <h3>Répartition Énergétique</h3>
                        <canvas id="energyChart" width="400" height="300"></canvas>
                    </div>
                    
                    <div class="chart-container">
                        <h3>Évolution des Économies</h3>
                        <canvas id="savingsChart" width="400" height="300"></canvas>
                    </div>
                </div>
            </div>
        </section>
        """
    
    def _generate_faq_section(self, project_data: Dict[str, Any]) -> str:
        """Génère la section FAQ."""
        faq_items = project_data['template']['faq']
        
        faq_html = ""
        for i, faq in enumerate(faq_items):
            faq_html += f"""
            <div class="faq-item">
                <div class="faq-question" onclick="toggleFAQ({i})">
                    <span>{faq['question']}</span>
                    <i class="fas fa-chevron-down faq-icon" id="faq-icon-{i}"></i>
                </div>
                <div class="faq-answer" id="faq-answer-{i}">
                    <p>{faq['answer']}</p>
                </div>
            </div>
            """
        
        return f"""
        <section class="faq-section">
            <div class="section-content">
                <h2 class="section-title">
                    <i class="fas fa-question-circle"></i>
                    Questions Fréquentes
                </h2>
                
                <div class="faq-container">
                    {faq_html}
                </div>
            </div>
        </section>
        """
    
    def _generate_footer_section(self, project_data: Dict[str, Any]) -> str:
        """Génère le pied de page."""
        return f"""
        <footer class="footer-section">
            <div class="section-content">
                <div class="footer-content">
                    <div class="footer-brand">
                        <h3>OptimPV</h3>
                        <p>Votre partenaire pour la transition énergétique</p>
                    </div>
                    
                    <div class="footer-contact">
                        <h4>Contact</h4>
                        <p><i class="fas fa-phone"></i> +33 1 23 45 67 89</p>
                        <p><i class="fas fa-envelope"></i> contact@optimpv.fr</p>
                        <p><i class="fas fa-map-marker-alt"></i> France</p>
                    </div>
                    
                    <div class="footer-social">
                        <h4>Suivez-nous</h4>
                        <div class="social-links">
                            <a href="#"><i class="fab fa-linkedin"></i></a>
                            <a href="#"><i class="fab fa-twitter"></i></a>
                            <a href="#"><i class="fab fa-facebook"></i></a>
                        </div>
                    </div>
                </div>
                
                <div class="footer-bottom">
                    <p>&copy; 2025 OptimPV. Tous droits réservés. | Proposition générée le {datetime.now().strftime("%d/%m/%Y")}</p>
                </div>
            </div>
        </footer>
        """
    
    def _get_complete_css(self) -> str:
        """Retourne le CSS complet pour la proposition."""
        return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Inter', sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f8f9fa;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            box-shadow: 0 0 30px rgba(0,0,0,0.1);
        }
        
        /* Cover Section */
        .cover-section {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
            display: flex;
            align-items: center;
            position: relative;
            overflow: hidden;
        }
        
        .cover-content {
            padding: 80px 40px;
            text-align: center;
            z-index: 2;
            width: 100%;
        }
        
        .cover-badge {
            display: inline-block;
            background: rgba(255,255,255,0.2);
            padding: 10px 25px;
            border-radius: 25px;
            font-weight: 600;
            margin-bottom: 30px;
            backdrop-filter: blur(10px);
        }
        
        .cover-title {
            font-size: 3.5em;
            font-weight: 700;
            margin-bottom: 20px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .cover-subtitle {
            font-size: 1.5em;
            opacity: 0.9;
            margin-bottom: 50px;
            font-weight: 400;
        }
        
        .cover-metrics {
            display: flex;
            justify-content: center;
            gap: 40px;
            margin: 50px 0;
            flex-wrap: wrap;
        }
        
        .cover-metric {
            background: rgba(255,255,255,0.15);
            padding: 30px;
            border-radius: 20px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.3);
            min-width: 200px;
            transition: transform 0.3s ease;
        }
        
        .cover-metric:hover {
            transform: translateY(-10px);
        }
        
        .metric-value {
            font-size: 3em;
            font-weight: 700;
            margin-bottom: 5px;
        }
        
        .metric-unit {
            font-size: 1.2em;
            opacity: 0.8;
            margin-bottom: 10px;
        }
        
        .metric-label {
            font-size: 1em;
            opacity: 0.9;
        }
        
        .cover-date {
            font-size: 1.1em;
            opacity: 0.8;
            margin-top: 30px;
        }
        
        /* Wave Divider */
        .wave-divider {
            position: absolute;
            bottom: 0;
            left: 0;
            width: 100%;
            overflow: hidden;
            line-height: 0;
        }
        
        .wave-divider svg {
            position: relative;
            display: block;
            width: calc(100% + 1.3px);
            height: 120px;
        }
        
        .wave-divider .shape-fill {
            fill: #FFFFFF;
        }
        
        /* Sections communes */
        .section-content {
            padding: 80px 40px;
        }
        
        .section-title {
            font-size: 2.5em;
            color: #2d3748;
            margin-bottom: 50px;
            text-align: center;
            position: relative;
        }
        
        .section-title i {
            margin-right: 15px;
            color: #667eea;
        }
        
        /* Summary Section */
        .summary-section {
            background: #f8f9fa;
        }
        
        .summary-content {
            max-width: 800px;
            margin: 0 auto;
            font-size: 1.2em;
            line-height: 1.8;
        }
        
        .highlight-box {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
            padding: 25px;
            border-radius: 15px;
            margin: 30px 0;
            text-align: center;
            font-size: 1.1em;
        }
        
        /* Metrics Section */
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 30px;
        }
        
        .metric-card {
            background: white;
            padding: 30px;
            border-radius: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .metric-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 20px 40px rgba(0,0,0,0.15);
        }
        
        .metric-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, #667eea, #764ba2);
        }
        
        .metric-icon {
            font-size: 2.5em;
            margin-bottom: 20px;
            color: #667eea;
        }
        
        .metric-card .metric-value {
            font-size: 2.5em;
            font-weight: 700;
            color: #2d3748;
            margin-bottom: 10px;
        }
        
        .metric-card .metric-label {
            font-size: 1.1em;
            color: #718096;
            margin-bottom: 15px;
        }
        
        .metric-trend {
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: 600;
        }
        
        .metric-trend.positive {
            background: #c6f6d5;
            color: #22543d;
        }
        
        .metric-info {
            color: #667eea;
            font-weight: 500;
        }
        
        /* Financial Section */
        .financial-section {
            background: #f8f9fa;
        }
        
        .financial-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 40px;
        }
        
        .financial-card {
            background: white;
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        
        .financial-card h3 {
            color: #2d3748;
            margin-bottom: 30px;
            font-size: 1.5em;
        }
        
        .price-comparison {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 20px;
        }
        
        .price-item {
            text-align: center;
            flex: 1;
        }
        
        .price-label {
            font-size: 1.1em;
            color: #718096;
            margin-bottom: 10px;
        }
        
        .price-value {
            font-size: 2.5em;
            font-weight: 700;
            margin-bottom: 10px;
        }
        
        .price-item.solar .price-value {
            color: #22543d;
        }
        
        .price-item.grid .price-value {
            color: #e53e3e;
        }
        
        .price-badge {
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: 600;
        }
        
        .price-badge:not(.variable) {
            background: #c6f6d5;
            color: #22543d;
        }
        
        .price-badge.variable {
            background: #fed7d7;
            color: #742a2a;
        }
        
        .vs-divider {
            font-size: 1.5em;
            font-weight: 700;
            color: #667eea;
        }
        
        .projection-timeline {
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        
        .timeline-item {
            text-align: center;
            flex: 1;
        }
        
        .timeline-year {
            font-size: 1.1em;
            color: #718096;
            margin-bottom: 10px;
        }
        
        .timeline-value {
            font-size: 1.8em;
            font-weight: 700;
            color: #2d3748;
        }
        
        .timeline-item.highlighted .timeline-value {
            color: #667eea;
            font-size: 2.2em;
        }
        
        .timeline-connector {
            flex: 0.5;
            height: 2px;
            background: linear-gradient(90deg, #667eea, #764ba2);
        }
        
        /* Environmental Section */
        .environmental-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 30px;
            margin-bottom: 50px;
        }
        
        .environmental-card {
            background: white;
            padding: 40px;
            border-radius: 20px;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }
        
        .environmental-card:hover {
            transform: translateY(-5px);
        }
        
        .env-icon {
            font-size: 3em;
            margin-bottom: 20px;
        }
        
        .env-value {
            font-size: 2.5em;
            font-weight: 700;
            color: #2d3748;
            margin-bottom: 10px;
        }
        
        .env-label {
            color: #718096;
            font-size: 1.1em;
        }
        
        .sustainability-message {
            background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
            color: white;
            padding: 40px;
            border-radius: 20px;
            text-align: center;
            font-size: 1.2em;
        }
        
        .sustainability-message i {
            font-size: 2em;
            margin-bottom: 20px;
            display: block;
        }
        
        /* Charts Section */
        .charts-section {
            background: #f8f9fa;
        }
        
        .charts-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 40px;
        }
        
        .chart-container {
            background: white;
            padding: 30px;
            border-radius: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        
        .chart-container h3 {
            color: #2d3748;
            margin-bottom: 30px;
            text-align: center;
            font-size: 1.3em;
        }
        
        /* FAQ Section */
        .faq-container {
            max-width: 800px;
            margin: 0 auto;
        }
        
        .faq-item {
            background: white;
            border-radius: 15px;
            margin-bottom: 20px;
            overflow: hidden;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        
        .faq-question {
            padding: 25px;
            cursor: pointer;
            background: #f8f9fa;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-weight: 600;
            font-size: 1.1em;
            transition: background 0.3s ease;
        }
        
        .faq-question:hover {
            background: #e2e8f0;
        }
        
        .faq-icon {
            transition: transform 0.3s ease;
        }
        
        .faq-icon.rotated {
            transform: rotate(180deg);
        }
        
        .faq-answer {
            padding: 0 25px;
            max-height: 0;
            overflow: hidden;
            transition: all 0.3s ease;
        }
        
        .faq-answer.open {
            padding: 25px;
            max-height: 200px;
        }
        
        /* Footer */
        .footer-section {
            background: #2d3748;
            color: white;
        }
        
        .footer-content {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 40px;
            margin-bottom: 40px;
        }
        
        .footer-brand h3 {
            color: #667eea;
            font-size: 2em;
            margin-bottom: 15px;
        }
        
        .footer-contact h4,
        .footer-social h4 {
            margin-bottom: 20px;
            color: #667eea;
        }
        
        .footer-contact p {
            margin-bottom: 10px;
        }
        
        .footer-contact i {
            margin-right: 10px;
            color: #667eea;
        }
        
        .social-links {
            display: flex;
            gap: 15px;
        }
        
        .social-links a {
            width: 40px;
            height: 40px;
            background: #667eea;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            text-decoration: none;
            transition: transform 0.3s ease;
        }
        
        .social-links a:hover {
            transform: translateY(-3px);
        }
        
        .footer-bottom {
            border-top: 1px solid #4a5568;
            padding-top: 30px;
            text-align: center;
            color: #a0aec0;
        }
        
        /* Animations */
        @keyframes slideUp {
            from {
                opacity: 0;
                transform: translateY(50px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        @keyframes fadeIn {
            from {
                opacity: 0;
                transform: scale(0.8);
            }
            to {
                opacity: 1;
                transform: scale(1);
            }
        }
        
        .animate-slide-up {
            animation: slideUp 1s ease-out;
        }
        
        .animate-fade-in {
            animation: fadeIn 1s ease-out;
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .cover-title {
                font-size: 2.5em;
            }
            
            .cover-metrics {
                flex-direction: column;
                align-items: center;
            }
            
            .section-content {
                padding: 40px 20px;
            }
            
            .price-comparison {
                flex-direction: column;
            }
            
            .vs-divider {
                margin: 20px 0;
            }
            
            .projection-timeline {
                flex-direction: column;
                gap: 20px;
            }
            
            .timeline-connector {
                width: 2px;
                height: 40px;
                background: linear-gradient(180deg, #667eea, #764ba2);
            }
        }
        """
    
    def _get_complete_javascript(self, project_data: Dict[str, Any]) -> str:
        """Retourne le JavaScript complet pour les animations et graphiques."""
        return f"""
        // Animation des compteurs
        function animateCounters() {{
            const counters = document.querySelectorAll('.metric-value[data-value]');
            counters.forEach(counter => {{
                const target = parseInt(counter.getAttribute('data-value'));
                const count = +counter.innerText.replace(/[^0-9]/g, '');
                const speed = target / 100;
                
                if (count < target) {{
                    counter.innerText = Math.ceil(count + speed).toLocaleString();
                    setTimeout(() => animateCounters(), 20);
                }}
            }});
        }}
        
        // FAQ Toggle
        function toggleFAQ(index) {{
            const answer = document.getElementById(`faq-answer-${{index}}`);
            const icon = document.getElementById(`faq-icon-${{index}}`);
            
            answer.classList.toggle('open');
            icon.classList.toggle('rotated');
        }}
        
        // Graphiques Chart.js
        function initCharts() {{
            // Graphique énergétique
            const energyCtx = document.getElementById('energyChart').getContext('2d');
            new Chart(energyCtx, {{
                type: 'doughnut',
                data: {{
                    labels: ['Production Solaire', 'Réseau'],
                    datasets: [{{
                        data: [{project_data['total_production']}, {max(0, project_data['total_consumption'] - project_data['total_production'])}],
                        backgroundColor: ['#667eea', '#e2e8f0'],
                        borderWidth: 0
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{
                            position: 'bottom'
                        }}
                    }}
                }}
            }});
            
            // Graphique des économies
            const savingsCtx = document.getElementById('savingsChart').getContext('2d');
            const years = Array.from({{length: 20}}, (_, i) => i + 1);
            const cumulativeSavings = years.map(year => year * {project_data['annual_savings']});
            
            new Chart(savingsCtx, {{
                type: 'line',
                data: {{
                    labels: years,
                    datasets: [{{
                        label: 'Économies Cumulées (€)',
                        data: cumulativeSavings,
                        borderColor: '#667eea',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        fill: true,
                        tension: 0.4
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{
                            display: false
                        }}
                    }},
                    scales: {{
                        y: {{
                            beginAtZero: true,
                            ticks: {{
                                callback: function(value) {{
                                    return value.toLocaleString() + ' €';
                                }}
                            }}
                        }}
                    }}
                }}
            }});
        }}
        
        // Intersection Observer pour animations
        function setupScrollAnimations() {{
            const observerOptions = {{
                threshold: 0.1,
                rootMargin: '0px 0px -50px 0px'
            }};
            
            const observer = new IntersectionObserver((entries) => {{
                entries.forEach(entry => {{
                    if (entry.isIntersecting) {{
                        entry.target.style.opacity = '1';
                        entry.target.style.transform = 'translateY(0)';
                    }}
                }});
            }}, observerOptions);
            
            // Observer tous les éléments avec animation
            document.querySelectorAll('.metric-card, .financial-card, .environmental-card, .chart-container').forEach(el => {{
                el.style.opacity = '0';
                el.style.transform = 'translateY(30px)';
                el.style.transition = 'all 0.6s ease-out';
                observer.observe(el);
            }});
        }}
        
        // Initialisation au chargement
        document.addEventListener('DOMContentLoaded', function() {{
            setTimeout(animateCounters, 500);
            setTimeout(initCharts, 1000);
            setupScrollAnimations();
        }});
        """
    
    def _get_error_template(self, error_message: str) -> str:
        """Template d'erreur en cas de problème de génération."""
        return f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Erreur - Génération de Proposition</title>
    <style>
        body {{ font-family: Arial, sans-serif; background: #f8f9fa; padding: 40px; }}
        .error-container {{ max-width: 600px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; }}
        .error-title {{ color: #e53e3e; margin-bottom: 20px; }}
        .error-message {{ background: #fed7d7; padding: 20px; border-radius: 5px; color: #742a2a; }}
    </style>
</head>
<body>
    <div class="error-container">
        <h1 class="error-title">Erreur de Génération</h1>
        <div class="error-message">
            <p>Une erreur s'est produite lors de la génération de la proposition :</p>
            <p><strong>{error_message}</strong></p>
            <p>Veuillez vérifier vos données et réessayer.</p>
        </div>
    </div>
</body>
</html>
        """
    
    def _get_premium_turquoise_css(self) -> str:
        """CSS pour le template turquoise premium."""
        return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Open Sans', sans-serif;
            line-height: 1.6;
            color: #2C3E50;
            background: #FFFFFF;
        }
        
        .turquoise-container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
        }
        
        .turquoise-header {
            background: linear-gradient(135deg, #4ECDC4 0%, #44A08D 100%);
            color: white;
            padding: 60px 40px;
            text-align: center;
            border-radius: 20px;
            margin-bottom: 30px;
        }
        
        .turquoise-title {
            font-family: 'Montserrat', sans-serif;
            font-size: 48px;
            font-weight: 700;
            margin-bottom: 20px;
        }
        
        .turquoise-subtitle {
            font-size: 24px;
            opacity: 0.9;
            margin-bottom: 30px;
        }
        
        .turquoise-price-box {
            background: rgba(255,255,255,0.2);
            padding: 30px;
            border-radius: 15px;
            display: inline-block;
        }
        
        .turquoise-price {
            font-size: 54px;
            font-weight: 700;
            margin: 15px 0;
        }
        
        .turquoise-metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 30px;
            margin: 40px 0;
            padding: 0 20px;
        }
        
        .turquoise-metric-card {
            color: white;
            padding: 30px;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
        }
        
        .turquoise-metric-card.primary {
            background: #4ECDC4;
        }
        
        .turquoise-metric-card.secondary {
            background: #44A08D;
        }
        
        .turquoise-metric-card.accent {
            background: #26C6DA;
        }
        
        .turquoise-metric-value {
            font-size: 36px;
            font-weight: 700;
            margin-bottom: 10px;
        }
        
        .turquoise-benefits {
            background: #f8f9fa;
            padding: 40px;
            border-radius: 20px;
            margin: 30px 20px;
        }
        
        .turquoise-benefits-title {
            color: #4ECDC4;
            margin-bottom: 20px;
            font-family: 'Montserrat', sans-serif;
            font-size: 28px;
        }
        
        .turquoise-benefits-text {
            font-size: 18px;
            line-height: 1.6;
            margin-bottom: 30px;
        }
        
        .turquoise-cta {
            background: #4ECDC4;
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            font-weight: 600;
        }
        
        .turquoise-footer {
            background: #2C3E50;
            color: white;
            padding: 40px;
            text-align: center;
            margin-top: 40px;
        }
        
        @media (max-width: 768px) {
            .turquoise-title {
                font-size: 36px;
            }
            
            .turquoise-price {
                font-size: 42px;
            }
            
            .turquoise-metrics {
                grid-template-columns: 1fr;
                padding: 0 10px;
            }
        }
        """
    
    def _generate_turquoise_header(self, project_data: Dict[str, Any]) -> str:
        """Génère l'en-tête turquoise premium."""
        return f"""
        <div class="turquoise-header">
            <h1 class="turquoise-title">PROPOSITION AUTOCONSOMMATION</h1>
            <h2 class="turquoise-subtitle">Projet pour {project_data.get('client_name', '[NOM DU CLIENT]')}</h2>
            <div class="turquoise-price-box">
                <h3>Prix Garanti</h3>
                <div class="turquoise-price">{project_data.get('solar_price', 15.0):.1f} ct/kWh</div>
                <p>Économie sur 20 ans: {project_data.get('total_savings_20y', 150000):,} €</p>
            </div>
        </div>
        """.replace(",", " ")
    
    def _generate_turquoise_metrics(self, project_data: Dict[str, Any]) -> str:
        """Génère les métriques turquoise."""
        return f"""
        <div class="turquoise-metrics">
            <div class="turquoise-metric-card primary">
                <div class="turquoise-metric-value">{project_data.get('annual_savings', 7500):,} €</div>
                <p>Économie Annuelle</p>
            </div>
            
            <div class="turquoise-metric-card secondary">
                <div class="turquoise-metric-value">{project_data.get('power_kwc', 100)} kWc</div>
                <p>Puissance Installée</p>
            </div>
            
            <div class="turquoise-metric-card accent">
                <div class="turquoise-metric-value">{project_data.get('co2_avoided', 7.5):.1f} T</div>
                <p>CO₂ Évité/An</p>
            </div>
        </div>
        """.replace(",", " ")
    
    def _generate_turquoise_benefits(self, project_data: Dict[str, Any]) -> str:
        """Génère la section avantages turquoise."""
        return f"""
        <div class="turquoise-benefits">
            <h3 class="turquoise-benefits-title">Votre Avantage Principal</h3>
            <p class="turquoise-benefits-text">
                En rejoignant ce projet d'autoconsommation collective, vous bénéficiez d'une électricité 
                produite localement à un tarif fixe et compétitif, à l'abri des hausses du marché.
                Cela représente une économie de {project_data.get('savings_percentage', 20):.1f}% 
                sur votre facture d'électricité.
            </p>
            <div class="turquoise-cta">
                <strong>C'est simple, sécurisé et sans investissement de votre part !</strong>
            </div>
        </div>
        """
    
    def _generate_turquoise_footer(self, project_data: Dict[str, Any]) -> str:
        """Génère le pied de page turquoise."""
        return f"""
        <div class="turquoise-footer">
            <h3>Votre Contact OptimPV</h3>
            <p>📞 01 23 45 67 89 | ✉️ contact@optimpv.fr</p>
            <p>Document généré le {datetime.now().strftime('%d/%m/%Y')}</p>
        </div>
        """