"""Exemples concrets des fonctionnalités commerciales professionnelles.

Ce fichier contient des exemples détaillés pour chaque amélioration
suggérée pour atteindre un dashboard commercial 10/10.
"""

# ============================================================================
# 1. MÉTRIQUES PROFESSIONNELLES AVANCÉES
# ============================================================================

class MetricsExamples:
    """Exemples de métriques avancées."""
    
    # ARR (Annual Recurring Revenue)
    arr_example = {
        "definition": "Revenus récurrents annuels garantis",
        "calcul": """
        ARR = Σ (Prix kWh × Consommation annuelle client × Durée contrat)
        
        Exemple client SolarPark:
        - Prix: 0.15€/kWh
        - Consommation: 500,000 kWh/an
        - Contrat: 10 ans
        → ARR = 0.15 × 500,000 = 75,000€/an
        """,
        "affichage": "ARR: 2.4M€ (+18% YoY)",
        "drill_down": "Cliquer pour voir ARR par client, par zone, par commercial"
    }
    
    # LTV/CAC Ratio
    ltv_cac_example = {
        "definition": "Valeur vie client / Coût d'acquisition",
        "calcul": """
        LTV = (Revenu moyen par client × Marge brute × Durée de vie moyenne)
        CAC = (Coûts marketing + Coûts commerciaux) / Nouveaux clients
        
        Exemple:
        - LTV: 150,000€ (10 ans × 15,000€/an)
        - CAC: 30,000€ (salaires + marketing)
        → Ratio: 5.0x (Excellent si > 3x)
        """,
        "visualisation": "Gauge avec zones: Rouge <2x, Jaune 2-3x, Vert >3x"
    }
    
    # Sales Velocity
    velocity_example = {
        "formule": "(Nb Opportunités × Taux conversion × Valeur moyenne) / Cycle de vente",
        "exemple": """
        - 50 opportunités/mois
        - 30% taux conversion
        - 80,000€ valeur moyenne
        - 45 jours cycle moyen
        → Velocity = (50 × 0.3 × 80,000) / 45 = 26,667€/jour
        """,
        "utilisation": "Identifier les leviers d'amélioration (plus d'opps, meilleur taux, cycle plus court)"
    }


# ============================================================================
# 2. INTELLIGENCE ARTIFICIELLE & MACHINE LEARNING
# ============================================================================

class AIExamples:
    """Exemples d'IA appliquée au commercial."""
    
    # Scoring des leads
    lead_scoring_example = {
        "modèle": "Random Forest avec 25 features",
        "features": [
            "Taille entreprise (CA, effectifs)",
            "Secteur d'activité (score par secteur)",
            "Consommation énergétique estimée",
            "Localisation (distance de nos installations)",
            "Engagement (emails ouverts, visites site)",
            "Données financières (solvabilité, croissance)",
            "Timing (renouvellement contrat concurrent)"
        ],
        "output": """
        Lead: Green Energy Corp
        Score: 92/100 🟢
        
        Facteurs positifs:
        • CA 50M€ (+20% croissance)
        • Secteur industriel (forte conso)
        • 3 sites dans notre zone
        • CEO a visité notre site 5x
        
        Action recommandée:
        → Appeler sous 24h
        → Proposer audit gratuit
        → Mentionner référence client similaire
        """,
        "mise_a_jour": "Le modèle apprend des conversions réelles"
    }
    
    # Prédiction de churn
    churn_prediction_example = {
        "signaux_alerte": [
            "Baisse consommation -15% sur 3 mois",
            "Pas de réponse aux 3 derniers emails",
            "Factures payées en retard",
            "Pas de contact depuis 60 jours",
            "Visite site concurrent détectée",
            "Plainte non résolue"
        ],
        "exemple_client": """
        🔴 ALERTE CHURN - EcoFactory SA
        Risque: 85% (Critique)
        
        Signaux détectés:
        • Consommation -22% vs N-1
        • Contact perdu depuis 75 jours
        • 2 factures en retard
        • Recherche "alternative panneaux solaires" détectée
        
        Plan de rétention suggéré:
        1. Appel du directeur commercial sous 48h
        2. Proposer rencontre avec direction
        3. Offrir audit gratuit optimisation
        4. Remise commerciale 10% si renouvellement anticipé
        """,
        "taux_reussite": "78% des clients à risque sauvés avec plan d'action"
    }
    
    # Cross-sell / Upsell
    expansion_example = {
        "analyse": "Algorithme analyse consommation et compare avec clients similaires",
        "exemple": """
        💎 Opportunité détectée - TechPark Industries
        
        Situation actuelle:
        • 200 kWc installés (1 site)
        • Consommation: 300,000 kWh/an
        
        Potentiel identifié:
        • Site 2 non équipé (150,000 kWh/an)
        • Stockage batterie absent
        • Pas de contrat maintenance
        
        Recommandations:
        1. Proposer installation site 2: +100 kWc (+75k€/an)
        2. Ajouter stockage 500 kWh: (+25k€/an)
        3. Contrat maintenance premium: (+15k€/an)
        
        Potentiel total: +115k€/an (probabilité 65%)
        """
    }


# ============================================================================
# 3. AUTOMATISATION DES PROCESSUS
# ============================================================================

class AutomationExamples:
    """Exemples d'automatisation commerciale."""
    
    # Relances automatiques
    relance_workflow = {
        "déclencheurs": [
            "Pas de réponse email après 3 jours",
            "Proposition sans retour après 7 jours",
            "Client inactif depuis 30 jours"
        ],
        "exemple_sequence": """
        Séquence 'Proposition envoyée':
        
        J+0: Envoi proposition + email
        J+3: Si pas ouvert → SMS commercial
        J+5: Si ouvert mais pas réponse → Email relance douce
        J+7: Si toujours pas réponse → Appel commercial
        J+10: Email manager avec offre limitée
        J+14: Dernière chance + urgence
        J+21: Passage en 'perdu' + analyse
        
        Personnalisation:
        - Ton adapté selon profil client
        - Horaires selon préférences
        - Canal préféré (email/tel/SMS)
        """,
        "taux_efficacite": "+35% de réponses vs relances manuelles"
    }
    
    # Alertes temps réel
    alertes_examples = [
        {
            "type": "🔥 Opportunité chaude",
            "trigger": "Lead visite page tarifs 3x en 24h",
            "action": "Notification push commercial + appel sous 1h"
        },
        {
            "type": "⚠️ Risque commercial",
            "trigger": "Client important sans activité 45j",
            "action": "Task manager + rapport direction"
        },
        {
            "type": "🎯 Objectif proche",
            "trigger": "Commercial à 90% objectif mensuel",
            "action": "Push opportunités scorées + coaching"
        },
        {
            "type": "💰 Grosse opportunité",
            "trigger": "Devis >100k€ créé",
            "action": "Validation manager + support pricing"
        }
    ]
    
    # Workflows configurables
    workflow_builder = {
        "interface": "Drag & drop style Zapier",
        "exemple": """
        Workflow 'Nouveau client grands comptes':
        
        [Déclencheur: CA client > 10M€]
            ↓
        [Action: Assigner au senior commercial]
            ↓
        [Action: Créer tâches onboarding VIP]
            ↓
        [Condition: Si secteur industriel]
            ├─OUI→ [Programmer audit technique]
            └─NON→ [Programmer RDV découverte]
            ↓
        [Action: Alerter direction commerciale]
            ↓
        [Action: Ajouter au segment VIP CRM]
        """,
        "templates": [
            "Onboarding nouveau client",
            "Renouvellement contrat",
            "Gestion réclamation",
            "Processus de vente complexe"
        ]
    }


# ============================================================================
# 4. INTÉGRATIONS EXTERNES
# ============================================================================

class IntegrationExamples:
    """Exemples d'intégrations avec outils tiers."""
    
    # Calendrier intelligent
    calendar_integration = {
        "fonctionnalités": [
            "Sync bidirectionnelle Google Calendar/Outlook",
            "Blocage automatique créneaux",
            "Suggestion meilleurs horaires selon client",
            "Rappels intelligents"
        ],
        "exemple": """
        📅 RDV Intelligent - M. Dupont (SolarTech SA)
        
        Analyse IA:
        • Historique: Préfère mardi/jeudi matin
        • Distance: 45min de trajet
        • Contexte: Renouvellement contrat
        
        Créneaux suggérés:
        1. Mardi 10h-11h30 (optimal)
        2. Jeudi 9h-10h30 (bon)
        3. Mercredi 14h-15h30 (acceptable)
        
        Actions automatiques:
        ✓ Bloquer 45min avant/après (trajet)
        ✓ Ajouter lien visio secours
        ✓ Attacher documents pertinents
        ✓ Brief commercial 24h avant
        """
    }
    
    # Intégration email
    email_integration = {
        "tracking": "Ouvertures, clics, temps lecture",
        "templates": """
        Template 'Proposition commerciale énergie':
        
        Variables dynamiques:
        {{client.nom}}
        {{commercial.signature}}
        {{proposition.montant}}
        {{proposition.economie_estimee}}
        
        Personnalisation IA:
        - Ajuste ton selon profil client
        - Insère références secteur pertinentes
        - Optimise objet selon taux ouverture
        
        A/B testing automatique:
        Version A: Focus économies
        Version B: Focus écologie
        → IA sélectionne la meilleure
        """,
        "automation": "Envoi au meilleur moment selon habitudes client"
    }
    
    # API & Webhooks
    api_examples = {
        "webhooks_entrants": [
            {
                "source": "Site web",
                "event": "Nouveau formulaire contact",
                "action": "Créer lead + scorer + assigner"
            },
            {
                "source": "Facturation",
                "event": "Facture impayée 30j",
                "action": "Alerte churn + task recouvrement"
            }
        ],
        "api_sortantes": [
            {
                "destination": "Slack",
                "event": "Deal > 50k€ gagné",
                "payload": "Message canal #victories"
            },
            {
                "destination": "PowerBI",
                "event": "Mise à jour KPIs",
                "payload": "Push metrics temps réel"
            }
        ]
    }


# ============================================================================
# 5. TABLEAUX DE BORD PERSONNALISABLES
# ============================================================================

class DashboardExamples:
    """Exemples de dashboards personnalisés."""
    
    # Vue Directeur Commercial
    executive_dashboard = {
        "widgets": [
            "ARR temps réel avec projection fin d'année",
            "Pipeline pondéré par probabilité",
            "Performance équipe (ranking + tendances)",
            "Carte chaleur activité commerciale",
            "Top 10 deals en cours",
            "Alertes critiques"
        ],
        "exemple_visuel": """
        ┌─────────────────────────────────────────────┐
        │ 💼 EXECUTIVE DASHBOARD          Jean Martin │
        ├─────────────────┬───────────────┬───────────┤
        │ ARR: 2.4M€      │ Pipeline: 4.2M│ Win: 68%  │
        │ ↑18% YoY        │ 3.2x coverage │ ↑5pp MoM  │
        ├─────────────────┴───────────────┴───────────┤
        │ [Graphique ARR 12 mois avec projection]     │
        ├─────────────────┬───────────────────────────┤
        │ Top Performers  │ Deals Critiques           │
        │ 1.Marie +142%   │ • EDF: 450k€ (80%)       │
        │ 2.Paul +98%     │ • Total: 380k€ (60%)     │
        │ 3.Julie +87%    │ • Carrefour: 290k€ (40%) │
        └─────────────────┴───────────────────────────┘
        """
    }
    
    # Vue Commercial terrain
    rep_dashboard = {
        "widgets": [
            "Ma to-do list du jour",
            "Mon pipeline personnel",
            "Mes RDV semaine",
            "Mes objectifs (progress bars)",
            "Leads chauds à traiter",
            "Coaching tips IA"
        ],
        "interactivité": """
        Actions rapides disponibles:
        • Glisser-déposer pour changer étape pipeline
        • Click droit → Actions (appeler, emailer, planifier)
        • Double-click → Ouvrir fiche complète
        • Swipe → Marquer comme fait
        
        Notifications temps réel:
        🔔 "Client TechCorp vient d'ouvrir votre devis"
        🔔 "RDV dans 30min - Préparez-vous"
        🔔 "Nouveau lead assigné - Score 85/100"
        """
    }
    
    # Création custom
    custom_builder = {
        "interface": "Drag & drop widgets",
        "widgets_disponibles": [
            "KPI simple", "Graphique ligne", "Camembert",
            "Tableau données", "Carte géographique", "Timeline",
            "Kanban", "Calendrier", "Chat équipe", "Notes"
        ],
        "exemple_config": """
        Mon Dashboard 'Suivi Grands Comptes':
        
        [KPI: CA Grands Comptes] [KPI: Nb Clients VIP]
        [Graphique: Evolution CA par client TOP 10    ]
        [Timeline: Prochains renouvellements          ]
        [Tableau: Activité derniers 30j par compte    ]
        
        Sauvegardé comme template réutilisable
        """
    }


# ============================================================================
# 6. GAMIFICATION & MOTIVATION
# ============================================================================

class GamificationExamples:
    """Exemples de gamification commerciale."""
    
    leaderboard_example = {
        "affichage": """
        🏆 LEADERBOARD NOVEMBRE 2024
        
        ┌──┬─────────────┬─────────┬──────┬────────┐
        │🥇│ Marie D.    │ 142% obj│ 12 ✓ │ 🔥🔥🔥 │
        │🥈│ Paul R.     │ 128% obj│ 10 ✓ │ 🔥🔥   │
        │🥉│ Julie M.    │ 115% obj│ 8 ✓  │ 🔥     │
        │4 │ Thomas B.   │ 98% obj │ 7 ✓  │ 💪     │
        └──┴─────────────┴─────────┴──────┴────────┘
        
        Badges débloqués ce mois:
        🎯 Sniper (3 deals one-shot)
        🚀 Rocket (plus forte progression)
        💎 Whale Hunter (deal >100k€)
        """,
        "système_points": {
            "Appel effectué": 5,
            "RDV obtenu": 20,
            "Devis envoyé": 50,
            "Deal gagné": "100 + (10% du montant)",
            "Client satisfait": 200
        }
    }
    
    achievements_example = [
        {
            "badge": "🎯 First Blood",
            "condition": "Premier deal du mois",
            "reward": "Café offert par le manager"
        },
        {
            "badge": "🔥 On Fire",
            "condition": "3 deals gagnés en 1 semaine",
            "reward": "Demi-journée off"
        },
        {
            "badge": "👑 Closer King",
            "condition": "Meilleur taux de closing 3 mois",
            "reward": "Prime spéciale + parking VIP"
        }
    ]


# ============================================================================
# 7. ANALYSES PRÉDICTIVES AVANCÉES
# ============================================================================

class PredictiveAnalytics:
    """Exemples d'analyses prédictives."""
    
    forecast_example = {
        "méthode": "SARIMA + Random Forest + Réseaux de neurones",
        "inputs": [
            "Historique 3 ans",
            "Saisonnalité",
            "Pipeline actuel",
            "Tendances marché",
            "Events externes (réglementation, météo)"
        ],
        "output": """
        📈 Prévisions Q1 2025
        
        Scénario réaliste (70% confiance):
        • Janvier: 780k€ (±50k€)
        • Février: 820k€ (±60k€)  
        • Mars: 950k€ (±80k€)
        Total Q1: 2.55M€
        
        Facteurs d'influence:
        ↑ Nouvelle réglementation RE2025 (+15%)
        ↑ Prix énergie en hausse (+10%)
        ↓ Météo défavorable janv-fév (-5%)
        
        Recommandations:
        • Recruter 2 commerciaux avant janvier
        • Stock de panneaux +30% pour mars
        • Campagne marketing RE2025 dès décembre
        """
    }
    
    market_intelligence = {
        "sources": [
            "Veille concurrentielle automatisée",
            "Analyse actualités secteur",
            "Données économiques régionales",
            "Réseaux sociaux professionnels"
        ],
        "insights_exemple": """
        🔍 Intelligence Marché - Novembre 2024
        
        Opportunités détectées:
        • Zone Sophia Antipolis: 5 entreprises tech 
          en croissance cherchent solutions vertes
        • Concurrent X en difficulté sur Nice Est
          → 8 clients potentiels à approcher
        • Subventions régionales +50% en janvier
          → Préparer offres packagées
        
        Menaces identifiées:
        • Nouveau concurrent low-cost sur Cannes
        • Pénurie onduleurs prévue Q2 2025
        • Évolution norme peut impacter 15% clients
        """
    }