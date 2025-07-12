"""
Générateur de graphiques commerciaux professionnels pour propositions DOCX
Focus sur l'impact visuel et la persuasion commerciale
"""

import os
import tempfile
import io
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
import numpy as np

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    from matplotlib.patches import FancyBboxPatch, Circle, Wedge
    import matplotlib.colors as mcolors
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class CommercialChartGenerator:
    """
    Générateur de graphiques commerciaux haute qualité
    Créé spécifiquement pour les propositions commerciales OptimPV
    """
    
    def __init__(self):
        """Initialise le générateur avec la charte graphique OptimPV"""
        self.output_dir = tempfile.mkdtemp()
        
        # Charte graphique commerciale OptimPV
        self.colors = {
            'primary': '#27ae60',      # Vert OptimPV
            'secondary': '#2ecc71',    # Vert clair
            'accent': '#f39c12',       # Orange énergie
            'danger': '#e74c3c',       # Rouge économies
            'info': '#3498db',         # Bleu réseau
            'success': '#16a085',      # Vert foncé
            'warning': '#f1c40f',      # Jaune
            'dark': '#2c3e50',         # Bleu foncé
            'light': '#ecf0f1',        # Gris clair
            'gradient_start': '#27ae60',
            'gradient_end': '#2ecc71'
        }
        
        # Configuration haute qualité
        self.dpi = 300
        self.style = 'seaborn-v0_8-whitegrid' if hasattr(plt, 'style') else 'default'
        
        if MATPLOTLIB_AVAILABLE:
            plt.style.use('default')  # Fallback sûr
            plt.rcParams.update({
                'font.family': 'sans-serif',
                'font.sans-serif': ['Arial', 'DejaVu Sans', 'Liberation Sans'],
                'font.size': 12,
                'axes.linewidth': 1.5,
                'grid.alpha': 0.3,
                'figure.facecolor': 'white',
                'axes.facecolor': 'white'
            })
    
    def generate_hero_dashboard(self, data: Dict[str, Any]) -> str:
        """
        Génère un dashboard héro commercial - Premier impact visuel
        Combine tous les indicateurs clés en une seule image percutante
        """
        if not MATPLOTLIB_AVAILABLE:
            return None
            
        try:
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
            fig.suptitle('🌱 VOTRE PROJET SOLAIRE EN UN COUP D\'ŒIL', 
                        fontsize=24, fontweight='bold', color=self.colors['dark'], y=0.95)
            
            # 1. Jauges d'autonomie et autoconsommation (TOP LEFT)
            self._create_dual_gauge(ax1, data)
            
            # 2. Comparaison des coûts (TOP RIGHT)  
            self._create_cost_comparison_bars(ax2, data)
            
            # 3. Évolution des économies (BOTTOM LEFT)
            self._create_savings_evolution_curve(ax3, data)
            
            # 4. Répartition énergétique (BOTTOM RIGHT)
            self._create_energy_distribution_pie(ax4, data)
            
            plt.tight_layout()
            plt.subplots_adjust(top=0.90, hspace=0.3, wspace=0.3)
            
            # Sauvegarder
            output_path = os.path.join(self.output_dir, 'hero_dashboard.png')
            plt.savefig(output_path, dpi=self.dpi, bbox_inches='tight', 
                       facecolor='white', edgecolor='none')
            plt.close()
            
            return output_path
            
        except Exception as e:
            print(f"❌ Erreur dashboard héro: {e}")
            return None
    
    def _create_dual_gauge(self, ax, data: Dict[str, Any]):
        """Crée des jauges doubles pour autonomie/autoconsommation"""
        autonomy = data.get('autonomy_rate', 40.9)
        autocons = data.get('autoconsumption_rate', 78.2)
        
        ax.set_xlim(-1.5, 1.5)
        ax.set_ylim(-1.2, 1.2)
        ax.set_aspect('equal')
        ax.axis('off')
        
        # Jauge autonomie (gauche)
        self._draw_single_gauge(ax, -0.7, 0, autonomy, "AUTONOMIE", self.colors['primary'])
        
        # Jauge autoconsommation (droite)
        self._draw_single_gauge(ax, 0.7, 0, autocons, "AUTOCONSOMMATION", self.colors['accent'])
        
        ax.set_title('📊 INDICATEURS DE PERFORMANCE', fontsize=14, fontweight='bold', 
                    color=self.colors['dark'], pad=20)
    
    def _draw_single_gauge(self, ax, x_center, y_center, value, label, color):
        """Dessine une jauge circulaire moderne"""
        radius = 0.4
        
        # Cercle de fond
        bg_circle = Circle((x_center, y_center), radius, 
                          facecolor=self.colors['light'], edgecolor='none')
        ax.add_patch(bg_circle)
        
        # Arc de progression
        theta1, theta2 = 180, 180 - (value/100 * 180)
        wedge = Wedge((x_center, y_center), radius, theta2, theta1, 
                     facecolor=color, alpha=0.8, width=0.1)
        ax.add_patch(wedge)
        
        # Texte central
        ax.text(x_center, y_center + 0.1, f'{value:.1f}%', 
               ha='center', va='center', fontsize=16, fontweight='bold', 
               color=self.colors['dark'])
        ax.text(x_center, y_center - 0.15, label, 
               ha='center', va='center', fontsize=10, fontweight='bold', 
               color=color)
    
    def _create_cost_comparison_bars(self, ax, data: Dict[str, Any]):
        """Barres de comparaison des coûts - Impact visuel fort"""
        cout_sans_pv = data.get('cout_sans_pv', 9000)
        cout_avec_pv = data.get('cout_avec_pv_total', 6500)
        economie = cout_sans_pv - cout_avec_pv
        
        categories = ['SANS Solaire', 'AVEC Solaire']
        values = [cout_sans_pv, cout_avec_pv]
        colors = [self.colors['danger'], self.colors['success']]
        
        bars = ax.bar(categories, values, color=colors, alpha=0.8, width=0.6)
        
        # Annotations des valeurs
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 100,
                   f'{value:,.0f}€/an'.replace(',', ' '),
                   ha='center', va='bottom', fontweight='bold', fontsize=12)
        
        # Flèche d'économie
        ax.annotate(f'💰 ÉCONOMIE\n{economie:,.0f}€/an'.replace(',', ' '), 
                   xy=(0.5, max(values)/2), xytext=(0.5, max(values)*0.8),
                   ha='center', va='center', fontsize=12, fontweight='bold',
                   color=self.colors['primary'],
                   arrowprops=dict(arrowstyle='<->', color=self.colors['primary'], lw=3))
        
        ax.set_title('💸 COMPARAISON DES COÛTS ANNUELS', fontsize=14, fontweight='bold', 
                    color=self.colors['dark'])
        ax.set_ylabel('Coût annuel (€)', fontsize=12)
        ax.grid(True, alpha=0.3)
    
    def _create_savings_evolution_curve(self, ax, data: Dict[str, Any]):
        """Courbe d'évolution des économies - Vision long terme"""
        economie_annuelle = data.get('economie_annuelle_calculee', 2500)
        duree = data.get('duree_projet', 20)
        taux_inflation = data.get('taux_inflation', 0.02)
        
        years = np.arange(0, duree + 1)
        # Calcul avec inflation progressive
        economies_cumul = []
        total = 0
        for year in years:
            if year == 0:
                economies_cumul.append(0)
            else:
                annual_saving = economie_annuelle * (1 + taux_inflation) ** year
                total += annual_saving
                economies_cumul.append(total)
        
        # Courbe principale
        ax.plot(years, economies_cumul, color=self.colors['primary'], linewidth=4, 
               marker='o', markersize=6, alpha=0.9)
        
        # Zone sous la courbe
        ax.fill_between(years, economies_cumul, alpha=0.3, color=self.colors['secondary'])
        
        # Points remarquables
        milestones = [5, 10, 15, 20]
        for milestone in milestones:
            if milestone <= duree:
                idx = milestone
                ax.plot(milestone, economies_cumul[idx], 'o', markersize=10, 
                       color=self.colors['accent'], markeredgecolor='white', markeredgewidth=2)
                ax.annotate(f'{economies_cumul[idx]/1000:.0f}K€', 
                           (milestone, economies_cumul[idx]), 
                           xytext=(5, 10), textcoords='offset points',
                           fontweight='bold', fontsize=10, color=self.colors['dark'])
        
        ax.set_title('📈 ÉVOLUTION DE VOS ÉCONOMIES CUMULÉES', fontsize=14, fontweight='bold', 
                    color=self.colors['dark'])
        ax.set_xlabel('Années', fontsize=12)
        ax.set_ylabel('Économies cumulées (€)', fontsize=12)
        ax.grid(True, alpha=0.3)
        
        # Formatage de l'axe Y
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1000:.0f}K€'))
    
    def _create_energy_distribution_pie(self, ax, data: Dict[str, Any]):
        """Camembert de répartition énergétique - Compréhension rapide"""
        solar_consumption = data.get('total_autoconsumption', 18.5) * 1000  # MWh to kWh
        grid_consumption = data.get('total_grid_purchase', 26.7) * 1000
        
        labels = ['🌞 Énergie Solaire\nAutoconsommée', '⚡ Énergie Réseau\nAchetée']
        sizes = [solar_consumption, grid_consumption]
        colors = [self.colors['accent'], self.colors['info']]
        explode = (0.1, 0)  # Explode solar section
        
        wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors, 
                                         autopct=lambda pct: f'{pct:.1f}%\n({pct/100*sum(sizes)/1000:.1f} MWh)',
                                         explode=explode, shadow=True, startangle=90,
                                         textprops={'fontsize': 10, 'fontweight': 'bold'})
        
        # Améliorer l'apparence
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        ax.set_title('🔋 RÉPARTITION DE VOTRE CONSOMMATION', fontsize=14, fontweight='bold', 
                    color=self.colors['dark'])
    
    def generate_roi_timeline(self, data: Dict[str, Any]) -> str:
        """Génère une timeline ROI commerciale percutante"""
        if not MATPLOTLIB_AVAILABLE:
            return None
            
        try:
            fig, ax = plt.subplots(figsize=(14, 8))
            
            # Données financières
            economie_annuelle = data.get('economie_annuelle_calculee', 2500)
            duree = data.get('duree_projet', 20)
            
            # Calcul du ROI progressif
            years = np.arange(1, duree + 1)
            roi_cumul = np.cumsum([economie_annuelle * (1.02 ** year) for year in years])
            
            # Courbe ROI
            ax.plot(years, roi_cumul/1000, color=self.colors['primary'], linewidth=5, 
                   marker='D', markersize=8, markerfacecolor=self.colors['accent'])
            
            # Zone de rentabilité
            ax.fill_between(years, roi_cumul/1000, alpha=0.2, color=self.colors['success'])
            
            # Milestones importantes
            milestones = {
                5: "1ère période\nd'amortissement",
                10: "ROI\nsignificatif",
                15: "Bénéfices\nsustantiels", 
                20: f"TOTAL\n{roi_cumul[-1]/1000:.0f}K€"
            }
            
            for year, label in milestones.items():
                if year <= duree:
                    value = roi_cumul[year-1]/1000
                    ax.plot(year, value, 'o', markersize=15, 
                           color=self.colors['danger'], markeredgecolor='white', markeredgewidth=3)
                    ax.annotate(label, (year, value), xytext=(0, 30), 
                               textcoords='offset points', ha='center',
                               fontweight='bold', fontsize=11, color=self.colors['dark'],
                               bbox=dict(boxstyle="round,pad=0.3", facecolor=self.colors['light'], alpha=0.8))
            
            ax.set_title('💰 RETOUR SUR INVESTISSEMENT - VISION 20 ANS', 
                        fontsize=18, fontweight='bold', color=self.colors['dark'], pad=20)
            ax.set_xlabel('Années du projet', fontsize=14, fontweight='bold')
            ax.set_ylabel('Économies cumulées (K€)', fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3)
            
            # Styling
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_linewidth(2)
            ax.spines['bottom'].set_linewidth(2)
            
            plt.tight_layout()
            
            output_path = os.path.join(self.output_dir, 'roi_timeline.png')
            plt.savefig(output_path, dpi=self.dpi, bbox_inches='tight', 
                       facecolor='white', edgecolor='none')
            plt.close()
            
            return output_path
            
        except Exception as e:
            print(f"❌ Erreur timeline ROI: {e}")
            return None
    
    def generate_competitive_advantage(self, data: Dict[str, Any]) -> str:
        """Génère un graphique d'avantage concurrentiel"""
        if not MATPLOTLIB_AVAILABLE:
            return None
            
        try:
            fig, ax = plt.subplots(figsize=(12, 8))
            
            # Données comparatives
            scenarios = ['Sans Solaire', 'Concurrence\nMoyenne', 'OptimPV\nOptimisé']
            cout_annuel = [
                data.get('cout_sans_pv', 9000),
                data.get('cout_sans_pv', 9000) * 0.85,  # 15% économie concurrence
                data.get('cout_avec_pv_total', 6500)
            ]
            
            colors = [self.colors['danger'], self.colors['warning'], self.colors['success']]
            
            # Barres avec gradient effect
            bars = ax.bar(scenarios, cout_annuel, color=colors, alpha=0.8, width=0.6)
            
            # Annotations avec économies
            for i, (bar, cout) in enumerate(zip(bars, cout_annuel)):
                height = bar.get_height()
                
                # Valeur
                ax.text(bar.get_x() + bar.get_width()/2., height + 200,
                       f'{cout:,.0f}€/an'.replace(',', ' '),
                       ha='center', va='bottom', fontweight='bold', fontsize=14)
                
                # Économie vs sans solaire
                if i > 0:
                    economie = cout_annuel[0] - cout
                    pourcentage = (economie / cout_annuel[0]) * 100
                    ax.text(bar.get_x() + bar.get_width()/2., height/2,
                           f'-{economie:,.0f}€\n({pourcentage:.0f}%)'.replace(',', ' '),
                           ha='center', va='center', fontweight='bold', fontsize=12,
                           color='white', 
                           bbox=dict(boxstyle="round,pad=0.3", facecolor=colors[i], alpha=0.9))
            
            ax.set_title('🏆 OPTIMPV : L\'AVANTAGE CONCURRENTIEL', 
                        fontsize=18, fontweight='bold', color=self.colors['dark'], pad=20)
            ax.set_ylabel('Coût énergétique annuel (€)', fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3, axis='y')
            
            # Styling
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            
            plt.tight_layout()
            
            output_path = os.path.join(self.output_dir, 'competitive_advantage.png')
            plt.savefig(output_path, dpi=self.dpi, bbox_inches='tight', 
                       facecolor='white', edgecolor='none')
            plt.close()
            
            return output_path
            
        except Exception as e:
            print(f"❌ Erreur avantage concurrentiel: {e}")
            return None
    
    def generate_all_commercial_charts(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Génère tous les graphiques commerciaux"""
        charts = {}
        
        print("🎨 Génération des graphiques commerciaux...")
        
        # Dashboard héro principal
        hero_path = self.generate_hero_dashboard(data)
        if hero_path:
            charts['hero_dashboard'] = hero_path
            print("  ✅ Dashboard héro")
        
        # Timeline ROI
        roi_path = self.generate_roi_timeline(data)
        if roi_path:
            charts['roi_timeline'] = roi_path
            print("  ✅ Timeline ROI")
        
        # Avantage concurrentiel
        competitive_path = self.generate_competitive_advantage(data)
        if competitive_path:
            charts['competitive_advantage'] = competitive_path
            print("  ✅ Avantage concurrentiel")
        
        print(f"✅ {len(charts)} graphiques commerciaux générés")
        return charts
    
    def cleanup_charts(self):
        """Nettoie les fichiers temporaires"""
        try:
            import shutil
            if os.path.exists(self.output_dir):
                shutil.rmtree(self.output_dir)
                print("🧹 Graphiques temporaires nettoyés")
        except Exception as e:
            print(f"⚠️ Erreur nettoyage: {e}")