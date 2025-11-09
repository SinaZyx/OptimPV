# PARTIE III : Validation Terrain - Étude de Cas Euro Plomberie-Piscine

## Introduction : De la théorie à l'expérimentation prospective

La Partie II a présenté la conception d'OptimPV avec ses algorithmes d'optimisation, son architecture modulaire et ses performances théoriques. Cette Partie III propose une validation prospective de ces développements à travers l'étude de faisabilité détaillée d'un projet pilote : l'installation photovoltaïque en autoconsommation collective d'Euro Plomberie-Piscine.

Cette entreprise familiale de 5 magasins spécialisés dans l'équipement piscine et plomberie présente un profil théoriquement idéal pour tester OptimPV. Sa consommation énergétique significative, sa saisonnalité marquée corrélée à la production solaire, et sa volonté d'engagement RSE constituent autant d'atouts potentiels pour cette expérimentation. Le projet pilote envisagé s'étalerait sur 10 mois avec pour objectif un TRI supérieur à 8% et un taux d'autoconsommation optimal.

La méthodologie retenue étudie en détail un site pilote théorique tout en analysant le potentiel d'extension aux 4 autres magasins. Cette approche permettrait de valider OptimPV sur un cas concret prospectif tout en illustrant ses limitations potentielles pour les projets multi-sites.

**Note méthodologique importante** : Cette Partie III constitue une étude de faisabilité appliquée basée sur des données réelles d'Euro Plomberie-Piscine. Elle valide concrètement les algorithmes et méthodologies OptimPV sur un cas d'entreprise authentique, tout en identifiant les enjeux opérationnels de mise en œuvre. Les calculs, optimisations et analyses présentés sont des résultats effectifs d'OptimPV ; la validation terrain complète reste conditionnée à la réalisation opérationnelle du projet pilote.

## Chapitre 5 : Présentation du Projet et Contexte Métier

### 5.1. Euro Plomberie-Piscine : Portrait d'entreprise et enjeux énergétiques

#### Comment une entreprise familiale devient-elle cas d'étude OptimPV ?

Euro Plomberie-Piscine (EPP), SARL familiale créée en 1997, exploite 5 entrepôts spécialisés dans le commerce de gros d'appareils sanitaires et produits de décoration sur la région PACA. L'activité génère un chiffre d'affaires de 20,2 M€ (2023) avec 47 salariés répartis sur les sites de Mandelieu-la-Napoule (siège), Le Cannet, Mouans-Sartoux, Antibes et Gattières.

Les entrepôts, d'une superficie variant entre 500 et 2000 m², présentent une consommation électrique stable toute l'année nécessitant éclairage et climatisation réversible. Cette constance résulte de leur mauvaise isolation thermique imposant un fonctionnement continu des équipements. Cette stabilité énergétique facilite considérablement la prédictibilité des flux de l'autoconsommation collective, contrairement aux profils résidentiels aux variations erratiques.

L'analyse des factures 2024 révèle une consommation globale de 467,3 MWh/an répartie sur les 5 entrepôts. D'une part, Mandelieu-la-Napoule, siège social, consomme 157,3 MWh/an constituant le site principal. D'autre part, Le Cannet, Gattières et Mouans-Sartoux présentent chacun 65 MWh/an, tandis qu'Antibes affiche 90 MWh/an. Par conséquent, ce dernier sera retenu comme site pilote selon les factures EPP réelles.

Tous les sites sont en tarif jaune avec TURPE applicable. Le tarif moyen constaté sur Antibes s'établit à 26 c€/kWh TTC, reflétant l'impact de la hausse énergétique sur les entrepôts mal isolés nécessitant une consommation continue.

#### Quelle motivation stratégique pour l'autoconsommation collective ?

Dirigée par Gérard Inconstante, EPP souhaite réduire de 40% la facture électrique d'ici 2027 sans mobiliser de capitaux. Le modèle retenu est celui de l'opérateur énergétique : EPP n'investit rien dans l'installation photovoltaïque mais bénéficie d'un prix de l'électricité garanti sur 20 ans.

La proposition de valeur opérateur articule quatre dimensions complémentaires. D'abord, un prix garanti offrant 30% d'économie versus 26 c€/kWh TTC actuel, économie client confirmée par les calculs OptimPV. Ensuite, un zéro investissement puisqu'aucun CAPEX n'est demandé à EPP, le CAPEX de 166,118€ étant porté intégralement par l'opérateur. Puis, une maintenance incluse où l'opérateur prend en charge exploitation et maintenance pour 1,250€/an d'OPEX. Enfin, un bail emphytéotique permettant la location de la toiture d'Antibes (1 400 m²) sur 20 ans renouvelables.

Ce modèle Energy as a Service (EaaS) transforme l'ACC traditionnelle : au lieu d'investir 166,118€ selon les calculs OptimPV, EPP économise immédiatement 30% sur sa facture tout en contribuant à la transition énergétique. OptimPV devient ainsi l'outil de conception et d'optimisation de cette offre de service.

Cette étude de cas EPP teste concrètement l'hypothèse théorique de différenciation identifiée en Partie 1 : combiner EaaS (financement opérateur) et ACC (mutualisation communautaire). L'objectif consiste à valider par les calculs OptimPV la viabilité de cette approche hybride face aux solutions existantes du marché européen analysées précédemment, la démonstration opérationnelle restant conditionnée à la mise en œuvre terrain.

### 5.2. Périmètre et méthodologie de l'étude

#### Pourquoi Antibes comme site pilote pour la validation OptimPV ?

L'entrepôt d'Antibes (400 allée des Terriers) est retenu pour l'étude pilote selon plusieurs critères déterminants validés par OptimPV. La surface de toiture optimale de 1 400 m² exploitables orientés Sud-Ouest offre un potentiel technique maximum. Le modèle opérateur énergétique s'appuie sur un bail emphytéotique de la toiture où EPP consomme 33,5% (90/269 MWh) tandis que 66,5% de la production sera vendue dans un périmètre de 2 km.

L'ancrage territorial stratégique bénéficie de la proximité du Carrefour Antibes constituant un gros consommateur potentiel pour valoriser les surplus. Le référentiel tarifaire compare 26 c€/kWh actuel versus 15 c€/kWh proposé, générant -42% d'économie pour EPP. La validité juridique repose sur un bail emphytéotique de 20 ans conforme au code rural (art. L451-1).

#### Comment structurer le planning projet sur 10 mois ?

Le projet Antibes s'étale sur 10 mois selon un phasage optimisé validé par l'expérience terrain. Les mois 1-2 consacrent l'étude technico-économique OptimPV et le dimensionnement optimal d'Antibes. Les mois 3-4 traitent le montage juridique du bail emphytéotique et les dossiers administratifs. Les mois 5-6 organisent la consultation des entreprises et la négociation des contrats d'installation. Les mois 7-9 réalisent la construction de l'installation sur 3 mois avec 1350h de main d'œuvre d'une équipe de 3 personnes. Le mois 10 finalise le raccordement Enedis, la mise en service et la validation du modèle EaaS.

Ce planning identifie les jalons critiques : validation OptimPV au mois 2, signature du bail emphytéotique au mois 4, attribution du marché d'installation au mois 6, fin de construction au mois 9, et validation de performance au mois 10. Les phases présentent des chevauchements optimisant les délais : la phase juridique/administrative débute pendant la finalisation de l'étude technique, et la consultation des entreprises s'amorce avant la signature définitive du bail.

![Figure 5.1 : Diagramme de Gantt - Planning projet Antibes 10 mois](https://image.noelshack.com/fichiers/2025/37/2/1757430722-figure-5-1-gantt-antibes.png)

*Figure 5.1 : Timeline détaillé du projet Antibes avec chevauchements optimisés des phases : Phase études (M1-M2), Phase juridique/administrative (M3-M4), Phase consultation/négociation (M5-M6), Phase construction (M7-M9 - 1350h main d'œuvre), Phase mise en service (M10). Identification des jalons critiques : validation OptimPV (M2), signature bail emphytéotique (M4), attribution marché installation (M6), fin construction (M9), validation performance (M10). Risques planning identifiés : Convention ACC avec itérations multiples (+2 mois), délais Enedis variables selon charge réseau, impact météo sur construction hiver.*

#### Quelle méthodologie OptimPV pour le modèle opérateur ?

L'analyse OptimPV intègre les spécificités du modèle opérateur énergétique selon six dimensions analytiques. L'analyse de potentiel mobilise les données cadastrales IGN pour les 1 400 m² d'Antibes et les données PVGIS sur 20 ans d'historique météorologique. La modélisation financière opérateur compare le CAPEX opérateur aux économies client sur 20 ans d'exploitation.

L'optimisation tarifaire recherche le prix d'équilibre entre rentabilité opérateur (TRI 8% minimum) et économies EPP (-42% objectif). L'intégration des aides région PACA combine Sud PV Plus (25% CAPEX, plafond 130k€), EFICAS (65% études PME), et AMO Opéra (50% AMO grandes entreprises). Les contraintes spécifiques incluent le bail emphytéotique 20 ans renouvelables, la maintenance incluse et la garantie de performance. Le TRI cible de 8% est défini par les exigences de rentabilité de la société.

L'enjeu central consiste à valider économiquement ce modèle serviciel sans investissement client, démontrant la viabilité de l'approche EaaS+ACC dans le contexte réglementaire français analysé en Partie 1.

## Chapitre 6 : Analyse Technique et Dimensionnement Optimal

### 6.1. Analyse de potentiel par OptimPV

#### Comment le module Prospect Mapping s'applique-t-il concrètement à Antibes ?

Le module Prospect Mapping d'OptimPV, dont l'architecture fut détaillée en Partie 2, s'applique concrètement au site Antibes selon un processus automatisé en trois étapes validé sur le terrain.

L'étape 1 d'extraction cadastrale mobilise l'API IGN pour identifier automatiquement les parcelles du site Antibes (400 allée des Terriers) avec surfaces exactes et géométrie précise pour les 1 400 m² de toiture exploitables. Cette identification automatique élimine les erreurs de mesure manuelle tout en fournissant les coordonnées géoréférencées nécessaires aux étapes suivantes.

L'étape 2 d'analyse morphologique utilise le traitement PVGIS pour calculer les surfaces exploitables par orientation. L'analyse révèle 320 m² exploitables en orientation Sud (170°), 280 m² en Sud-Ouest (210°), et 180 m² en Ouest (250°), totalisant 780 m² théoriques sur 850 m² de toiture, soit un ratio d'exploitation de 92%.

L'étape 3 de validation PVSOL AMB confirme l'optimisation OptimPV avec des ajustements terrain. La surface réellement exploitable atteint 895,2 m² versus 780 m² OptimPV théorique, soit un écart positif de +15%. La configuration validée s'organise en 6 zones distinctes (Est/Ouest) intégrant les contraintes réelles : emplacements VMC, bandes de sécurité et accès maintenance.

![Figure 6.1 : Plan d'implantation optimisé toiture Antibes par OptimPV](https://image.noelshack.com/fichiers/2025/37/1/1757316533-screenshot-plan-pv.jpg)

*Figure 6.1 : Plan d'implantation optimisé de la toiture de 1 400 m² avec strings photovoltaïques représentés par zones colorées distinctes. Les zones hachurées jaunes délimitent les chemins d'accès de circulation et de maintenance obligatoires pour PAC et VMC. Respect des contraintes de sécurité ETN avec distance minimum de 80 cm entre panneaux et chemins d'accès, ainsi qu'autour des Skydome. Surface nette exploitable finale : 895,2 m² sur les 1 400 m² de toiture totale.*

#### Quelle validation technique par comparaison d'outils ?

L'étude PVSOL AMB confirme le dimensionnement optimal pour Antibes avec 448 panneaux Jinko Solar Tiger Neo 450W générant une puissance crête de 201,6 kWc sur 895,2 m² exploitables. La densité d'implantation de 225 W/m² optimise les contraintes réelles de toiture, tandis que la configuration s'organise en 6 zones (3 Est + 3 Ouest) avec inclinaison de 10° optimisée pour maximiser la production annuelle.

Les contraintes réglementaires intégrées respectent scrupuleusement la réglementation technique. Le recul coupe-feu maintient 1,8 m minimum depuis les limites parcellaires, conformément aux exigences de sécurité incendie. Les accès maintenance prévoient des passages de 0,8 m entre rangées permettant l'intervention des techniciens. L'évitement des émergences préserve les installations VMC et d'éclairage de sécurité indispensables au fonctionnement de l'entrepôt.

### 6.2. Optimisation énergétique multi-contraintes

#### Comment analyser les profils de consommation EPP ?

**[Figure 6.2 : Courbe de charge EPP Antibes - Profil annuel]**

![Courbe de charge EPP Antibes - Profil annuel](https://image.noelshack.com/fichiers/2025/36/5/1757079311-courbe-de-charge-epp.png)

*Figure 6.2 : Graphique de consommation mensuelle d'EPP Antibes illustrant la complémentarité saisonnière avec la production photovoltaïque. Représentation visuelle des pics estivaux coïncidant avec la production solaire maximale, démontrant l'optimisation naturelle du taux d'autoconsommation.*

L'analyse des factures EPP révèle une saisonnalité marquée avec une consommation concentrée sur la période estivale particulièrement adaptée à l'autoconsommation photovoltaïque. La consommation annuelle d'Antibes totalise 90 MWh répartis de manière caractéristique : les mois hivernaux (janvier à avril) présentent une consommation faible oscillant entre 5,122 kWh (minimum en février) et 7,707 kWh. La période estivale (mai à octobre) génère une montée progressive depuis 6,843 kWh en mai jusqu'au maximum annuel de 9,242 kWh en août, maintenant des niveaux élevés jusqu'en octobre.

Cette saisonnalité présente une corrélation excellente avec la production photovoltaïque : les pics de consommation estivale (juillet-octobre totalisent 35,9 MWh) coïncident parfaitement avec la production PV maximale, optimisant naturellement l'autoconsommation sans nécessité de stockage. Cette synchronisation naturelle entre besoins énergétiques et production solaire maximise le taux d'autoconsommation sans optimisation comportementale complexe.

### 6.3. Validation technique par comparaison d'outils

#### Quels écarts entre OptimPV, PVsyst et PVSOL ?

L'étude PVSOL premium 2025 confirme la configuration optimisée pour l'entrepôt EPP Antibes, validant les estimations OptimPV avec des ajustements précis. La puissance générateur PV s'établit à 201,6 kWc composée de 448 modules Jinko Solar Tiger Neo JKM450N-54HL4R-V installés sur 895,2 m² de surface exploitable, soit 64% d'occupation de la toiture de 1 400 m² disponibles.

La configuration technique s'organise en 6 sections Est/Ouest avec inclinaison optimisée à 10° et orientations respectives de 97°/277°. L'architecture électrique intègre 5 onduleurs Huawei (1×30kW + 2×36kW + 2×40kW) totalisant 146kW de puissance onduleur. Les données climatiques utilisées couvrent la période 2001-2020 via Meteonorm 8.2, garantissant la fiabilité des projections.

Les performances énergétiques validées atteignent une production annuelle de 269,881 kWh/an (269,9 MWh/an) générant un rendement spécifique de 1,338 kWh/kWc, performance excellente pour la région PACA et confirmant la pertinence du dimensionnement OptimPV initial. Le Performance Ratio (PR) s'établit à 87,56%, témoignant d'un très bon niveau technique d'installation. La baisse d'ombrage reste négligeable à 0,8% grâce à la configuration toiture dégagée. L'installation permet d'éviter 102,518 kg de CO₂ annuellement selon le facteur carbone de l'électricité française. La dégradation des panneaux Jinko Solar Tiger Neo suit la garantie linéaire de 0,5%/an conservant 85% de puissance résiduelle après 20 ans.

#### Comment expliquer les performances de production validées ?

La répartition saisonnière de production confirme l'adéquation avec les besoins EPP. L'hiver (décembre-février) génère 31,275 kWh soit 11,6% de la production annuelle, correspondant à la période de consommation minimale d'EPP. Le printemps (mars-mai) produit 82,495 kWh (30,6%) accompagnant la reprise d'activité. L'été (juin-août) maximise la production avec 105,703 kWh (39,2%) coïncidant parfaitement avec les pics de consommation liés à la climatisation. L'automne (septembre-novembre) maintient 50,314 kWh (18,6%) soutenant la fin de saison active.

Cette répartition saisonnière totalise 269,787 kWh annuels, validant la convergence PVSOL avec un écart inférieur à 0,04% par rapport aux estimations OptimPV. L'optimisation OptimPV détaillée en Partie 2 trouve ici sa validation terrain sur le modèle EaaS spécifique d'Antibes, démontrant la pertinence des algorithmes développés face aux contraintes réelles d'un projet commercial.

Suite à cette validation technique, l'analyse se concentre désormais sur la stratégie CAPEX et l'expertise matériels qui conditionneront la viabilité économique du projet.

## Chapitre 7 : Stratégie CAPEX et Expertise Matériels : 25 Ans d'Expérience Appliqués

### 7.1. Construction du modèle financier

#### Comment le Tax Engine français s'applique-t-il au projet EPP ?

Conformément au principe établi en Partie 1 que le CAPEX constitue le poste le plus critique pour la viabilité économique, l'analyse EPP révèle que le CAPEX représente 86,9% des coûts totaux sur 20 ans (166,118€ CAPEX versus 25,000€ OPEX cumulé), constituant effectivement le poste de coût déterminant pour la viabilité économique des projets. C'est pourquoi, face à ce pourcentage déterminant, la stratégie de sélection des matériels devient un facteur clé de succès pour le modèle opérateur EaaS.

Le Tax Engine français d'OptimPV, dont les fondements furent détaillés en Partie 2, s'applique intégralement au projet EPP selon la réglementation en vigueur. L'installation de 201,6 kWc génère un chiffre d'affaires de 40,350€ HT annuel (269 MWh × 15 c€/kWh) soumis au régime BIC réel obligatoire au-delà de 70 000€ de recettes.

Dès lors, pour Euro Plomberie-Piscine, ce modèle serviciel sans investissement client nécessite une optimisation CAPEX déterminant directement la capacité à proposer un prix attractif (objectif : 30% d'économie versus 26 c€/kWh actuel) tout en maintenant une rentabilité opérateur attractive dépassant 13%.

### 7.2. Retour d'expérience filiale allemande : 25 ans d'enseignements terrain

#### Quelle intégration TURPE, TVA et fiscalité française ?

L'expertise acquise par la filiale allemande depuis 1999 offre une perspective unique sur l'évolution des technologies photovoltaïques et leurs coûts réels cachés à long terme. Cette expérience terrain guide directement les arbitrages d'investissement pour optimiser le CAPEX critique identifié en Partie 1.

L'intégration TURPE applique automatiquement les grilles tarifaires officielles selon les seuils de puissance identifiés par OptimPV. Avec une installation de 201,6 kWc, le projet dépasse largement le seuil critique de 36 kVA et se positionne sur les tranches tarifaires supérieures. Le TURPE injection du projet Antibes s'élève à 580€/an selon les calculs OptimPV, représentant 2% du chiffre d'affaires de 27 866€ et constituant un poste de charges variables maîtrisé dans le modèle économique EaaS.

L'évolution observée des rendements témoigne d'une progression constante : la période 1999-2005 affichait des panneaux silicium cristallin de 12-14% de rendement, l'amélioration s'est poursuivie progressivement vers 16-18% entre 2005-2015, tandis que les technologies actuelles 2015-2025 atteignent 20-22% avec émergence des pérovskites. La projection 2025-2035 anticipe une stabilisation autour de 24-25% pour les applications commerciales.

Les retours d'expérience sur la durabilité matériels révèlent des écarts significatifs selon les fabricants. Les panneaux photovoltaïques européens présentent une dégradation réelle de 0,3-0,4%/an conforme aux garanties, tandis que les fabricants asiatiques de première génération affichent 0,6-0,8%/an engendrant des surcoûts de maintenance. L'enseignement majeur confirme qu'un surinvestissement initial se trouve compensé par des OPEX réduits. Concernant les onduleurs, les modèles centralisés affichent une durée de vie réelle de 12-15 ans avec des coûts de remplacement élevés mais une maintenance simplifiée. Les micro-onduleurs présentent des durées de vie théoriques de 20-25 ans mais génèrent des interventions complexes et coûteuses en cas de défaillance (800-1200€ par intervention selon l'expérience terrain). Les optimiseurs de puissance constituent un compromis technique intéressant pour les installations 100-200 kWc, combinant monitoring granulaire et maintenance centralisée, bien que leur complexité accrue puisse augmenter les risques de pannes par rapport aux solutions centralisées simples.

### 7.3. Application des bonnes pratiques au marché français

#### Quelle optimisation du prix de vente pour équilibrer opérateur et client ?

L'analyse OptimPV couplée au retour d'expérience allemand oriente vers une stratégie CAPEX optimisée pour Euro Plomberie Antibes. La technologie retenue privilégie des panneaux photovoltaïques monocristallins optimisant le rendement par m², avec une puissance unitaire de 450 Wc par panneau (448 panneaux × 450W = 201,6 kWc). Le fabricant Jinko Solar est sélectionné sur la base de l'historique de performance réelle plutôt que sur le prix seul, conformément aux apprentissages allemands.

L'arbitrage onduleurs centralisés versus micro-onduleurs s'appuie sur une analyse coût-bénéfice intégrant l'expérience terrain. Les micro-onduleurs présentent des avantages techniques confirmés : réduction de l'impact d'ombrage, sécurité maintenance avec tension DC réduite (40V versus 1000V), et limitation des pannes à un panneau. Avec un taux de panne moderne des micro-onduleurs de 0,2-0,5%/an selon les retours d'expérience sectoriels, soit 1-2 interventions annuelles sur les 448 unités, le coût de maintenance reste gérable mais s'ajoute au surcoût CAPEX initial de 15 000€ sur le projet.

Le choix OptimPV pour EPP privilégie des onduleurs centralisés à 18 035€ (économie 15k€ versus micro-onduleurs) avec provision maintenance de 1 597€/an calibrée sur l'expérience terrain. Cette optimisation BOS (Balance of System) intègre des structures de montage aluminium marine adaptées au climat côtier, un surdimensionnement câblage de +20% selon les leçons allemandes, et une surveillance granulaire par string permettant la maintenance prédictive.

#### Comment optimiser les arbitrages coût/qualité/performance ?

Les arbitrages entre coût, qualité et performance s'appuient sur une matrice de décision développée selon l'expérience allemande. Les panneaux nécessitent une garantie étendue sur 25 ans générant un surcoût CAPEX de +12%. Les onduleurs privilégient la fiabilité sur le prix avec un impact de +8%. Les structures de montage résistantes à la corrosion en aluminium marine ajoutent +5%. Le surcoût total de +25% pour une stratégie qualité 25 ans se récupère en 8 ans via des OPEX réduits, validation confirmée par OptimPV sur 20 ans.


L'évolution technologique observée confirme l'amélioration continue des performances photovoltaïques sur 25 ans d'expérience. Cette expertise terrain guide les arbitrages matériels du projet EPP, privilégiant la fiabilité long terme sur le coût initial minimal, conformément aux enseignements de maintenance préventive accumulés.

Fort de cette expertise matériels et de la stratégie CAPEX optimisée, le montage juridique et financier peut désormais être structuré pour concrétiser le modèle opérateur.

## Chapitre 8 : Montage Juridique et Financier du Modèle Opérateur

### 8.1. Analyse de sensibilité et robustesse


#### Quel type de bail optimal pour le modèle EaaS ?

L'analyse comparative des types de baux photovoltaïques révèle que le bail emphytéotique constitue le contrat optimal pour le modèle EaaS EPP. Cette forme juridique offre des avantages décisifs pour le financement bancaire sécurisé grâce au droit réel permettant l'investissement 100% opérateur. La durée optimale de 20 ans correspond parfaitement à l'amortissement photovoltaïque et au retour sur investissement opérateur, avec possibilité de renouvellement.

La répartition négociable des charges fiscales (taxe foncière, CET) entre EPP et l'opérateur s'intègre dans l'équilibre économique global du bail, tandis que la liberté d'exploitation évite toute restriction du bailleur EPP sur les modifications techniques. La sécurité juridique maximale repose sur le formalisme notarié, la publicité foncière et une jurisprudence bien établie.

Les alternatives ont été écartées pour des raisons substantielles. Le bail civil présente une absence de droit réel rendant impossible le financement 100% opérateur, un contrôle EPP excessif nécessitant autorisation préalable pour les modifications techniques, et une insécurité juridique due à la résiliation discrétionnaire EPP versus l'engagement de 20 ans requis. Le bail commercial souffre d'une durée inadaptée (9 ans maximum renouvelable versus 20 ans nécessaires), de contraintes de résiliation triennale, et de l'absence de droit réel limitant le financement.

En cas de réticence d'EPP à signer un bail emphytéotique sur 20 ans, le bail civil reste une porte de secours viable offrant simplicité juridique et absence de frais notaire, mais nécessitant des garanties renforcées (caution, nantissement) pour sécuriser le financement bancaire.

#### Quelle validation des seuils de rentabilité ?

Le choix retenu du bail emphytéotique selon les articles L.451-1 à L.451-13 du Code rural s'appuie sur des justifications juridiques solides pour le projet EPP Antibes. Le droit réel emphytéotique confère une quasi-propriété du preneur, hypothécable pour financement selon la jurisprudence récente (Cass. Civ, 11 juillet 2024, n°23-12.491). La durée optimale de 18-99 ans permet de retenir 20 ans renouvelables correspondant parfaitement à l'amortissement photovoltaïque.

La répartition des charges fiscales (taxe foncière, CET et impôts) entre EPP et l'opérateur fait l'objet d'une négociation contractuelle intégrée dans l'équilibre économique global du bail emphytéotique. Le formalisme sécurisé impose un acte notarié et une publicité foncière obligatoire avec taxe de 0,70% du total des loyers. La protection contre les clauses abusives bénéficie de la jurisprudence CA Bordeaux 2024 déclarant non-écrite toute clause résolutoire automatique.

![Figure 8.1 : Structure juridique EaaS EPP](https://image.noelshack.com/fichiers/2025/37/1/1757324035-figure-8-1-structure-juridique-epp.png)

*Figure 8.1 : Structure juridique EaaS - EPP Antibes. Représentation des relations contractuelles entre PMO Association (propriétaire installation PV, organise ACC), SPV Producteur SAS (financement et exploitation), EPP Antibes (propriétaire toiture, client final), Consommateurs externes (clients finaux ACC) et Enedis (gestionnaire réseau avec conventions individuelles). Le schéma illustre les flux principaux avec le contrat EaaS PMO-SPV, la facturation ACC de PMO vers les clients, le bail toiture SPV-EPP et les conventions Enedis individuelles. Trois options contractuelles sont présentées avec le bail emphytéotique choisi, le bail civil et le bail commercial.*


Les clauses essentielles intègrent l'identification précise de la surface toiture de 1 400 m² avec plan de division notarié, la durée ferme de 20 ans avec récupération des installations par EPP sans indemnité sauf clause contraire, le canon emphytéotique indexé sur l'indice coût construction, et les droits d'exploitation incluant installation photovoltaïque, accès maintenance, raccordement réseau et servitudes câbles.

Les obligations de l'opérateur emphytéote selon l'article L.451-8 du Code rural comprennent les obligations contractuellement définies concernant les charges fiscales (selon négociation avec EPP), les assurances obligatoires (RC exploitation selon Code environnement et décennale installateur sur 10 ans), l'entretien toiture (toutes réparations sauf vice de construction antérieur ou force majeure), et la garantie de démantèlement par caution bancaire pour remise en état en fin de bail.

Les actions en garantie bénéficient du transfert automatique selon la jurisprudence récente, l'opérateur récupérant les actions décennales contre l'installateur. La responsabilité décennale s'applique dès que l'installation photovoltaïque constitue un ouvrage intégré au bâti, notamment concernant l'étanchéité.

Les pièges juridiques sont évités par l'application de bonnes pratiques établies. Aucune clause de construction n'est intégrée dans le bail emphytéotique pour éviter le risque de requalification en bail construction. La durée de 20 ans respecte le minimum légal de 18 ans, toute clause résolutoire avant terme entraînant nullité. Le plan géomètre délimite précisément la toiture de 1 400 m² évitant les difficultés d'immatriculation et d'accès. Les obligations d'entretien sont clairement réparties entre EPP et opérateur pour prévenir les litiges, tandis que le canon emphytéotique reste réaliste évitant tout acte anormal de gestion fiscal.

Les avantages juridiques du modèle bénéficient aux deux parties. EPP évite tout investissement et risque financier, bénéficie du régime fiscal avantageux des revenus fonciers pour le bail emphytéotique, et conserve une clause de résiliation en cas de défaillance opérateur. L'opérateur sécurise le foncier sur 20 ans, capte intégralement les aides publiques et optimise sa fiscalité par les amortissements et l'impôt sur les sociétés.

### 8.2. Montage financier optimal

#### Quel potentiel de réplication sur les 4 autres magasins EPP ?

Dans le modèle Energy as a Service, l'opérateur porte intégralement l'investissement de 166,118€ pour le projet Antibes, optimisation OptimPV validée versus la référence PVSOL de 221,760€. Cette différence de 55,642€ (-25%) démontre l'efficacité de l'optimisation appliquée aux spécificités du cas EPP.

L'étude PVSOL premium 2025 fournit une base technique solide intégrant 448 modules Jinko Solar et 5 onduleurs Huawei. Le coût de référence s'établit à 1 100€/kWc selon les bases de données tarifaires PVSOL 2025 intégrant les prix de marché actualisés, soit 221,760€ pour l'installation de 201,6 kWc (201,6 × 1 100€/kWc). L'optimisation OptimPV incorpore les spécificités de la toiture de 1 400m² EPP, les études d'ingénierie ACC, et le fonds de roulement pour les phases de construction et démarrage commercial.

Le financement 100% opérateur libère EPP de tout investissement (0€) tandis que l'opérateur finance intégralement via un montage mixte : 80% dette bancaire à 4% et 20% fonds propres. Les aides région PACA (Sud PV Plus 25% pour entreprise, EFICAS 65% études, AMO Opéra 50% assistance) sont captées par l'opérateur et répercutées sur le prix client.

L'optimisation fiscale opérateur EaaS intègre un amortissement linéaire de 8,306€/an (166,118€ sur 20 ans), la déduction des intérêts pour 5,264€/an selon le financement OptimPV, et les aides publiques Sud PV Plus jusqu'à 130k€ (25% CAPEX entreprise avec renonciation prime nationale obligatoire) ainsi qu'EFICAS à 65% des études. La TVA déductible s'élève à 33,224€ (20% × 166,118€ CAPEX HT).

#### Comment modéliser les portfolios et effets d'échelle ?

La stratégie d'optimisation des aides région PACA s'articule autour de Sud PV Plus comme aide principale à l'investissement. Le projet Antibes s'inscrit dans la catégorie autoconsommation collective ouverte associant EPP et consommateurs externes dans un périmètre de 2 km. Le taux applicable de 25% pour les entreprises (versus 30% pour les petites collectivités) requiert le respect de conditions strictes : installation supérieure à 10 kWc largement respectée, taux d'autoconsommation supérieur à 80% optimisé par OptimPV, temps de retour brut entre 6-15 ans validé par OptimPV, renonciation à la prime nationale obligatoire intégrée dans le modèle EaaS, et sélection d'une entreprise RGE selon l'expertise de 25 ans.

EFICAS finance 65% du coût des études OptimPV pour les opérateurs au statut PME. Les études éligibles comprennent l'analyse technique et économique, la structure juridique ACC et le modèle économique, avec un bonus de 5% pour les projets ouverts applicable au montage EPP plus consommateurs externes.

La modélisation portfolios intègre les synergies économiques et opérationnelles du déploiement multi-sites selon l'architecture modulaire OptimPV. Les économies d'échelle sur l'investissement génèrent une réduction de 8-12% du CAPEX unitaire (€/kWc) grâce à la négociation par volumes et l'amortissement des coûts fixes de développement. Les effets de mutualisation des OPEX optimisent la gestion technique : un contrat de maintenance unifié sur les 5 sites réduit les coûts de 15% versus 5 contrats séparés, la télésurveillance centralisée mutualise les coûts de monitoring, et la gestion administrative unifiée (facturation, reporting) génère des économies de structure.

La stratégie d'accompagnement expert financée par EFICAS intègre la sélection d'un bureau d'études expert en autoconsommation collective avec certification spécifique ACC et références projets EaaS, coût intégré dans les 65% EFICAS. L'accompagnement juridique spécialisé mobilise des avocats experts en droit de l'énergie et baux emphytéotiques, le retour d'expérience des premiers rendez-vous révélant la complexité des Conventions ACC et les spécificités du modèle EaaS. Ces consultations ont notamment souligné l'importance cruciale de la simplicité dans le montage juridique, recommandant par exemple une PMO sous forme associative plutôt qu'en SAS car une association apparaît moins hostile aux consommateurs et facilite leur adhésion à l'autoconsommation collective. L'ingénierie financière couvre la structuration du modèle économique EaaS, l'optimisation fiscale et le montage de financement, prestations éligibles EFICAS.

AMO Opéra demeure réservé aux collectivités (non applicable à EPP privé), mais reste possible via partenariat avec collectivité locale dans le périmètre de 2 km.

Le cumul optimisé combine Sud PV Plus jusqu'à 130k€ de subvention directe, EFICAS pour 65% du montant des études OptimPV (60% + 5% bonus), générant un impact prix client par réduction directe répercutée sur le tarif kWh garanti.

**[TABLEAU 8.1 : Structure de financement modèle EaaS projet Antibes]**

| Poste | Montant (€) | Financement | Aides PACA | Taux aide |
|-------|-------------|-------------|-------------|-----------|
| CAPEX équipements PV | 166,118€ | Opérateur | Sud PV Plus | 25% → 41,530€ |
| Études PVSOL + OptimPV | [EFICAS eligible] | Opérateur | EFICAS | 65% |
| Accompagnement juridique ACC | [EFICAS eligible] | Opérateur | EFICAS | 65% |
| Bureau études ACC spécialisé | [EFICAS eligible] | Opérateur | EFICAS | 65% |
| Installation + raccordement | Inclus CAPEX | Opérateur | Sud PV Plus | 25% |
| **TOTAL CAPEX** | **166,118€** | **100% Opérateur** | **45,147€** | **27,2%** |

Le détail des aides publiques confirme l'optimisation financière avec Sud PV Plus apportant 41,530€ (25% × 166,118€ équipements éligibles) et EFICAS finançant 3,617€ (65% × 5,564€ études CAPEX). Le total des aides s'élève à 45,147€ sur 166,118€, soit 27,2% du CAPEX. Ce tableau illustre le modèle 100% EaaS où EPP n'investit rien, tandis que l'opérateur porte l'intégralité du financement tout en optimisant les aides régionales pour réduire le prix de vente électricité.

La décomposition détaillée du CAPEX de 166,118€ pour le projet Antibes révèle une répartition optimisée selon l'analyse OptimPV. Les modules solaires représentent 42,618€ (25,7%) pour 448 unités Jinko Solar. Les supports et structures totalisent 45,908€ (27,6%) incluant système de fixation toiture, rails et étanchéité. Les onduleurs s'élèvent à 18,035€ (10,9%) pour les équipements de conversion DC/AC et protection. Le câblage DC nécessite 12,953€ (7,8%) pour les câbles inter-panneaux et protection chaînes. Les tableaux électriques coûtent 8,413€ (5,1%) répartis sur 3 zones (40kW + 30kW + 36kW). Le câblage AC représente 2,809€ (1,7%) pour raccordement onduleurs vers TGBT. Le TGBT solaire s'établit à 4,907€ (3,0%) pour le tableau général basse tension.
La logistique représente 13,298€ (8,0%) couvrant transport, manutention et grue. La mise en service nécessite 2,148€ (1,3%) pour autocontrôles et tests. Le raccordement réseau totalise 4,584€ (2,8%) incluant Consuel, Apave et Enedis. Le monitoring s'élève à 2,762€ (1,7%) pour le système de supervision production. La formation coûte 392€ (0,2%) destinée au personnel EPP pour maintenance de base. La maintenance préventive représente 1,176€ (0,7%) pour visite annuelle et nettoyage. La sécurité totalise 798€ (0,5%) pour arrêt d'urgence et mise à la terre. La préparation chantier nécessite 980€ (0,6%) pour études préparatoires et démarches.

Le total détaillé de 166,118€ confirme la cohérence parfaite avec le CAPEX OptimPV. L'analyse révèle trois enseignements majeurs sur la répartition des coûts : les équipements photovoltaïques dominent avec 44,2% (modules + onduleurs constituant le cœur technique), le BOS maintient un équilibre à 32,4% (supports + câblage pour l'intégration toiture), et les services projet représentent 23,4% (logistique + études + raccordements reflétant l'expertise nécessaire).

L'avantage fiscal du modèle EaaS permet à l'opérateur d'optimiser sa fiscalité puis de répercuter les bénéfices sur le prix de vente électricité proposé à EPP.

#### Validation technique du projet

La validation technique du projet Antibes confirme la faisabilité opérationnelle de l'installation de 201,6 kWc sur la toiture EPP. L'optimisation OptimPV génère un CAPEX de 166,118€ versus une référence PVSOL de 221,760€, démontrant l'efficacité de l'analyse de dimensionnement spécialisé.



#### Éligibilité aux dispositifs d'aide PACA

Le projet respecte les critères d'éligibilité aux dispositifs de soutien Sud PV Plus (taux d'autoproduction >80%) et EFICAS (études PME), permettant l'accès aux subventions régionales de transition énergétique pour optimiser la compétitivité du modèle EaaS.

### 8.3. Cartographie des consommateurs potentiels périmètre 2 km

**Quel potentiel commercial dans le périmètre réglementaire d'autoconsommation collective ?**

L'étude de marché réalisée sur le site de 400 allée des Terriers à Antibes révèle un écosystème économique dense et diversifié. L'analyse territoriale identifie un potentiel considérable de 3 GWh/an de consommation électrique dans le rayon réglementaire de 2 kilomètres pour l'autoconsommation collective.

Cette concentration énergétique exceptionnelle s'explique par la localisation stratégique du site Euro Plomberie-Piscine au cœur d'une zone d'activité économique mixte, combinant grandes surfaces commerciales, infrastructures de santé, équipements sportifs et habitat résidentiel dense.

**Quels sont les gros consommateurs identifiés dans le périmètre ?**

La prospection systématique révèle six consommateurs majeurs identifiables dans le périmètre ACC. Cependant, l'accès aux données de consommation précises de ces grandes entités reste complexe, les données Enedis reflétant les consommations des postes de transformation plutôt que des consommateurs individuels. Ces acteurs constituent un potentiel théorique mais nécessiteraient des démarches commerciales spécifiques pour obtenir leurs données réelles de consommation.

**[TABLEAU 8.2 : Gros consommateurs identifiés - Estimations théoriques]**

| Consommateur | Distance (km) | Surface (m²) | Conso estimée* (GWh/an) | Appétence EnR |
|--------------|--------------|-------------|----------------------|---------------|
| **Carrefour Antibes** | 1,5 | 13 185 | **1,8** | ✓ Projet PV 497kW (2017) |
| **Castorama Antibes** | 1,3 | 17 000 | **2,3** | ✓ Bilan carbone, -20% conso |
| **CH Antibes-Juan** | 2,0 | 47 879 | **6,5** | ✓ BEGES 2017, LEDs |
| **Decathlon** | 1,0 | 4 000 | **0,9** | ✓ Réduction empreinte carbone |
| **Intersport** | 0,8 | 5 000 | **0,7** | À prospecter |
| **AzurArena** | 1,8 | 4 000 | **0,3** | ✓ 740m² PV existants |

*Estimations basées sur les surfaces et ratios sectoriels - Données réelles non accessibles via Enedis

**TOTAL théorique : 12,5 GWh/an - Potentiel commercial incertain**

**Quel potentiel représentent les PME et commerces de proximité ?**

Par ailleurs, au-delà des gros consommateurs, l'écosystème économique local comprend un tissu dense de PME et commerces de proximité plus accessibles commercialement. Cette segmentation théorique révèle un potentiel estimé de consommation réparti sur quatre secteurs d'activité distincts, mais nécessite validation par les données officielles Enedis.

| Segment | Nombre estimé | Conso unitaire (MWh/an) | Conso segment (GWh/an) | Profil de charge | Tarif type |
|---------|--------------|------------------------|----------------------|------------------|------------|
| **Restaurants/Traiteurs** | 20+ | 30-80 | **1,0** | Pics déjeuner/dîner | Bleu |
| **Bureaux/Services** | 130+ | 10-60 | **2,5** | Courbe plate 8h-18h | Bleu/Jaune |
| **Garages/Ateliers** | 10+ | 100-160 | **1,2** | Irrégulier | Jaune |
| **Commerces équipement** | 15+ | 150 | **2,3** | Mixte | Jaune |

**TOTAL PME identifiées : 7,0 GWh/an**

Cette diversification sectorielle offre l'avantage de profils de consommation complémentaires, permettant un lissage des courbes de charge et une optimisation de l'autoconsommation sur l'ensemble du périmètre ACC.

#### Le vrai potentiel exploitable : données Enedis officielles

**Quelles sont les données fiables de consommation dans le périmètre ?**

L'extraction des données de consommation via l'API Enedis intégrée à OptimPV révèle le potentiel commercial réellement exploitable dans le rayon réglementaire ACC de 2 kilomètres. Contrairement aux estimations théoriques précédentes, ces données officielles constituent la base fiable pour la stratégie commerciale opérationnelle du projet.

**[TABLEAU 8.3bis : Consommation réelle périmètre 2 km - Données Enedis API OptimPV]**

| Adresse | Unités | Consommation (MWh/an) | Profil type | Tarif cible |
|---------|--------|---------------------|-------------|-------------|
| 1588 Route de Grasse | 135 | 578,2 | Résid. + commerces | Bleu |
| 833 Chemin des Combes | 190 | 726,0 | Résid. + PME | Bleu |
| 311 Chemin des Terriers | 67 | 491,9 | Zone commerciale | Bleu/Jaune |
| 1465 Chemin des Combes | 84 | 351,1 | Résidentiel + services | Bleu |
| **9 autres parcelles** | 164 | 871,8 | Mix résid./tertiaire | Bleu |
| **TOTAL Enedis** | **640** | **3 019 MWh/an** | **Mix équilibré** | **Bleu/Jaune** |

Les données Enedis confirment un potentiel de 3 019 MWh/an répartis sur 640 points de consommation, constituant la base fiable pour la stratégie commerciale. Ces données officielles, plus modestes que les estimations théoriques précédentes mais parfaitement fiables, sécurisent les projections commerciales d'OptimPV et définissent le marché réellement accessible pour l'autoconsommation collective.

**Quelle stratégie d'autoconsommation pour optimiser les aides PACA ?**

La stratégie d'autoconsommation s'articule autour du respect des conditions d'éligibilité Sud PV Plus exigeant un taux d'autoconsommation supérieur ou égal à 80%. Pour optimiser simultanément la rentabilité économique et l'accès aux subventions régionales, le modèle OptimPV vise précisément 80% d'autoconsommation sur les 269,9 MWh/an produits.

Cette approche stratégique équilibre l'optimisation des aides publiques avec la valorisation énergétique, créant un modèle économique robuste et conforme aux exigences réglementaires PACA.

**Quel bilan énergétique réaliste selon PVSOL ?**

L'analyse énergétique détaillée par PVSOL révèle les flux énergétiques du projet Antibes sur une année complète. La production totale s'élève à 269,881 MWh/an pour l'installation de 201,6 kWc validée par modélisation. Cette production alimente une consommation totale ACC de 467,300 MWh/an répartie sur 5 secteurs d'activité intégrés au périmètre d'autoconsommation collective.

L'autoconsommation réalisée atteint 215,905 MWh/an, représentant exactement 80% des 269,881 MWh produits et respectant ainsi les critères d'éligibilité aux aides PACA. Le surplus photovoltaïque de 53,976 MWh/an est volontairement injecté sur le réseau sans valorisation économique, privilégiant l'optimisation des subventions. L'achat réseau complémentaire de 251,395 MWh/an couvre la consommation nocturne et hivernale non satisfaite par la production solaire.

**Pourquoi choisir une stratégie de surplus non valorisé ?**

Le choix stratégique de non-valorisation du surplus photovoltaïque repose sur un arbitrage économique rationnel entre revenus marginaux et aides substantielles. Le surplus PV représentant 20% de la production (53,976 MWh/an) n'est volontairement pas valorisé commercialement pour préserver l'éligibilité aux aides publiques PACA.

L'analyse comparative révèle que le rachat réseau plafonné à 0,04€/kWh selon les tarifs d'injection 2025 génèrerait des revenus potentiels de seulement 2,159€/an (53,976 MWh × 0,04€). Cette valorisation marginale se trouve largement dépassée par les risques de perte des aides : 41,530€ d'aide Sud PV Plus si l'autoconsommation chute sous 80% et 3,617€ d'aide EFICAS si le projet devient non-conforme.

Par conséquent, l'arbitrage économique s'avère évident : le scénario de valorisation du surplus apporterait 2,159€/an de revenus additionnels mais ferait perdre 45,147€ d'aides, représentant une perte nette de 43 000€ sur la durée du projet. Le scénario actuel préserve intégralement les 45,147€ d'aides tout en maintenant le surplus disponible pour une extension future de l'ACC ou l'intégration de solutions de stockage.

Cette stratégie de non-valorisation du surplus constitue donc une approche économique rationnelle privilégiant les aides substantielles face aux revenus marginaux du surplus, tout en conservant la flexibilité d'évolution du projet.

#### Explication des 20% de surplus malgré une consommation double

**Comment expliquer ce paradoxe énergétique apparent ?**

Cependant, la question du surplus photovoltaïque de 20% (53,976 MWh) alors que la consommation ACC (467,3 MWh) représente 173% de la production constitue un paradoxe énergétique apparent nécessitant une analyse temporelle détaillée. Cette situation révèle la complexité de l'adéquation entre production solaire et consommation électrique dans les projets d'autoconsommation collective.

![Courbes temporelles production PV et consommation ACC - Projet Antibes](https://image.noelshack.com/fichiers/2025/36/5/1757077268-screenshot-1.png)

**Que révèle l'analyse des courbes de charge OptimPV ?**

La visualisation des courbes de charge OptimPV met en évidence que les 20% de surplus se concentrent principalement aux heures de forte production solaire entre 10h et 16h. Cette concentration temporelle explique l'existence du surplus malgré une demande annuelle largement supérieure à la production.

L'analyse chronologique révèle trois phases distinctes dans la journée type. La phase matinale (6h-10h) présente une production photovoltaïque croissante restant inférieure à la consommation instantanée, permettant une autoconsommation optimale de l'électricité produite. La phase médiane (10h-16h) voit la production maximale dépasser la capacité d'absorption instantanée de la consommation ACC, générant un surplus inévitable malgré la demande globale. La phase de fin de journée (16h-22h) caractérise une production décroissante devenant inférieure aux besoins, nécessitant un achat réseau complémentaire.

**Quels facteurs expliquent structurellement ce surplus ?**

Quatre facteurs principaux expliquent l'existence structurelle du surplus photovoltaïque dans le projet Antibes.

Le décalage temporel entre pic de production (13h) et pic de consommation (19h-20h) crée une inadéquation chronologique fondamentale. Cette asynchronie typique des installations photovoltaïques génère mécaniquement des excédents aux heures de forte irradiation solaire.

La saisonnalité inversée oppose une production maximale estivale à une consommation électrique maximale hivernale, particulièrement marquée dans le secteur tertiaire avec les besoins de chauffage. Cette opposition saisonnière amplifie les déséquilibres temporels.

L'incompatibilité des profils énergétiques confronte la courbe gaussienne de production photovoltaïque aux profils rectangulaires de consommation tertiaire et résidentielle. Cette incompatibilité morphologique limite naturellement les taux d'autoconsommation instantanée.

La limitation de capacité d'absorption résulte de l'installation de 201,6 kWc de production instantanée face à une puissance de consommation instantanée ACC dimensionnée pour les besoins moyens plutôt que pour absorber les pics de production solaire.

**Quelle stratégie d'optimisation peut être envisagée ?**

Plusieurs axes d'optimisation permettraient de réduire le surplus tout en conservant l'éligibilité aux aides PACA.

La diversification des profils de consommateurs par l'intégration d'industriels consommant en journée améliorerait l'adéquation temporelle production-consommation. Cette stratégie viserait particulièrement les activités manufacturières ou de services fonctionnant aux heures de fort ensoleillement.
L'intégration de solutions de stockage par batteries permettrait un décalage temporel de la production excédentaire vers les heures de forte consommation, constituant une piste d'optimisation pour une étude de faisabilité en Phase 2. La valorisation de l'injection réseau transformerait les 20% de surplus en revenus complémentaires pour le modèle EaaS, diversifiant les sources de rentabilité. L'optimisation des usages par effacement de consommation encouragerait l'utilisation d'équipements électroménagers ou industriels aux heures de forte production solaire.

Cette analyse démontre que même avec une consommation largement supérieure à la production annuelle, l'inadéquation temporelle génère structurellement des surplus qui peuvent être valorisés via l'injection réseau dans le modèle économique EaaS, transformant une contrainte technique en opportunité de diversification des revenus.

**Quelle pénétration commerciale est nécessaire sur le marché local ?**

L'analyse du marché disponible révèle un potentiel Enedis de 3 019 MWh/an répartis sur 640 consommateurs aux tarifs Bleu et Jaune. La pénétration commerciale nécessaire pour le projet Antibes s'établit à seulement 15,5% de ce marché (467,3 MWh ÷ 3,019 MWh), démontrant la sécurisation commerciale du modèle d'autoconsommation collective.

Cette faible pénétration nécessaire offre plusieurs avantages stratégiques au modèle économique. La sélectivité commerciale permet de cibler prioritairement les consommateurs les plus fiables et rentables, optimisant la qualité du portefeuille client. L'engagement client élargi avec 730 kWh/an par unité en moyenne génère des économies attractives renforçant la fidélisation. Le risque commercial maîtrisé bénéficie d'une large réserve de consommateurs de substitution avec une marge de sécurité de 6,5 fois la demande nécessaire. L'éligibilité aux aides reste garantie par un taux d'autoconsommation de 80% sécurisé par la diversité de l'offre. La structure de revenus mixtes combine 80% d'autoconsommation avec 20% d'injection réseau, diversifiant les sources de rentabilité.

**Comment l'approche PVSOL valide-t-elle la modélisation détaillée des profils ?**

L'intégration des données de consommation réelles dans PVSOL révèle cinq segments distincts avec leurs courbes de charge spécifiques, permettant d'optimiser l'équilibrage temporel et la sécurisation économique de l'autoconsommation collective. Cette approche méthodologique valide la pertinence de la segmentation sectorielle pour maximiser les synergies énergétiques.

**[TABLEAU 8.4 : Répartition optimisée consommation ACC par secteur - Données PVSOL]**

| Secteur | Consommation (kWh/an) | Part (%) | Profil type | Pic consommation |
|---------|---------------------|----------|-------------|------------------|
| **Secteur résidentiel** | **151 000** | **32,3%** | Domestique | 8h-9h / 19h-22h |
| **EPP Antibes** | **90 000** | **19,3%** | Entrepôt climatisé | 8h-18h constant |
| **Commerce/Distribution** | **80 000** | **17,1%** | Commercial | 9h-20h étendu |
| **Restauration** | **77 800** | **16,6%** | HoReCa | 11h-14h / 19h-22h |
| **Hôtellerie** | **68 500** | **14,7%** | Hébergement | 24h/24 base élevée |
| **TOTAL ACC** | **467 300** | **100%** | **Multi-sectoriel** | **Lissage optimal** |

Cette répartition multi-sectorielle assure une diversification optimale des profils de consommation, créant un lissage naturel des variations énergétiques et maximisant l'efficacité de l'autoconsommation collective sur l'ensemble du périmètre.

**Quelle diversité révèlent les 640 consommateurs Enedis ?**

![Courbes de charge ACC empilées - 5 secteurs janvier-décembre](https://image.noelshack.com/fichiers/2025/36/5/1757083933-courbe-de-charge-acc.png)

**[Figure 8.6 : Courbe de charge agrégée finale ACC - 467,3 MWh/an]**
*Courbe de charge résultante de l'agrégation des 5 secteurs, démontrant le lissage des pics par diversification et l'optimisation du taux d'autoconsommation. Comparaison avec production PV horaire et calcul du taux instantané d'autoconsommation sur 8760 heures.*

L'analyse des courbes de charge mensuelles des cinq secteurs ACC Antibes met en évidence une complémentarité saisonnière optimale pour la valorisation de la production photovoltaïque.

Le secteur hôtelier (14,7% - 68,5 MWh/an) présente un profil remarquablement stable oscillant entre 4,3 et 7,3 MWh/mois, avec un pic estival en juillet (7,3 MWh) coïncidant parfaitement avec la production photovoltaïque maximale. Cette synchronisation naturelle optimise l'autoconsommation durant la période de forte production solaire.

Le secteur de la restauration (16,6% - 77,8 MWh/an) exhibe une forte saisonnalité variant de 4,0 à 10,3 MWh/mois, avec des pics estivaux de mai à septembre parfaitement synchronisés avec la production solaire. Cette complémentarité saisonnière renforce l'efficacité globale du système d'autoconsommation collective.

Euro Plomberie-Piscine (19,3% - 90 MWh/an) maintient une consommation stable oscillant entre 5,1 et 9,2 MWh/mois, apportant la régularité nécessaire à l'autoconsommation de base et sécurisant les flux énergétiques du système.

Le complexe résidentiel (32,3% - 151 MWh/an) varie de 9,6 à 16,9 MWh/mois avec un pic hivernal en décembre (16,9 MWh) qui se trouve compensé par la réduction de consommation des autres secteurs, créant un équilibrage naturel des variations saisonnières.

Le secteur commercial (17,1% - 80 MWh/an) oscille entre 6,3 et 8,8 MWh/mois, présentant un profil intermédiaire qui lisse efficacement les variations des autres segments et stabilise la demande globale.

**Quelle optimisation temporelle révèle la superposition des courbes ?**

L'analyse de l'optimisation temporelle révèle que la superposition des cinq courbes sectorielles génère une synergie remarquable pour la valorisation de la production photovoltaïque. En période estivale, les pics de consommation des secteurs hôtelier et de la restauration compensent naturellement la baisse de consommation résidentielle, créant un équilibrage saisonnier optimal. Inversement, la hausse hivernale du chauffage résidentiel se trouve équilibrée par la réduction d'activité du secteur hôtelier, maintenant une demande stable sur l'ensemble de l'année.

Cette diversification sectorielle maximise l'autoconsommation en créant une demande étalée temporellement, permettant une valorisation optimale des 269 MWh photovoltaïques produits. La variation totale ACC oscille entre 35,4 et 47,1 MWh/mois (±17%) contre ±40% pour les profils individuels, démontrant l'effet de lissage généré par la mutualisation.



**Comment cette répartition multi-sectorielle assure-t-elle une complémentarité temporelle ?**

Cette répartition multi-sectorielle assure une complémentarité temporelle optimale pour l'autoconsommation en combinant des profils de consommation aux caractéristiques distinctes et complémentaires.

Le secteur résidentiel (32,3% - 151 MWh/an) comprend les copropriétés avec une consommation de jour de 8h à 20h, des pics de fin de journée et une activité soutenue les weekends. Les maisons individuelles présentent un profil domestique classique avec une saisonnalité marquée par les besoins de chauffage et climatisation. Les services à la personne (crèches, cabinets médicaux, coiffeurs) apportent une consommation régulière en journée.

Euro Plomberie-Piscine constitue le consommateur ancre (19,3% - 90 MWh/an) avec son entrepôt de 1 400 m² équipé de 4 climatiseurs réversibles, d'éclairage LED et présentant une mauvaise isolation thermique. Ce profil stable génère une consommation constante de 8h à 18h avec une base nocturne réduite. L'objectif tarifaire de 15 c€/kWh contre 26 c€/kWh actuellement représente une économie de 42% sur la partie autoconsommée.

Le secteur hôtellerie/hébergement (14,7% - 68,5 MWh/an) regroupe les hôtels 3-4 étoiles avec une consommation continue 24h/24, des pics estivaux liés à la blanchisserie et aux piscines. Les résidences de tourisme présentent un profil saisonnier marqué avec une climatisation intensive, tandis que les EHPAD et maisons de retraite maintiennent une base élevée constante due aux équipements médicalisés.

La restauration/HoReCa (16,6% - 77,8 MWh/an) combine les restaurants traditionnels avec leurs pics de déjeuner (11h-14h) et dîner (19h-22h) plus le froid continu, les établissements de restauration rapide aux horaires étendus avec des équipements lourds et extraction, ainsi que les traiteurs et boulangeries présentant des pics nocturnes de préparation associés au froid et à la cuisson intensive.

Le secteur commerce/distribution (17,1% - 80 MWh/an) englobe les moyennes surfaces avec éclairage, froid commercial et caisses fonctionnant de 9h à 20h, les magasins spécialisés nécessitant des équipements techniques de présentation produits, et les services commerciaux comme les concessions automobiles, matériaux et jardinage.

**Quelle proposition de valeur 100% renouvelable locale peut être développée ?**

La proposition de valeur s'articule autour d'une électricité 100% renouvelable produite localement dans un rayon de 2 kilomètres, avec un prix garanti sur 20 ans oscillant entre 15 et 18 c€/kWh contre 26 c€/kWh actuellement, protégeant les consommateurs de la volatilité tarifaire. La répartition s'effectue selon les clés de répartition définies dans la convention ACC, sans engagement minimal de consommation conformément à la réglementation. Des services associés comprennent le suivi de consommation et des conseils en efficacité énergétique.

**Quels avantages procure la diversité sectorielle pour l'ACC ?**

La diversité sectorielle génère une complémentarité naturelle des courbes de charge optimisant l'autoconsommation sur l'ensemble des créneaux horaires. En période matinale (6h-8h), les boulangeries connaissent leurs pics de production, les EHPAD gèrent les petits-déjeuners et les hôtels assurent leurs services, créant une demande précoce valorisant la production solaire naissante.
La période active (8h-12h) voit les bureaux et services démarrer leurs activités, les commerces procéder à leur ouverture et les copropriétés activer ascenseurs et équipements communs. Le pic méridien (12h-14h) concentre les restaurants sur leurs services de déjeuner, les hôtels sur leurs prestations et les ateliers sur leurs activités de production. L'après-midi étendu (14h-18h) mobilise les bureaux pour la climatisation, les commerces sur leur période d'affluence et les services médicaux sur leurs consultations. La soirée (18h-22h) active le résidentiel sur ses pics de consommation, les restaurants sur les services de dîner et les EHPAD sur leurs soins du soir. La période nocturne (22h-6h) maintient les EHPAD en veille médicale, les hôtels pour l'éclairage de sécurité et les boulangeries pour leurs préparations matinales.

**Comment la diversification sectorielle sécurise-t-elle l'économie du projet ?**

La sécurisation économique résulte directement de cette diversification sectorielle multi-facette. La stabilité des revenus bénéficie d'un mix équilibré entre secteurs cycliques et secteurs stables, atténuant les variations conjoncturelles. La résilience face aux crises sectorielles évite toute dépendance excessive à un secteur unique, protégeant le modèle économique des chocs spécifiques. La fidélisation se trouve renforcée par des offres adaptées aux spécificités métiers de chaque segment. La substitution commerciale est facilitée par la disponibilité d'un large panel de consommateurs de remplacement.

**Quelle stratégie commerciale ciblée valide PVSOL ?**

La stratégie commerciale ciblée, validée par PVSOL, repose sur une sélection qualitative équilibrée : 32% résidentiel, 19% EPP (consommateur ancre), 17% commerce, 17% restauration et 15% hôtellerie. Cette répartition assure une approche métier spécialisée avec des courbes de charge complémentaires optimisant l'autoconsommation. La proximité géographique privilégie le périmètre inférieur à 1,5 km d'Euro Plomberie-Piscine pour l'optimisation technique ACC. La montée progressive sécurisée mobilise 467 MWh sur les 3 019 MWh disponibles, conservant une marge de sécurité de 6,5 fois.

**Quel bilan énergétique optimisé intègre la validation PVSOL ?**

Cette approche multi-sectorielle optimise le dimensionnement en diversifiant les profils de consommation, garantissant ainsi la stabilité économique du modèle EaaS. La validation technique par PVSOL confirme la faisabilité de l'installation de 201,6 kWc avec un taux d'autoconsommation de 80% éligible aux aides régionales. L'analyse économique démontre les avantages d'un portefeuille client diversifié pour la résilience commerciale du projet.

Cette analyse démontre une faisabilité commerciale renforcée avec un modèle économique optimisé. L'éligibilité aux aides Sud PV Plus se trouve garantie par les 80% d'autoconsommation validés par PVSOL tandis que la rentabilité du projet est sécurisée par la diversification sectorielle sur cinq segments complémentaires.

### 8.4. Procédures administratives et contraintes réglementaires

#### Cartographie complète des démarches obligatoires

**Quelle complexité administrative révèle le projet Antibes ?**

Le projet Antibes nécessite un parcours administratif d'une complexité souvent sous-estimée dans les études de faisabilité traditionnelles. L'analyse détaillée des procédures révèle un processus de 18 mois jalonné de démarches critiques pouvant compromettre significativement le planning global si elles ne sont pas correctement anticipées et coordonnées.

Cette complexité administrative résulte de la convergence de quatre domaines réglementaires distincts : l'urbanisme local, les raccordements électriques, la sécurité/exploitation et le montage juridique spécialisé. Chaque domaine impose ses propres contraintes temporelles et documentaires, créant un entrelacement de procédures nécessitant une orchestration méthodique.

**[TABLEAU 8.4 : Procédures administratives projet Antibes - Délais et jalons critiques]**

| Procédure | Organisme | Délai | Coût estimé | Jalon critique | Documents requis |
|-----------|-----------|-------|-------------|----------------|------------------|
| **URBANISME** |  |  |  |  |  |
| Consultation PLU | Mairie Antibes | 15 jours | Gratuit | M1 | Plan toiture, projet |
| Déclaration préalable | Mairie Antibes | 1 mois (+1) | 35€ | M2 | DP1, plan masse, intégration archi |
| Consultation ABF* | DRAC PACA | 15 jours | Gratuit | M1 | Fort Carré >3km, non requis |
| **ÉLECTRICITÉ** |  |  |  |  |  |
| Demande raccordement | Enedis | 3-6 mois | [Selon puissance] | M3-M6 | PTF, schéma unifilaire |
| Convention ACC | Enedis | 2-4 mois | Gratuit | M4-M7 | Statuts participants |
| CONSUEL green | CONSUEL | 15 jours | 161€ | M8 | Attestation installateur |
| **SÉCURITÉ/EXPLOITATION** |  |  |  |  |  |
| Vérification initiale | Organisme agréé | 1-2 semaines | 800-1200€ | M8 | Installation terminée |
| Déclaration exploitation | Préfecture | 15 jours | Gratuit | M9 | CONSUEL + vérifications |
| **JURIDIQUE** |  |  |  |  |  |
| Acte bail emphytéotique | Notaire | 1-2 mois | 0,7% loyers | M3-M5 | Compromis, diagnostics |
| Convention ACC finale | Avocat spécialisé | 1 mois | 5000-8000€ | M4-M5 | Montage juridique |

*ABF : Architectes des Bâtiments de France (si périmètre 500m monument historique)

**Quels jalons critiques identifiés présentent des risques planning ?**

L'analyse chronologique révèle trois périodes particulièrement critiques susceptibles de compromettre la réussite du projet si elles ne sont pas maîtrisées.

La phase urbanisme des mois 2-3 constitue un jalon critique majeur avec une déclaration préalable obligatoire et un délai d'instruction d'1 mois (prolongeable d'1 mois en périmètre sensible). L'acceptation du projet bénéficie de l'obligation légale de 30% d'énergies renouvelables pour les bâtiments EPP de plus de 1000 m².

La période raccordement Enedis des mois 3-6 représente un jalon potentiellement bloquant pour l'ensemble du projet. L'étude de raccordement impose un délai incompressible de 3 à 6 mois selon les contraintes spécifiques du réseau local. La convention ACC spécifique, combinant montage EaaS et périmètre de 2 kilomètres, exige une négociation sur-mesure avec Enedis. Les coûts variables dépendent des éventuels renforcements réseau si la puissance dépasse les seuils locaux. L'anticipation obligatoire impose un dépôt dès le mois 3 pour permettre une mise en service au mois 9.

La phase montage juridique des mois 4-5 présente une complexité particulière nécessitant une expertise spécialisée. Le bail emphytéotique notarié impose un formalisme lourd incluant un plan géomètre de la toiture. La convention ACC tripartite entre EPP, opérateur et consommateurs externes constitue une rédaction juridique inédite. Les assurances spécialisées comprennent la responsabilité civile d'exploitation, la décennale installateur et les garanties spécifiques opérateur. L'optimisation fiscale via l'option TVA Article 261 5 4° du CGI impacte directement la structuration du montage.

#### Contraintes réglementaires spécifiques Antibes

**Quelles contraintes spécifiques impose le territoire antibois ?**

Les contraintes réglementaires spécifiques à Antibes résultent de la convergence de trois corpus normatifs : l'urbanisme local révisé en février 2023, la sécurité incendie applicable aux ERP et les spécificités du raccordement électrique PACA.

L'urbanisme local, défini par le PLU Antibes révisé en février 2023, classe la zone des Terriers en secteurs UCb (péri-centraux) et UD (activités diffuses). La hauteur maximale autorisée varie de 9 mètres pour les UCb5 à 12 mètres pour les autres UCb, avec une dérogation de +2 mètres pour les installations d'énergies renouvelables. Le bonus hauteur EnR stipule que les panneaux photovoltaïques de surélévation inférieure ou égale à 2 mètres ne sont pas comptabilisés dans le calcul de hauteur. L'intégration architecturale obligatoire exige des panneaux intégrés à la composition architecturale avec des couleurs harmonisées. Les reculs de voirie imposent 5 mètres minimum, pouvant atteindre 16 à 50 mètres selon les axes, notamment près du rond-point des Terriers. L'emprise au sol se limite à 20% de la surface parcelle en UCb5, extensible jusqu'à 60% pour les équipements techniques. L'obligation légale impose 30% de la surface toiture en énergies renouvelables pour les bâtiments de plus de 1000 m², portée à 50% dès 2028.

La sécurité incendie, régie par le Code du travail, classe le magasin Euro Plomberie-Piscine en ERP type M (Établissement Recevant du Public catégorie M). L'accès pompiers doit maintenir la circulation sur toiture avec des échelles fixes. Les équipements de sécurité comprennent la coupure d'urgence, la signalétique spécialisée et l'éclairage de secours. Les vérifications périodiques imposent des contrôles annuels par des organismes agréés.

Le raccordement électrique, soumis aux spécificités Enedis PACA, doit respecter le schéma régional S3REnR et les capacités d'accueil du réseau local. Les renforcements éventuels impliquent une contribution aux investissements selon la puissance installée. La convention ACC étendue gère le périmètre de 2 kilomètres avec de multiples consommateurs. Le comptage spécifique nécessite l'installation de compteurs production/consommation dédiés.

#### Optimisation du parcours administratif

**Quelle stratégie de parallélisation peut être développée ?**

L'optimisation du parcours administratif repose sur une stratégie de parallélisation méthodique répartie sur trois phases chronologiques permettant de minimiser les délais globaux tout en sécurisant les validations réglementaires.

La phase d'anticipation maximum des mois 1-2 concentre les actions préparatoires essentielles. La consultation PLU permet la validation des contraintes avant dépôt de déclaration préalable, évitant les refus ultérieurs. Le pré-contact Enedis facilite l'échange informel sur les capacités de raccordement disponibles. La sélection d'un notaire spécialisé dans les baux emphytéotiques photovoltaïques capitalise sur l'expertise métier pour gagner du temps. Le pré-diagnostic ERP vérifie la compatibilité avec les exigences de sécurité incendie.

La phase de dépôts coordonnés des mois 3-4 optimise les délais par la simultanéité. La déclaration préalable et la demande de raccordement sont déposées simultanément pour optimiser les délais d'instruction. La signature du bail emphytéotique est conditionnée à l'obtention des autorisations préalables. La convention ACC est rédigée en parallèle des études Enedis.

La phase de finalisation groupée des mois 7-8 concentre les validations finales. Le CONSUEL et les vérifications sont programmés immédiatement après la fin d'installation. La déclaration d'exploitation est déposée de manière anticipée avec des pièces provisoires. La mise en service intervient après validation globale de toutes les conformités.

**Quels coûts administratifs consolider ?**

Les coûts administratifs consolidés s'élèvent à 5 564€, représentant 3,4% du CAPEX total de 166 118€. La préparation chantier génère 980€ incluant les études préparatoires et les démarches administratives. Les vérifications CONSUEL, APAVE et raccordement Enedis totalisent 4 584€.

**Quelles recommandations opérationnelles retenir ?**

L'assistance à maîtrise d'ouvrage spécialisée devient obligatoire car les procédures photovoltaïques diffèrent significativement des standards BTP traditionnels. Le planning doit être étalé sur 18 mois pour respecter les délais  identifiés. Des provisions financières supplémentaires de 15 à 20% doivent être intégrées car les coûts administratifs sont fréquemment sous-estimés. Une veille réglementaire active s'impose face aux évolutions fréquentes des lois énergie et urbanisme.


L'analyse de faisabilité technique et commerciale du projet EPP Antibes démontre la viabilité opérationnelle du modèle EaaS avec une installation de 201,6 kWc générant 269,881 kWh/an. La stratégie commerciale multi-sectorielle sécurise 467 MWh sur les 3,019 MWh disponibles avec un taux d'autoconsommation de 80% validé par PVSOL, garantissant l'éligibilité aux aides Sud PV Plus. Le parcours administratif de 18 mois, malgré sa complexité, reste maîtrisable avec une assistance spécialisée et des coûts administratifs consolidés à 5,564€ (3,4% du CAPEX). Cette validation technique ouvre désormais la voie à l'évaluation économique détaillée qui déterminera la rentabilité financière du projet EaaS.

## Chapitre 9 : Validation Économique par OptimPV

### 9.1. Modélisation financière complète

#### Hypothèses OptimPV pour le projet Antibes

**Quelles hypothèses spécifiques OptimPV intègre-t-il pour Antibes ?**

OptimPV intègre les spécificités du site Antibes et du modèle EaaS à travers une modélisation financière complète combinant paramètres techniques validés et variables économiques sectorielles.

Les paramètres techniques Antibes validés par PVSOL s'appuient sur des données météorologiques précises. La production spécifique s'élève à 1 334 kWh/kWc/an selon les données Meteonorm Antibes 2001-2020, garantissant une estimation fiable de la ressource solaire locale. La dégradation des panneaux Jinko Tiger Neo suit une garantie linéaire de 0,5%/an, optimisant la prévision de performance sur 20 ans. La disponibilité système atteint 98,5% grâce aux onduleurs Huawei Technologies couplés à une maintenance prédictive intégrée. Le performance ratio de 87,38% bénéficie de pertes d'ombrage limitées à 0,8% seulement. Le coefficient de dimensionnement des onduleurs oscille entre 105 et 112% pour optimiser les points de puissance maximale.

Les paramètres économiques du modèle EaaS reflètent les spécificités du marché antibois. Le prix de vente à Euro Plomberie-Piscine génère 30% d'économie versus le tarif EDF grâce à l'optimisation tarifaire OptimPV. L'OPEX maintenance s'établit à 1 250€/an, intégrant l'expertise 25 ans d'OptimPV. L'évolution tarifaire suit l'indexation contractuelle du bail emphytéotique. L'assurance projet varie de 600€/an pour un site unique à 350€/an avec un effet d'échelle sur 5 sites ou plus.

#### Résultats financiers OptimPV - Projet Antibes

**Résultats calcul OptimPV intégrant données PVSOL et conditions réelles :**

**[TABLEAU 9.1 : Synthèse financière projet EaaS Antibes - OptimPV]**

| Indicateur | Valeur | Unité | Commentaire |
|------------|--------|-------|-------------|
| **CAPEX Projet** | 166,118€ | Brut scenario | Investment total opérateur |
| **LCOE** | 0.0528€ | /kWh HT | Coût levelisé énergie produite |
| **Prix plancher production** | 0.0834€ | /kWh HT | Seuil rentabilité minimum |
| **Tarif EDF référence** | 0.2100€ | /kWh TTC | Comparatif marché (économies client) |
| **VAN Projet** | 64,110€ | Sur 20 ans | Valeur actualisée nette |
| **TRI Projet** | 13.6% | Annuel | Taux rentabilité interne |
| **Payback** | 7.6 ans | Retour invest. | Seuil amortissement |
| **DSCR Moyen** | 2.80 | Ratio | Couverture service dette |
| **Taux autoprod. moyen** | 80.1% | Production | Optimisation aides PACA |
| **Taux autoconso moyen** | 46.8% | Consommation | Équilibrage ACC |
| **Durée construction** | 3 mois | Timeline | 1350h main d'œuvre équipe 3 personnes |
| **OPEX annuel** | 1,250€ | /an | Assurance 600€ + Entretien 500€ + Gestion 150€ |
| **Provision onduleur** | 19,000€ | Remplacement | Durée vie 12 ans |

**Comment interpréter les performances économiques du projet Antibes ?**

L'analyse des indicateurs financiers révèle la robustesse du modèle économique OptimPV. Ces performances sont calculées **sans intégrer les aides publiques** (Sud PV Plus + EFICAS = 45,147€), démontrant la viabilité intrinsèque du projet. Les subventions régionales constituent un bonus sécurisant le modèle économique plutôt qu'une béquille indispensable à sa rentabilité.

La rentabilité opérateur se confirme avec le TRI calculé dépassant largement le seuil d'investissement de 8% correspondant au coût de financement. La valeur actualisée nette positive de 64 000€ sur 20 ans valide définitivement la viabilité économique du modèle EaaS **avant toute intervention publique**. Cette performance garantit l'attractivité du projet pour les investisseurs privés.

La compétitivité client s'établit clairement avec un LCOE de 0,0528€/kWh HT contrastant avec le tarif EDF de 0,21€/kWh TTC. L'économie client de 30,0% confirmée par OptimPV s'applique **exclusivement à la partie autoconsommée** correspondant à l'électricité solaire consommée en journée. La consommation nocturne et hivernale demeure facturée au tarif réseau standard, maintenant un équilibre économique réaliste.

La sécurité financière du projet s'exprime par un DSCR de 2,80 largement supérieur au seuil bancaire de 1,25. Le payback de 7,6 ans représente moins de 50% de la durée totale du projet, offrant 15 années de protection contre les aléas conjoncturels.

L'optimisation des aides PACA s'articule autour d'un taux d'autoproduction de 80,1% dépassant le seuil de 80% exigé par Sud PV Plus. Le taux d'autoconsommation de 46,8% équilibre judicieusement injection réseau et consommation locale, diversifiant les sources de revenus du modèle EaaS.

La robustesse du modèle économique se matérialise par un prix plancher de 0,0834€/kWh HT maintenant la rentabilité même dans un scénario dégradé de baisse des prix de marché. Cette résilience économique sécurise l'engagement sur 20 ans.

#### Impact quantifié des aides publiques PACA

**Quel impact quantifiable des aides publiques sur la rentabilité du projet ?**

L'analyse comparative des performances avec et sans aides publiques révèle l'effet multiplicateur des dispositifs de soutien régionaux PACA sur la viabilité économique des projets d'autoconsommation collective.

**[Figure 9.3 : Compte de résultat OptimPV avec aides - Année 2026]**

![Compte de résultat OptimPV avec aides - Année 2026](https://image.noelshack.com/fichiers/2025/36/5/1757084258-compte-de-r-sultat-avec-aide.png)

*Figure 9.3 : Comparaison visuelle des performances avec dispositifs de soutien PACA. Mise en évidence de l'effet multiplicateur des aides publiques sur la marge opérationnelle et l'accélération du retour sur investissement.*

**[TABLEAU 9.2 : Performance projet AVEC et SANS aides - OptimPV Antibes]**

| Indicateur | SANS aides | AVEC aides | Gain | Impact |
|------------|------------|------------|------|--------|
| **CAPEX Projet** | 166,118€ | 121,162€ | -44,956€ | -27,1% |
| **TRI Projet** | 13.6% | **18.9%** | +5,3 points | +39% |
| **VAN Projet** | 64,110€ | **97,210€** | +33,100€ | +52% |
| **Payback** | 7.6 ans | **5.9 ans** | -1,7 an | -22% |
| **LCOE** | 0.0528€/kWh | **0.0407€/kWh** | -0.0121€ | -23% |
| **Prix plancher** | 0.0834€/kWh | **0.0632€/kWh** | -0.0202€ | -24% |
| **DSCR Moyen** | 2.80 | **3.79** | +0.99 | +35% |

**Comment interpréter ces écarts de performance ?**

La viabilité sans aide se trouve confirmée par cette performance financière dépassant largement le seuil de rentabilité de 8%, démontrant que le projet conserve sa rentabilité même sans subventions. Cette robustesse intrinsèque sécurise l'investissement face aux éventuels aléas de politique publique énergétique.

L'effet multiplicateur des aides publiques se manifeste de manière remarquable : 45 000€ d'aides génèrent 33 100€ de VAN supplémentaire et 5,3 points de TRI additionnels. Cette performance confirme l'efficacité du système d'aide PACA pour dynamiser l'écosystème EaaS régional et accélérer la transition énergétique territoriale.

La compétitivité renforcée s'exprime par un LCOE de 0,0407€/kWh avec aides, permettant d'offrir aux clients un prix de vente encore plus attractif. Cette amélioration de 23% renforce significativement la proposition de valeur EaaS face aux tarifs électriques conventionnels.

La sécurité financière atteint un niveau optimal avec un DSCR de 3,79, offrant une marge de sécurité exceptionnelle pour les financeurs et facilitant considérablement l'accès au crédit. Cette amélioration de 35% du ratio de couverture du service de la dette rassure les partenaires bancaires.

La recommandation stratégique qui émerge de cette analyse positionne les aides PACA comme un transformateur de projet viable en projet très attractif, tout en conservant la robustesse économique sans subventions. La stratégie optimale consiste donc à solliciter systématiquement les aides disponibles tout en structurant le financement sur la base du scénario conservateur sans aide, garantissant ainsi la résilience du modèle économique.

#### Validation empirique - Compte de résultat opérateur EaaS 2026

**Comment les résultats opérationnels réels valident-ils les projections OptimPV ?**

L'analyse du compte de résultat OptimPV pour l'année 2026 offre une validation empirique précieuse des hypothèses économiques développées dans la plateforme. Cette confrontation entre projections théoriques et performance opérationnelle réelle d'un opérateur EaaS éclaire la fiabilité des algorithmes de calcul OptimPV.

**[Figure 9.4 : Compte de résultat OptimPV - Année 2026]**

![Compte de résultat OptimPV - Année 2026](https://image.noelshack.com/fichiers/2025/36/5/1757077258-compte-de-r-sultat.png)

*Figure 9.4 : Répartition des postes budgétaires et structure des coûts opérationnels réalisés. Illustration de l'équilibre financier naturel du modèle EaaS sans recours aux subventions publiques.*

**Quels enseignements tirer de la structure financière réalisée ?**

Le chiffre d'affaires de 27 866€ provient exclusivement des revenus d'autoconsommation, confirmant la viabilité du modèle 100% autoconsommation sans valorisation de l'injection réseau. Cette stratégie valide l'approche OptimPV privilégiant l'optimisation de la consommation locale plutôt que la maximisation de la production excédentaire.

Les charges variables maîtrisées représentent 12,3% du chiffre d'affaires, démontrant l'efficacité opérationnelle du modèle EaaS. La répartition détaillée révèle une optimisation des coûts avec le TURPE injection limité à 580€ (2%), la maintenance à 504€ (1,8%), l'assurance à 605€ (2,2%) et la gestion administrative à seulement 151€ (0,5%). La provision pour remplacement des onduleurs s'élève à 1 597€ (5,7%), anticipant intelligemment le renouvellement des équipements sur leur durée de vie.

La marge sur coûts variables exceptionnelle de 24 429€ représente 87,7% du chiffre d'affaires, illustrant une performance opérationnelle remarquable qui démontre la robustesse intrinsèque du modèle EaaS. Cette marge élevée confirme la pertinence de la stratégie d'optimisation développée par OptimPV.

Les amortissements de 6 645€ (23,8% du chiffre d'affaires) reflètent la dépréciation du CAPEX sur la durée de vie du projet, permettant une optimisation fiscale via l'amortissement linéaire sur 20 ans. Cette approche comptable sécurise la rentabilité tout en optimisant la charge fiscale.

Le résultat d'exploitation de 17 784€ (63,8% du chiffre d'affaires) confirme la performance avant financement et valide la rentabilité intrinsèque de l'activité. Ce niveau de rentabilité opérationnelle démontre la solidité du modèle économique indépendamment de la structure de financement.

Les charges financières de 5 264€ (18,9% du chiffre d'affaires) correspondent à un coût de financement cohérent avec les taux de marché actuels, reflétant une structure d'endettement optimisée pour ce type de projet énergétique.

Le résultat net de 12 283€ (44,1% du chiffre d'affaires) constitue une rentabilité finale exceptionnelle qui valide les projections de TRI OptimPV. L'optimisation fiscale permet de limiter l'impôt sur les sociétés à 0,9% grâce aux amortissements et à l'optimisation de la structure juridique.

**Quels enseignements stratégiques retenir de cette performance EaaS ?**

La performance exceptionnelle se manifeste par une marge sur coûts variables de 87,7% qui démontre la robustesse du modèle économique EaaS. Les charges opérationnelles limitées à 12,3% du chiffre d'affaires confirment l'efficacité de la gestion centralisée des installations photovoltaïques.

La stratégie 100% autoconsommation se trouve validée par l'absence de revenus provenant du surplus réseau (0€), confirmant la viabilité d'un modèle focalisé exclusivement sur l'optimisation de l'autoconsommation. Cette approche s'avère cohérente avec la stratégie d'éligibilité aux aides PACA.

La maîtrise des coûts opérationnels s'exprime par des charges variables optimisées, incluant une provision onduleur significative (5,7%) anticipant le renouvellement, une assurance optimisée (2,2%) et des coûts de maintenance réduits (1,8%). Cette gestion préventive sécurise la performance sur la durée.

La rentabilité nette remarquable de 44,1% du chiffre d'affaires confirme la performance du secteur EaaS et valide les projections de rentabilité OptimPV. Cette convergence entre projections théoriques et résultats opérationnels renforce la crédibilité de la méthodologie OptimPV.

L'optimisation fiscale se concrétise par un impôt sur les sociétés limité à 0,9% grâce aux amortissements représentant 23,8% du chiffre d'affaires et à l'optimisation de la structure juridique. Cette approche fiscale maximise la rentabilité nette pour l'opérateur.

#### Validation par benchmarks sectoriels

**Quelle validation des hypothèses OptimPV par rapport aux benchmarks sectoriels ?**

La confrontation des résultats OptimPV avec les références de marché valide la crédibilité de l'approche méthodologique développée. Cette analyse comparative positionne le projet Antibes dans l'écosystème national du photovoltaïque commercial et industriel.

**[TABLEAU 9.3 : Validation OptimPV face aux benchmarks sectoriels français]**

| Paramètre | OptimPV | Benchmark PV France | Écart | Validation |
|-----------|---------|-------------------|-------|------------|
| TRI moyen | 13.6% | 8-15% (EaaS) | ✓ | Dans fourchette |
| LCOE | 52.8€/MWh | 45-65€/MWh | ✓ | Médiane secteur |
| Payback | 7.6 ans | 6-9 ans | ✓ | Standard EaaS |
| CAPEX/kWc | 824€ | 800-1000€ | ✓ | Tarif marché 2025 |

La convergence des indicateurs OptimPV avec les standards sectoriels confirme la crédibilité financière du projet Antibes. Cette performance de rentabilité se situe dans la fourchette haute des projets EaaS français, reflétant l'optimisation apportée par la méthodologie OptimPV. Le LCOE positionne le projet sur la médiane du marché national, garantissant une compétitivité équilibrée sans sous-valorisation ni surenchère tarifaire.

#### Modèle économique EaaS - Cash-flows opérateur

**Comment le moteur OptimPV génère-t-il les flux du modèle Energy as a Service ?**

Le moteur OptimPV génère une modélisation complète des flux financiers du modèle Energy as a Service, équilibrant revenus diversifiés et charges opérationnelles optimisées.

Les revenus opérateur du projet Antibes se décomposent en trois sources principales. La vente d'électricité à Euro Plomberie-Piscine génère 30% d'économie sur 90 MWh EPP représentant 33,5% de la consommation totale. La vente aux consommateurs externes du périmètre 2 kilomètres porte sur 179 MWh représentant 66,5% de la production totale. La redevance du bail emphytéotique fait l'objet d'une négociation avec EPP selon les conditions de marché. Le total des revenus annuels s'élève à 27 866€ selon la référence OptimPV 2026.

Les charges opérateur comprennent les postes essentiels du modèle serviciel. L'OPEX maintenance de 1 250€/an capitalise sur l'expertise 25 ans intégrée d'OptimPV. L'assurance installation varie de 600€/an en site unique à 350€/an dans un groupement de 5 sites ACC ou plus. L'amortissement fiscal représente 8 306€/an sur la base de 166 118€ amortis sur 20 ans. Le total des charges annuelles atteint 3 437€/an selon la référence OptimPV 2026.

#### Indicateurs rentabilité modèle EaaS

**Comment OptimPV valide-t-il la viabilité économique du modèle opérateur ?**

OptimPV valide la viabilité économique du modèle opérateur à travers des indicateurs financiers dépassant les seuils de rentabilité requis et sécurisant l'investissement sur la durée contractuelle.

Les indicateurs opérateur du projet Antibes confirment la solidité économique du montage. La rentabilité opérateur dépasse largement l'objectif de 8% fixé par OptimPV, validant la rentabilité intrinsèque du projet. La VAN opérateur de 64 110€ sur les cash-flows EaaS 20 ans confirme la création de valeur actualisée. Le payback opérateur de 7,6 ans selon le modèle serviciel OptimPV assure un retour sur investissement dans les deux tiers de la période contractuelle. La rentabilité garantie pour EPP s'appuie sur un prix fixe 20 ans évitant la volatilité tarifaire du marché électrique.

La validation des contraintes projet par OptimPV confirme que toutes les exigences sont respectées : TRI minimum 8%, bail emphytéotique 20 ans et maintenance incluse dans le modèle EaaS Antibes. Cette convergence entre objectifs et réalisations valide définitivement la faisabilité économique du projet.

### 9.2. Analyse de sensibilité et scénarios

#### Variables critiques identifiées

**Quelles variables critiques OptimPV identifie-t-il dans l'analyse de sensibilité ?**

L'analyse de sensibilité OptimPV identifie trois variables critiques dont l'impact sur la rentabilité nécessite un suivi particulier dans la gestion du projet.

La première variable critique concerne le prix de l'électricité avec une variation de +/- 1 c€/kWh générant un impact TRI de +/- 1,5% selon l'analyse de sensibilité OptimPV. Le scénario haut avec +1 c€/kWh de marché porte le TRI à 15,1%, tandis que le scénario bas avec -1 c€/kWh ramène le TRI à 12,1%, conservant néanmoins une rentabilité largement supérieure au seuil de 8%.

La deuxième variable critique porte sur la production photovoltaïque avec une variation de +/- 10% impactant le TRI de +/- 0,8%. Une année exceptionnelle avec +10% de production élève le TRI à 14,4%, tandis qu'une année défavorable avec -10% de production maintient le TRI à 12,8%, préservant la viabilité économique.

La troisième variable critique concerne les coûts de maintenance avec une variation de +/- 50% générant un impact TRI de +/- 0,5%. Bien que l'impact reste limité, cette variable nécessite une vigilance particulière dans la gestion opérationnelle du projet.

#### Simulations Monte Carlo

L'analyse de robustesse probabiliste du projet EPP Antibes s'appuie sur 1000 simulations Monte Carlo intégrant les principales sources d'incertitude identifiées. Cette approche permet d'évaluer la stabilité des performances économiques face aux aléas opérationnels et de marché.

La modélisation intègre six paramètres d'incertitude calibrés sur les données empiriques. Premièrement, la production photovoltaïque présente une variabilité de ±20%, reflétant les fluctuations météorologiques interannuelles observées sur la région d'Antibes. Deuxièmement, l'évolution des coûts d'investissement fluctue de ±15%, intégrant la volatilité des marchés de matériaux et de main d'œuvre du secteur photovoltaïque. Troisièmement, la consommation d'EPP varie modérément de ±5%, correspondant à la relative stabilité des profils de consommation commerciale. Par ailleurs, les coûts de maintenance présentent une incertitude de ±25%, reflétant l'expérience opérationnelle sur des durées de 20 ans. De plus, les prix de l'électricité fluctuent de ±20%, suivant la volatilité tarifaire historiquement observée. Enfin, la dégradation des panneaux varie autour de 0,6% par an selon les spécifications techniques des constructeurs.

L'évaluation porte ensuite sur quatre contraintes de viabilité économique. D'une part, le TRI projet doit atteindre au minimum 12% pour assurer la rentabilité de l'investissement. D'autre part, le temps de retour sur fonds propres ne doit pas dépasser 10 ans pour maintenir l'attractivité financière. En outre, le gain client doit atteindre au moins 30% pour garantir l'adhésion d'EPP au projet. Enfin, le DSCR doit rester supérieur à 1,2 pour assurer la solvabilité technique du financement.

Les résultats des 1000 simulations révèlent une robustesse économique très satisfaisante du projet. La probabilité d'atteindre un TRI supérieur à 12% s'établit à 72,7%, démontrant une viabilité dans près des trois quarts des scénarios possibles. Le respect du temps de retour inférieur à 8 ans présente une probabilité de 63,8%, confirmant la rentabilité dans une majorité substantielle des configurations testées. La probabilité globale de viabilité du projet, intégrant simultanément l'ensemble des contraintes, atteint 72,7%.

L'analyse statistique approfondie révèle des caractéristiques intéressantes de la distribution des résultats. Le TRI projet présente une moyenne de 13,9% avec un écart-type de 3,0%, situé dans un intervalle de confiance à 95% de [13,1%, 14,7%]. Cette distribution ne suit pas une loi normale, révélant une asymétrie liée aux effets de seuil des contraintes réglementaires. Le temps de retour affiche une moyenne de 7,74 ans avec un écart-type de 1,47 an, confirmant l'impact des variabilités de production sur la rapidité de récupération de l'investissement. Le coût actualisé de l'énergie s'établit en moyenne à 6,0 c€/kWh avec un écart-type de 1,5 c€/kWh, cette métrique présentant une distribution normale qui valide la robustesse du modèle économique.

L'interprétation de ces résultats révèle des performances économiques remarquables pour le projet EPP. En premier lieu, la probabilité de succès de 72,7% dépasse très significativement le seuil d'acceptabilité sectoriel de 60% généralement requis pour les projets d'énergies renouvelables de cette envergure, confirmant une robustesse exceptionnelle du modèle économique. Par ailleurs, le TRI moyen de 13,9% se situe nettement au-dessus du minimum requis de 12%, avec un intervalle de confiance dont la borne inférieure (13,1%) reste supérieure à ce seuil critique. Cette performance témoigne d'une marge de sécurité très appréciable face aux incertitudes opérationnelles.

En outre, la stabilité des résultats statistiques, matérialisée par un écart-type de 3,0% pour le TRI, atteste d'une volatilité parfaitement maîtrisée dans un environnement d'incertitude multi-paramétrique. De même, le temps de retour moyen de 7,74 ans, inférieur à la contrainte de 8 ans dans 63,8% des cas, valide l'attractivité financière renforcée du projet pour l'investisseur. Ces éléments convergent vers une évaluation très positive de la viabilité économique du projet EPP, justifiant pleinement la validation de sa mise en œuvre opérationnelle.

**[Figure 9.1 : Analyse de sensibilité - Tornado Diagram TRI projet Antibes]**

![Tornado Diagram](https://image.noelshack.com/fichiers/2025/37/1/1757341935-figure-9-1-tornado-diagram.png)

*Diagramme en tornade illustrant l'impact des 3 variables critiques sur le TRI de base : prix électricité (barre la plus longue), production photovoltaïque (barre intermédiaire), coûts maintenance (barre la plus courte). Visualisation des scénarios optimiste/pessimiste pour chaque variable avec impact sur TRI en points de pourcentage.*

**Note méthodologique** : *L'analyse de sensibilité repose sur la variation unitaire de chaque paramètre (ceteris paribus), les amplitudes de variation reflétant l'expertise OptimPV : ±1 c€/kWh prix électricité (volatilité tarifaire observée), ±10% production PV (variabilité météorologique PVGIS), ±50% coûts maintenance (incertitude opérationnelle 25 ans). Les impacts linéaires présentés sont validés par les simulations Monte Carlo sur 1000 itérations. Tous les scénarios conservent un TRI > 8% (seuil de rentabilité), démontrant la robustesse intrinsèque du projet Antibes.*


## Chapitre 10 : Perspectives Multi-Sites et Scalabilité

### 10.1. Extension aux 4 autres magasins

#### Pré-analyse OptimPV des 4 sites restants

**Quel potentiel révèle l'analyse automatique des autres entrepôts ?**

OptimPV analyse automatiquement le potentiel d'extension aux quatre autres sites Euro Plomberie-Piscine, révélant des opportunités significatives de déploiement du modèle EaaS+ACC sur l'ensemble du réseau commercial.

Les quatre autres entrepôts EPP (Le Cannet, Mouans-Sartoux, Gattières, Mandelieu-la-Napoule) présentent des caractéristiques techniques prometteuses avec une surface toiture moyenne de 1 500 m² exploitables par site, supérieure aux 1 400 m² d'Antibes. Cette surface additionnelle offre un potentiel d'installation photovoltaïque élargi et des économies d'échelle renforcées.

L'estimation technique préliminaire révèle une surface moyenne de 1 500 m² par site permettant l'installation de 200 kWc par site. La production estimée varierait entre 380 et 420 MWh/an selon l'exposition spécifique de chaque bâtiment. Le CAPEX estimé oscillerait entre 80 et 200 k€ par site, représentant un coût de 800 à 950€/kWc selon la configuration retenue.

La rentabilité prévisionnelle, établie sur des estimations larges, présenterait un TRI estimé de 10 à 15% selon le contexte local et le marché ACC du périmètre considéré. La VAN sur 20 ans s'échelonnerait entre 80 et 150 k€ par site selon l'optimisation commerciale développée. Le payback varierait de 6 à 9 ans selon les conditions de financement et les aides disponibles localement.

Ces estimations demeurent indicatives et nécessiteront une analyse OptimPV dédiée pour chaque site lors des phases de déploiement prévues entre 2026 et 2028, permettant une modélisation précise intégrant les spécificités locales.

#### Méthodologie d'industrialisation du modèle EaaS+ACC

**Comment transformer l'expérience EPP en méthode réplicable ?**

L'expérience EPP révèle les facteurs clés de succès nécessaires à la reproductibilité du modèle EaaS+ACC sur d'autres entreprises multi-sites. Cette analyse méthodologique dépasse le cas spécifique pour identifier les conditions généralisables de déploiement.

Les critères de sélection client s'avèrent déterminants : stabilité financière de l'entreprise garantissant la pérennité contractuelle sur 20 ans, diversité géographique des sites créant des opportunités de mutualisation, profils de consommation complémentaires optimisant l'autoconsommation collective, et engagement RSE facilitant l'adhésion aux objectifs environnementaux.

La standardisation des processus opérationnels permettrait l'industrialisation : checklist de pré-qualification terrain automatisant la détection des contraintes techniques, templates juridiques pré-rédigés réduisant les délais de montage contractuel, méthodologie d'animation commerciale structurant la conduite de projet client, et outils de suivi post-installation garantissant la conformité aux performances prévues.

Cette approche méthodologique pourrait transformer l'expérience EPP en modèle économique reproductible, réduisant les coûts de développement commercial et accélérant la mise en œuvre sur de nouveaux clients aux profils similaires.


### 10.2. Retours d'expérience terrain et découvertes pratiques

#### Difficultés opérationnelles identifiées lors de l'étude de faisabilité

**Quelles difficultés opérationnelles l'étude de faisabilité EPP révèle-t-elle ?**

L'étude de faisabilité approfondie révèle des difficultés opérationnelles significatives non anticipées par la modélisation théorique OptimPV, nécessitant des adaptations méthodologiques pour les futurs déploiements opérationnels.

La complexité administrative s'avère largement sous-estimée dans les projections initiales. Les délais Enedis se révèlent plus longs que prévu, nécessitant une documentation précise lors du projet pour calibrer les futurs planning. La Convention d'Autoconsommation Collective exige de multiples itérations pour intégrer les spécificités du bail emphytéotique Euro Plomberie-Piscine, révélant que OptimPV n'anticipe pas suffisamment ces délais administratifs variables selon les territoires.

Les données de consommation partielles constituent un obstacle méthodologique majeur. Les factures Euro Plomberie ne détaillent pas la répartition horaire, obligeant à utiliser des profils types ENEDIS approximatifs. L'écart entre profil théorique et consommation réelle impacte directement l'optimisation, le taux d'autoconsommation réel risquant de différer sensiblement des prévisions OptimPV.

Les questions client non anticipées révèlent des besoins pratiques qu'OptimPV ne traite pas dans sa modélisation standard. Euro Plomberie soulève des interrogations opérationnelles concrètes : "Que se passe-t-il si on ferme le magasin 3 semaines en août ?", "Peut-on moduler la puissance selon la fréquentation ?", "Comment gérer la maintenance sans interrompre l'activité ?". Ces questions pratiques nécessitent des réponses techniques et contractuelles adaptées.

**Quelles complexités juridiques révèlent les consultations préparatoires spécialisées ?**

Les consultations juridiques préparatoires menées avec des avocats spécialisés révèlent des complexités substantielles dans le montage EaaS+ACC envisagé, particulièrement sur le volet bail emphytéotique.

Le bail emphytéotique spécifique EaaS impose un formalisme notarial renforcé incluant un plan de division de la toiture de 1 400 m², l'intervention d'un géomètre et la rédaction d'un acte authentique, générant un délai supplémentaire d'un mois. La clause de canon emphytéotique soulève la question de l'intégration ou de la séparation du prix au kWh avec un impact direct sur la fiscalité via l'option TVA Article 261 5 4° du CGI. La répartition négociée des charges fiscales détermine la prise en charge de la taxe foncière et de la CET selon l'équilibre contractuel convenu entre EPP et l'opérateur, incluant la négociation sur la taxe de publicité foncière. L'application de l'arrêt de la Cour de Cassation Civile du 11 juillet 2024 confirme le transfert automatique des actions décennale à l'opérateur, sécurisant le montage juridique.

La convention ACC combinée au modèle EaaS constitue un montage juridique nécessitant une rédaction sur-mesure. L'absence de modèle standard impose une rédaction spécifique de la Convention ACC intégrant EaaS, générant un délai supplémentaire de 2 mois et un coût à documenter lors du projet. La répartition des consommateurs externes exige une convention entre la PMO (opérateur) et les consommateurs du périmètre 2 kilomètres, incluant la gestion préventive des défaillances. Par ailleurs, concernant le bail emphytéotique lui-même, la jurisprudence récente de la Cour d'Appel de Bordeaux 2024 confirme l'interdiction de clause résolutoire, empêchant la résiliation automatique du bail et sécurisant ainsi la pérennité contractuelle sur 20 ans.

Les assurances et responsabilités révèlent des obligations spécifiques au secteur photovoltaïque. La responsabilité civile obligatoire pour l'opérateur, régie par le Code de l'environnement, doit couvrir les dommages d'exploitation de la centrale PV. La garantie décennale s'applique car l'installation PV intégrée constitue un ouvrage impactant l'étanchéité de la toiture, engageant l'installateur sur 10 ans. La garantie de démantèlement nécessite une caution bancaire obligatoire pour assurer la remise en état, sécurisant Euro Plomberie.

L'optimisation fiscale détectée révèle des opportunités substantielles. L'option TVA sur le bail selon l'Article 261 5 4° du CGI permet la récupération de TVA sur les équipements si l'option est exercée. L'impôt sur les sociétés de l'opérateur bénéficie de déductions d'amortissements et charges d'exploitation comprenant loyers, maintenance et assurances.

La nécessité d'un accompagnement expert se trouve confirmée par la complexité inédite du montage juridique EaaS+ACC+bail emphytéotique. Le financement EFICAS couvrant 65% du coût se justifie pleinement par cette complexité réglementaire exceptionnelle.

L'inadéquation de l'interface utilisateur face aux besoins du client final constitue une lacune significative. OptimPV génère des rapports techniques comportant 240 colonnes de cash-flow totalement illisibles pour un dirigeant de PME. Euro Plomberie exprime clairement ses besoins : "juste 3 chiffres : investissement, économies annuelles, retour sur investissement". Cette demande révèle que l'outil manque cruellement d'une vue synthétique adaptée aux dirigeants.

#### Écarts prévision/réalité identifiés

**Quels coûts cachés et contraintes techniques pourrait révéler l'analyse terrain ?**

L'analyse terrain pourrait révéler des écarts significatifs entre prévisions OptimPV et réalité opérationnelle, nécessitant une révision méthodologique des processus d'estimation.

Les coûts cachés potentiels comprennent la mise aux normes électriques préalable, l'assurance spécifique au local commercial et les frais notariaux de convention d'autoconsommation, dont les montants réels devront être documentés précisément lors du projet pour calibrer les futures estimations.

Les contraintes techniques susceptibles d'être révélées sur site incluent la détection potentielle d'amiante en toiture nécessitant un désamiantage dont le coût dépendrait du diagnostic détaillé, des limites de structure porteuse imposant d'éventuels renforcements sur une surface à définir, et des difficultés d'accès générant un surcoût de main-d'œuvre dont le pourcentage resterait à documenter.

Ces éléments, non détectables par l'analyse cadastrale automatisée OptimPV, pourraient créer un écart CAPEX significatif par rapport aux estimations initiales, dont le montant total devrait être documenté lors du projet pour améliorer la précision des futures estimations.

#### Besoins fonctionnels exprimés par l'utilisateur

**Quels besoins fonctionnels complémentaires expriment les utilisateurs ?**

Les utilisateurs expriment des besoins fonctionnels complémentaires révélant les limites de l'approche actuelle OptimPV et orientant les développements futurs.

Premièrement, la simulation de scénarios pratiques constitue une demande récurrente : "Et si on installe d'abord 50 kWc puis 50 kWc l'année suivante ?", "Quel impact d'une extension future du magasin ?", "Peut-on déplacer des panneaux entre magasins ?". Ces questions révèlent un besoin de modélisation dynamique et évolutive.

Par ailleurs, les outils de communication client nécessitent une refonte complète : graphiques simplifiés pour présentation en conseil d'administration, comparaison visuelle "avec/sans photovoltaïque" sur 5 ans, calcul d'impact environnemental en tonnes de CO2 évitées. Ces demandes orientent vers une interface de communication dirigeant.

Enfin, le suivi post-installation révèle une lacune majeure d'OptimPV qui se limite à l'étude initiale. Euro Plomberie interroge : "Comment suivre si les performances sont conformes aux prévisions ?". Cette demande légitime nécessiterait un module de monitoring comparant production réelle versus prévisions théoriques.

## Chapitre 11 : Vers un Écosystème Digital Complet

### 11.1. L'angle mort d'OptimPV : l'expérience utilisateur final

#### La demande Euro Plomberie-Piscine non satisfaite

**Quelle lacune fondamentale révèlent les échanges avec Euro Plomberie ?**

Lors des échanges avec la direction Euro Plomberie, une demande récurrente émerge du gérant : "Comment puis-je suivre concrètement les performances de mes 5 magasins et l'impact de l'autoconsommation collective sur ma rentabilité ?" Cette interrogation révèle une lacune fondamentale d'OptimPV concernant l'absence totale d'interface de suivi pour les dirigeants d'entreprise.

OptimPV excelle remarquablement dans l'étude de faisabilité mais s'arrête brutalement à la mise en service, créant une rupture dans l'accompagnement du dirigeant. Le gérant d'Euro Plomberie, responsable de la stratégie énergétique de ses 5 sites, se trouve dépourvu de tout moyen pour visualiser les performances opérationnelles réelles, comprendre les écarts entre prévisions et réalité, suivre l'impact financier concret de l'investissement ou comparer les performances entre ses différents magasins.

Cette limitation transforme le suivi post-installation en "boîte noire" totalement opaque pour le dirigeant, compromettant gravement sa capacité à piloter sa stratégie énergétique et à valoriser son investissement.

#### Applications utilisateur existantes : benchmark et lacunes

**Quel panorama révèle l'analyse du marché des applications ACC ?**

L'analyse du marché révèle quelques tentatives dispersées d'applications de monitoring énergétique, mais aucune ne répond aux besoins spécifiques des dirigeants d'entreprises multi-sites en autoconsommation collective. MySmartBattery développée par Saft se limite exclusivement au stockage résidentiel sans vision consolidée entreprise. Enerplan Monitor propose une interface technique uniquement, inadaptée aux besoins de pilotage stratégique des dirigeants. Linky Connect d'Enedis traite les données site par site sans intégrer la consolidation multi-sites pourtant essentielle aux entreprises comme EPP.

Cette analyse confirme qu'aucune solution ne répond spécifiquement aux besoins de pilotage stratégique des dirigeants d'entreprises multi-sites en ACC. Cette carence manifeste crée une opportunité stratégique significative pour le développement d'un module complémentaire à OptimPV, répondant à un besoin de marché non satisfait.

### 11.2. Conception d'une interface dirigeant multi-sites

#### Fonctionnalités essentielles identifiées

**Comment traduire ces besoins en spécifications techniques concrètes ?**

La traduction des besoins utilisateurs identifiés précédemment en spécifications techniques nécessite une approche architecturale différenciée selon les profils d'utilisateurs finaux.

Pour les dirigeants d'entreprise, la priorité porte sur l'agrégation de données multi-sites avec des indicateurs de synthèse immédiatement exploitables en réunion de direction. L'architecture doit intégrer nativement les flux de données Enedis via les API Linky, tout en proposant une interface épurée limitant l'affichage aux 3 métriques essentielles identifiées par EPP.

Concernant les utilisateurs finaux des logements, l'enjeu technique réside dans la simplification maximale de l'expérience utilisateur, privilégiant l'affichage direct des économies en euros plutôt que les données techniques kWh. Cette approche nécessite un moteur de calcul en temps réel convertissant automatiquement les données de production en bénéfices financiers personnalisés par profil tarifaire.

#### Architecture technique envisagée

**Quelle architecture technique optimale pour l'application utilisateur ACC ?**

L'application s'appuierait judicieusement sur l'infrastructure OptimPV existante, créant des synergies techniques et économiques significatives. Néanmoins, l'enjeu principal réside dans la conception d'une interface accessible à tous les profils d'utilisateurs, incluant les personnes âgées, avec une visualisation immédiate des économies réalisées.

L'interface utilisateur privilégierait une approche de simplicité maximale inspirée des applications bancaires grand public. L'écran d'accueil afficherait directement les économies mensuelles en euros, avec des graphiques colorés et des comparaisons visuelles instantanées (avant/après autoconsommation). Les fonctionnalités seraient limitées aux essentiels : suivi des économies, historique simplifié, et notifications claires sur les bénéfices générés. Cette approche garantirait une compréhension immédiate des avantages financiers, même pour des utilisateurs peu familiarisés avec les technologies numériques.

Le backend s'articulerait autour d'une extension du moteur OptimPV avec une API REST dédiée, permettant la récupération des données Linky via l'API Enedis, les calculs de répartition en temps réel, la gestion d'authentification multi-utilisateurs et le stockage d'historiques individuels en conformité RGPD.

Le frontend mobile reposerait sur une application native iOS/Android proposant une interface intuitive de type "application bancaire", des notifications push pour les alertes et objectifs, un mode hors-ligne pour la consultation des données et une synchronisation automatique avec les données Linky.

L'intégration OptimPV constituerait un module complémentaire optionnel avec import automatique des participants depuis OptimPV, paramétrage des clés de répartition configurées, dashboard administrateur pour le PMO et exports comptables automatisés.


### 11.3. Impact business et perspectives de déploiement

#### Valorisation de l'engagement utilisateur

**Quel impact business génèrerait cette application pour Euro Plomberie ?**

L'application transformerait fondamentalement l'autoconsommation collective d'un mécanisme financier abstrait en outil d'engagement RSE concret et mesurable. Pour Euro Plomberie, les bénéfices attendus s'articulent autour de quatre axes stratégiques.

L'adhésion renforcée transformerait les employés de bénéficiaires passifs en acteurs conscients de leur contribution énergétique. La communication interne bénéficierait d'un outil concret de valorisation de la politique RSE entreprise. L'optimisation comportementale s'opèrerait naturellement par la réduction de consommation induite par la gamification. La différenciation concurrentielle s'appuierait sur l'argument commercial "entreprise digitale et verte", renforçant l'image de marque d'Euro Plomberie.

#### Modèle économique potentiel

**Quelle viabilité économique pour ce développement complémentaire ?**

L'application créerait un flux de revenus récurrents complémentaire à OptimPV, diversifiant le modèle économique de la plateforme. La structure tarifaire comprendrait une licence SaaS, un setup initial et une maintenance évolutive dont les montants restent à définir selon le modèle économique retenu et les coûts de développement.

Pour Euro Plomberie, le coût global sur 47 utilisateurs représenterait un pourcentage marginal du budget total projet, garantissant l'acceptabilité économique de cette extension fonctionnelle tout en créant de la valeur ajoutée significative.

#### Roadmap de développement

**Quelle stratégie de développement séquencé pour cette application ?**

La roadmap de développement s'articulerait sur trois phases permettant une validation progressive des fonctionnalités et une montée en charge maîtrisée.

La Phase 1 de 6 mois développerait un MVP Dashboard web responsive incluant les fonctionnalités essentielles (économies, comparaisons), l'intégration API Linky via Enedis et les tests sur Euro Plomberie avec 28 utilisateurs pilotes sélectionnés.

La Phase 2 de 12 mois étendrait le développement vers une application mobile native iOS/Android intégrant les notifications push et le mode hors-ligne, ainsi que la gamification avancée et les challenges inter-sites.

La Phase 3 de 18 mois introduirait l'intelligence artificielle prédictive avec des recommandations personnalisées d'optimisation, la prédiction de consommation/production sur 7 jours et la détection automatique d'anomalies, transformant l'application en assistant intelligent de l'autoconsommation collective.

## Conclusion : Validation du concept OptimPV et perspectives d'industrialisation

### Performance validée sur cas réel

**Comment l'étude de cas Euro Plomberie-Piscine valide-t-elle les performances d'OptimPV ?**

L'étude de cas Euro Plomberie-Piscine valide concrètement les performances d'OptimPV à travers une application exhaustive des algorithmes et méthodologies sur des données réelles, démontrant la robustesse de l'approche méthodologique développée. Cette validation algorithmique et calculatoire constitue une étape préalable essentielle à la validation opérationnelle terrain.

Les gains opérationnels mesurés confirment l'efficacité de l'outil avec une réduction significative des temps d'analyse comparativement aux méthodes manuelles Excel, une précision d'optimisation tarifaire automatisée surpassant l'estimation manuelle, une exhaustivité permettant le traitement simultané de contraintes multiples versus l'approche séquentielle traditionnelle, et une traçabilité complète via des logs détaillés contrastant avec l'absence d'auditabilité des tableurs.

La validation économique s'appuie sur un TRI projet robuste confirmé par les données PVSOL, une probabilité de succès élevée validée par l'analyse Monte Carlo et une robustesse financière démontrée sur la durée contractuelle de 20 ans. Cette convergence entre modélisation théorique et validation empirique renforce la crédibilité d'OptimPV.

### Enseignements terrain et évolutions nécessaires

**Quels besoins non anticipés révèle l'étude de faisabilité Euro Plomberie-Piscine ?**

L'étude de faisabilité Euro Plomberie-Piscine révèle des besoins non anticipés dans la conception initiale d'OptimPV, orientant la feuille de route d'évolution vers une approche plus intégrée et utilisateur-centrée.

Les évolutions prioritaires identifiées comprennent huit modules complémentaires stratégiques. Le module de pré-diagnostic terrain automatiserait la checklist des contraintes techniques incluant amiante, structure et normes électriques. L'interface dirigeant simplifiée proposerait un dashboard à 3 indicateurs clés remplaçant les 240 colonnes actuelles illisibles. La gestion des profils de fermeture modéliserait les arrêts d'activité saisonniers spécifiques aux secteurs tertiaires. Le module de suivi post-installation comparerait performance réelle versus prévisions théoriques.

L'intégration réseau experts constituerait une base de données référençant bureaux d'études ACC certifiés et avocats spécialisés en droit énergétique, avec coûts éligibles EFICAS à 65%. Les templates juridiques EaaS proposeraient des modèles contractuels pré-rédigés Convention ACC et bail emphytéotique pour modèle opérateur, incluant clauses obligatoires (formalisme notarial, répartition négociable charges fiscales, assurances obligatoires), clauses interdites (résolutoire automatique selon CA Bordeaux 2024, interdiction cession, obligation construction) et optimisations fiscales (TVA option Article 261 5 4° CGI, déduction IS, actions garantie décennale).

Les outils de gestion communautaire développeraient des fonctionnalités de répartition des flux et suivi des participants ACC. Le module de tarification transparente opposerait une interface claire à la complexité tarifaire des concurrents, renforçant l'avantage concurrentiel identifié en Partie 1.

La feuille de route adaptée aux retours terrain prioriserait l'interface synthétique dirigeant à T0+3 mois répondant à la demande client prioritaire, le module pré-diagnostic contraintes techniques à T0+6 mois sécurisant les estimations, et l'outil de suivi monitoring post-installation à T0+12 mois complétant l'écosystème OptimPV.


### Perspectives d'industrialisation OptimPV

#### Validation de l'hypothèse concurrentielle identifiée en Partie 1

**Comment l'étude de faisabilité EPP confronte-t-elle modélisation et réalité concurrentielle ?**

L'étude de faisabilité Euro Plomberie-Piscine permet une confrontation directe entre les hypothèses théoriques de différenciation EaaS+ACC développées en Partie 1 et les contraintes opérationnelles concrètes, validant par les calculs OptimPV le positionnement stratégique face à l'écosystème concurrentiel analysé.

La validation de l'hypothèse de différenciation se confirme sur plusieurs dimensions stratégiques. La transparence tarifaire trouve une validation concrète avec Euro Plomberie appréciant le prix garanti sur 20 ans, contrastant avec la confidentialité opaque des contrats PPA des grands groupes énergétiques. L'ancrage territorial génère effectivement de la valeur ajoutée, la mutualisation dans le périmètre de 2 kilomètres créant du lien local appréciable face à l'anonymat des solutions industrielles standardisées. Le financement 100% opérateur se confirme comme différenciateur décisif, l'absence totale de CAPEX pour EPP constituant un avantage concurrentiel tangible face aux modèles hybrides traditionnels. La complexité réglementaire ACC valide son rôle de barrière à l'entrée, l'expertise spécialisée développée constituant un avantage concurrentiel durable face aux solutions génériques du marché.

Les limites identifiées révèlent les contraintes structurelles du modèle. La surface financière limitée des opérateurs indépendants contraint effectivement la capacité de financement face aux grands énergéticiens, fixant un plafond au nombre de projets simultanés réalisables. Le réseau commercial nécessite une construction méthodique, la prospection client s'avérant plus complexe sans structure commerciale préexistante face aux forces de vente établies d'Engie ou TotalEnergies. La standardisation reste un défi permanent, le modèle sur-mesure OptimPV générant des coûts de développement commercial supérieurs aux solutions industrialisées concurrentes.

Le positionnement concurrentiel validé confirme l'existence d'une niche défendable. La combinaison EaaS+ACC+optimisation demeure effectivement inoccupée par la concurrence traditionnelle, validant l'hypothèse stratégique développée en Partie 1. La différenciation s'avère réelle et valorisée, les clients privilégiant transparence et mutualisation face aux solutions anonymes du marché. La scalabilité reste conditionnelle mais réalisable, l'industrialisation OptimPV nécessitant des partenariats financiers stratégiques tout en conservant sa viabilité économique à grande échelle.

Cette validation empirique confirme définitivement la viabilité du positionnement unique OptimPV EaaS+ACC face aux solutions existantes, tout en révélant précisément les conditions de succès nécessaires pour l'industrialisation à grande échelle.

#### Conditions d'industrialisation identifiées

**Quels prérequis pour le passage à l'échelle OptimPV révèle l'étude de faisabilité terrain ?**

L'étude de faisabilité Euro Plomberie-Piscine révèle trois conditions critiques pour l'industrialisation réussie d'OptimPV, permettant de transformer le concept validé en solution commerciale scalable sur le marché français de l'autoconsommation collective.

La construction d'un réseau de partenaires financiers spécialisés dans le secteur énergétique permet de lever la contrainte structurelle de surface financière identifiée. L'intégration de fonds d'investissement sectoriels ou d'énergéticiens moyens comme Séolis ou Alterna élargit significativement la capacité de financement simultané de projets, dépassant les limitations intrinsèques des opérateurs indépendants.

Le développement d'une force commerciale dédiée PME/ETI optimise l'efficacité de prospection client face aux forces de vente établies de la concurrence. La spécialisation sectorielle (distributeurs, industriels, services) et la formation spécialisée aux spécificités ACC accélèrent la transformation commerciale et réduisent les cycles de vente.

La création d'une plateforme digitale complète intégrant étude, monitoring et application utilisateur industrialise le processus de déploiement. Cette standardisation technologique réduit les coûts marginaux de développement tout en conservant la personnalisation client, résolvant le dilemme industrialisation versus sur-mesure.

**Quelle trajectoire d'industrialisation recommander ?**

La trajectoire d'industrialisation optimale s'articule autour de trois phases séquencées permettant une validation progressive et une montée en puissance sécurisée.

La première phase de consolidation régionale PACA permet de valider le modèle opérationnel sur 10 à 15 projets similaires à Euro Plomberie-Piscine. Cette étape sécurise les processus métier, constitue un portefeuille de références client et valide la rentabilité du modèle dans des conditions réelles d'exploitation.

La deuxième phase d'expansion nationale s'appuie sur les retours d'expérience régionaux pour adapter l'offre aux spécificités locales incluant aides publiques variables, contraintes urbanistiques territorialisées et écosystèmes concurrentiels différenciés selon les régions.

La troisième phase de partenariats stratégiques intègre OptimPV dans l'écosystème énergétique national via des alliances avec des acteurs complémentaires : bureaux d'études spécialisés, installateurs certifiés, énergéticiens régionaux et institutions financières sectorielles.

Cette validation méthodologique confirme la viabilité théorique et calculatoire du concept OptimPV développé en Partie 2 et sa capacité à répondre efficacement aux enjeux concurrentiels identifiés en Partie 1. L'étude de cas Euro Plomberie-Piscine démontre par ses résultats que l'innovation OptimPV EaaS+ACC constitue une réponse théoriquement pertinente et différenciée aux besoins du marché français de l'autoconsommation collective.

Néanmoins, bien que les projections soient encourageantes avec une probabilité de succès de 72,7%, la mise en œuvre opérationnelle nécessitera une vigilance constante pour maintenir les performances prévisionnelles. L'expérience terrain EPP révèle déjà des écarts entre modélisation théorique et réalité opérationnelle, notamment sur la complexité administrative sous-estimée et les coûts cachés non anticipés. Ces décalages, inhérents à tout projet innovant, exigeront des adaptations méthodologiques et des ajustements stratégiques réguliers.

La trajectoire d'industrialisation identifiée, bien que prometteuse, demeure conditionnée à la capacité d'OptimPV à s'adapter aux surprises opérationnelles inévitables des phases de déploiement. Le maintien des marges de rentabilité projetées nécessitera une amélioration continue des processus d'estimation, une meilleure anticipation des contraintes terrain, et une réactivité commerciale face aux évolutions concurrentielles. Cette approche prudente et adaptative constitue la condition sine qua non de transformation du concept validé en succès industriel durable.