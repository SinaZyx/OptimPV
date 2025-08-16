# Visualisations Interactives - Graphiques Plotly

## Vue d'ensemble

Les visualisations interactives d'OptimPV utilisent Plotly pour créer des graphiques dynamiques permettant l'exploration visuelle des résultats d'optimisation et l'ajustement en temps réel des paramètres.

## Graphique Prix vs Bénéfice Client

### Implémentation Principale
```python
def create_price_analysis_chart(self, prix_range, benefits_data):
 """
 Crée le graphique principal Prix HT vs Bénéfice Client
 Avec marqueurs pour prix sélectionné et prix optimal
 """
 import plotly.graph_objects as go
 from plotly.subplots import make_subplots

 fig = go.Figure()

 # Courbe principale Prix vs Bénéfice
 fig.add_trace(go.Scatter(
 x=prix_range,
 y=benefits_data,
 mode='lines',
 name='Bénéfice Client Annuel',
 line=dict(color='#2E86AB', width=3),
 hovertemplate=(
 '<b>Prix de vente HT:</b> %{x:.4f} €/kWh<br>'
 '<b>Bénéfice client:</b> %{y:.0f} €/an<br>'
 '<extra></extra>'
 )
 ))

 # Marqueur prix sélectionné (slider)
 if hasattr(self, 'prix_selectionne'):
 benefit_selectionne = self._calculate_benefit_at_price(self.prix_selectionne)

 fig.add_trace(go.Scatter(
 x=[self.prix_selectionne],
 y=[benefit_selectionne],
 mode='markers',
 name='Prix Sélectionné',
 marker=dict(
 color='#F18F01',
 size=12,
 symbol='circle',
 line=dict(color='white', width=2)
 ),
 hovertemplate=(
 '<b>Prix sélectionné:</b> %{x:.4f} €/kWh<br>'
 '<b>Bénéfice:</b> %{y:.0f} €/an<br>'
 '<extra></extra>'
 )
 ))

 # Marqueur prix optimal (si optimisation réussie)
 if hasattr(self, 'prix_optimal') and self.prix_optimal:
 benefit_optimal = self._calculate_benefit_at_price(self.prix_optimal)

 fig.add_trace(go.Scatter(
 x=[self.prix_optimal],
 y=[benefit_optimal],
 mode='markers',
 name='Prix Optimal',
 marker=dict(
 color='#C73E1D',
 size=15,
 symbol='star',
 line=dict(color='white', width=2)
 ),
 hovertemplate=(
 '<b>Prix optimal:</b> %{x:.4f} €/kWh<br>'
 '<b>Bénéfice:</b> %{y:.0f} €/an<br>'
 '<extra></extra>'
 )
 ))

 # Ligne de référence (bénéfice = 0)
 fig.add_hline(
 y=0,
 line_dash="dash",
 line_color="gray",
 annotation_text="Équilibre client (0€ bénéfice)",
 annotation_position="bottom right"
 )

 # Configuration du layout
 fig.update_layout(
 title={
 'text': 'Analyse Prix de Vente HT vs Bénéfice Client Annuel',
 'x': 0.5,
 'xanchor': 'center',
 'font': {'size': 16, 'color': '#2E86AB'}
 },
 xaxis_title='Prix de Vente HT (€/kWh)',
 yaxis_title='Bénéfice Client Annuel (€)',

 # Styling
 plot_bgcolor='white',
 paper_bgcolor='white',

 # Grille
 xaxis=dict(
 gridcolor='lightgray',
 gridwidth=1,
 zeroline=True,
 zerolinecolor='gray'
 ),
 yaxis=dict(
 gridcolor='lightgray',
 gridwidth=1,
 zeroline=True,
 zerolinecolor='gray'
 ),

 # Légende
 legend=dict(
 orientation="h",
 yanchor="bottom",
 y=1.02,
 xanchor="right",
 x=1
 ),

 # Marges
 margin=dict(l=80, r=80, t=100, b=80),

 # Interactivité
 hovermode='closest'
 )

 return fig

def _calculate_benefit_at_price(self, prix_vente_ht):
 """
 Calcule le bénéfice client à un prix donné
 """
 # Données projet
 autoconso_kwh = self.analysis_engine.get_autoconsommation_annuelle()
 tarif_edf_ttc = self.analysis_engine.get_tarif_edf_reference()

 # Prix TTC client (avec TVA 20%)
 prix_vente_ttc = prix_vente_ht * 1.20

 # Bénéfice = Économies vs tarif EDF
 benefice_unitaire = tarif_edf_ttc - prix_vente_ttc
 benefice_total = benefice_unitaire * autoconso_kwh

 return benefice_total
```

### Slider Interactif
```python
def create_interactive_price_slider(self):
 """
 Crée un slider pour ajustement interactif du prix
 """
 # Bornes du slider
 prix_min = max(self.prix_plancher, self.lcoe)
 prix_max = min(self.tarif_edf / 1.20, self.prix_plancher * 2) # Prix EDF HT

 # Valeur initiale
 if hasattr(self, 'prix_optimal') and self.prix_optimal:
 initial_value = self.prix_optimal
 else:
 initial_value = (prix_min + prix_max) / 2

 # Slider Streamlit
 prix_selectionne = st.slider(
 label=" Prix de Vente Sélectionné (€/kWh HT)",
 min_value=float(prix_min),
 max_value=float(prix_max),
 value=float(initial_value),
 step=0.0001,
 format="%.4f",
 key="prix_slider_interactive",
 help="Ajustez le prix pour voir l'impact en temps réel"
 )

 # Mise à jour temps réel des métriques
 self._update_realtime_metrics(prix_selectionne)

 return prix_selectionne

def _update_realtime_metrics(self, prix_selectionne):
 """
 Met à jour les métriques en temps réel selon le prix sélectionné
 """
 # Calcul des métriques au prix sélectionné
 self.analysis_engine.update_selling_price(prix_selectionne)
 metrics = self.analysis_engine.calculate_all_metrics()

 # Affichage temps réel
 col1, col2, col3, col4 = st.columns(4)

 with col1:
 tri_value = metrics.get('tri_projet', 0) * 100
 st.metric(
 "TRI Projet",
 f"{tri_value:.1f}%",
 delta=f"{tri_value - 8.0:.1f}pp" if tri_value else None
 )

 with col2:
 payback_value = metrics.get('payback_equity', 0)
 st.metric(
 "Payback",
 f"{payback_value:.1f} ans",
 delta=f"{18.0 - payback_value:.1f} ans" if payback_value else None
 )

 with col3:
 benefice_client = self._calculate_benefit_at_price(prix_selectionne)
 st.metric(
 "Bénéfice Client",
 f"{benefice_client:.0f} €/an",
 delta="Positif" if benefice_client > 0 else "Négatif"
 )

 with col4:
 marge_vs_plancher = ((prix_selectionne / self.prix_plancher) - 1) * 100
 st.metric(
 "Marge vs Plancher",
 f"{marge_vs_plancher:.1f}%",
 delta=f"+{marge_vs_plancher:.1f}%" if marge_vs_plancher > 0 else f"{marge_vs_plancher:.1f}%"
 )
```

## Graphique Répartition Énergétique

### Camembert Autoconsommation/Surplus
```python
def create_energy_distribution_pie(self):
 """
 Crée un camembert de la répartition énergétique
 Autoconsommation vs Surplus injecté
 """
 # Données énergétiques
 production_totale = self.analysis_engine.get_annual_production()
 autoconsommation = self.analysis_engine.get_autoconsommation_annuelle()
 surplus = production_totale - autoconsommation

 # Calcul des pourcentages
 pct_autoconso = (autoconsommation / production_totale) * 100
 pct_surplus = (surplus / production_totale) * 100

 # Données pour le graphique
 labels = ['Autoconsommation', 'Surplus Injecté']
 values = [autoconsommation, surplus]
 colors = ['#2E86AB', '#F18F01']

 fig = go.Figure(data=[go.Pie(
 labels=labels,
 values=values,
 marker_colors=colors,

 # Style du texte
 textinfo='label+percent+value',
 texttemplate='<b>%{label}</b><br>%{percent}<br>%{value:.0f} kWh',
 textfont_size=12,

 # Style des bordures
 marker=dict(
 line=dict(color='white', width=2)
 ),

 # Hover template
 hovertemplate=(
 '<b>%{label}</b><br>'
 'Quantité: %{value:.0f} kWh<br>'
 'Pourcentage: %{percent}<br>'
 '<extra></extra>'
 ),

 # Explosion légère pour l'autoconsommation
 pull=[0.1, 0]
 )])

 # Configuration layout
 fig.update_layout(
 title={
 'text': f'Répartition Annuelle Énergie Produite<br><sub>Total: {production_totale:.0f} kWh/an</sub>',
 'x': 0.5,
 'xanchor': 'center',
 'font': {'size': 16, 'color': '#2E86AB'}
 },

 # Annotations avec valeurs
 annotations=[
 dict(
 text=f'<b>Taux d\'autoconsommation</b><br>{pct_autoconso:.1f}%',
 x=0.82, y=0.8,
 font_size=14,
 showarrow=False,
 bgcolor="rgba(255,255,255,0.8)",
 bordercolor="gray",
 borderwidth=1
 )
 ],

 # Style général
 plot_bgcolor='white',
 paper_bgcolor='white',

 # Marges
 margin=dict(l=20, r=20, t=80, b=20),

 # Taille
 height=400
 )

 return fig

def display_energy_distribution_details(self):
 """
 Affiche les détails de la répartition énergétique
 """
 production_totale = self.analysis_engine.get_annual_production()
 autoconsommation = self.analysis_engine.get_autoconsommation_annuelle()
 surplus = production_totale - autoconsommation

 st.subheader(" Détails Énergétiques")

 col1, col2, col3 = st.columns(3)

 with col1:
 st.metric(
 label="Production Totale",
 value=f"{production_totale:.0f} kWh/an",
 help="Énergie totale produite par l'installation"
 )

 with col2:
 pct_autoconso = (autoconsommation / production_totale) * 100
 st.metric(
 label="Autoconsommation",
 value=f"{autoconsommation:.0f} kWh/an",
 delta=f"{pct_autoconso:.1f}% du total"
 )

 with col3:
 pct_surplus = (surplus / production_totale) * 100
 st.metric(
 label="Surplus Injecté",
 value=f"{surplus:.0f} kWh/an",
 delta=f"{pct_surplus:.1f}% du total"
 )

 # Recommandations d'optimisation
 if pct_autoconso < 60:
 st.warning(
 f" Taux d'autoconsommation faible ({pct_autoconso:.1f}%). "
 "Considérer l'ajout de stockage ou l'ajustement du profil de consommation."
 )
 elif pct_autoconso > 90:
 st.info(
 f" Excellent taux d'autoconsommation ({pct_autoconso:.1f}%). "
 "Le système est bien dimensionné pour les besoins."
 )
 else:
 st.success(
 f" Bon équilibre autoconsommation/injection ({pct_autoconso:.1f}%)."
 )
```

## Graphiques de Comparaison

### Évolution Métriques vs Prix
```python
def create_metrics_vs_price_chart(self):
 """
 Graphique multi-axes: TRI, Payback, Bénéfice vs Prix
 """
 # Gamme de prix pour l'analyse
 prix_range = np.linspace(self.prix_plancher, self.tarif_edf/1.20, 50)

 # Calcul des métriques pour chaque prix
 tri_values = []
 payback_values = []
 benefit_values = []

 for prix in prix_range:
 self.analysis_engine.update_selling_price(prix)
 metrics = self.analysis_engine.calculate_all_metrics()

 tri_values.append(metrics.get('tri_projet', 0) * 100)
 payback_values.append(metrics.get('payback_equity', 0))
 benefit_values.append(self._calculate_benefit_at_price(prix))

 # Création du graphique avec axes secondaires
 fig = make_subplots(
 specs=[[{"secondary_y": True}]],
 subplot_titles=('Évolution des Métriques selon le Prix de Vente',)
 )

 # TRI (axe principal)
 fig.add_trace(
 go.Scatter(
 x=prix_range,
 y=tri_values,
 name='TRI Projet (%)',
 line=dict(color='#2E86AB', width=2),
 yaxis='y'
 ),
 secondary_y=False
 )

 # Payback (axe principal)
 fig.add_trace(
 go.Scatter(
 x=prix_range,
 y=payback_values,
 name='Payback (ans)',
 line=dict(color='#C73E1D', width=2),
 yaxis='y'
 ),
 secondary_y=False
 )

 # Bénéfice client (axe secondaire)
 fig.add_trace(
 go.Scatter(
 x=prix_range,
 y=benefit_values,
 name='Bénéfice Client (€)',
 line=dict(color='#F18F01', width=2),
 yaxis='y2'
 ),
 secondary_y=True
 )

 # Lignes de contraintes
 if hasattr(self, 'constraints'):
 # Ligne TRI minimum
 if self.constraints.get('tri_min'):
 fig.add_hline(
 y=self.constraints['tri_min'],
 line_dash="dash",
 line_color="#2E86AB",
 annotation_text=f"TRI Min: {self.constraints['tri_min']:.1f}%",
 secondary_y=False
 )

 # Ligne Payback maximum
 if self.constraints.get('payback_max'):
 fig.add_hline(
 y=self.constraints['payback_max'],
 line_dash="dash",
 line_color="#C73E1D",
 annotation_text=f"Payback Max: {self.constraints['payback_max']:.1f} ans",
 secondary_y=False
 )

 # Configuration des axes
 fig.update_xaxes(title_text="Prix de Vente HT (€/kWh)")
 fig.update_yaxes(title_text="TRI (%) / Payback (ans)", secondary_y=False)
 fig.update_yaxes(title_text="Bénéfice Client (€/an)", secondary_y=True)

 # Layout
 fig.update_layout(
 height=500,
 hovermode='x unified',
 legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
 )

 return fig
```

## Interface Interactive

### Contrôles Streamlit
```python
def create_interactive_controls(self):
 """
 Crée les contrôles interactifs pour les visualisations
 """
 st.subheader(" Contrôles Interactifs")

 col1, col2 = st.columns(2)

 with col1:
 # Sélection du type de graphique
 chart_type = st.selectbox(
 "Type de visualisation",
 options=[
 "Prix vs Bénéfice Client",
 "Répartition Énergétique",
 "Métriques vs Prix",
 "Comparaison Tarifs"
 ],
 key="chart_type_selector"
 )

 with col2:
 # Options d'affichage
 show_markers = st.checkbox(
 "Afficher les marqueurs",
 value=True,
 help="Prix sélectionné et prix optimal"
 )

 show_constraints = st.checkbox(
 "Afficher les contraintes",
 value=True,
 help="Lignes de contraintes TRI/Payback"
 )

 # Graphique selon sélection
 if chart_type == "Prix vs Bénéfice Client":
 prix_range = self._generate_price_range()
 benefits = [self._calculate_benefit_at_price(p) for p in prix_range]
 fig = self.create_price_analysis_chart(prix_range, benefits)

 elif chart_type == "Répartition Énergétique":
 fig = self.create_energy_distribution_pie()

 elif chart_type == "Métriques vs Prix":
 fig = self.create_metrics_vs_price_chart()

 # Configuration d'affichage
 config = {
 'displayModeBar': True,
 'displaylogo': False,
 'modeBarButtonsToRemove': ['pan2d', 'lasso2d', 'select2d'],
 'toImageButtonOptions': {
 'format': 'png',
 'filename': f'optimpv_analysis_{chart_type.lower().replace(" ", "_")}',
 'height': 600,
 'width': 1000,
 'scale': 2
 }
 }

 # Affichage du graphique
 st.plotly_chart(fig, use_container_width=True, config=config)

 return chart_type

def _generate_price_range(self, points=100):
 """
 Génère une gamme de prix pour l'analyse
 """
 prix_min = max(self.prix_plancher * 0.99, self.lcoe * 0.95)
 prix_max = min(self.tarif_edf / 1.20, self.prix_plancher * 1.5)

 return np.linspace(prix_min, prix_max, points)
```

---

*Les visualisations interactives d'OptimPV offrent une exploration intuitive des résultats d'optimisation, permettant aux utilisateurs de comprendre visuellement les trade-offs entre rentabilité et attractivité commerciale.*