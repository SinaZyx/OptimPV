# Module Prospect Mapping - OptimPV

## 🎯 Fonctionnalités

### **Mode Proximité Mougins (Recommandé)**
- **Chargement ultra-rapide** : 15-30 secondes pour la zone Mougins
- **10 communes les plus proches** automatiquement sélectionnées
- **BD TOPO en arrière-plan** : Carte utilisable immédiatement, enrichissement progressif

### **Mode Personnalisé**
- Sélection manuelle de communes du département 06
- Chargement et enrichissement automatique BD TOPO/DPE

## 🚀 Utilisation

```bash
streamlit run app.py
```

1. Accédez à "Carte de Prospection"
2. Sélectionnez le mode proximité (recommandé)
3. Naviguez sur la carte pendant que BD TOPO charge
4. Cliquez sur un bâtiment pour voir les détails enrichis

## 📁 Structure

```
prospect_mapping/
├── ui.py                    # Interface principale Streamlit
├── __init__.py             # Configuration module
├── core/                   # Modules principaux
│   ├── data_handler.py     # Gestion données + enrichissement arrière-plan
│   ├── map_visualizer_robust.py  # Visualisation cartographique
│   ├── cadastre_analyzer.py      # Enrichissement OSM/DPE
│   ├── solar_simulator.py        # Simulation solaire
│   └── ...                       # Autres utilitaires
└── data/                   # Données externes (BD TOPO IGN)
    └── BDTOPO_*/
```

## ⚡ Optimisations

- **Threading** : Enrichissement BD TOPO non-bloquant
- **Géocodage intelligent** : Cache + fallback par commune
- **Parallélisation Enedis** : 4 workers simultanés
- **Distance géographique** : Calcul précis avec fallback

## 🛠️ Technologies

- **Streamlit** : Interface utilisateur
- **Pandas** : Traitement données
- **geopy** : Calculs géographiques (avec fallback)
- **Threading** : Enrichissement asynchrone
- **APIs** : Enedis, IGN BD TOPO, ADEME DPE

---

*Module optimisé pour performance et expérience utilisateur*