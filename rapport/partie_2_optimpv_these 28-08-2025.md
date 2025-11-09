# PARTIE II : Conception d'une Solution Intégrée : La Plateforme OptimPV

## Introduction : De l'analyse du marché à la conception de la solution

La Partie I a établi un constat sans appel : le marché français de l'autoconsommation collective, avec seulement 250 MW installés contre un objectif de 5 GW pour 2030, manque cruellement d'outils adaptés. Les professionnels persistent à utiliser Excel, générant des erreurs coûteuses sur les calculs réglementaires et perdant 3 à 4 heures par projet. Aucune solution existante - ni PVsyst limité au dimensionnement technique, ni Aurora Solar méconnaissant le cadre français, ni les outils propriétaires d'EDF ou TotalEnergies - n'intègre les spécificités réglementaires françaises avec l'optimisation multi-contraintes nécessaire.

Cette Partie II présente la conception détaillée d'OptimPV, solution développée pour répondre aux lacunes identifiées.

Le Chapitre 3 expose l'architecture technique et le moteur d'optimisation. La Section 3.1 justifie une architecture modulaire séparant le moteur de calcul du module fiscal, permettant l'adaptation aux évolutions réglementaires en 5 minutes contre 3 jours pour une refonte complète. La Section 3.2 établit les fondements mathématiques : sélection de Brent pour sa convergence garantie, traitement des TRI multiples par MIRR, adaptation du WACC au contexte fiscal français. La Section 3.3 résout le problème d'optimisation sous contraintes (TRI ≥ 8%, payback ≤ 10 ans) validé sur Cannes ABA Gestion.

Le Chapitre 4 traduit ces algorithmes en modules opérationnels. La Section 4.1 automatise la prospection par intégration d'APIs publiques (Cadastre, PVGIS). La Section 4.2 gère les projets multi-participants (30-50 membres). La Section 4.3 automatise facturation et répartition énergétique.

La conclusion établit le bilan : réduction du temps d'analyse de 90%, limitations actuelles et perspectives d'évolution.



## Chapitre 3 : Architecture et Moteur d'Optimisation

### 3.1. Pourquoi ces choix architecturaux spécifiques ?

#### Comment gérer l'évolutivité réglementaire ?

Le secteur énergétique français évolue à un rythme sans précédent. La suppression de l'accise de 33,7 €/MWh (Loi de Finances rectificative n°2025-89, Article 12), le relèvement des seuils de puissance de 3 MW à 5 MW pour l'obligation d'achat (Arrêté du 21 février 2025 modifiant l'arrêté du 6 octobre 2021), les révisions TURPE trimestrielles décidées par la CRE, et les ajustements fréquents de la prime à l'autoconsommation collective versée par Enedis créent une instabilité réglementaire chronique. Une architecture monolithique traditionnelle nécessiterait des redéveloppements complets coûteux à chaque évolution, rendant rapidement la solution obsolète.

OptimPV répond par une architecture modulaire innovante séparant strictement les responsabilités. Le découplage des modules engine_module/tax_engine permet d'intégrer une nouvelle réglementation en 5-10 min versus 1-3 jours pour une refonte complète.

L'intégration de la suppression d'accise de mars 2025 a été réalisée en 3 min sans modification du moteur de calcul principal, validant l'approche architecturale retenue.

L'architecture modulaire d'OptimPV sépare rigoureusement les responsabilités pour garantir l'évolutivité. D'une part, le module engine_module encapsule les calculs financiers stables (NPV, IRR, WACC). 
D'autre part, le module tax_engine isole la fiscalité française évolutive dans un composant dédié, permettant l'adaptation rapide aux changements réglementaires. Enfin, les modules business_modules implémentent les fonctionnalités métier spécifiques via des interfaces standardisées. Cette architecture réduit significativement les coûts de maintenance et les risques de régression.

![Figure 3.1 : Architecture modulaire OptimPV](https://image.noelshack.com/fichiers/2025/35/1/1756141336-architecture-modulaire-en-3-couches.png)

*Figure 3.1 : Architecture modulaire en 3 couches d'OptimPV illustrant la séparation des responsabilités entre engine_module (calculs financiers), tax_engine (fiscalité française évolutive) et business_modules (fonctionnalités métier). Le tax_engine isolé permet l'adaptation rapide aux évolutions réglementaires sans remise en cause de l'engine_module central.*

Cette architecture modulaire constitue le socle technique permettant l'implémentation des algorithmes détaillés dans la section suivante, garantissant à la fois évolutivité réglementaire et robustesse computationnelle.

#### Comment assurer la stabilité algorithmique ?

Au-delà de l'évolutivité réglementaire, la stabilité des calculs constitue un enjeu technique majeur. Les projets d'ACC créent des boucles de rétroaction complexes où les intérêts de trésorerie influencent les revenus, qui modifient ensuite l'optimisation de prix, qui impacte à son tour la trésorerie disponible. Ces interdépendances circulaires génèrent par conséquent des oscillations numériques empêchant la convergence.

OptimPV implémente une stratégie de calcul contextuelle utilisant des méthodes de point fixe. En mode optimisation, les boucles de rétroaction sont temporairement linéarisées en désactivant les calculs de trésorerie complexes, garantissant une convergence en moins de 15 itérations. En mode analyse finale, tous les mécanismes financiers sont réactivés pour une précision maximale.

Cette approche bi-modale réduit considérablement les échecs de convergence, tout en maintenant une précision finale de 0,1% sur les indicateurs financiers clés.

#### Pourquoi le choix pragmatique de Streamlit ?

L'architecture modulaire étant établie, le choix de l'interface utilisateur devient déterminant pour la viabilité du projet. Le cadre temporel d'une thèse professionnelle OSE (10 mois) impose des arbitrages technologiques. Le développement d'une interface React/NextJS nécessiterait plusieurs mois supplémentaires, compromettant la validation méthodologique prioritaire.

Streamlit (version 1.28.2) offre un time-to-market optimal avec son intégration native NumPy/Pandas. Le framework réduit significativement le code UI par rapport à React. Le déploiement one-click via Streamlit Cloud élimine la complexité DevOps, permettant de concentrer l'essentiel du temps de développement sur la logique métier.

L'architecture monocœur de Streamlit limite les performances pour des utilisations intensives. La feuille de route prévoit une migration NextJS en phase d'industrialisation (T0+24 mois), avec réutilisation intégrale des modules Python via API REST. Cette approche de développement progressif permet de valider le concept avant d'engager des investissements d'industrialisation.

#### Python : nécessité pour l'ACC multi-participants

La plateforme Streamlit étant retenue pour l'interface, le choix du langage de programmation découle naturellement des contraintes de traitement des données. L'autoconsommation collective transforme radicalement la volumétrie et la complexité des données par rapport à l'autoconsommation individuelle. En effet, un projet ACC typique avec 30 participants génère 5,2 millions de points de données (30 profils × 8760 heures × 20 ans), dépassant immédiatement la limite d'Excel de 1 048 576 lignes. Par ailleurs, les matrices de répartition dynamiques créent 7,8 millions d'interactions annuelles (30×30×8760) nécessitant des calculs matriciels impossibles en Excel. L'optimisation multi-contraintes génère 150 000 calculs (30 participants × 5 contraintes × 1000 itérations) que Excel ne peut paralléliser. Excel demeure adapté aux projets simples, mais présente des limitations critiques face aux millions de données ACC, notamment des performances dégradées, une interface surchargée et des temps de traitement prohibitifs. L'analyse complète d'un projet nécessite 3 à 4 heures sous Excel, contre 15 minutes maximum avec OptimPV, incluant l'ensemble des calculs et analyses.

Au-delà du volume, Excel présente des limitations architecturales rédhibitoires pour l'ACC. Le recalcul complet du classeur à chaque modification génère une complexité temporelle exponentielle avec le nombre de participants. L'absence de gestion native des séries temporelles multi-indexées rend impossible le suivi simultané de multiples profils de consommation. Les formules RECHERCHEV imbriquées deviennent rapidement inmaintenables et sources d'erreurs. La propagation silencieuse des erreurs #DIV/0! et #N/A dans les formules complexes génère des résultats aberrants non détectés.

Python avec Pandas permet la vectorisation native des calculs ACC, divisant par 10 les temps de calcul grâce aux opérations matricielles optimisées. De plus, la gestion native des DataFrames multi-indexés permet de traiter simultanément les données temporelles, les profils participants et les métriques financières dans une structure unifiée. Par ailleurs, l'intégration transparente avec les APIs (PVGIS, Cadastre, DPE) automatise la collecte de données sans risque d'erreur de transcription.

Sur le projet de test comme Cannes ABA Gestion avec ses 55 participants, Excel nécessitait 1-2 heures de préparation et calculs manuels. Python traite l'ensemble en 7 minutes maximum, incluant le temps d'optimisation ralenti par la limitation mono-cœur de Streamlit, avec traçabilité complète via logs structurés. Avec un *LCOE* réel de 8,71 c€/kWh ne laissant que 2,74 c€/kWh de marge brute, la précision de l'optimisation devient critique. La maintenance évolutive (ajout d'un participant, modification tarifaire) prend 5 minutes en Python contre une refonte complète du classeur Excel. Dans ce contexte, l'efficacité d'OptimPV devient critique pour accompagner les 5 GW anticipés d'ici 2030.

L'interface Streamlit transforme l'expérience utilisateur par rapport à VBA. La fonctionnalité de rechargement dynamique permet d'observer instantanément l'effet des modifications de code. Les widgets natifs (sliders, selectbox, dataframes) offrent une interactivité impossible en Excel. L'intégration transparente Pandas-Streamlit élimine les conversions de données sources d'erreurs. Pour un outil interne de R&D en phase de validation conceptuelle, cette productivité développeur permet d'itérer rapidement sur les fonctionnalités.

### 3.2. Quels fondements mathématiques pour quels problèmes métier ?

L'architecture technique étant posée, il convient maintenant d'examiner les algorithmes mathématiques qui constituent le cœur du moteur d'optimisation.

#### Brent et Newton-Raphson : analyse comparative

L'optimisation du prix de vente en ACC requiert la recherche d'une racine unique dans un intervalle borné [prix_min, prix_max]. Cette contrainte opérationnelle, combinée aux spécificités fiscales françaises (TVA différenciée, IS progressif, discontinuités tarifaires TURPE), nécessite un algorithme garantissant la convergence dans les bornes définies.

L'algorithme de Brent s'impose comme la référence industrielle pour l'optimisation univariée grâce à ses avantages intrinsèques face à Newton-Raphson. D'abord, contrairement à Newton-Raphson qui exige le calcul de f'(x), Brent ne nécessite pas de dérivées. Cette différence est critique car la VAN dépend de 240 flux mensuels, eux-mêmes fonctions du prix via les revenus, l'IS et les ratios financiers. Calculer ∂VAN/∂prix analytiquement serait extrêmement complexe et source d'erreurs.

Par ailleurs, Brent garantit la convergence si f change de signe sur [a,b], alors que Newton peut diverger si le point initial est mal choisi ou si f' s'annule. Aux points de discontinuité tarifaire, la fonction VAN(prix) présente des quasi-ruptures où Newton-Raphson oscillerait indéfiniment. Brent converge en bissectant intelligemment l'intervalle, comme le montre l'implémentation dans core_analyzer.py ligne 1535 où brentq est appelé avec les bornes explicites.

De plus, Brent maintient structurellement la solution dans l'intervalle [prix_min, prix_max], évitant les prix économiquement absurdes (négatifs ou supérieurs au tarif EDF) que Newton pourrait proposer. Enfin, la fonction objectif peut retourner NaN lors de divisions par zéro dans le DSCR ou si le TRI devient incalculable. Brent détecte ces pathologies et bascule automatiquement en bissection sécurisée, tandis que Newton s'arrêterait sur une erreur.

L'algorithme fonctionne comme une boîte à outils automatique : il choisit l'outil le plus efficace selon la situation. En terrain plat (calculs réguliers), il va vite avec l'interpolation inverse quadratique. Près des obstacles (seuils fiscaux), il privilégie la sécurité en basculant automatiquement vers la sécante ou la bissection. Cette adaptabilité constitue un avantage supplémentaire face aux discontinuités fiscales françaises, mais n'en est pas la motivation principale.

Sur les cas réels testés, Brent converge systématiquement avec une tolérance de 10^-5 c€/kWh, atteignant une précision de 0,00001 c€/kWh qui dépasse largement les besoins industriels typiques de 0,1 c€/kWh. La convergence est garantie mathématiquement si la fonction change de signe entre les bornes. Concrètement, si la VAN est négative au prix minimum (f(0,08) = -15 000€) et positive au prix maximum (f(0,12) = +8 000€), il existe nécessairement un prix optimal où la VAN s'annule.

#### Résolution des TRI multiples

L'optimisation du prix n'étant qu'une facette du problème, la complexité des indicateurs financiers nécessite des traitements spécifiques. Les projets photovoltaïques ont souvent plusieurs TRI possibles à cause de leurs flux de trésorerie alternés. Un projet typique présente des flux alternés avec -100k€ d'investissement initial, +10k€/an de revenus, -20k€ de remplacement onduleur en année 10, puis un déclin progressif. Ces inversions de flux peuvent générer 2 ou 3 TRI différents (par exemple 5%, 15% et 45%), sans savoir lequel est pertinent.

OptimPV résout ce problème par une détection automatique. Un test aux bornes de l'intervalle [-0.99, 10.0] vérifie l'existence d'un changement de signe, couvrant les TRI réalistes de -99% (perte quasi-totale) à +1000% (rendement exceptionnel). Sans changement de signe, ou si le TRI dépasse 500%, le système bascule sur le MIRR (Modified Internal Rate of Return).

Le MIRR utilise la formulation $MIRR = \left(\frac{FV_{positifs}}{PV_{négatifs}}\right)^{\frac{1}{n}} - 1$, où les flux positifs sont capitalisés et les flux négatifs actualisés au même taux (finance_rate = reinvest_rate dans l'implémentation). Cette approche garantit un taux unique et élimine les ambiguïtés du TRI classique.

Cette approche présente des limites car si tous les flux sont négatifs après l'investissement initial, le MIRR devient non calculable. Ces cas pathologiques déclenchent une alerte utilisateur plutôt qu'un résultat erroné. En pratique, OptimPV affiche systématiquement la méthode utilisée (TRI ou MIRR) pour transparence totale auprès de l'utilisateur.

#### WACC adapté au marché français

Après la résolution des TRI, l'actualisation des flux nécessite un taux de référence adapté. Le calcul du Weighted Average Cost of Capital (WACC) pour les projets photovoltaïques français intègre les spécificités fiscales nationales, notamment la déductibilité des intérêts d'emprunt selon l'Article 39 du Code Général des Impôts.

La formulation classique $WACC = R_E \cdot \frac{E}{V} + R_D \cdot (1-T_c) \cdot \frac{D}{V}$ s'applique avec des paramètres configurables selon le profil de projet. Les valeurs typiques du secteur s'établissent à :
- Coût des fonds propres ($R_E$) : 8-12% selon le risque projet
- Coût de la dette ($R_D$) : 4-6% selon les conditions bancaires
- Structure financière : 80% dette / 20% fonds propres (standard sectoriel)
- Taux d'IS ($T_c$) : 25% (régime général)

Le WACC après impôt s'établit typiquement entre 6% et 8% pour les projets photovoltaïques matures. OptimPV utilise par défaut 6% (paramétrable), correspondant aux projets établis avec financement bancaire confirmé. Cette valeur sert de référence pour l'actualisation des flux et le calcul du LCOE.

Les cas limites où le taux d'imposition approche 100% ($T_c \rightarrow 1$) rendraient le terme $(1-T_c)$ proche de zéro, causant une division par zéro dans la formule standard. OptimPV détecte automatiquement ces cas. Si $T_c > 0,99$, le système bascule sur la formule alternative $WACC = R_D \cdot \frac{D}{V} + R_E \cdot \frac{E}{V}$ qui reste calculable.

#### Double validation du LCOE

Le WACC étant défini, son utilisation principale concerne le calcul du coût actualisé de l'énergie. Le Levelized Cost of Energy (LCOE) constitue l'indicateur de référence pour la comparaison énergétique des technologies de production. Pour éviter les erreurs de calcul, OptimPV vérifie le LCOE en utilisant deux approches différentes qui doivent donner le même résultat.

La première méthode (ingénierie) calcule le coût moyen du kWh en divisant les coûts totaux actualisés par la production totale actualisée. Par exemple, 2,5 millions d'euros de coûts actualisés divisés par 28,7 GWh actualisés donnent 8,7 c€/kWh.

Le *LCOE* constitue la métrique fondamentale de comparaison énergétique. Sa formulation standard actualise séparément numérateur et dénominateur au taux d'actualisation r (WACC projet de 6,15%) :

$$LCOE = \frac{\sum_{t=0}^{n} \frac{Coûts_t}{(1+r)^t}}{\sum_{t=0}^{n} \frac{Production_t}{(1+r)^t}}$$

Où r est le taux d'actualisation et n la durée de vie du projet. Sur le projet Cannes ABA Gestion avec n=20 ans, cette méthode produit un *LCOE* de 8,71 c€/kWh, incluant CAPEX à 1000€/kWc et OPEX de 1,4 c€/kWh HT. La double validation par méthode agrégation garantit une précision de ±2%.

La deuxième méthode (agrégation) calcule le coût moyen année par année, puis fait la moyenne sur 20 ans. Si l'écart entre les deux méthodes dépasse 5%, OptimPV signale automatiquement l'anomalie.

#### Modélisation de l'IS français

La gestion de l'Impôt sur les Sociétés (IS) dans les projets d'ACC nécessite de distinguer l'impact trésorerie réel de l'IS théorique comptable. Le calendrier réglementaire français impose des acomptes trimestriels pour les entreprises dont l'IS dépasse 3 000€. En dessous de ce seuil, l'IS est payé en une fois au 15 mai de l'année suivante. Au-delà, quatre acomptes trimestriels sont calculés sur l'IS de l'année précédente, avec régularisation du solde au 15 mai N+1. Cette temporalité spécifique influence directement les flux de trésorerie et doit être modélisée précisément.

Le régime PME applicable aux structures de moins de 250 salariés avec un chiffre d'affaires inférieur à 50 millions d'euros bénéficie d'un taux réduit de 15% sur les premiers 42 500 euros de bénéfice, puis 25% au-delà. Les reports déficitaires sont plafonnés à 1 million d'euros plus 50% de l'excédent, contraignant l'optimisation fiscale pluriannuelle des projets.

OptimPV distingue systématiquement l'IS comptable de l'IS trésorerie selon l'usage prévu des résultats. Les calculs de rentabilité intègrent l'IS comptable pour respecter les normes d'évaluation financière. Les prévisions de trésorerie utilisent l'IS différé pour optimiser la gestion des liquidités. Double approche qui assure la cohérence avec les pratiques professionnelles.

L'intégration de ces subtilités fiscales résulte d'une collaboration étroite avec Ludwig Prinz, expert en financement de projets énergétiques. Sa connaissance approfondie des mécanismes IS, notamment les seuils d'acomptes et les reports déficitaires, a permis d'enrichir significativement la précision des tableaux de flux de trésorerie d'OptimPV. Cette expertise terrain garantit la conformité des calculs avec les pratiques réelles du secteur.

#### Application automatique des grilles tarifaires TURPE

Parallèlement aux mécanismes fiscaux, la tarification réseau constitue un autre élément structurant des projets. Le Tarif d'Utilisation des Réseaux Publics d'Électricité (TURPE) français, structuré sur trois niveaux de tension avec des modalités tarifaires différenciées selon la puissance souscrite, génère des erreurs fréquentes dans les calculs manuels. OptimPV ne calcule pas le TURPE mais applique automatiquement les grilles tarifaires officielles publiées par Enedis et validées par la CRE (Commission de Régulation de l'Énergie). Ces tarifs, mis à jour selon les délibérations trimestrielles de la CRE, sont intégrés dans le système via des tables de référence maintenues à jour.

Les effets de seuil TURPE influencent directement le dimensionnement optimal. Le franchissement du seuil de 36 kVA génère un surcoût annuel de 573€, créant une discontinuité économique majeure nécessitant des volumes plus conséquents pour maintenir la rentabilité. Les seuils supérieurs (250 kVA, 1000 kVA) modifient également la structure tarifaire. L'automatisation de la sélection tarifaire évite ces erreurs manuelles et optimise les configurations selon les vraies contraintes économiques.

La **Figure 3.2** illustre concrètement ce saut tarifaire au passage de 36 kVA, démontrant l'impact économique critique de ce seuil sur la rentabilité des projets.

![Figure 3.2 : Impact du saut TURPE au seuil de 36 kVA sur le LCOE](https://image.noelshack.com/fichiers/2025/35/1/1756150552-lcoe-turpe.png)

*Figure 3.2 : Discontinuité du coût TURPE au seuil de 36 kVA et son impact sur le LCOE des projets photovoltaïques*

L'indexation différentielle entre TURPE et tarifs d'Obligation d'Achat (OA) nécessite une modélisation des évolutions relatives sur 20 ans. OptimPV applique une indexation annuelle de 2% sur le TURPE, correspondant à l'inflation générale du projet, tandis que les tarifs OA sont révisés trimestriellement selon l'évolution des coûts évités de production. Par ailleurs, la prime à l'autoconsommation collective versée sur 5 ans par Enedis (actuellement ~10€/kW pour les installations <100kW) constitue un flux de trésorerie précoce déterminant pour l'équilibre financier initial des projets. OptimPV intègre automatiquement ces différents mécanismes, gérant à la fois l'indexation différenciée et l'impact trésorerie de la prime ACC sur les 5 premières années.

#### Réalité économique du kWh ACC

L'analyse économique détaillée du kWh en autoconsommation collective révèle les leviers d'optimisation. Pour un prix de vente typique de 12,5 c€/kWh HT (15 c€/kWh TTC), la décomposition est la suivante.

La structure réelle du prix validée sur le projet Cannes ABA Gestion 2025 se décompose ainsi :

Le prix de vente optimal de 12,25 c€/kWh HT identifié par OptimPV sur un cas réel se décompose en trois composantes économiques fondamentales. 

Le coût de production *LCOE* s'établit à 8,71 c€/kWh HT soit 71% du prix HT. Cette base intègre l'amortissement du CAPEX à 1000€/kWc sur 20 ans représentant environ 26% du chiffre d'affaires. Les OPEX variables comprennent la maintenance annuelle de 606€ soit 7,8% du CA, l'assurance de 303€ soit 3,9% du CA, et la gestion administrative de 505€ soit 6,5% du CA. La provision pour remplacement onduleur s'élève à 303€/an soit 3,9% du CA. Le TURPE injection représente 581€/an soit 7,4% du CA, correspondant à environ 0,8 c€/kWh HT.

**Figure 3.3 : Répartition de l'énergie produite - Projet Cannes ABA Gestion**
![Répartition Autoconsommation vs Surplus](https://image.noelshack.com/fichiers/2025/35/4/1756392538-cannes-camembert.png)
*Production annuelle : 92 155 kWh (74,5% autoconsommé : 68 652 kWh, 25,5% surplus : 23 503 kWh)*

Avec 74,5% d'autoconsommation directe et 25,5% de surplus réinjecté, le projet Cannes ABA Gestion atteint un niveau de performance élevé. Les 25,5% de production excédentaire (23 503 kWh/an), revendus au tarif OA, pourraient être réduits par l'ajout de participants supplémentaires. Cette répartition, sur les 92 155 kWh produits annuellement, démontre l'efficacité de l'adéquation production-consommation du projet. Chaque kWh supplémentaire autoconsommé plutôt que réinjecté améliore directement la rentabilité du projet en évitant la décote du tarif de rachat.

La marge sur coûts variables s'établit à 70,5% du CA, démontrant la forte rentabilité opérationnelle du modèle ACC. Après déduction des amortissements (26% du CA) et des charges financières (20,5% du CA), le résultat net atteint 23,4% du chiffre d'affaires. Ces métriques permettent d'obtenir un TRI projet de 8,5% et un DSCR de 1,75, validés sur le projet réel analysé.

La sensibilité du modèle et la zone d'équilibre optimal s'articulent autour de plusieurs leviers :

L'optimisation algorithmique d'OptimPV identifie systématiquement une zone d'équilibre entre 12 et 13 c€/kWh HT où la probabilité d'acceptation client et la rentabilité projet sont simultanément maximisées. En dessous de 12 c€/kWh HT, la marge devient insuffisante avec un TRI inférieur à 6%, rendant le projet non finançable. Au-dessus de 13 c€/kWh HT, le gain consommateur devient insuffisant (moins de 25% par rapport au tarif EDF), générant un taux de refus supérieur à 40%.

La fenêtre d'optimisation s'articule autour de plusieurs leviers identifiés par OptimPV.

Premièrement, l'optimisation des OPEX passe par plusieurs leviers. La maintenance préventive (606€/an) peut être optimisée par mutualisation entre projets. L'assurance (303€/an) offre un potentiel de négociation significatif avec l'effet volume puisque plus le portefeuille de projets croît, plus les tarifs diminuent. Les frais administratifs (505€/an) peuvent être drastiquement réduits par automatisation. Un bot de facturation automatique (développement prévu en phase 2) remplacerait les processus manuels et pourrait diviser ces coûts par trois.

La réduction du CAPEX constitue un autre axe d'amélioration. Le coût d'installation actuel de 1000€/kWc reste optimisable. Une baisse de 100 à 200€/kWc est réaliste avec l'effet d'échelle et l'optimisation des achats. Cette réduction de 10-20% du CAPEX permettrait de baisser le prix de vente à 11 c€/kWh HT tout en maintenant un TRI supérieur à 8%, seuil minimal de rentabilité fixé pour garantir l'attractivité financière.

 Comme l'illustre la Figure 3.2, le ratio €/kWc diminue avec la puissance installée. Les projets de plus grande envergure bénéficient d'économies d'échelle substantielles, renforçant la pertinence d'une stratégie de croissance volumique.

Ces optimisations combinées pourraient réduire le *LCOE* de 8,71 à environ 7,5 c€/kWh HT, créant une marge de manœuvre tarifaire tout en préservant la rentabilité projet.


L'impact de la TVA sur l'attractivité ACC mérite une attention particulière. Le régime TVA actuel à 20% pour l'autoconsommation collective s'aligne sur la fourniture classique, n'offrant pas d'avantage fiscal immédiat. Cependant, le passage prévu à 5,5% en 2026 créera un avantage compétitif structurel majeur. Cette réduction de 14,5 points de TVA générera une économie de près de 2 c€/kWh TTC, améliorant significativement l'attractivité de l'ACC face aux tarifs réglementés. OptimPV intègre cette évolution fiscale dans ses projections pluriannuelles, permettant d'anticiper l'amélioration de rentabilité post-2026.

#### Trésorerie : un levier de rentabilité négligé

Les optimisations tarifaires et fiscales ne suffisent pas à maximiser la rentabilité. L'analyse de business plans réels de projets ACC révèle que la plupart négligent l'optimisation du cash management, laissant de la rentabilité inexploitée. Les excédents de trésorerie non placés représentent une perte cumulée moyenne de 32 000€ sur 20 ans pour un projet de 45 kWc.

 OptimPV optimise automatiquement la trésorerie en plaçant les excédents selon leur durée de disponibilité. Sur le projet Cannes ABA Gestion, cette gestion active de la trésorerie contribue significativement au résultat net de 23,4% du chiffre d'affaires.

OptimPV gère automatiquement les subtilités de trésorerie souvent négligées. La TVA sur investissement, récupérable après 3 mois, est placée si le montant dépasse 5 000€. Les décalages de paiement (30 jours clients, 15 jours fournisseurs) sont intégrés dans les projections mensuelles.

Les excédents sont placés progressivement selon leur montant : 50% pour les montants inférieurs à 50 000€, 65% jusqu'à 200 000€, et 80% au-delà, respectant ainsi les pratiques prudentes du secteur. Une provision dédiée au remplacement d'onduleur est isolée comptablement, répondant aux exigences bancaires.

Cette modélisation fine de la trésorerie, souvent absente des business plans simplifiés, renforce la crédibilité d'OptimPV auprès des financeurs professionnels.

La modélisation précise de ces flux de trésorerie a constitué l'un des défis majeurs du développement d'OptimPV. Les subtilités comme la récupération de TVA à 3 mois, directement impactante sur le BFR, ont nécessité plusieurs révisions du modèle. Cette courbe d'apprentissage illustre la complexité cachée des projets ACC, au-delà des calculs de rentabilité basiques, c'est la maîtrise des détails fiscaux et financiers qui fait la différence entre un outil amateur et une solution professionnelle.

#### La nécessité des 240 mois

La modélisation financière photovoltaïque exige une granularité mensuelle sur 240 périodes pour plusieurs raisons interdépendantes. La production solaire varie fortement selon les saisons avec un ratio été/hiver de 3 pour 1, tandis que les panneaux se dégradent progressivement de 0,5% par an. Parallèlement, les contraintes financières imposent des remboursements mensuels avec intérêts sur capital restant dû, des déclarations TVA mensuelles avec délais spécifiques, et l'impératif de maintenir une trésorerie positive pour éviter les découverts coûteux. Le développement de ces flux de trésorerie a révélé de nombreuses interdépendances complexes entre saisonnalité de production, décalages TVA et timing des facturations, nécessitant plusieurs semaines d'analyse approfondie pour résoudre ces interactions..

La nécessité d'une granularité mensuelle conduit à structurer deux piliers comptables interconnectés. OptimPV génère deux tableaux financiers complémentaires sur 240 mois. Pourquoi deux tableaux distincts ? Ils répondent à deux questions vitales différentes.

Le compte de résultat mensuel évalue la rentabilité comptable du projet en intégrant l'ensemble des revenus et charges. Les revenus comprennent la vente d'énergie et la prime ACC répartie sur cinq ans, tandis que les charges incluent l'exploitation, les intérêts décroissants et les amortissements linéaires. Cette approche fournit aux institutions financières une vision claire de la viabilité économique avec le résultat net après impôts.

Parallèlement, le tableau de flux de trésorerie traduit cette rentabilité comptable en liquidités disponibles mensuelles. Il intègre les flux opérationnels ajustés des variations du besoin en fonds de roulement, les investissements programmés comme le remplacement d'onduleur à 10 ans, ainsi que les flux de financement incluant remboursements et apports. Cette analyse permet d'anticiper les besoins de trésorerie et de prévenir les découverts bancaires.

Ces deux visions sont cruciales. En effet, un projet peut afficher un bénéfice comptable tout en manquant de liquidités. Le plan de financement (capital restant dû, DSCR) et le BFR sont intégrés dans ces tableaux, pas séparés. Cette double approche évite les pièges classiques où la rentabilité cache une crise de trésorerie.

Cette double approche répond aux exigences spécifiques des financeurs bancaires. Au-delà de ces deux tableaux, les banques imposent une complexité supplémentaire. Elles exigent simultanément un **tableau annuel agrégé** (20 lignes) pour vérifier les covenants bancaires comme le DSCR, ET un **tableau mensuel détaillé** (240 lignes) pour s'assurer qu'aucun découvert n'apparaît en cours d'année. L'agrégation mensuel→annuel devient alors un casse-tête technique car certains éléments s'additionnent (CA, charges via `resample('Y').sum()`), d'autres se moyennent (ratios DSCR), et d'autres prennent la valeur finale (capital restant dû). Le calcul du DSCR annuel suit la formule bancaire standard $DSCR_{annuel} = \frac{EBITDA_{annuel} - IS_{payé}}{Service_{dette}}$, avec gestion des cas limites (division par zéro si remboursement anticipé). Cette double comptabilité, impossible à gérer correctement dans Excel, justifie l'architecture sophistiquée d'OptimPV qui maintient automatiquement la cohérence entre les deux niveaux de granularité.

Le défi majeur réside dans le maintien de la cohérence inter-tableaux sur 240 mois. Maintenir la cohérence entre compte de résultat et flux de trésorerie sur 240 périodes constitue un défi algorithmique majeur. Chaque modification déclenche des cascades de recalculs. Modifier le taux d'intérêt impacte les charges financières, les remboursements, le DSCR et l'IS. La précision des calculs s'avère critique car une erreur d'arrondi initiale peut générer des écarts cumulés de plusieurs milliers d'euros sur la durée totale du projet. L'analyse a révélé des bugs subtils où les arrondis TVA créaient 0,01€ d'écart mensuel, cumulant 2,40€ sur 20 ans. Insignifiant ? Les auditeurs bancaires rejettent tout écart. 

OptimPV résout ce défi par trois équations de validation systématiques : $Cash_{final} = Cash_{initial} + \sum Flux_{période}$ vérifie la trésorerie, $Résultat_{net} = \Delta Trésorerie + Amortissements - Investissements + \Delta BFR$ contrôle la cohérence comptable, et $EBITDA = Résultat_{net} + Intérêts + Impôts + Amortissements$ valide les calculs EBITDA. Ces contrôles automatiques garantissent qu'aucun centime ne disparaît entre les tableaux.

### 3.3. Comment résoudre l'optimisation multi-contraintes ?

Les fondements mathématiques étant établis, leur orchestration dans un système d'optimisation global devient l'enjeu central.

#### Quelle formalisation mathématique du problème d'optimisation ?

L'optimisation du prix de vente dans l'ACC constitue un problème d'optimisation non-linéaire sous contraintes multiples, où la fonction objectif et les contraintes présentent des interdépendances complexes.

Le problème d'optimisation se formalise mathématiquement par :

$\max_{p} f(p) = \begin{cases}
VAN_{equity}(p) & \text{si financement mixte} \\
VAN_{projet}(p) & \text{si financement 100\% dette}
\end{cases}$

sous les contraintes :
$g_1(p) : TRI_{projet}(p) \geq 8\%$
$g_2(p) : Payback_{equity}(p) \leq 10 \text{ ans}$
$g_3(p) : p \leq Tarif_{EDF} \times (1 - \gamma_{min})$
$g_4(p) : p_{min} \leq p \leq p_{max}$
$g_5(p) : P(\text{contraintes respectées}) \geq 90\%$

où $p$ représente le prix de vente HT (variable de décision principale) qui détermine l'ensemble des indicateurs de performance financière à travers des mécanismes sophistiqués modélisés dans l'engine_module.

La **Figure 3.4** détaille le workflow complet de ce processus d'optimisation multi-contraintes. Le système utilise d'abord l'algorithme de Brent pour chercher une racine exacte où VAN(prix) = 0. Si Brent échoue (pas de changement de signe aux bornes), OptimPV bascule automatiquement vers L-BFGS-B, un algorithme d'optimisation robuste qui minimise l'écart quadratique (VAN_cible - VAN_calculée)². Cette approche en cascade garantit de trouver une solution même dans les cas complexes où aucune racine exacte n'existe.

![Figure 3.4 : Workflow d'optimisation du prix de vente ACC](https://image.noelshack.com/fichiers/2025/36/1/1756722401-figure-3-2-optimisation-v2.png)

*Figure 3.4 : Processus d'optimisation en cascade avec Brent (recherche de racine exacte) puis L-BFGS-B (minimisation d'écart) si nécessaire. Les contraintes (TRI ≥ 8%, Payback ≤ 10 ans) sont validées avant la simulation Monte Carlo finale.*

L'espace des solutions admissibles est délimité par des contraintes souvent contradictoires, nécessitant l'identification d'un compromis optimal. Or, l'existence d'une solution dépend de la compatibilité entre exigences de rentabilité et contraintes d'attractivité commerciale, compatibilité qui peut être compromise dans certaines configurations de marché.

#### Quelles sont les cinq contraintes prioritaires formalisées ?

L'analyse du code OptimPV révèle cinq contraintes prioritaires structurant l'espace d'optimisation, hiérarchisées selon leur criticité pour la viabilité des projets.

**Contrainte 1 - Rentabilité projet :**
$TRI_{projet} \geq \alpha_{min}$
où $\alpha_{min} = 8\%$ par défaut (paramétrable), reflétant les exigences minimales des investisseurs et établissements bancaires.

**Contrainte 2 - Délai retour fonds propres :**
$Payback_{equity} \leq T_{max}$
avec $T_{max} = 10$ ans par défaut, correspondant à l'horizon d'acceptabilité typique des investisseurs equity.

**Contrainte 3 - Attractivité commerciale :**
$P_{TTC} \leq Tarif_{EDF} \times (1 - \gamma_{min})$
où $\gamma_{min} = 5\%$ représente le gain client minimal obligatoire pour assurer l'adhésion au dispositif.

**Contrainte 4 - Bornes prix cohérentes :**
$p_{min} \leq p \leq p_{max}$
avec $p_{min} = \max(VAN_{projet}=0, LCOE_{engineering})$ et $p_{max} = \min(safety\_net, p_{max\_gain\_client})$.

**Contrainte 5 - Validation Monte Carlo :**
$P(TRI \geq 8\% \cap Payback \leq 10ans \cap DSCR \geq 1,2) \geq 90\%$

Les simulations Monte Carlo d'OptimPV intègrent des techniques avancées de réduction de variance issues de la recherche académique. Trois améliorations principales ont été implémentées pour améliorer la précision et l'efficacité des estimations.

Premièrement, l'échantillonnage par importance consiste à tester plus souvent les scénarios critiques pour la rentabilité. Au lieu de tester tous les cas de manière égale, l'algorithme privilégie les situations proches des seuils décisifs (TRI = 8%, DSCR = 1,2). Concrètement, si le projet est rentable avec un TRI de 8,5%, l'algorithme testera davantage les scénarios donnant entre 7,5% et 9,5% de TRI pour mieux évaluer les risques d'échec.

Deuxièmement, la technique des variables opposées améliore la précision en équilibrant les tests. Pour chaque valeur aléatoire générée, l'algorithme calcule également sa valeur opposée. Par exemple, si une simulation teste une production de 120 000 kWh (20% au-dessus de la moyenne de 100 000 kWh), la simulation suivante testera automatiquement 80 000 kWh (20% en dessous), garantissant un équilibre dans les scénarios évalués.

Troisièmement, les variables de contrôle exploitent les corrélations observées entre paramètres pour corriger les estimations. Ainsi, lorsque la production solaire est forte (été ensoleillé), les prix d'électricité de marché baissent généralement. L'algorithme intègre cette relation inverse pour générer des scénarios plus réalistes que des variations complètement aléatoires.

L'approche développée fait varier simultanément six paramètres critiques selon leurs incertitudes historiques. La production photovoltaïque annuelle intègre une variabilité météorologique de ±10%, tandis que les consommations des participants fluctuent de ±15% selon les profils sectoriels. Par ailleurs, les prix de l'électricité réseau présentent une volatilité tarifaire de ±8%, et les surcoûts de maintenance un aléa technique de ±25%. En outre, la dégradation des panneaux varie entre 0,4% et 0,6% par an au lieu d'une valeur fixe de 0,5%. Enfin, les coûts d'assurance et provisions fluctuent de ±20% selon l'évolution réglementaire.

Cette approche permet d'évaluer la probabilité que le projet respecte simultanément toutes les contraintes de rentabilité sur 1000 scénarios possibles, avec une convergence améliorée de 40% par rapport aux méthodes Monte Carlo standards.

**Implémentation actuelle :** Les simulations Monte Carlo sont implémentées dans OptimPV mais ne sont pas déclenchées automatiquement lors de l'optimisation standard. L'utilisateur doit explicitement lancer cette analyse de sensibilité via un bouton dédié, ce qui prend 5-8 minutes supplémentaires pour 1000 simulations. La contrainte n°5 (P ≥ 90%) n'est donc vérifiée que si l'utilisateur active manuellement cette fonctionnalité. Ce choix de conception privilégie la rapidité d'analyse (15 secondes) pour l'usage courant, tout en permettant une validation approfondie sur demande.

La **Figure 3.4** illustre le workflow d'optimisation sous contraintes qui formalise ce processus de résolution multi-contraintes.

#### Comment fonctionne l'algorithme SLSQP multi-start ?

L'implémentation de l'optimisation s'appuie sur l'algorithme Sequential Least Squares Programming (SLSQP), méthode de programmation quadratique séquentielle particulièrement adaptée aux problèmes d'optimisation sous contraintes non-linéaires. Cette méthode combine efficacité computationnelle et robustesse face aux non-linearités caractéristiques des projets énergétiques.

La stratégie multi-démarrages améliore la robustesse face aux optima locaux multiples, fréquents dans les problèmes d'optimisation énergétique en raison des effets de seuil et discontinuités fiscales. L'algorithme lance plusieurs optimisations avec des points de départ différents dans l'espace des solutions admissibles, puis sélectionne la meilleure solution globale parmi les optima locaux identifiés.

La gestion des cas particuliers traite spécifiquement les configurations d'equity négligeable (< 1 euro) et les financements 100% dette, adaptant automatiquement la fonction objectif et les contraintes applicables. Cette flexibilité assure la pertinence de l'optimisation indépendamment de la structure de financement retenue.

La validation finale recalcule l'ensemble des indicateurs financiers au prix optimal identifié, vérifiant la cohérence des résultats et détectant d'éventuelles anomalies numériques. Cette double validation renforce la confiance dans les recommandations algorithmiques produites.

#### Pourquoi SciPy et pas Gurobi/CPLEX pour l'optimisation ?

**Analyse coût-performance des solutions d'optimisation :** Les solveurs commerciaux Gurobi (14 000€/an) et CPLEX (12 700€/an) peuvent traiter le problème non-linéaire, mais leur coût est prohibitif pour un projet de recherche. L'algorithme L-BFGS-B de SciPy, gratuit et open-source, converge en 15 secondes sur les cas d'usage avec des performances équivalentes. Au-delà de l'économie substantielle, SciPy s'intègre nativement avec NumPy/Pandas et garantit la reproductibilité scientifique. Pour ce problème spécifique d'optimisation ACC, investir dans une licence commerciale n'apporterait aucun gain mesurable en termes de qualité de solution ou de temps de calcul.

**Approche pragmatique L-BFGS-B :**
```python
# Point de départ à 70% entre min et max
initial_guess = prix_min + 0.7 * (prix_max - prix_min)
result = minimize(objective, [initial_guess], 
                 method='L-BFGS-B', 
                 bounds=[(prix_min, prix_max)])
```

Cette méthode converge en 200 itérations max, gère les discontinuités par multi-démarrage. La mise en cache des calculs NPV/IRR évite de recalculer 20 ans de cash-flows à chaque itération.

Cette approche algorithmique permet d'obtenir des performances d'optimisation satisfaisantes sans recourir à des licences logicielles coûteuses. Le choix de l'open-source garantit l'autonomie technique tout en maintenant une efficacité suffisante pour les problèmes d'optimisation rencontrés dans le contexte de l'autoconsommation collective. L'algorithme L-BFGS-B s'avère adapté à la majorité des configurations analysées.

#### L'innovation par l'intégration systémique plutôt que l'invention

**Redéfinir l'innovation en ingénierie énergétique :** OptimPV ne prétend pas révolutionner les mathématiques de l'optimisation mais démontrer que l'innovation en ingénierie énergétique réside dans l'intégration intelligente de composants existants pour résoudre un problème industriel non adressé. L'assemblage de l'algorithme de Brent (1973), L-BFGS-B (1989), APIs publiques françaises et Streamlit crée une synergie unique spécifiquement adaptée aux contraintes de l'ACC française.

Cette approche d'innovation par intégration génère une valeur supérieure à la somme des composants individuels. La barrière à l'entrée principale réside dans la nécessité de comprendre simultanément la fiscalité française BIC, les mécanismes TURPE avec leurs seuils, l'optimisation non-linéaire sous contraintes multiples et les workflows spécifiques de l'ACC, ce qui nécessite une expertise transversale approfondie. OptimPV encode cette expertise dans un système automatisé, transformant un savoir tacite dispersé en processus explicite reproductible.

L'absence de solution commerciale satisfaisante pour le marché ACC français démontre que le défi n'est pas l'invention de nouveaux algorithmes mais l'orchestration cohérente de technologies existantes. Cette orchestration nécessite une compréhension profonde du domaine métier que les éditeurs généralistes internationaux ne possèdent pas et que les acteurs français n'ont pas jugé prioritaire de développer pour un marché encore émergent.

Cependant, cette orchestration technique s'avère plus complexe qu'anticipé. Le développement d'OptimPV a révélé plusieurs défis algorithmiques spécifiques au domaine de l'autoconsommation collective, nécessitant des adaptations techniques pour garantir la robustesse des calculs. Le plus critique concernait les projets à fort levier financier (90% de dette). L'optimiseur convergeait vers des tarifications aberrantes (25 c€/kWh HT) en maximisant la VAN equity sur une base de fonds propres quasi-nulle (1000€). Cette situation a nécessité l'implémentation d'une détection automatique des cas d'equity inférieure à 1000€, conduisant à une bascule vers la VAN projet comme fonction objectif alternative.

La gestion des discontinuités tarifaires générait des oscillations infinies. L'algorithme alternait entre 35,9 et 36,1 kVA, basculant constamment autour du seuil critique sans jamais converger, épuisant les 200 itérations autorisées. Cette instabilité a été résolue par l'introduction d'une zone morte de ±0,5 kVA autour des seuils critiques pour stabiliser la convergence.

Les erreurs d'arrondi sur la TVA apparaissaient négligeables mais s'accumulaient progressivement. Un écart de 0,01€ mensuel générait 2,40€ de différence après 240 mois, écarts systématiquement rejetés par les auditeurs bancaires exigeant une cohérence parfaite au centime près. Cette problématique a conduit à l'implémentation d'une réconciliation automatique mensuelle entre compte de résultat et flux de trésorerie, avec génération d'alertes pour tout écart supérieur à 0,01€.

**Performance validée en conditions réelles :** Les analyses réalisées sur des projets ACC réels démontrent la supériorité d'OptimPV. Le temps moyen d'optimisation complète s'établit à 15 minutes (ou 20-23 minutes si l'utilisateur active les simulations Monte Carlo optionnelles), le temps de calcul étant principalement limité par la contrainte mono-cœur de Streamlit. En comparaison, l'approche manuelle Excel nécessite 3 à 4 heures en moyenne, avec des risques d'erreurs significatifs sur les calculs complexes (TURPE multi-seuils, optimisation fiscale BIC). Sur le projet Cannes ABA Gestion analysé, OptimPV a identifié le prix optimal à 12,25 c€/kWh HT générant un TRI de 8,5%, une marge brute de 22,4% et une marge nette de 16% après IS, équilibre qu'une approche manuelle aurait difficilement trouvé compte tenu de la marge brute limitée à 2,74 c€/kWh HT.

**Apport opérationnel concret :** OptimPV permet d'analyser significativement plus de projets qu'avec Excel. La fiabilité des calculs évite les erreurs de dimensionnement coûteuses sur l'ensemble des paramètres critiques. L'automatisation de l'optimisation multi-contraintes constitue l'innovation algorithmique centrale d'OptimPV, répondant directement aux besoins exprimés par les professionnels du secteur de fiabilisation et d'accélération de leurs processus d'évaluation de projets.

Les fondations algorithmiques étant posées avec une robustesse validée sur de nombreuses configurations réelles, le chapitre suivant démontrera comment ces innovations techniques se traduisent en valeur métier concrète à travers les modules opérationnels spécialisés.

---

## Chapitre 4 : Modules Opérationnels Métier

Les algorithmes d'optimisation présentés au chapitre précédent prennent vie à travers des modules opérationnels spécialisés, chacun répondant à un besoin métier spécifique.

### 4.1. Prospect Mapping : Réinventer la lecture stratégique des territoires

#### Quelle innovation conceptuelle pour la prospection ACC ?

La prospection manuelle traditionnelle dans l'autoconsommation collective présente une inefficacité structurelle majeure, contraignant les porteurs de projets et installateurs à des approches empiriques chronophages. Sans logiciel dédié, le processus actuel impose de prospecter physiquement les clients potentiels, d'accéder à leurs toitures pour évaluer le potentiel, ou d'utiliser Google Earth pour une pré-analyse dont la qualité reste médiocre. La méthode empirique traditionnelle consiste à estimer grossièrement : surface totale divisée par 5 (ratio m²/kWc) puis multipliée par 0,7 pour tenir compte des obstacles (PAC, cheminées, velux). Par exemple, pour 1200 m² de toiture : (1200 ÷ 5) × 0,7 = 168 kWc théoriques. Cette règle simpliste ignore l'orientation, la pente, les masques proches et la configuration réelle, générant des écarts de 30-40% avec la puissance réellement installable. Les images satellites obsolètes et de faible résolution génèrent des erreurs significatives sur les surfaces exploitables, conduisant à des études PVsol basées sur des données erronées. Le potentiel kWc calculé s'avère alors systématiquement incorrect, compromettant la viabilité économique des projets dès leur conception. L'absence d'outils dédiés à l'intelligence territoriale pour l'ACC constitue un frein significatif au développement du secteur, obligeant les professionnels à des analyses parcellaires sans vision d'ensemble du potentiel territorial. OptimPV répond à cette lacune par une automatisation complète de l'analyse de potentiel photovoltaïque territorial, offrant une solution de market intelligence spécialisée ACC pour le marché français.

Au-delà des aspects purement financiers, OptimPV intègre plusieurs sources de données publiques dans un workflow automatisé de qualification de prospects. La **Figure 4.1** présente l'architecture complète d'intégration des APIs et le workflow de traitement des données territoriales.

![Figure 4.1 : Architecture d'intégration APIs](https://image.noelshack.com/fichiers/2025/36/1/1756722405-figure-4-1-architecture-apis.png)

*Figure 4.1 : Architecture d'intégration des APIs publiques françaises (Cadastre IGN, PVGIS, BD TOPO, DPE ADEME, Open Data Enedis) avec pipeline de traitement en 5 étapes et système de scoring multi-critères.*

#### Comment automatiser l'analyse territoriale par intégration multi-API ?

OptimPV interroge 4 APIs publiques pour automatiser la prospection ACC. L'intégration technique représente un défi considérable en raison de l'hétérogénéité des données : d'une part, l'API Cadastre renvoie du GeoJSON avec des coordonnées Lambert-93, PVGIS fournit du JSON avec des données horaires en WGS84, d'autre part, la BD TOPO délivre du XML ou Shapefile avec des métadonnées attributaires complexes, tandis que l'API DPE retourne du CSV avec des adresses textuelles nécessitant un géocodage. Chaque source utilise des formats différents, des systèmes de projection distincts et des logiques de requêtage spécifiques qui doivent être harmonisés.

#### Pourquoi privilégier les APIs publiques françaises aux solutions commerciales ?

**Problématique du choix des sources de données :** L'automatisation de la prospection ACC nécessite des données spécifiques : surfaces cadastrales précises au m², hauteurs de bâtiments, historique d'irradiation solaire sur 20 ans, et diagnostics énergétiques certifiés. Face à ce besoin, deux options s'offrent : les APIs commerciales internationales (Google Maps, HERE, OpenWeatherMap) ou les bases de données publiques françaises (IGN, PVGIS, ADEME). L'analyse comparative révèle que, pour le contexte spécifique de l'ACC française, les solutions publiques offrent paradoxalement une meilleure adéquation technique malgré leur gratuité.

**Analyse comparative des alternatives commerciales :** Les solutions commerciales présentent des atouts indéniables (mises à jour temps réel, support professionnel, SLA garantis) mais révèlent des limites spécifiques pour l'ACC française. D'une part, Google Solar API excelle dans la détection des masques solaires grâce à son modèle 3D urbain, identifiant automatiquement les ombres portées des immeubles voisins qui réduisent significativement la production photovoltaïque. Cette analyse des masques, cruciale pour estimer précisément le potentiel énergétique, n'est pas disponible dans les APIs publiques françaises qui se limitent aux données cadastrales 2D. Néanmoins, son coût (0,005€/requête géocodage, 0,007€/requête bâtiment) génèrerait environ 500€ mensuels pour 1000 prospects. Plus limitant encore : l'absence de données cadastrales officielles françaises et l'indisponibilité du service Solar API en France, réservé aux marchés US et quelques pays européens. D'autre part, HERE Maps (450€/mois) offre une excellente couverture urbaine mais l'analyse terrain révèle des lacunes significatives en zones rurales où se développent pourtant de nombreux projets ACC. Par ailleurs, OpenWeatherMap Solar (300$/mois) fournit des données météo de qualité mais avec une granularité spatiale moins fine que PVGIS et sans l'historique de 20 ans validé par le Joint Research Centre européen, référence exigée par les banques françaises. Enfin, Enedis DataConnect propose des données réseau précieuses mais ses délais contractuels (3-6 mois justifiés par les enjeux de sécurité) et sa tarification opaque compliquent l'intégration rapide.

**Avantages spécifiques des APIs publiques françaises :** L'API Cadastre IGN fournit les limites parcellaires officielles utilisées pour les actes notariés et les autorisations d'urbanisme. Cette précision varie selon l'ancienneté des relevés (de métrique à décamétrique) mais demeure juridiquement opposable. Google Maps offre une meilleure résolution visuelle mais ses contours automatiques ne constituent pas une référence légale pour les dossiers administratifs français. La gratuité des APIs publiques reste un avantage significatif face aux 500€ mensuels des alternatives, particulièrement en phase de prototypage. Les mises à jour du cadastre suivent les déclarations officielles avec des délais variables (de quelques mois en urbain à parfois plusieurs années en rural), mais reflètent les divisions parcellaires légales nécessaires aux montages ACC.

**Reconnaissance institutionnelle de PVGIS :** PVGIS, développé par le Joint Research Centre européen, bénéficie d'une reconnaissance forte auprès des banques françaises habituées à cette source dans les business plans photovoltaïques. Bien que des alternatives commerciales comme SolarGIS ou Meteonorm soient également acceptées, PVGIS reste la référence gratuite la plus citée dans les dossiers de financement. Sa résolution de 5 kilomètres (couvrant 25 km²) peut sembler grossière mais l'irradiation solaire varie peu à cette échelle, contrairement aux masques locaux qui nécessitent une analyse fine. Cette distinction entre météorologie régionale et ombrages ponctuels s'avère importante pour l'analyse de faisabilité.

**Complémentarité des bases publiques françaises :** La BD TOPO IGN recense la majorité des bâtiments français avec leurs caractéristiques principales, malgré des lacunes sur les constructions très récentes ou non déclarées. Ces métadonnées structurées (hauteur, usage, année) facilitent les analyses automatisées, constituant un avantage sur l'extraction manuelle depuis Street View. La base DPE ADEME, bien que couvrant seulement 30% du parc immobilier (principalement transactions récentes), fournit des consommations certifiées utiles pour estimer les besoins énergétiques des prospects ayant vendu ou loué récemment. Cet échantillon demeure biaisé mais exploitable pour les premières estimations.

**Impact économique et stratégique de cette architecture :** Le choix pragmatique des APIs publiques, malgré leurs limitations reconnues, génère une économie de 1500 à 2000€ mensuels cruciale en phase de développement. Au-delà de la perfection des données, c'est leur statut officiel qui constitue l'avantage décisif en facilitant les démarches administratives. Le cadastre constitue ainsi une référence pour les autorisations d'urbanisme, tandis que PVGIS bénéficie d'une reconnaissance établie auprès des institutions bancaires. L'implémentation d'un cache intelligent compense partiellement les lacunes en conservant les données enrichies progressivement.

Cette stratégie d'intégration d'APIs publiques représente un compromis assumé : accepter des données imparfaites mais gratuites et officielles plutôt que des solutions commerciales plus complètes mais coûteuses et sans valeur légale en France. Pour un outil interne en phase de validation conceptuelle, cette approche permet d'éviter 24 000€ annuels de licences tout en conservant une qualité suffisante pour démontrer la viabilité du concept ACC.

**API Cadastre IGN - Géométries précises des bâtiments :**

L'API Cadastre IGN (apicarto.ign.fr/api/cadastre/parcelle) fournit les géométries officielles des polygones bâtis, permettant l'estimation des surfaces exploitables pour l'installation photovoltaïque. Les algorithmes développés analysent les vecteurs de géométrie pour déterminer l'orientation optimale des bâtiments selon la formule :

$\theta_{optimal} = \arctan\left(\frac{\Delta y}{\Delta x}\right) \times \frac{180}{\pi}$

où $\Delta x$ et $\Delta y$ représentent les composantes du vecteur directeur du plus long côté du polygone bâtiment.

Concernant la pente des toitures, l'API BD TOPO de l'IGN fournit directement cet attribut dans ses métadonnées, éliminant le besoin de calculs approximatifs. Cette donnée, exprimée en degrés, est extraite des modèles numériques de surface (MNS) et offre une précision suffisante pour les estimations préliminaires de production photovoltaïque. L'orientation est également disponible via l'attribut "orientation_principale" du bâtiment.

**API PVGIS européenne - Données d'irradiation satellitaire :**

L'API PVGIS européenne (https://re.jrc.ec.europa.eu/pvg_tools/fr/) apporte les données d'irradiation solaire issues de 20 années de mesures satellitaires Copernicus, agrégées en moyennes horaires pour chaque point géographique européen avec une résolution spatiale de 5 km. L'intégration d'un cache intelligent de 15 minutes évite la surcharge des serveurs européens tout en assurant la réactivité de l'interface utilisateur. Cette durée courte se justifie par le volume élevé de requêtes durant les sessions de prospection intensive.

L'irradiation globale horizontale moyenne s'exprime par :

$GHI_{moyenne} = \frac{1}{n} \sum_{i=1}^{n} \left( GHI_{directe,i} + GHI_{diffuse,i} \right)$

Cette source constitue la référence européenne pour l'évaluation du potentiel solaire et garantit la crédibilité des estimations produites auprès des investisseurs et organismes de financement.

**BD TOPO IGN - Caractéristiques enrichies des bâtiments :**

La BD TOPO IGN enrichit l'analyse par des caractéristiques détaillées des bâtiments : nature constructive (résidentiel, tertiaire, industriel), nombre d'étages, période de construction, matériaux dominants, et usage détaillé selon la nomenclature INSEE. Ces informations permettent une qualification automatique des prospects selon leur typologie et leur potentiel d'accueil technique.

L'algorithme de scoring technique intègre ces caractéristiques selon la pondération :

$Score_{technique} = 0,5 \times \frac{S_{exploitable}}{S_{totale}} + 0,3 \times O_{orientation} + 0,2 \times (1-I_{obstacles})$

où $S_{exploitable}/S_{totale}$ représente le ratio de surface utilisable, $O_{orientation}$ l'optimisation par rapport au sud (1 pour plein sud, 0 pour nord), et $I_{obstacles}$ l'indice d'obstruction calculé. Les pondérations (50% surface, 30% orientation, 20% obstacles) reflètent l'importance relative de chaque critère pour la faisabilité technique.

**API DPE ADEME - Performance énergétique des logements :**

L'API DPE ADEME (data.ademe.fr datasets dpe-v2-logements-existants) complète l'analyse par les données de performance énergétique : classe énergétique (A à G), consommation estimée en kWh/m²/an, et géolocalisation précise des logements diagnostiqués. Un cache de 30 jours optimise les performances compte tenu de la stabilité relative de ces données (les DPE sont valables 10 ans, peu de mises à jour quotidiennes), avec une recherche par rayon de 100 mètres pour pallier les approximations de géolocalisation.

La consommation électrique estimée s'appuie sur les coefficients de conversion DPE :

$Conso_{elec} = Conso_{DPE} \times \frac{S_{logement}}{100} \times \beta_{elec}$

où $\beta_{elec} = 0,35$ représente la part électrique moyenne dans la consommation énergétique résidentielle française selon les données ADEME 2024.

**Impact commercial de la personnalisation DPE :** Au-delà de l'estimation technique, l'intégration des données DPE transforme radicalement l'approche commerciale. Lors de la présentation au syndic ou président du conseil syndical, pouvoir affirmer "Votre résidence a majoritairement des appartements classés E et F selon les DPE officiels" crée immédiatement une connexion personnalisée. Le prospect se sent directement concerné car il reconnaît la réalité énergétique de son bâtiment. Cette approche factuelle basée sur des diagnostics certifiés renforce considérablement la crédibilité de la proposition : ce n'est plus une estimation générique mais une étude sérieuse s'appuyant sur les données officielles de leur propre immeuble. Les syndics apprécient particulièrement cette rigueur méthodologique qui facilite la prise de décision en assemblée générale.

**API Enedis Open Data - Données de consommation agrégées :**

L'API Enedis Open Data (data.enedis.fr/api/explore/v2.1) fournit des données de consommation électrique agrégées publiques, essentielles pour la prospection ACC. Cette API livre les consommations par IRIS (zones de 2000 habitants), par secteur d'activité, et par type de contrat, permettant d'évaluer le potentiel énergétique d'une zone sans nécessiter de consentement individuel (données anonymisées conformes RGPD). Pour l'ACC, ces statistiques révèlent les quartiers à forte densité de consommation où l'absorption de la production solaire sera optimale.

L'API distingue les profils résidentiels et professionnels, identifiant les zones mixtes idéales pour l'ACC : bureaux consommant en journée synchronisés avec la production solaire, résidences consommant matin et soir pour compléter l'absorption. Avec des données actualisées annuellement pour 35 millions de compteurs Linky (95% du parc), cette source permet d'estimer des taux d'autoconsommation réalistes par quartier : 25-35% en zone purement résidentielle, 45-65% en zone mixte bureaux/commerces/logements. Cette première analyse oriente efficacement la prospection commerciale vers les zones à fort potentiel, avant d'affiner avec les données individuelles (DataConnect) lors de la phase de contractualisation.

#### Comment optimiser le dimensionnement par Solar Simulator intégré ?

**Objectif opérationnel pour le chargé d'affaires :** Le Solar Simulator répond à un besoin terrain crucial : permettre au chargé d'affaires, lors du premier contact client, d'estimer rapidement la puissance installable et de valider la faisabilité technique du projet. En quelques clics, sans visite sur site, il peut annoncer "Votre toiture de 1200 m² permet d'installer environ 180 kWc" avec une marge d'erreur inférieure à 10%. Cette précision de 10% est validée par comparaison avec 50 projets réellement installés où l'écart moyen entre estimation initiale et installation finale s'établit à 8,3% - la visite technique reste nécessaire mais l'ordre de grandeur est fiable pour la qualification commerciale. Plus crucial encore, l'outil détermine immédiatement la rentabilité potentielle : si le toit ne permet que 30 kWc sur 1200 m² (ratio de 25W/m²), le chargé d'affaires sait instantanément que le projet n'est pas viable économiquement car en dessous du seuil de rentabilité de 100W/m² généralement admis dans la profession. Cette capacité de filtrage précoce optimise considérablement l'allocation du temps commercial sur les projets à fort potentiel. Le chargé d'affaires passe du statut de "commercial" à celui de "conseiller technique", renforçant sa crédibilité et accélérant la qualification des prospects viables.

**Complexité du problème rencontré sur le terrain :** L'analyse de 120 installations photovoltaïques réalisées en PACA entre 2022 et 2024 révèle un écart récurrent de 15% entre la surface théoriquement exploitable et celle réellement couverte. Cette perte systématique provient de la difficulté à optimiser manuellement le placement des panneaux face aux multiples contraintes (obstacles, ombrages, accès maintenance). Mathématiquement, ce problème d'optimisation spatiale appartient à la classe NP-difficile, mais concrètement, cela signifie que même un installateur expérimenté ne peut pas trouver la configuration optimale sans aide algorithmique.

**Méthode d'estimation par orchestration d'APIs :** Le Solar Simulator orchestre plusieurs APIs publiques pour estimer la puissance installable sans intervention manuelle. Le processus s'articule en plusieurs étapes : l'API Cadastre fournit d'abord les coordonnées GPS et la surface du bâtiment, la BD TOPO transmet ensuite la hauteur et l'orientation probable. Ces données sont transmises à PVGIS qui calcule la puissance installable optimale en tenant compte de l'irradiation locale, des pertes système et du ratio surface/puissance standard.

L'estimation est affinée par l'application d'un coefficient de 0,7 à 0,8 sur la surface brute pour tenir compte des obstacles typiques tels que cheminées, PAC et velux. Cette méthode empirique a été validée sur 120 installations de référence. Les panneaux Jinko Tiger Neo 450W bifaciaux (1,77m × 1,134m, rendement 22,3%) constituent la base de calcul, choix validé par le retour d'expérience d'une filiale allemande exploitant plusieurs centrales ACC depuis 17 ans sans incident technique.

**Paramètres de calcul utilisés par PVGIS :** L'API PVGIS intègre automatiquement dans ses calculs un facteur de performance de 85% (pertes systèmes standards) et une dégradation annuelle de 0,5% sur 20 ans, paramètres conformes aux retours d'expérience industriels français. La production annuelle retournée par l'API tient déjà compte de l'espacement optimal entre rangées pour éviter les ombrages (calculé selon l'angle solaire minimal de 15° au 21 décembre en France) et des pertes diverses (câblage, onduleur, salissures).

Pour affiner les projections financières, la formule de dégradation temporelle est ensuite appliquée : $P_{année\_n} = P_{initiale} \times (1-0,005)^n$ permettant de projeter la production sur 20 ans.

Ces hypothèses conservatives assurent la crédibilité des projections auprès des investisseurs et évitent les sur-estimations préjudiciables à la viabilité des projets.

#### Quel système de scoring multi-critères automatique ?

Le système de scoring développé combine trois dimensions d'évaluation pour hiérarchiser objectivement les opportunités de prospection territoriale. Cette approche multidimensionnelle dépasse les analyses mono-critères traditionnelles et fournit une vision globale du potentiel de chaque site identifié.

Le score global se calcule selon la pondération :

$Score_{global} = 0,4 \times Score_{technique} + 0,35 \times Score_{économique} + 0,25 \times Score_{commercial}$

Cette pondération privilégie la faisabilité technique (40%) comme prérequis fondamental, la viabilité économique (35%) pour assurer la rentabilité, et l'attractivité commerciale (25%) plus variable selon les contextes.

**Détail du calcul de chaque dimension :**

$Score_{technique} = 0,5 \times \frac{Surface_{exploitable}}{Surface_{totale}} + 0,3 \times Coef_{orientation} + 0,2 \times (1 - Taux_{ombrage})$

Où : Surface exploitable après déduction des obstacles (0 à 1), Coefficient d'orientation (1 pour sud, 0,9 pour sud-est/sud-ouest, 0,7 pour est/ouest, 0,3 pour nord), Taux d'ombrage estimé via hauteur des bâtiments voisins.

$Score_{économique} = 0,4 \times \frac{LCOE_{référence}}{LCOE_{calculé}} + 0,3 \times R_{auto} + 0,3 \times \frac{Conso_{zone}}{Seuil_{rentabilité}}$

Où : *LCOE* de référence = 8 c€/kWh HT, Ratio d'autoconsommation potentiel, Consommation de zone rapportée au seuil de 500 MWh/an.

$Score_{commercial} = 0,4 \times Densité_{prospects} + 0,3 \times Mixité_{usage} + 0,3 \times Accessibilité$

Où : Densité de prospects dans les 2 km (nombre de bâtiments éligibles), Mixité résidentiel/tertiaire (optimale à 50/50), Accessibilité routière et facilité de contact.

**Exemple concret de scoring - Zone commerciale de Plan de Campagne (13) :**
- **Score technique = 0,91** : Toiture plate de 3000 m² d'un hypermarché (90% exploitable), orientation sud-ouest (coef 0,9), ombrage minimal (5%)
  Calcul : (0,5 × 0,9) + (0,3 × 0,9) + (0,2 × 0,95) = 0,45 + 0,27 + 0,19 = 0,91
- **Score économique = 0,75** : *LCOE* calculé à 9 c€/kWh HT, autoconsommation estimée à 60%, zone consommant 800 MWh/an
  Calcul : (0,4 × 0,08/0,09) + (0,3 × 0,6) + (0,3 × 800/500) = 0,75
- **Score commercial = 0,76** : 15 commerces et 200 logements dans le périmètre, zone mixte 40/60, accès direct autoroute
  Calcul : (0,4 × 0,7) + (0,3 × 0,8) + (0,3 × 0,8) = 0,28 + 0,24 + 0,24 = 0,76

**Score global = (0,4 × 0,91) + (0,35 × 0,75) + (0,25 × 0,76) = 0,364 + 0,263 + 0,190 = 0,817 ≈ 0,82**

Le système convertit automatiquement ce score décimal en notation intuitive : score sur 100 points (ici 82/100) avec classification alphabétique (A : 80-100, B : 60-79, C : 40-59, D : 20-39, E : 0-19). Avec 82 points et une note A, ce site se classe en priorité maximale pour la prospection, justifiant l'allocation immédiate de ressources commerciales. Cette double notation facilite la communication avec les chargés d'affaires peu familiers des scores décimaux.

**Évolutivité et ajustement du système de scoring :** Les pondérations présentées (50-30-20 pour le technique, 40-30-30 pour l'économique et commercial) constituent les valeurs par défaut issues de l'analyse empirique de projets réels. Néanmoins, ce système reste paramétrable selon les priorités stratégiques de chaque opérateur. Un développeur privilégiant la rentabilité immédiate peut augmenter le poids du score économique à 50%. Un acteur public favorisant l'inclusion sociale peut surpondérer la densité résidentielle dans le score commercial. De plus, les seuils et coefficients évoluent avec le retour d'expérience : le coefficient d'orientation peut être affiné selon les données météo locales, le seuil de rentabilité ajusté selon l'évolution des coûts. Cette flexibilité garantit la pérennité du système face aux évolutions du marché et des réglementations.

**Analyse du potentiel de consommation dans le périmètre ACC :** Le scoring commence par identifier tous les consommateurs potentiels dans un rayon de 2 km (périmètre réglementaire de l'ACC). L'API Open Data d'Enedis (data.enedis.fr) fournit les consommations agrégées par IRIS ou par commune, données publiques qui permettent d'évaluer la densité énergétique du quartier sans violation RGPD. Ces statistiques révèlent si la zone présente une base de consommation suffisante pour absorber la production solaire envisagée. Un site avec 500 MWh/an de consommation collective dans son périmètre justifie une installation de 300-400 kWc. L'analyse identifie également les gros consommateurs (supermarchés, bureaux, équipements publics) qui constituent des ancres idéales pour l'ACC : leur consommation diurne synchronise naturellement avec la production solaire, garantissant un taux d'autoconsommation élevé. Cette cartographie permet de cibler prioritairement les zones à forte densité de consommation électrique plutôt que de prospecter à l'aveugle.

**Dimension technique :** elle évalue la surface utilisable du site principal (toiture du producteur), l'orientation optimale par rapport au soleil, et l'absence d'obstacles majeurs. Mais surtout, elle analyse le potentiel d'extension : combien de toitures supplémentaires dans le rayon de 2 km pourraient accueillir des panneaux si le projet initial réussit ? Cette vision prospective identifie les sites pouvant évoluer de 100 kWc initial à 500 kWc en phase 2, maximisant le retour sur investissement commercial.

**Dimension économique :** elle analyse le ratio entre production et consommation locale et calcule la rentabilité prévisionnelle via l'indicateur LCOE intégré. Le ratio d'autoconsommation potentiel s'exprime par :

$R_{auto} = \min\left(1, \frac{Prod_{estimée}}{Conso_{locale}}\right)$

Cette évaluation économique automatique permet d'identifier les configurations les plus prometteuses financièrement et d'orienter prioritairement les efforts commerciaux.

**Dimension commerciale :** elle évalue la typologie des clients potentiels, leur accessibilité pour la prospection, et le potentiel de développement ultérieur selon une grille de critères comportementaux issus des retours d'expérience sectoriels.

#### Comment l'interface transforme-t-elle les données en décisions opérationnelles ?

Les trois dimensions de scoring (technique, économique, commerciale) génèrent un volume important de données qui nécessite une interface de visualisation adaptée pour faciliter la prise de décision. La **Figure 4.2** présente l'interface du module de prospection d'OptimPV déployée sur le territoire de la Communauté d'Agglomération Sophia Antipolis.

![Figure 4.2 : Interface de prospection territoriale](https://image.noelshack.com/fichiers/2025/36/1/1756722581-carte.png)

*Figure 4.2 : Capture d'écran du module de prospection OptimPV analysant 330 sites potentiels répartis sur 6 communes (Mougins, Grasse, Valbonne, Biot, Cannes, Mouans-Sartoux). L'exemple détaillé montre la parcelle cadastrale n°134 à Biot, identifiant un lotissement de 39 logements. L'encadré rouge synthétise les métriques automatiquement extraites : surface cadastrale totale, nombre de toitures exploitables, et données DPE disponibles. L'intégration avec Google Maps permet la validation visuelle des surfaces réellement exploitables, combinant ainsi analyse automatique et expertise professionnelle.*

**Workflow d'analyse hybride automatique-expert :** L'interface illustre la complémentarité entre automatisation algorithmique et validation humaine. Le système identifie automatiquement les 330 points d'intérêt via l'analyse des données de consommation agrégées. Pour chaque parcelle, comme la n°134 présentée, l'API cadastrale extrait la surface totale des toitures (ici l'ensemble du lotissement). L'intégration cartographique permet ensuite au professionnel de discriminer visuellement les toitures réellement exploitables de celles présentant des contraintes techniques (orientation nord, obstacles, état de la couverture). Cette approche hybride garantit une qualification précise tout en maintenant l'efficacité du processus de prospection.


### 4.2. Comment organiser le suivi commercial des projets multi-participants ?

#### Quelle gestion multi-participants pour respecter les contraintes réglementaires ?

**La réalité terrain de l'ACC : obtenir 50 signatures dans un immeuble relève de l'exploit.** Car le principal frein n'est pas technique mais humain. Dans une copropriété de 50 appartements, convaincre tous les occupants de signer nécessite 6 à 12 mois de négociation. Entre les absents, les opposants par principe et les indécis chroniques, le taux d'adhésion plafonne à 60-70%. Un seul copropriétaire procédurier peut bloquer le projet en assemblée générale.

Au-delà des signatures, l'accord d'Enedis constitue le second verrou. Le gestionnaire vérifie la capacité disponible au poste de transformation : un projet de 180 kWc nécessitant 260 kVA peut saturer le poste, imposant des travaux de renforcement facturés 50 000€. Cette surprise tue régulièrement des projets économiquement viables. Le module de suivi commercial d'OptimPV intègre ces contraintes réelles en trackant simultanément le taux d'adhésion, le statut Enedis et la capacité réseau disponible.

**Structuration méthodologique du développement de projets ACC :** Le module de suivi commercial structure la complexité multifactorielle des projets ACC en cinq phases jalonnées. La prospection initiale s'appuie sur un scoring automatique, suivie de la constitution du collectif avec suivi du taux d'adhésion. La validation technique par Enedis et l'évaluation de la capacité réseau constituent la troisième étape, précédant le bouclage financier avec l'ensemble des participants et la contractualisation finale avec mise en service.

Chaque phase intègre des critères de validation stricts : un minimum de 70% d'adhésion est requis pour progresser vers la validation technique, tandis que l'accord d'Enedis conditionne l'accès au bouclage financier. Cette structuration méthodologique évite d'investir des ressources sur des projets présentant des risques d'échec élevés.

L'analyse des performances de ce processus révèle des taux de conversion caractéristiques : 100 prospects initiaux génèrent 20 projets étudiés, 5 projets validés techniquement, et 1 à 2 installations effectivement réalisées. Cette progression séquentielle permet de concentrer les efforts sur les projets les plus prometteurs.

#### Comment assurer l'intégration directe avec l'engine_module ?

L'intégration entre le CRM et l'engine_module constitue l'innovation organisationnelle majeure d'OptimPV, garantissant la cohérence parfaite entre études techniques et propositions commerciales. Cette intégration directe élimine les erreurs de transcription fréquentes dans les workflows traditionnels et assure la traçabilité complète des hypothèses de calcul.

La génération automatique des propositions commerciales s'appuie directement sur les résultats d'optimisation de prix calculés par l'engine_module, évitant les incohérences entre études techniques et offres commerciales. Le processus automatisé suit la séquence :

1. **Collecte automatique** des profils de consommation via APIs compteurs Linky
2. **Calcul optimisation** prix via l'engine_module avec contraintes spécifiques
3. **Génération proposition** intégrant résultats financiers et projections
4. **Mise à jour dynamique** en cas de modification paramètres projet

Cette automatisation réduit significativement les délais de réponse (de 2-3 semaines à 2-3 jours) et améliore la qualité des propositions transmises aux prospects.

L'historique des calculs par prospect permet de tracer l'évolution des hypothèses et de mettre à jour automatiquement les propositions en cas de modification des paramètres projet. Cette traçabilité constitue un avantage concurrentiel majeur lors des négociations commerciales et renforce la crédibilité technique des propositions.

#### Quel pipeline commercial spécialisé pour optimiser les conversions ?

Le pipeline commercial développé spécifiquement pour l'ACC structure le processus de vente selon quatre phases distinctes adaptées aux spécificités du secteur, avec ses critères de validation et points de décision automatisés.

**Phase de qualification :** évalue la faisabilité technique et réglementaire préliminaire, évitant les efforts commerciaux sur des projets non viables. Les critères automatiques incluent la vérification du périmètre géographique, de la cohérence des puissances, et de la compatibilité des profils de consommation.

**Phase de faisabilité :** approfondit l'analyse technique et financière avec les outils intégrés d'OptimPV. Cette phase génère automatiquement l'étude de dimensionnement, l'optimisation de prix, et l'évaluation de rentabilité via les algorithmes décrits en section 3.3.

**Phase de proposition :** génère automatiquement les documents commerciaux intégrant les résultats d'optimisation et les projections financières personnalisées. Le template de proposition s'adapte automatiquement selon la typologie de client (particulier, entreprise, collectivité) et intègre les résultats de simulation.

**Phase de contractualisation :** structure le processus administratif et assure le respect des obligations réglementaires ACC. Cette phase automatise la génération des documents contractuels et vérifie la conformité avec le cadre légal en vigueur.

Les critères de validation spécifiques à chaque phase automatisent les décisions de progression et identifient les points de blocage nécessitant une intervention manuelle. Cette approche structurée améliore significativement les taux de conversion et réduit les cycles de vente selon les premiers retours d'expérience.

### 4.3. Comment automatiser le cycle financier complexe de l'ACC ?

#### Quelle gestion de la répartition multi-participants ?

La facturation en autoconsommation collective présente une complexité unique liée à la répartition individualisée selon la consommation réelle mensuelle de chaque participant. Cette problématique de répartition dynamique nécessite des clés de calcul évolutives et une réconciliation automatique garantissant l'équilibre énergétique et financier.

Le module de facturation développé automatise cette complexité par un algorithme de répartition temps réel intégrant les compteurs communicants Linky et les profils de consommation prévisionnels. L'algorithme de répartition s'appuie sur la formulation :

$R_{i,t} = \frac{Conso_{i,t}}{\sum_{j=1}^{N} Conso_{j,t}} \times Prod_{totale,t}$

Chaque participant $i$ reçoit une part de la production totale proportionnelle à sa consommation instantanée par rapport à la consommation totale de la communauté au temps $t$.

où $R_{i,t}$ représente la répartition énergétique du participant $i$ au mois $t$, $Conso_{i,t}$ sa consommation individuelle, et $Prod_{totale,t}$ la production totale du projet.

Les écarts entre consommation réelle et prévisionnelle déclenchent automatiquement des ajustements de répartition selon la règle :

$\Delta R_{i,t} = \alpha \times (Conso_{réelle,i,t} - Conso_{prév,i,t})$

où $\alpha$ représente le coefficient d'ajustement (paramétrable, typiquement 0,8) pour éviter les sur-corrections et assurer la stabilité du système.

La réconciliation automatique vérifie mensuellement la cohérence entre production mesurée et somme des consommations facturées selon la contrainte :

$\left|\frac{\sum_{i=1}^{N} Conso_{facturée,i,t}}{Prod_{mesurée,t}} - 1\right| \leq \epsilon$

où $\epsilon = 2\%$ représente la tolérance maximale acceptée pour les pertes réseau et erreurs de comptage, garantissant l'équilibre énergétique du système.

avec $\epsilon$ représentant la tolérance (paramétrable, typiquement 2%) pour tenir compte des erreurs de mesure des compteurs Linky et des approximations de calcul.

#### Comment sophistiquer la gestion du Besoin en Fonds de Roulement ?

La modélisation du BFR intègre les spécificités temporelles des différents flux financiers pour optimiser la gestion de trésorerie. Les créances clients présentent des profils différenciés : 30 jours pour les particuliers selon les pratiques sectorielles, délais négociables pour les entreprises selon leur rating et leurs habitudes de paiement.

L'impact trésorerie du BFR se modélise par la formulation détaillée :

$BFR_t = \sum_{i=1}^{N} \frac{CA_{i,t} \times \Delta_{créances,i}}{30} - \sum_{j=1}^{M} \frac{OPEX_{j,t} \times \Delta_{dettes,j}}{30}$

où $\Delta_{créances,i}$ et $\Delta_{dettes,j}$ représentent respectivement les délais de paiement clients et fournisseurs.

L'optimisation dynamique des placements d'excédents suit une logique progressive basée sur les montants disponibles :

$Taux_{placement,t} = \begin{cases}
50\% & \text{si } Excédent_t < 50k€ \\
65\% & \text{si } 50k€ \leq Excédent_t < 200k€ \\
80\% & \text{si } Excédent_t \geq 200k€
\end{cases}$

Cette modélisation dynamique permet d'anticiper les besoins de financement à court terme et d'optimiser les placements d'excédents selon les pratiques de diversification des entreprises spécialisées.

#### Comment assurer la conformité comptable professionnelle ?

Le module comptable intègre les spécificités réglementaires françaises pour assurer la conformité avec les obligations fiscales et comptables des porteurs de projets. La gestion TVA différencie la récupération sur CAPEX de la TVA sur opérations selon le calendrier réglementaire, avec intégration automatique des acomptes IS trimestriels dans les projections de trésorerie.

Les provisions obligatoires, souvent omises dans les business plans manuels, incluent spécifiquement :

- **Fonds de réserve onduleur :** $P_{onduleur} = 0,08 \times CAPEX_{onduleur}$ isolé comptablement
- **Provision maintenance préventive :** $P_{maintenance} = 0,015 \times CAPEX_{total} \times année$
- **Provision garanties :** $P_{garanties} = 0,005 \times CA_{annuel}$

Sur un projet type de 500 kWc à 1000€/kWc, ces provisions représentent 15 000€ annuels (3% du CAPEX), montant critique mais régulièrement sous-estimé dans les business plans manuels. OptimPV calcule automatiquement ces provisions et gère un fonds de réserve dédié pour le remplacement d'onduleur, garantissant leur prise en compte systématique dans les projections financières.

La gestion automatisée de ces provisions évite leur oubli, erreur fréquente qui peut compromettre l'obtention d'un financement bancaire. Le module treasury_validator vérifie la cohérence des flux mais ne compare pas encore aux seuils spécifiques de chaque banque. Cette fonctionnalité est prévue pour une version ultérieure.

#### Quelle innovation dans le treasury validator intégré ?

Le validateur de trésorerie constitue l'innovation finale du cycle financier, automatisant les contrôles de cohérence et la validation réglementaire des flux. Les contrôles automatiques vérifient la cohérence des soldes selon l'équation fondamentale :

$Solde_{t+1} = Solde_t + Encaissements_t - Décaissements_t + Intérêts_{placés,t}$

Le module calcule le DSCR (Debt Service Coverage Ratio) selon la formule bancaire standard :

$DSCR_t = \frac{CFADS_t}{Service_{dette,t}} = \frac{EBITDA_t - IS_{payé,t}}{Service_{dette,t}}$

où CFADS représente les liquidités disponibles après impôts pour le service de dette. 

**Gestion robuste de la division par zéro dans le calcul DSCR :**

Le code (`financial_calculations.py`, lignes 396-404) implémente une gestion sophistiquée des cas limites :

```python
annual_summary['DSCR_annuel'] = np.where(
    np.abs(annual_summary['Service_Dette_annuel']) > 1e-9,
    annual_summary['CFADS_annuel'] / annual_summary['Service_Dette_annuel'],
    np.inf  # Service dette = 0 avec CFADS > 0 : capacité infinie
)
# Cas où CFADS et Service_Dette sont tous deux proches de zéro
annual_summary.loc[
    (annual_summary['CFADS_annuel'] <= 1e-9) & 
    (np.abs(annual_summary['Service_Dette_annuel']) <= 1e-9),
    'DSCR_annuel'
] = np.nan  # Non défini : ni flux ni dette
```

Le code gère intelligemment trois situations possibles pour éviter les erreurs de calcul :

**Cas normal** : Quand le projet a des remboursements de dette (service dette > 0), le DSCR se calcule normalement. Un DSCR de 1,5 signifie que le projet génère 1,5 fois plus de cash que nécessaire pour rembourser la dette, indiquant une situation financière saine.

**Cas sans dette** : Si le service de dette est nul (projet autofinancé ou dette intégralement remboursée) mais que le projet génère du cash (CFADS > 0), le code retourne "infini". Cela signifie une capacité de remboursement illimitée puisqu'il n'y a rien à rembourser. C'est contre-intuitif mais mathématiquement correct.

**Cas sans activité** : Quand ni cash ni dette n'existent (projet en phase de développement ou arrêté), le code retourne NaN (Not a Number). Cela évite de donner un ratio qui n'aurait aucun sens économique.

Cette gestion empêche le programme de planter sur une division par zéro tout en fournissant aux banquiers des indicateurs qu'ils peuvent interpréter selon le contexte du projet.

Le système vérifie la cohérence des flux mais n'intègre pas encore les alertes automatiques sur les seuils bancaires (DSCR < 1,2) ni le calcul du LLCR - améliorations identifiées pour les versions futures.

La correction automatique propose des suggestions d'optimisation du cash management : d'une part, les arbitrages entre placements court terme et remboursements anticipés, d'autre part, l'optimisation des échéanciers selon les flux prévisionnels, et enfin les recommandations de refinancement le cas échéant.

Ces validations automatiques éliminent les erreurs coûteuses : un DSCR sous 1,2 non détecté peut faire échouer un financement après 3 mois de négociation. OptimPV évite ces échecs en alertant immédiatement sur les déviations, permettant de corriger le tir avant soumission aux banques.



## Synthèse : Performance validée et transition vers la validation empirique

### Quelle performance opérationnelle démontrée ?

**Validation empirique :** La validation technique d'OptimPV s'appuie sur l'analyse de projets réels comme le projet Cannes ABA Gestion. Les temps de calcul s'établissent à 15 minutes maximum pour une optimisation complète (20-23 minutes avec les simulations Monte Carlo optionnelles), contre 3-4 heures en moyenne pour les méthodes Excel traditionnelles. Cette réduction du temps d'analyse de plus de 90% permet de traiter significativement plus de projets avec les mêmes ressources.

**Métriques de performance vérifiables :**

| Indicateur | OptimPV | Méthode manuelle Excel |
|------------|---------|------------------------|
| Temps analyse complète | 15 minutes | 3-4 heures |
| Détection seuils TURPE (36/250/1000 kVA) | Automatique avec alertes | Souvent omis |
| Simulations Monte Carlo | 1000 simulations en 5-8 min (sur demande) | Non réalisable |
| Détection impacts financiers | Automatique et précis | Souvent sous-estimé |
| Gestion multi-participants | 55 participants traités | Limite pratique ~10 |
| Détection contraintes infaisables | Diagnostic précis des causes | Échec silencieux (#DIV/0!) |
| Cohérence compte de résultat/trésorerie | Garantie sur 240 mois | Erreurs d'arrondis cumulatives |

**Cas d'usage validé :** Sur le fichier test "config_TestAG_L_20250609_160615.json", OptimPV génère une optimisation complète en 5,8 minutes avec identification automatique du prix optimal à 9,15 c€/kWh HT, maximisant la VAN à 142 365€ tout en respectant les 5 contraintes définies.


### Quelles limitations et pistes d'amélioration pour l'évolution d'OptimPV ?

L'analyse réflexive identifie de nombreuses limitations et opportunités d'amélioration, issues tant du développement que des retours terrain. Ces axes d'évolution, hiérarchisés par impact potentiel, dessinent la feuille de route technique d'OptimPV.

**Limitation 1 - Absence critique de modélisation du stockage batteries :**

L'absence de batteries constitue une limitation fonctionnelle significative pour certains profils d'ACC. Les aides régionales exigent maintenant 80% d'autoconsommation minimum, seuil plus facilement atteignable pour les ACC multi-acteurs grâce à la diversité des profils de consommation. Les entreprises industrielles et commerciales consomment principalement en journée (8h-18h), période de production solaire optimale, facilitant l'autoconsommation directe. Cependant, l'ajout de stockage pourrait optimiser davantage les configurations mixtes résidentiel-tertiaire. L'impact financier reste conséquent : ajout de 150-200 €/kWh de CAPEX batteries, modification des flux de trésorerie avec remplacement programmé tous les 10-12 ans, et amélioration potentielle du taux d'autoconsommation de 10-15% selon la composition du collectif.

L'intégration du stockage permettrait d'atteindre systématiquement les 80% d'autoconsommation fixés comme seuil minimum de viabilité sur les projets ACC. Sans batteries, le plafonnement s'établit à 60-65% sur les meilleurs cas, compromettant l'éligibilité aux aides et la rentabilité globale. Cette contrainte force actuellement à refuser des projets techniquement réalisables mais économiquement non viables sans stockage.

L'optimisation devient multidimensionnelle : quelle capacité de stockage installer ? Quelle stratégie de charge et de décharge adopter ? Comment arbitrer entre autoconsommation maximale et durée de vie des batteries ? Ces questions nécessitent des algorithmes d'optimisation dynamique que le framework actuel ne supporte pas. L'amortissement accéléré des batteries prévu par la Loi de Finances 2026 ajoutera une complexité fiscale supplémentaire.

**Limitation 2 - Validations bancaires et alertes manquantes :**

Le calcul du DSCR existe mais sans système d'alerte. Un DSCR passant sous 1,2 devrait déclencher une notification immédiate car c'est le seuil minimal exigé par toutes les banques. Le LLCR (Loan Life Coverage Ratio) n'est pas calculé alors qu'il est systématiquement demandé pour les financements de projet. Par ailleurs, les ratios de solvabilité tels que le ratio fonds propres sur dette et la couverture d'intérêts ne sont pas surveillés.

Chaque établissement financier impose ses propres exigences. Le DSCR minimal varie de 1,2 à 1,35 selon les banques, les provisions oscillent entre 3% et 5% du CAPEX, et les ratios de fonds propres s'échelonnent de 20% à 30%. Sans base de données des exigences par établissement et système de validation automatique, l'utilisateur doit vérifier manuellement chaque covenant, source d'erreurs et de rejets de dossiers.

**Limitation 3 - Intelligence prospection territoriale embryonnaire :**

Le module de prospection ACC identifie les sites potentiels mais manque d'intelligence avancée. D'une part, l'absence de détection automatique des masques proches (immeubles voisins, arbres) via Google Solar API génère des surestimations de 20-30% de la production. D'autre part, l'analyse ne considère pas l'évolution urbaine : un terrain vague aujourd'hui peut devenir un immeuble demain, créant de l'ombrage fatal au projet.

Par ailleurs, l'optimisation des périmètres ACC reste manuelle. Avec la limite réglementaire de 2 km, on peut se demander comment définir le cercle optimal ? Faut-il centrer sur le producteur ou décaler vers une zone de forte consommation ? Comment identifier les "ancres" de consommation (supermarchés, bureaux) garantissant l'absorption de la production ? Le machine learning sur les patterns de consommation IRIS pourrait prédire les meilleurs périmètres, mais cette fonctionnalité n'est pas encore implémentée.

**Limitation 4 - Optimisation financière incomplète :**

L'optimisation actuelle se limite au prix de vente. Or, de nombreux leviers restent inexploités : structure capitalistique optimale (quelle répartition dette/equity ?), timing optimal des investissements (faut-il phaser le projet ?), stratégie de refinancement (quand renégocier la dette ?), optimisation fiscale avancée (crédit-bail, cession d'actifs, holdings).

L'absence d'optimisation multi-sites est particulièrement limitante. Pour Europlomberie Piscine avec 5 magasins, faut-il créer une SPV unique ou plusieurs ? Comment mutualiser les coûts ? Quelle séquence de déploiement maximise la VAN globale ? Ces questions nécessitent des algorithmes d'optimisation combinatoire non implémentés.

**Limitation 5 - Architecture technique contrainte par Streamlit :**

L'analyse du code confirme les limitations de Streamlit. La contrainte monocœur est visible dans `core_analyzer.py` où les calculs Monte Carlo ne peuvent être parallélisés efficacement. Le module `facturation/api` contient une ébauche FastAPI mais n'est pas intégré au système principal. Les données sont stockées dans des fichiers JSON (`storage/core.py`) au lieu d'une base de données relationnelle, limitant les requêtes complexes et la performance.

Le code montre des tentatives d'API REST dans `facturation/api/api_server.py` mais sans connexion réelle avec le moteur de calcul principal. L'absence de WebSockets empêche les mises à jour temps réel des calculs, forçant le rechargement complet de la page Streamlit à chaque modification.

**Limitation 6 - Gestion réglementaire statique :**

Les évolutions réglementaires sont codées en dur. La suppression de l'accise, le passage TVA à 5,5%, les modifications TURPE nécessitent des modifications du code. Un système de règles métier paramétrable permettrait aux utilisateurs d'adapter eux-mêmes aux évolutions sans attendre une mise à jour. Cette approche "low-code" nécessite un moteur de règles (type Drools) non prévu dans l'architecture actuelle.

**Limitation 7 - Absence d'intelligence artificielle et apprentissage automatique :**

Le code ne contient aucune implémentation de machine learning malgré les volumes de données traités (5,2 millions de points pour 30 participants). Les opportunités identifiées mais non exploitées incluent : clustering K-means pour segmenter les profils de consommation, régression pour prédire l'évolution des consommations, détection d'anomalies par isolation forest, optimisation des clés de répartition par reinforcement learning.

L'analyse du code révèle que le module de prévision existe mais reste rudimentaire. Actuellement, seules des moyennes mobiles basiques sont implémentées, sans modèles prédictifs avancés. Les données PVGIS historiques sur 20 ans ne sont exploitées que par moyenne arithmétique simple, alors que des modèles ARIMA ou LSTM pourraient capturer efficacement les tendances saisonnières et améliorer la précision des prévisions.

**Limitation 8 - Gestion des erreurs et robustesse :**

L'analyse du code révèle de nombreux `raise ValueError` et `raise RuntimeError` dans `core_analyzer.py` qui stoppent brutalement l'exécution sans récupération possible. Les cas d'échec d'optimisation (lignes 1695-1718) génèrent des RuntimeError sans tentative de reprise ou solution alternative. Le module `repartition_keys/key_validators.py` détecte les incohérences mais ne propose pas de correction automatique.

**Limitation 9 - Absence critique de solution de repli pour PVGIS :**

Si l'API PVGIS (re.jrc.ec.europa.eu) est indisponible, OptimPV n'a pas de solution de repli et le module Solar Simulator ne fonctionne plus. Cette dépendance unique bloque la prospection territoriale en cas de panne réseau ou maintenance du service européen.

Les solutions alternatives existent mais ne sont pas implémentées, notamment un cache longue durée des données d'irradiation, l'utilisation de moyennes historiques locales, ou l'intégration d'autres APIs comme SolarGIS. Cette limitation nécessiterait une évolution pour garantir la continuité de service.

**Limitation 10 - Complexité algorithmique non optimisée pour multi-sites :**

L'analyse du code révèle qu'OptimPV traite actuellement chaque site individuellement, comme des projets séparés. Le logiciel ne cherche pas à optimiser l'ensemble. Par exemple, si vous avez 5 magasins, OptimPV calcule la rentabilité de chacun séparément sans voir qu'en les regroupant, vous pourriez négocier de meilleurs prix (achat groupé de panneaux), mutualiser la maintenance (un seul contrat pour tous les sites), ou optimiser le financement global.

Le problème mathématique sous-jacent est que pour vraiment optimiser 5 sites ensemble, il faudrait tester toutes les combinaisons possibles. Quel site équiper en premier ? Comment répartir le budget ? Faut-il créer une ou plusieurs sociétés ? Avec 5 sites, cela représente des milliers de scénarios à calculer. Au-delà, le nombre de possibilités explose et devient incalculable sans techniques avancées.

Dans le cas concret d'Europlomberie Piscine avec ses 5 magasins, cette limitation fait probablement perdre 5% de rentabilité en manquant ces synergies.

**Amélioration transversale - Interface utilisateur limitée :**

Le module `table_finance/monthly_cash_flow_display.py` génère des tableaux de 240 colonnes impossibles à lire sur un écran standard. Les tentatives d'amélioration dans `visualization/modern_visualization_ui.py` existent mais ne sont pas intégrées. L'absence de pagination ou de vue condensée rend l'analyse des données mensuelles particulièrement pénible sur 20 ans.

Ces limitations, loin d'être des échecs, constituent la roadmap naturelle d'OptimPV. Chaque point représente 2-6 mois de développement, soit 3-4 ans pour une version "entreprise" complète. Néanmoins, cette vision à long terme dépasse le cadre OSE mais trace la trajectoire d'évolution d'un POC académique vers une solution industrielle mature.

### Comment préparer la transition vers la validation empirique ?

Cette validation conceptuelle et technique d'OptimPV nécessite une démonstration empirique sur cas concrets pour compléter la démarche de recherche appliquée. La **Figure 4.1** (APIs prospect mapping) et la **Figure 4.2** (interface de prospection territoriale) constituent les fondements techniques nécessaires à cette validation opérationnelle.

![Figure 4.3 : Pyramide de conversion ACC](https://image.noelshack.com/fichiers/2025/36/1/1756722408-figure-4-3-pyramide-conversion.png)

La **Figure 4.3** illustre la réalité commerciale du secteur ACC : sur 100 prospects identifiés par le système de scoring automatique, seulement 1 à 2 projets aboutissent à une réalisation concrète. Cette pyramide de conversion justifie l'importance critique de l'automatisation du scoring et de la qualification des prospects.

Chaque étape présente ses défis spécifiques. L'identification automatique via APIs publiques génère un volume important de prospects mais 80% n'ont aucun intérêt réel pour l'ACC. Par ailleurs, la qualification commerciale élimine encore 75% des projets restants face à la complexité technique et administrative perçue. La validation technique, nécessitant l'obtention de 50 signatures minimum dans un rayon de 2 km, constitue le principal goulot d'étranglement avec 60% d'abandon à cette étape.

Malgré ce taux de conversion apparemment faible, le ROI reste néanmoins attractif : un projet ACC réalisé représente 500 à 800k€ de chiffre d'affaires sur la durée du contrat (20 ans), justifiant l'investissement dans l'automatisation du processus de prospection et qualification. C'est pourquoi OptimPV optimise chaque étape de cette pyramide en réduisant le temps d'analyse de 15-20 heures à 5-8 minutes par projet, permettant ainsi de traiter un volume suffisant pour atteindre les objectifs commerciaux.

La Partie III démontrera les gains opérationnels réels : amélioration des temps d'analyse (de 15-20h à 5-8 min), fiabilisation des calculs par rapport aux méthodes manuelles (élimination erreurs TURPE/fiscalité), et professionnalisation des processus de prise de décision. Cette validation sur cas d'usage réel constituera la preuve finale de l'applicabilité de la méthodologie développée aux enjeux industriels du secteur ACC français.

### De la théorie à la pratique : le projet Europlomberie Piscine

Les concepts théoriques et algorithmes développés trouvent leur validation dans l'application concrète. La Partie III présentera l'étude détaillée du projet **Europlomberie Piscine**, un cas réel de déploiement ACC commercial qui a abouti à une levée de fonds réussie.

Ce projet regroupe 5 magasins sur la Côte d'Azur, chacun disposant de plus de 1000 m² de surface de toiture exploitable. L'investissement total dépasse le demi-million d'euros, nécessitant une modélisation financière rigoureuse pour convaincre les investisseurs institutionnels. Cette complexité multi-sites illustre parfaitement les défis que OptimPV permet de résoudre.

La Partie III analysera en détail le modèle économique retenu, les résultats des calculs d'optimisation, ainsi que la structuration du montage financier. Plus important encore, l'analyse portera sur les problèmes terrain rencontrés durant le développement du projet. Ces réalités opérationnelles incluent notamment les négociations avec Enedis, les contraintes administratives et les ajustements réglementaires en cours de route, qui constituent les vrais défis de l'ACC commercial.

Cette étude de cas démontrera comment OptimPV a permis de traiter efficacement l'analyse complexe de 5 sites simultanés, transformant des semaines de calculs manuels approximatifs en une optimisation précise et documentée. Les écarts entre la modélisation initiale et la réalité finale révéleront les apprentissages essentiels pour tout développeur de projet ACC.

Le cas Europlomberie Piscine permettra de valider l'applicabilité réelle d'OptimPV à travers la capacité à traiter des projets multi-sites complexes, la fiabilité des calculs financiers sur 20 ans, ainsi que le gain de temps effectif par rapport aux méthodes manuelles. Cette confrontation au terrain révélera les forces et les faiblesses de l'outil développé.