# 🎨 Module de Visualisation Moderne OptimPV

## 📋 Vue d'ensemble

Le module de visualisation moderne d'OptimPV offre une interface utilisateur professionnelle et hautement interactive pour visualiser les données d'optimisation photovoltaïque.

## ✨ Fonctionnalités Principales

### 🎨 Design System Complet
- **Dark/Light Mode** avec persistence des préférences
- **3 Thèmes** : Light, Dark, Corporate
- **Glassmorphism Effects** pour un design moderne
- **Animations fluides** sur tous les composants

### 📊 Graphiques Avancés
- **Diagrammes de Sankey** pour les flux énergétiques
- **Heatmaps temporelles** pour l'analyse de consommation
- **Surfaces 3D** pour l'optimisation multi-paramètres
- **Graphiques Radar** pour les comparaisons multi-critères
- **Diagrammes de Gantt** pour la planification
- **Network Graphs** pour la distribution d'énergie

### 🎯 Interactivité Avancée
- **Zoom synchronisé** entre graphiques
- **Brush & Link** pour la sélection de données
- **Drill-down progressif** dans les hiérarchies
- **Animations temporelles** avec contrôles
- **Tooltips enrichis** avec prédictions

### 🏗️ Dashboard Personnalisable
- **Widgets drag & drop**
- **Layouts sauvegardables**
- **Mode édition intuitif**
- **Presets de configuration**
- **Export multi-format**

## 🚀 Utilisation

### Installation
```python
# Le module est automatiquement chargé avec OptimPV
from modules.visualization import ModernVisualizationUI
```

### Utilisation de base
```python
# Créer l'interface moderne
ui = ModernVisualizationUI()

# Afficher l'interface
ui.show_ui()
```

### Utilisation des composants individuels

#### Thèmes
```python
from modules.visualization import theme_manager

# Changer de thème
theme_manager.switch_theme('dark')

# Obtenir les couleurs actuelles
colors = theme_manager.get_colors()
```

#### Cards modernes
```python
from modules.visualization import render_metric_card

render_metric_card(
    title="NPV",
    value="45,000€",
    delta="+15%",
    icon="💰",
    gradient=True,
    animate=True
)
```

#### Graphiques avancés
```python
from modules.visualization import create_energy_sankey_diagram

# Créer un diagramme de Sankey
fig = create_energy_sankey_diagram({
    'source': [0, 1, 0],
    'target': [2, 2, 3],
    'value': [5000, 3000, 2000],
    'labels': ['PV', 'Réseau', 'Consommation', 'Injection']
})
```

#### Dashboard personnalisable
```python
from modules.visualization import CustomizableDashboard, WidgetType

# Créer un dashboard
dashboard = CustomizableDashboard("my_dashboard")

# Ajouter un widget
dashboard.add_widget(
    WidgetType.METRIC,
    "Titre",
    config={"metric": "npv"},
    position={"x": 1, "y": 1, "w": 4, "h": 2}
)
```

## 📁 Structure du Module

```
visualization/
├── modern_visualization_ui.py    # Interface principale moderne
├── main_visualization_ui.py      # Interface classique (compatibilité)
│
├── ui/                          # Composants UI
│   ├── cards/                   # Cards modernes
│   ├── buttons/                 # Boutons animés
│   └── theme_selector.py        # Sélecteur de thème
│
├── charts/                      # Graphiques
│   ├── interactive/             # Charts interactifs avancés
│   └── advanced/                # Visualisations complexes (Sankey, etc.)
│
├── components/                  # Composants complexes
│   └── dashboard/               # Dashboard personnalisable
│
├── styles/                      # Styles et thèmes
│   ├── themes/                  # Gestionnaire de thèmes
│   └── animations/              # Système d'animations
│
└── tests/                       # Tests unitaires et d'intégration
```

## 🧪 Tests

Exécuter les tests :
```bash
python tests/test_modern_visualization.py
python tests/test_visualization_integration.py
```

## 🔧 Configuration

### Thèmes personnalisés
```python
# Ajouter un thème personnalisé
from modules.visualization.styles.themes.theme_manager import ThemeManager, ColorPalette

ThemeManager.THEMES['custom'] = ColorPalette(
    primary='#FF6B6B',
    secondary='#4ECDC4',
    # ... autres couleurs
)
```

### Widgets personnalisés
```python
# Créer un renderer de widget personnalisé
def render_custom_widget(config):
    # Logique de rendu personnalisée
    pass

# L'utiliser dans le dashboard
widget_renderers = {
    "custom": render_custom_widget
}
```

## 📈 Performance

- **Lazy Loading** : Les composants sont chargés à la demande
- **Caching intelligent** : Les données sont mises en cache avec Streamlit
- **Animations optimisées** : Utilisation de CSS pour les performances
- **Rendu progressif** : Les graphiques complexes sont rendus progressivement

## 🎯 Bonnes Pratiques

1. **Toujours appliquer le thème** au démarrage :
   ```python
   theme_manager.apply_theme_css()
   ```

2. **Utiliser les animations avec parcimonie** pour ne pas surcharger l'interface

3. **Préférer les widgets métrique** pour les KPIs importants

4. **Grouper les graphiques liés** pour la synchronisation

5. **Sauvegarder les layouts** de dashboard pour les réutiliser

## 🆘 Dépannage

### Le thème ne s'applique pas
- Vérifier que `theme_manager.apply_theme_css()` est appelé
- Rafraîchir la page (F5)

### Les animations sont saccadées
- Réduire le nombre d'animations simultanées
- Vérifier la performance du navigateur

### Les graphiques ne se synchronisent pas
- S'assurer que `sync_enabled` est True dans chart_state
- Vérifier que les graphiques partagent le même axe temporel

## 📝 Changelog

### v2.0.0 (2024-01)
- Interface moderne complète
- Système de thèmes Dark/Light/Corporate
- Dashboard personnalisable avec drag & drop
- Nouveaux types de graphiques (Sankey, Heatmaps, 3D, etc.)
- Animations et transitions fluides
- Export multi-format amélioré

### v1.0.0
- Interface de visualisation de base
- Graphiques Plotly standards
- Export PDF simple

## 📄 Licence

Module propriétaire OptimPV - Tous droits réservés