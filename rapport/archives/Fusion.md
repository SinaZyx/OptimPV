 Analyse du marché de l'autoconsommation collective et développement d'une plateforme intégrée d'aide à la décision pour l'optimisation technico-économique des projets photovoltaïques : Le cas OptimPV

## Introduction Générale

### Problématique et enjeux de l'autoconsommation collective

L'autoconsommation collective d'électricité (ACC) émerge comme une modalité prometteuse de la décentralisation énergétique française. Définie par l'article L.315-2 du Code de l'énergie, cette pratique permet à plusieurs producteurs et consommateurs de partager localement l'électricité produite via une personne morale organisatrice (PMO). Le marché français compte 102 opérations actives fin 2022, représentant 1150 consommateurs et 4,4 MWc de puissance installée, avec une croissance remarquable de +149% en 18 mois.

Toutefois, cette croissance révèle une complexité opérationnelle considérable. Les développeurs de projets d'ACC multi-acteurs - segment représentant environ 33% des opérations mais présentant les enjeux technico-économiques les plus sophistiqués - font face à des défis d'optimisation spécifiques. Contrairement aux ACC patrimoniales communales qui se contentent d'un prix au coût technique (LCOE), les ACC multi-acteurs nécessitent une optimisation fine du prix de vente pour équilibrer rentabilité du porteur de projet et attractivité pour les consommateurs.

Cette optimisation s'avère particulièrement critique dans un contexte réglementaire et fiscal en mutation rapide. La suppression de l'accise sur l'électricité depuis mars 2025, l'évolution des seuils de puissance autorisée, et la complexité des mécanismes tarifaires (TURPE, TVA différentielle) créent un environnement d'analyse où les paramètres changent constamment.

### Limites des outils existants et justification d'OptimPV

L'analyse des solutions disponibles révèle des limitations significatives pour les ACC multi-acteurs françaises. PVsyst, référence internationale, ne traite pas spécifiquement les contraintes réglementaires françaises et nécessite une expertise technique élevée. Les outils ADEME restent trop simplifiés pour les analyses professionnelles. Les solutions commerciales européennes (PV*SOL, Glint Solar) adoptent une approche généraliste inadaptée aux spécificités du marché français.

Cette inadéquation oblige les développeurs d'ACC multi-acteurs à utiliser des approches manuelles (Excel, VBA) pour des optimisations complexes nécessitant l'intégration simultanée de multiples variables : dimensionnement, prix de vente, clés de répartition, fiscalité, et génération de rapports différenciés selon les parties prenantes.

Face à ces limitations, le développement de la plateforme OptimPV répond à un besoin spécifique : automatiser et optimiser les tâches complexes de modélisation technico-économique pour les ACC multi-acteurs, tout en intégrant nativement les évolutions réglementaires françaises.

### Démarche et structuration du mémoire

Cette recherche appliquée vise à démontrer la valeur ajoutée d'OptimPV dans le contexte spécifique des ACC multi-acteurs. La démarche s'articule autour de trois axes complémentaires : analyse stratégique du secteur, conception et développement de la plateforme, puis validation empirique de sa valeur ajoutée opérationnelle.

La première partie présente l'analyse stratégique du secteur photovoltaïque français, avec un focus spécifique sur le marché de l'autoconsommation collective et l'identification des leviers d'optimisation technico-économique. Ce socle théorique et empirique guide la conception de la solution logicielle.

La deuxième partie détaille la conception et le développement de la plateforme OptimPV, en explicitant les choix architecturaux et les algorithmes d'optimisation implémentés. Les modules opérationnels développés sont décrits dans leur fonctionnement intégré, démontrant la traduction des besoins identifiés en spécifications techniques opérationnelles.

La troisième partie présente la validation de la valeur ajoutée apportée par OptimPV à travers une étude de cas concrète qui démontre l'applicabilité opérationnelle de la solution et quantifie les améliorations de performance obtenues.



## Partie I : Analyse Stratégique du Secteur Photovoltaïque

### Chapitre 1 : Le Marché de l'Autoconsommation Collective en France

L'autoconsommation collective française s'inscrit dans un cadre réglementaire complexe dont la maîtrise conditionne la viabilité des projets. Cette analyse détaille les spécificités du marché français et identifie les segments présentant des besoins d'optimisation technico-économique.

<!-- TODO: AJOUTER FIGURE 1.0 - Principe de fonctionnement de l'ACC 
Inspirée de Figure 9 du rapport HAL : Exemple d'opération ACC avec périmètre 2km
- Montrer concrètement : production PV → consommateurs dans périmètre
- Illustrer les contraintes géographiques (2km, réseau BT)
- Différencier visuellement ACC patrimoniale vs multi-acteurs
- Placer AVANT la timeline réglementaire pour expliquer les bases -->

L'analyse de ce marché nécessite d'examiner successivement trois dimensions structurantes : le cadre réglementaire et ses évolutions récentes, l'écosystème d'acteurs et leurs interactions, puis la segmentation par modèles de PMO qui détermine les besoins d'optimisation spécifiques.

#### Cadre réglementaire : opportunités et contraintes du marché
La maîtrise de ce cadre constitue un prérequis essentiel pour le développement de projets viables. D'une part, l'analyse révèle une progression législative favorable au développement du secteur, mais d'autre part, des contraintes structurelles maintenues influencent directement les modèles économiques applicables.

##### L'évolution législative depuis 2015 : structuration progressive du marché
L'autoconsommation collective trouve ses fondements juridiques dans la loi de transition énergétique pour la croissance verte (LTECV) de 2015. En effet, cette loi a introduit ce concept innovant dans le droit français. L'article L.315-2 du Code de l'énergie définit précisément ce dispositif ﹕ "L'opération d'autoconsommation est collective lorsque la fourniture d'électricité est effectuée entre un ou plusieurs producteurs et un ou plusieurs consommateurs finals liés entre eux au sein d'une personne morale et dont les points de soutirage et d'injection sont situés dans le même bâtiment, y compris des immeubles résidentiels" (rapport HAL, 2022). 

La France a privilégié dès 2016 la mise en place d'une structure juridique spécifique : la Personne Morale Organisatrice (PMO), chargée d'assurer l'interface entre les participants au projet et le gestionnaire du réseau de distribution. La nature juridique de cette PMO est laissée libre et peut être une société de droit privé, une association ou une personne morale de droit public. Toutefois, la structuration juridique de la PMO ne permet pas de répondre à la question de la qualification juridique de la relation producteur/consommateur mais permet d'identifier cette relation auprès du gestionnaire du réseau et du fournisseur de complément.
Par la suite, l'ordonnance de 2016 et le décret de 2017 ont précisé les modalités techniques et administratives, établissant trois types d'opérations d'ACC selon le périmètre géographique (rapport HAL, 2022) :

- **Autoconsommation collective restreinte :** les points de soutirage et d'injection sont situés dans un même bâtiment
- **Autoconsommation collective étendue :** les points de soutirage et d'injection sont situés sur le réseau basse tension et respectent les critères de proximité géographique  
- **Autoconsommation collective étendue 100% EnR :** les points peuvent être situés sur le réseau public de distribution d'électricité

Cette évolution historique du périmètre illustre les assouplissements successifs : de "l'antenne basse tension" initiale (projet d'ordonnance 2016), au "poste de transformation BT/HT" (loi février 2017), puis à la distance maximale de 2 kilomètres (arrêté novembre 2019). Si cette règle garantit une cohérence territoriale, elle limite néanmoins le potentiel de développement géographique.

### Chronologie des évolutions réglementaires majeures

La Figure 1.1 synthétise les principales étapes d'évolution du cadre réglementaire français de l'autoconsommation collective, révélant une trajectoire d'assouplissements progressifs en réponse aux retours d'expérience des acteurs du secteur.

![Timeline de l'évolution réglementaire de l'ACC](https://image.noelshack.com/fichiers/2025/36/1/1756722410-timeline-acc.png)
*Figure 1.1 : Chronologie des évolutions réglementaires de l'autoconsommation collective en France (2015-2025)*

Cette chronologie illustre la corrélation directe entre assouplissements réglementaires et dynamique de marché. Le premier pic de créations d'opérations (fin 2019-début 2020) correspond à l'arrêté d'extension du périmètre géographique, tandis que la suppression de l'accise en 2025 ouvre une nouvelle phase d'accélération du secteur (rapport HAL, 2022).
L'évolution la plus significative intervient avec l'arrêté du 21 février 2025 (Commission de Régulation de l'Énergie, 2025). Cette modification relève substantiellement les paramètres du dispositif. Le seuil de puissance cumulée autorisée passe de 3 MW à 5 MW pour les opérations classiques. Cette évolution concerne la France métropolitaine continentale selon les termes précis de l'arrêté, et répond aux demandes récurrentes des acteurs professionnels, car le seuil antérieur était considéré comme limitant pour le développement de projets d'envergure territoriale.
L'impact de cette évolution dépasse la simple augmentation quantitative des seuils autorisés. En effet, elle traduit une volonté politique d'accélération du déploiement des énergies renouvelables décentralisées, dans un contexte de croissance soutenue du marché. Ainsi, les données Enedis révèlent une dynamique remarquable : 41 opérations actives fin novembre 2020, 55 fin mai 2021, pour atteindre 102 opérations actives en juin 2022, soit une progression de +149% en 18 mois (rapport HAL, 2022). Cette performance dépasse l'objectif PPE 2020 de 50 opérations à l'horizon 2023.

**Structure du marché français :** Ces 102 opérations regroupent 158 producteurs et 1150 consommateurs, pour une puissance totale de 4,4 MWc. La taille moyenne s'établit à 1,5 producteur et 11,5 consommateurs par opération, avec une majorité de projets inférieurs à 36 kW. 

**Typologie des PMO :** Les collectivités territoriales dominent massivement le portage de projets, représentant plus des deux tiers des opérations d'ACC en mai 2022 (rapport HAL, 2022). Cette prédominance s'explique par le développement d'ACC "patrimoniales", où le consommateur et le producteur sont une même personne morale disposant de PRM/PDL distincts. Les PMO constituées sous forme de sociétés et EPIC représentent 18% des opérations, loin derrière les PMO collectivités. Cette répartition illustre l'émergence de trois formes de PMO distinctes : ACC "patrimoniale", ACC "bailleur social" et ACC "multi-acteurs/communauté".

La capacité d'évolution du cadre normatif français justifie les nouvelles ambitions réglementaires pour 2025.

 Quelles contraintes géographiques et dérogations spécifiques encadrent les projets ?

La réglementation française impose des contraintes géographiques strictes visant plusieurs objectifs complémentaires. D'une part, ces contraintes préservent l'efficacité du réseau électrique selon les principes techniques établis, et d'autre part, elles maximisent les bénéfices de la consommation locale pour les participants. Ainsi, la règle générale impose un périmètre maximal de 2 kilomètres entre lieux de production et de consommation.
Une dérogation spécifique permet l'extension à 20 kilomètres pour les zones rurales. Adaptée aux spécificités des territoires moins denses, elle L'application de cette dérogation nécessite une justification technique et économique selon les critères établis. Elle facilite le développement de projets dans les territoires où la densité démographique limite les opportunités.
L'arrêté du 21 février 2025 introduit une innovation majeure concernant les dérogations publiques. Une dérogation spécifique s'applique aux projets portés par des communes ou des établissements publics de coopération intercommunale (EPCI) à fiscalité propre. 
Cette dérogation s'active lorsque l'ensemble des participants sont des organismes publics. Les entités exerçant une mission de service public peuvent également en bénéficier.
Dans ce cadre dérogatoire, la puissance cumulée peut atteindre jusqu'à 10 MW selon les dispositions spécifiques. Le périmètre de partage peut s'étendre à l'ensemble du territoire de l'EPCI concerné. Cette extension géographique facilite significativement le développement de projets territoriaux d'envergure. 
Elle illustre la volonté des pouvoirs publics de favoriser l'émergence de projets publics structurants.
L'analyse des critères cumulatifs révèle cependant une complexité administrative significative. Ce niveau de complexité peut constituer un frein pour certains porteurs de projets. La nécessité de justifier le caractère public de tous les participants peut compliquer la structuration juridique. La vérification du respect des critères nécessite un accompagnement juridique spécialisé.

Au-delà de ces évolutions des seuils et périmètres autorisés, la transformation la plus significative du secteur résulte des modifications fiscales récentes qui redéfinissent fondamentalement l'équation économique des projets.

#### La révolution fiscale : transformation de l'économie des projets

L'évolution la plus structurante pour l'économie de l'autoconsommation collective concerne la révolution fiscale récente. L'article 21 du Projet de loi de finances 2025, adopté le 6 février via le recours au 49.3, modifie profondément la fiscalité applicable. Cette réforme aligne le régime fiscal de l'autoconsommation collective sur celui de l'autoconsommation individuelle. L'alignement concerne les installations inférieures à 1 MW selon les seuils définis.
Concrètement, cette réforme entraîne la suppression de l'accise sur l'électricité pour ces installations. L'accise représentait une taxe de 33,7 €/MWh qui pénalisait significativement les projets collectifs. Depuis le 1er mars 2025, ce tarif est officiellement fixé à 0 €/MWh. L'article 75 de la loi de finances pour 2025 formalise cette suppression (République Française, 2025).

Cette mesure représente un avantage concurrentiel considérable pour l'autoconsommation collective. Les projets peuvent désormais proposer des prix plus attractifs aux consommateurs participants. L'élimination de cette taxation améliore directement la compétitivité face aux tarifs réglementés standards. Cette amélioration facilite le développement de projets et accélère l'adoption par les consommateurs participants.
L'impact économique de cette suppression est quantifiable et significatif. Les projets d'autoconsommation collective peuvent proposer une baisse d'environ 25% du prix de l'électricité. Cette réduction concerne les consommateurs participants selon les simulations économiques réalisées. Cette amélioration renforce l'attractivité économique du modèle considérablement. Elle accélère potentiellement le déploiement selon les prévisions de marché établies.
Parallèlement aux évolutions fiscales, le Tarif d'Utilisation des Réseaux Publics d'Électricité (TURPE) a fait l'objet d'adaptations spécifiques. La Commission de Régulation de l'Énergie a introduit en mai 2018 une formule tarifaire optionnelle destinée aux participants d'opérations d'ACC, créant une distinction entre flux autoproduits et alloproduits (rapport HAL, 2022). Cette adaptation technique reconnaît les spécificités économiques de l'autoconsommation collective tout en préservant les principes de péréquation du système électrique français.

Cette évolution illustre l'importance de la veille réglementaire pour les acteurs du secteur. Les outils d'analyse doivent intégrer rapidement ces évolutions pour maintenir leur pertinence. La capacité d'adaptation aux changements normatifs devient un critère de différenciation technique. La réactivité aux changements normatifs devient un avantage opérationnel décisif.

La compréhension de ces évolutions réglementaires et fiscales nécessite d'analyser l'organisation des acteurs qui mettent en œuvre ces dispositifs sur le terrain et leurs interactions opérationnelles.

#### L'écosystème d'acteurs et les rôles institutionnels

L'autoconsommation collective implique un écosystème complexe d'acteurs aux rôles différenciés et interconnectés. La Figure 1.2 schématise cette organisation institutionnelle, plaçant la Personne Morale Organisatrice (PMO) au centre du dispositif.

![Schéma de fonctionnement d'une opération d'ACC](schema_acteurs_acc.svg)
*Figure 1.2 : Écosystème d'acteurs d'une opération d'autoconsommation collective (adapté du rapport HAL, 2022)*

Au cœur de toute opération, la PMO constitue l'élément central structurant, ayant "pour mission principale de servir d'interface entre les acteurs (producteurs et consommateurs) et le gestionnaire du réseau de distribution, concluant une convention d'autoconsommation collective" (rapport HAL, 2022). Elle coordonne les flux énergétiques et informationnels entre :

- **Les participants internes** : producteur(s) et consommateur(s) liés par contrat onéreux ou non
- **Le gestionnaire de réseau** : principalement Enedis assurant mesure et distribution
- **L'acheteur de surplus** : valorisation de l'excédent de production
- **Le fournisseur de complément** : approvisionnement de l'énergie manquante

Cette configuration multi-acteurs génère une complexité de coordination que la plateforme OptimPV vise à automatiser et optimiser.

**Évolution des modèles de PMO :** Le cadre initial de 2016 a progressivement évolué vers trois configurations distinctes. Pour les bailleurs sociaux, un cadre juridique spécifique a été créé en 2019 via la loi relative à l'énergie et au climat : le bailleur social devient directement la PMO, l'information sur la présence d'une opération d'ACC étant assurée à la conclusion du contrat de location. Le locataire peut librement décider de ne pas participer à l'opération et peut également la quitter à tout moment (rapport HAL, 2022). Cette simplification répond aux spécificités de ce segment de marché et facilite considérablement le montage de projets.
Le gestionnaire de réseau de distribution, principalement Enedis, joue un rôle technique crucial. Il assure le raccordement des installations selon les normes techniques établies. La mesure des flux énergétiques s'effectue via les compteurs communicants Linky installés. La répartition de l'électricité produite localement suit les directives de la PMO. Cette répartition respecte les clés de répartition contractuellement définies entre les participants.
L'arrêté du 10 juillet 2024 a simplifié significativement les obligations administratives. Les collectivités territoriales bénéficient particulièrement de ces dispositions. Il n'est pas nécessaire de constituer de budget annexe pour les projets respectant certains critères. La constitution de régie n'est également pas obligatoire dans ces cas précis. Cette exemption s'applique tant que la puissance cumulée ne dépasse pas 1 MW.
Cette simplification administrative encourage l'engagement des collectivités dans le développement territorial. Elle réduit les coûts administratifs et facilite la prise de décision politique. L'élimination de contraintes procédurales accélère les délais de mise en œuvre. Cette facilitation répond aux demandes exprimées par les associations d'élus locaux.
L'analyse de l'écosystème révèle l'émergence d'acteurs spécialisés dans l'accompagnement technique et juridique. Ces prestataires développent une expertise spécifique à l'autoconsommation collective. Leur émergence témoigne de la structuration progressive de cette filière économique. L'émergence d'expertise spécialisée facilite l'accès au marché pour les porteurs non-experts.
La structuration de cet écosystème crée une chaîne de valeur spécialisée permettant la professionnalisation du secteur. Elle facilite l'émergence de standards techniques et commerciaux homogènes sur le territoire.

### Synthèse des modèles de PMO : segmentation du marché et périmètre d'OptimPV

L'évolution réglementaire a conduit à l'émergence de trois formes de PMO distinctes, inscrites dans le modèle de convention d'autoconsommation collective, présentant des enjeux d'optimisation radicalement différents (rapport HAL, 2022) :

#### **ACC "patrimoniale" : optimisation technique sans enjeu commercial**

Les opérations patrimoniales représentent 67% des ACC françaises selon les données Enedis. Dans ce modèle, le consommateur et le producteur constituent une même personne morale (typiquement collectivités territoriales) disposant de PRM/PDL distincts. La commune installe des panneaux photovoltaïques sur un site (mairie, école) et consomme l'électricité produite sur d'autres sites communaux (éclairage public, équipements municipaux).

**Spécificités économiques :** L'objectif n'est pas la rentabilité commerciale mais l'optimisation budgétaire interne. Le prix de l'électricité échangée correspond au coût technique de production (LCOE - Levelized Cost of Energy) sans marge commerciale. La collectivité cherche à réduire sa facture énergétique globale en mutualisant sa production entre ses différents sites de consommation.

**Besoins d'optimisation limités :** Ce modèle ne présente aucun enjeu d'optimisation de prix de vente puisqu'il n'y a pas de transaction commerciale. Les outils nécessaires relèvent davantage de la gestion technique (dimensionnement, suivi de production) que de l'optimisation économique sophistiquée.

#### **ACC "bailleur social" : modèle intermédiaire à gouvernance simplifiée**

Le bailleur social devient directement PMO avec intégration automatique des locataires (sortie libre possible). Ce modèle représente une part croissante des opérations mais conserve une logique sociale plutôt que commerciale. L'optimisation porte principalement sur l'équité de répartition et la réduction des charges locatives.

#### **ACC "multi-acteurs/communauté" : segment cible d'OptimPV**

Les opérations multi-acteurs, bien que minoritaires en nombre (environ 33% des opérations), constituent le segment présentant les enjeux d'optimisation technico-économique les plus complexes. Dans ce modèle, un développeur privé (SPV) installe une production photovoltaïque et vend l'électricité à des consommateurs tiers (particuliers, entreprises, collectivités).

**Enjeux d'optimisation cruciaux :** Contrairement aux ACC patrimoniales, ces projets nécessitent une optimisation fine du prix de vente pour équilibrer rentabilité du porteur de projet et attractivité pour les consommateurs. Le prix doit se positionner entre le coût de production (seuil de viabilité) et les tarifs réglementés (seuil d'attractivité), tout en intégrant les spécificités fiscales et réglementaires.

**Complexité de gouvernance :** La multiplicité des parties prenantes aux intérêts divergents (investisseurs, consommateurs, PMO) nécessite des outils d'aide à la décision sophistiqués pour identifier les configurations gagnant-gagnant.

#### **Périmètre et justification d'OptimPV**

**OptimPV cible exclusivement les ACC multi-acteurs**, seul segment présentant des besoins réels d'optimisation algorithmique des paramètres technico-économiques. Les ACC patrimoniales, bien que majoritaires en nombre, ne constituent pas un marché pertinent pour des outils d'optimisation commerciale avancés.

Bien que réduisant le marché adressable, cette focalisation le qualifie considérablement. Elle justifie le développement d'une solution spécialisée sur les enjeux spécifiques de ce segment : optimisation de prix, modélisation financière multi-parties, gestion des clés de répartition complexes, et aide à la négociation commerciale.

Cette analyse de la segmentation du marché permet d'identifier les freins opérationnels spécifiques aux ACC multi-acteurs qui justifient le développement d'outils d'optimisation dédiés.

### Identification des freins : justification du développement d'OptimPV

L'analyse des retours d'expérience révèle cependant des coûts de transaction significatifs inhérents aux opérations d'ACC. Comme l'identifie le rapport HAL (2022) ﹕ "Contrairement aux autres dispositifs de production décentralisée d'énergie, l'ACC nécessite des formes d'intermédiation assez développées, qui génèrent des coûts de transaction propres, d'un montant plus ou moins élevé. Ils correspondent aux différentes tâches que la PMO doit effectuer, notamment autour du traitement des données, pour faire fonctionner l'opération, c'est-à-dire assurer une mise en relation des producteurs et consommateurs qui soit efficace aux plans technique, économique et organisationnel".

La complexité opérationnelle, amplifiée par la multiplicité des paramètres technico-économiques et l'évolution réglementaire constante, justifie le développement de la plateforme OptimPV. L'automatisation et l'optimisation de ces processus de gestion constituent un enjeu majeur pour la viabilité économique des projets, particulièrement pour les opérations de taille modeste qui dominent le marché français.

 Quels modèles économiques structurent les flux de revenus et de coûts ?

L'économie de l'autoconsommation collective repose sur des modèles financiers complexes articulant multiples flux. Ces modèles intègrent des structures de revenus diversifiées et des postes de coûts spécifiques, et l'optimisation de ces modèles constitue l'enjeu central de la rentabilité des projets. L'optimisation nécessite une compréhension fine des mécanismes économiques sous-jacents selon l'analyse financière menée.

 #### Structure des revenus : autoconsommation et valorisation du surplus

Les revenus d'un projet d'autoconsommation collective se décomposent en deux flux principaux distincts. D'une part, les économies générées par l'autoconsommation locale constituent le premier flux de valeur, et d'autre part, la valorisation du surplus de production via la vente au réseau forme le second flux. Cette dualité structure l'ensemble du modèle économique et guide les stratégies d'optimisation.
L'autoconsommation génère des économies directes pour les consommateurs participants selon un mécanisme substitutif. L'électricité produite localement se substitue à l'électricité du réseau facturée aux tarifs réglementés. Le mécanisme substitutif présente un avantage économique proportionnel à l'écart entre coût de production local et prix réseau. L'analyse des données de marché révèle que cet avantage varie selon les profils de consommation. Les caractéristiques techniques des installations influencent également cette performance économique.
Le calcul de ces économies nécessite l'intégration de plusieurs composantes tarifaires. Le tarif de base de l'électricité réseau constitue la référence comparative principale. Les taxes et contributions spécifiques s'ajoutent à cette base tarifaire. La Contribution au Service Public de l'Électricité (CSPE) représente 22,5 €/MWh en 2025. La Taxe sur la Consommation Finale d'Électricité (TCFE) varie selon les collectivités territoriales. Ces éléments déterminent le tarif de référence pour le calcul des économies générées.
Le surplus de production non autoconsommé nécessite une valorisation externe optimisée. Les mécanismes d'obligation d'achat d'Électricité de France (EDF) constituent la voie principale de valorisation. Les tarifs d'achat varient selon la puissance installée et la technologie utilisée. Pour les installations photovoltaïques inférieures à 100 kW, le tarif s'établit à 13,17 c€/kWh en 2025. Ce tarif évolue trimestriellement selon les mécanismes de dégressivité établis par la Commission de Régulation de l'Énergie (CRE).

L'optimisation du ratio autoconsommation/surplus constitue un levier économique majeur. Si un taux d'autoconsommation élevé maximise les économies directes pour les participants, le surdimensionnement pour augmenter l'autoconsommation peut cependant dégrader la rentabilité globale. L'équilibre optimal dépend des profils de consommation et des caractéristiques techniques spécifiques. Par conséquent, cette optimisation nécessite des outils de simulation performants pour identifier les configurations optimales.

 Quelle structure de coûts caractérise les projets d'autoconsommation collective ?

La structure de coûts des projets d'autoconsommation collective intègre plusieurs postes spécifiques distincts. Généralement, les coûts d'investissement initial (CAPEX) représentent le poste le plus significatif, tandis que les charges d'exploitation annuelles (OPEX) impactent la rentabilité sur la durée de vie. En outre, les coûts de structure spécifiques à l'autoconsommation collective s'ajoutent aux postes traditionnels.
Les coûts d'investissement se décomposent en plusieurs sous-ensembles techniques identifiés. Les modules photovoltaïques représentent environ 30% du CAPEX total selon les études de marché récentes. Les onduleurs et équipements électriques constituent 15% de l'investissement initial. La structure porteuse et l'installation représentent 25% du coût total. Les raccordements électriques et les compteurs spécialisés ajoutent 20% au montant global. Les études et frais de développement complètent avec 10% de l'investissement total.
L'évolution des coûts d'investissement suit une tendance baissière constante depuis 2010. L'Agence Internationale de l'Énergie (AIE) quantifie cette baisse à 65% sur la période 2010-2024. Cette réduction provient principalement de la diminution du coût des modules photovoltaïques. L'amélioration des rendements de production contribue également à cette optimisation économique. Les économies d'échelle dans la production industrielle expliquent partiellement cette évolution favorable.
Les charges d'exploitation annuelles intègrent plusieurs postes récurrents spécifiques. La maintenance préventive et curative représente environ 1,5% du CAPEX annuellement. L'assurance multirisque ajoute 0,3% du montant de l'investissement initial. Le contrôle et la surveillance à distance nécessitent 0,2% du CAPEX par an. La gestion administrative et commerciale représente entre 2% et 4% du chiffre d'affaires. Ces charges varient selon la taille et la complexité du projet développé.
Les coûts spécifiques à l'autoconsommation collective révèlent une complexité particulière identifiée par le rapport HAL (2022). Ces coûts de transaction comprennent deux composantes distinctes : d'une part la gestion administrative (facturation, suivi des données de consommation, gestion des clés de répartition), et d'autre part "l'animation de l'opération" qui consiste à "constituer et entretenir le collectif".

La dimension relationnelle s'avère critique pour les ACC multi-acteurs. Le rapport HAL souligne que cette animation nécessite de "générer, dans le temps, de la confiance, de la crédibilité, de la simplicité et à gérer le risque d'échec potentiel pour le collectif". Ces coûts relationnels incluent la négociation commerciale initiale, la résolution des conflits de facturation, la communication régulière avec les participants, et la production de rapports différenciés selon les parties prenantes (investisseurs, consommateurs, autorités).

L'analyse terrain révèle que ces coûts d'intermédiation représentent généralement entre 8% et 15% des charges d'exploitation totales pour les ACC multi-acteurs, soit significativement plus que les 5% à 10% des ACC patrimoniales. Cet écart s'explique par la complexité des relations multi-parties et la nécessité de maintenir l'engagement des consommateurs sur la durée de vie du projet.

L'optimisation de cette structure de coûts constitue un levier de compétitivité majeur pour les développeurs d'ACC multi-acteurs. La mutualisation des coûts de gestion entre plusieurs projets permet des économies d'échelle substantielles. L'automatisation des processus administratifs réduit les charges de personnel dédiées à la gestion opérationnelle. 

Concernant les coûts relationnels, leur réduction passe par la standardisation et la clarification des processus de communication. Des rapports automatisés et personnalisés selon les parties prenantes réduisent les besoins d'accompagnement individuel. La transparence des données de consommation et de facturation, facilitée par des outils logiciels spécialisés, diminue les sources de conflit et maintient la confiance dans la durée. Cette optimisation des aspects relationnels s'avère particulièrement critique pour la viabilité économique des projets de taille modeste où les coûts fixes d'intermédiation pèsent davantage.

### Les clés de répartition : un paramètre d'optimisation sous-exploité

Au-delà de l'optimisation des coûts et du prix de vente, la méthode de partage de l'énergie produite constitue un levier technique et économique souvent négligé. L'analyse des données Enedis révèle que 80% des opérations utilisent la clé de répartition "par défaut", consistant en une répartition au prorata de la consommation instantanée (rapport HAL, 2022). Les clés "dynamiques" (15%) et "statiques" (5%), permettant des répartitions plus sophistiquées selon des critères de priorisation, restent largement sous-utilisées.

<!-- TODO: AJOUTER FIGURE 1.3 - Répartition schématique des flux énergétiques
Inspirée de Figure 64 du rapport HAL : Répartition schématique des flux
- Montrer visuellement comment l'électricité PV se répartit entre consommateurs
- Illustrer les différents types de clés : défaut (80%), dynamiques (15%), statiques (5%)
- Expliquer graphiquement le principe de l'autoconsommation vs surplus réseau
- Aide à comprendre l'enjeu d'optimisation des clés de répartition -->

Cette sous-utilisation représente une opportunité d'optimisation significative. La clé de répartition influence directement la satisfaction des participants et l'équité perçue du système. Une répartition dynamique peut privilégier certains profils de consommation selon des critères sociaux ou économiques. Elle peut également optimiser l'utilisation locale de l'électricité produite en priorisant les consommations les plus proches géographiquement ou temporellement de la production.

L'impact économique du choix de la clé de répartition varie selon la configuration du projet et les profils des participants. Une optimisation algorithmique de ce paramètre, intégrée à la plateforme OptimPV, permettrait d'identifier la méthode de répartition maximisant la satisfaction collective tout en respectant l'équité entre participants. La sophistication technique offre un avantage opérationnel aux projets utilisant des outils d'optimisation avancés.

### Le lien entre autoconsommation collective et sobriété énergétique

Au-delà de l'optimisation technico-économique, l'analyse des opérations d'ACC révèle une dimension souvent sous-estimée dans les modélisations financières : l'efficacité énergétique comme "fil conducteur commun" de nombreux projets. Le rapport HAL identifie ainsi que "l'efficacité énergétique est un élément commun très présent dans l'ensemble des opérations d'ACC" et qu'elle constitue parfois "une sorte de fil rouge" pour certaines initiatives.

Cette double finalité - économique et comportementale - s'avère particulièrement prégnante dans les projets portés par les collectivités territoriales et les bailleurs sociaux. D'une part, ces acteurs recherchent une optimisation des coûts énergétiques pour leurs usagers. D'autre part, ils utilisent l'ACC comme un outil pédagogique pour rendre les participants "acteurs de leur propre consommation" et les inciter à réduire leur consommation globale.

L'intégration de cette dimension dans les outils d'optimisation comme OptimPV ouvre des perspectives fonctionnelles spécifiques. Les modules de suivi et de reporting sur les économies d'énergie réalisées permettent de quantifier l'impact comportemental. Les outils de simulation du "gain de sobriété" potentiel enrichissent l'analyse de rentabilité par une valorisation des externalités positives. Les fonctionnalités de communication facilitent l'animation communautaire autour d'objectifs partagés de réduction de la consommation.

Cette approche intégrée distingue l'optimisation technique de la simple maximisation de production. Elle reconnaît que l'enjeu n'est pas seulement de mieux produire, mais aussi de mieux consommer. Une telle approche intégrée différencie les plateformes d'optimisation de nouvelle génération.

 #### Impact des mécanismes tarifaires et fiscaux sur la rentabilité

Les mécanismes tarifaires et fiscaux exercent une influence déterminante sur la rentabilité des projets. Leur évolution récente modifie substantiellement les équilibres économiques établis précédemment. La compréhension fine de ces mécanismes conditionne l'optimisation des modèles d'affaires. Cette maîtrise devient un facteur clé de succès pour les porteurs de projets.
La suppression de l'accise sur l'électricité constitue l'évolution fiscale la plus structurante récente. Effective depuis le 1er mars 2025, elle élimine une charge de 33,7 €/MWh. L'impact sur la compétitivité des projets d'autoconsommation collective est considérable selon les simulations réalisées. Cette mesure permet une réduction du prix de vente de l'électricité d'environ 3,4 c€/kWh. L'attractivité pour les consommateurs participants s'améliore ainsi directement.
Les tarifs réglementés de vente d'électricité constituent la référence concurrentielle principale. Le Tarif Réglementé de Vente (TRV) résidentiel s'établit à 25,16 c€/kWh toutes taxes comprises en 2025. Ce tarif intègre l'ensemble des composantes tarifaires et fiscales applicables. L'évolution de ce tarif influence directement la compétitivité de l'autoconsommation collective. Une augmentation du TRV améliore mécaniquement l'attractivité des projets décentralisés.
L'optimisation fiscale des structures juridiques constitue un levier additionnel de performance. Le choix de la forme juridique de la PMO influence la fiscalité applicable. Les structures associatives bénéficient d'exonérations spécifiques sous certaines conditions. Les sociétés commerciales supportent l'impôt sur les sociétés au taux de 25%. Cette différenciation guide le choix de structuration juridique selon les objectifs poursuivis.
La Taxe sur la Valeur Ajoutée (TVA) s'applique différemment selon la nature des opérations. Les ventes d'électricité sont soumises au taux réduit de 5,5% pour les installations inférieures à 3 kW. Le taux normal de 20% s'applique pour les puissances supérieures selon la réglementation. Les modèles économiques et choix de dimensionnement en dépendent directement. L'optimisation de la TVA nécessite une structuration juridique et technique cohérente.

La déductibilité de la TVA sur les investissements dépend du statut fiscal de la PMO. Les structures assujetties peuvent récupérer la TVA sur les équipements et prestations. Cette récupération améliore significativement l'économie du projet selon les simulations financières. Elle représente environ 16,7% du montant de l'investissement initial hors taxes. L'économie substantielle justifie souvent le choix d'un statut assujetti malgré les contraintes administratives.

 Quels facteurs déterminent l'équilibre économique des projets ?

L'équilibre économique des projets d'autoconsommation collective résulte de l'articulation complexe entre revenus et charges. Plusieurs facteurs clés déterminent cet équilibre selon une sensibilité variable. L'identification et la hiérarchisation de ces facteurs orientent les stratégies d'optimisation. Cette analyse guide les décisions de conception et de dimensionnement des installations.
Le prix de vente de l'électricité aux participants constitue le paramètre d'équilibre central. Ce prix doit assurer la viabilité économique du projet tout en restant attractif, et se positionne généralement entre le coût de production et le tarif réglementé. L'écart avec le tarif réglementé détermine l'attractivité pour les consommateurs, tandis que la marge par rapport au coût de production conditionne la rentabilité du porteur de projet.
Le taux d'autoconsommation influence directement les revenus du projet selon un effet multiplicateur. Si un taux élevé maximise la valorisation de la production au prix de vente négocié, un taux faible nécessite une valorisation importante du surplus au tarif d'obligation d'achat. L'optimisation de ce taux passe par l'adéquation entre profils de production et de consommation, cette adéquation dépendant de la saisonnalité et des habitudes de consommation des participants.
La durée de vie économique du projet détermine la répartition des charges d'investissement. Une durée de 20 ans constitue généralement la référence pour l'amortissement comptable. Les garanties constructeurs s'étendent sur 25 ans pour les modules photovoltaïques actuels. Cette extension de garantie améliore la sécurité financière et facilite l'obtention de financements. Elle permet également d'envisager des modèles économiques sur durées plus longues.
Le coût du financement impacte significativement la rentabilité selon le mode retenu. Si un financement par fonds propres évite les charges financières, il immobilise cependant les capitaux. À l'inverse, le recours à l'emprunt génère des intérêts mais optimise la rentabilité des capitaux propres. Les taux d'intérêt actuels pour les projets d'énergies renouvelables varient entre 3% et 5%, cette variation dépendant de la qualité du porteur de projet et des garanties offertes.
L'optimisation de ces paramètres nécessite des outils de simulation et d'aide à la décision performants. En effet, l'interdépendance entre variables complique l'identification des configurations optimales manuellement, tandis que les outils logiciels spécialisés facilitent l'exploration des scénarios et l'optimisation multi-critères. Par conséquent, cette optimisation constitue un avantage opérationnel décisif pour les développeurs de projets.

 ### Chapitre 2 : Analyse des Outils Existants et Spécifications d'OptimPV

Le marché des outils d'aide à la décision pour les projets photovoltaïques présente une segmentation importante. Cette segmentation reflète la diversité des acteurs et des besoins selon l'analyse menée. Or, les solutions existantes présentent des limitations significatives pour l'autoconsommation collective française, et ces lacunes justifient le développement d'une solution spécialisée interne.

 Quelles solutions académiques et institutionnelles structurent l'offre actuelle ?

Les solutions académiques et institutionnelles constituent un segment important de l'offre d'outils d'analyse. Ces solutions, développées par les organismes de recherche, offrent généralement une sophistication technique élevée. Ainsi, l'Institut National de l'Énergie Solaire (INES) propose des outils de dimensionnement reconnus par la profession, tandis que le Centre Scientifique et Technique du Bâtiment (CSTB) développe des logiciels de simulation énergétique spécialisés.
L'outil PVsyst constitue la référence internationale pour la simulation photovoltaïque selon les retours professionnels. Développé par l'Université de Genève, il intègre des modèles physiques sophistiqués, et sa base de données météorologiques couvre l'ensemble du territoire français avec précision. Les fonctionnalités de simulation permettent une modélisation fine des performances techniques, tandis que l'exportation de rapports détaillés facilite la documentation des projets pour les investisseurs.
Cependant, PVsyst présente des limitations importantes pour les ACC multi-acteurs françaises. D'une part, l'outil ne traite pas spécifiquement les contraintes réglementaires françaises, et la modélisation économique reste généraliste sans prendre en compte les spécificités fiscales. D'autre part, il ne propose aucune fonctionnalité pour gérer les coûts relationnels identifiés par le rapport HAL : génération de rapports différenciés, outils de communication avec les parties prenantes, ou suivi de la satisfaction des participants. L'interface utilisateur complexe nécessite une formation approfondie, et le coût de licence élevé limite l'accessibilité pour les développeurs de projets de taille modeste.
L'Agence de l'Environnement et de la Maîtrise de l'Énergie (ADEME) propose des outils gratuits accessibles en ligne. Ces outils visent à démocratiser l'accès à l'analyse technique selon la mission de l'agence. Cependant, leur simplicité limite la finesse d'analyse nécessaire pour les projets professionnels. La mise à jour des paramètres réglementaires suit les évolutions avec retard. L'absence d'intégration avec d'autres outils complique l'utilisation dans les workflows professionnels.
Les solutions académiques privilégient généralement la précision technique sur l'utilisabilité opérationnelle. Cette orientation répond aux besoins de recherche mais limite l'adoption par les praticiens. L'interface utilisateur souvent complexe constitue une barrière à l'adoption généralisée. L'inadaptation aux contraintes opérationnelles des entreprises limite leur diffusion professionnelle significativement.

 #### Solutions commerciales et réponse aux besoins du marché

Les solutions commerciales développées par des éditeurs logiciels privés structurent une part croissante du marché. Ces solutions offrent généralement une ergonomie supérieure aux outils académiques. L'intégration facilitée dans les processus commerciaux constitue leur avantage principal. Plusieurs acteurs européens proposent des plateformes spécialisées pour le photovoltaïque.
La société allemande Valentin Software développe PV*SOL, concurrent direct de PVsyst. Cet outil intègre des fonctionnalités de dimensionnement et d'analyse économique avancées. L'interface utilisateur modernisée facilite la prise en main pour les non-spécialistes. La génération automatique de rapports commerciaux accélère les processus de vente. Le coût de licence reste cependant élevé et limite l'accessibilité pour les petites structures.
Les solutions françaises restent limitées sur ce segment selon l'analyse de marché conduite. La société Tecsol propose des outils spécialisés mais destinés aux bureaux d'études experts. L'entreprise Sunology développe des calculateurs simplifiés pour l'autoconsommation individuelle. Ces solutions ne traitent pas spécifiquement l'autoconsommation collective avec sa complexité réglementaire.
L'émergence de solutions SaaS (Software as a Service) transforme progressivement le marché. Ces solutions cloud réduisent les coûts d'acquisition et facilitent les mises à jour. La société norvégienne Glint Solar propose une plateforme d'analyse géographique et technique. L'outil américain Folsom Labs développe HelioScope pour la conception d'installations complexes. Ces solutions internationales ne prennent cependant pas en compte les spécificités du marché français.
Les solutions commerciales présentent une approche généraliste qui limite leur adaptation aux spécificités nationales. La réglementation française de l'autoconsommation collective nécessite des développements spécifiques. Les optimisations fiscales récentes ne sont généralement pas intégrées rapidement. Cette inadaptation crée des opportunités pour des solutions spécialisées sur le marché français.




 Quels besoins non couverts créent des opportunités de différenciation ?

L'identification des besoins non couverts par les solutions existantes révèle plusieurs opportunités significatives. La première concerne l'intégration complète de la chaîne de valeur selon une approche holistique. Aucune solution actuelle ne propose une intégration depuis la prospection géographique jusqu'à la facturation. Cette lacune oblige les développeurs de projets à utiliser multiples outils sans cohérence. L'intégration complète permet une optimisation des processus internes et une réduction des coûts de développement.
La seconde opportunité porte sur la spécialisation française et l'intégration temps réel des évolutions réglementaires. Les récentes modifications du cadre fiscal et réglementaire nécessitent une adaptation rapide. La suppression de l'accise effective depuis mars 2025 illustre cette nécessité d'adaptation. Les outils actuels présentent des délais de mise à jour incompatibles avec la réactivité commerciale. Une solution spécialisée pourrait intégrer automatiquement les évolutions normatives françaises.
La troisième opportunité concerne l'optimisation automatisée des paramètres économiques selon une approche algorithmique. La détermination du prix de vente optimal nécessite une optimisation multi-contraintes complexe. Cette optimisation doit maximiser la rentabilité tout en respectant les contraintes réglementaires. Elle doit également maintenir l'attractivité pour les consommateurs participants. Aucune solution existante ne traite cette problématique d'optimisation de manière satisfaisante.
La quatrième opportunité porte sur l'accessibilité pour les non-spécialistes selon une approche démocratisante. Le développement de l'autoconsommation collective implique une diversification des acteurs. Les collectivités territoriales entrent sur le marché sans expertise technique approfondie. Les PME et particuliers porteurs de projets manquent souvent de compétences spécialisées. Les outils actuels requièrent un niveau de spécialisation élevé constituant une barrière.
La cinquième opportunité concerne la gestion des aspects relationnels spécifiques aux ACC multi-acteurs. Le rapport HAL identifie la nécessité de "générer, dans le temps, de la confiance, de la crédibilité, de la simplicité" pour maintenir l'engagement des participants. Cette dimension relationnelle nécessite des outils de communication adaptés : génération automatisée de rapports personnalisés selon les parties prenantes, tableaux de bord transparents sur les performances individuelles et collectives, et outils de suivi de satisfaction des participants. Les dossiers techniques pour les autorités administratives nécessitent un format spécifique, les présentations commerciales pour les prospects doivent être attractives et simplifiées, les rapports financiers pour les investisseurs exigent un niveau de détail élevé. Cette gestion multidimensionnelle des relations parties prenantes n'est traitée par aucune solution existante.
La sixième opportunité porte sur l'intégration d'outils de prospection et de qualification commerciale géographique. L'identification des opportunités de projets nécessite une analyse territoriale fine. La priorisation des efforts commerciaux selon le potentiel économique optimise les ressources. Cette dimension commerciale en amont n'est pas intégrée dans les outils techniques existants. L'intégration complète faciliterait l'identification et la conversion des prospects qualifiés.

 Quelle approche de développement assure une spécialisation technique durable ?

L'approche de développement retenue pour OptimPV s'appuie sur quatre piliers techniques complémentaires. Cette approche multi-dimensionnelle assure une spécialisation opérationnelle durable selon l'analyse conduite. L'articulation cohérente de ces piliers crée une expertise interne difficilement reproductible.
Le premier pilier concerne l'intégration fonctionnelle complète de la prospection à la facturation. Cette approche répond directement aux besoins exprimés par les professionnels de simplification. L'optimisation des workflows via une interface unique améliore l'efficacité opérationnelle. La réduction du nombre d'outils nécessaires diminue les coûts informatiques et de formation. Cette intégration constitue un avantage concurrentiel difficile à reproduire rapidement.
Le second pilier porte sur la spécialisation française et l'actualisation continue des paramètres normatifs. La plateforme intègre nativement les spécificités du marché français selon une approche dédiée. Les mécanismes de mise à jour automatisée maintiennent la cohérence avec l'évolution réglementaire. Cette spécialisation crée une expertise interne adaptée au contexte français. Elle constitue un avantage opérationnel par rapport aux outils généralistes.
Le troisième pilier concerne l'optimisation algorithmique des paramètres économiques via des fonctionnalités avancées. L'optimisation automatique du prix de vente maximise la rentabilité sous contraintes multiples. Cette capacité d'optimisation différencie OptimPV des approches purement descriptives concurrentes. Elle apporte une valeur ajoutée mesurable et démontrable pour les utilisateurs. Cette sophistication technique constitue un avantage compétitif durable.

Le quatrième pilier porte sur l'accessibilité et l'ergonomie pour démocratiser l'accès aux outils avancés. L'interface est conçue pour être utilisable par des non-spécialistes. Elle conserve simultanément la sophistication technique nécessaire aux experts. Cette dualité vise à accompagner la diversification des acteurs du secteur. Elle facilite l'utilisation interne par des équipes aux compétences techniques variables.
Cette approche de développement s'appuie sur des spécialisations techniques et fonctionnelles adaptées aux besoins internes. L'intégration complète nécessite des développements conséquents et une connaissance approfondie du métier. Cette combinaison d'expertise technique et sectorielle constitue un atout opérationnel durable pour la solution développée.

 Chapitre 2 : Analyse Technico-Économique et Leviers d'Optimisation

 Quels paramètres clés déterminent la performance des projets photovoltaïques ?
L'optimisation technico-économique des projets photovoltaïques nécessite une compréhension fine de l'influence des différents paramètres. Cette analyse de sensibilité permet d'identifier les leviers d'action prioritaires selon leur impact relatif, et l'orientation des efforts d'optimisation vers les variables les plus impactantes améliore l'efficacité des démarches. Par conséquent, cette hiérarchisation guide les stratégies de développement et les choix techniques fondamentaux.
 #### Structure des coûts d'investissement et impact sur la rentabilité

Les coûts d'investissement (CAPEX) constituent le poste le plus significatif dans l'économie des projets photovoltaïques. Ils présentent la plus forte sensibilité sur les indicateurs de rentabilité selon l'analyse financière menée, et l'optimisation de ces coûts représente le levier principal d'amélioration de la performance économique. Cette optimisation nécessite une décomposition précise des différents postes pour identifier les opportunités.
La structure détaillée des coûts d'investissement révèle plusieurs postes aux évolutions différenciées. Les modules photovoltaïques représentent 35% à 45% du CAPEX total selon les technologies retenues. Cette proportion varie selon le type de cellules (silicium monocristallin, polycristallin ou couches minces). Les onduleurs et équipements électriques constituent 12% à 18% de l'investissement initial. La structure porteuse et l'installation représentent 20% à 30% du coût total selon la complexité.
Les raccordements électriques et comptages spécialisés ajoutent 8% à 15% au montant global. Cette variation dépend de la distance au point de raccordement et des spécificités techniques. Les études, développement et frais annexes complètent avec 8% à 12% de l'investissement total. Ces frais incluent les études d'ingénierie, les autorisations administratives et l'accompagnement juridique nécessaire.
L'évolution temporelle de ces coûts suit des trajectoires différenciées selon les composants. L'Agence Internationale de l'Énergie (AIE, 2024) quantifie la baisse des modules à 85% sur la période 2010-2024. Cette réduction massive provient des économies d'échelle dans la production asiatique. L'amélioration des rendements contribue également à cette optimisation par unité de puissance installée.

Les coûts d'installation et de raccordement suivent une évolution moins favorable. Ces postes intègrent principalement de la main-d'œuvre locale aux coûts stables. L'amélioration de la productivité compense partiellement l'inflation des coûts salariaux. Les gains proviennent de la standardisation des procédures et de l'expérience des installateurs.

L'optimisation du CAPEX nécessite une approche globale intégrant tous les postes simultanément. En effet, la recherche du composant le moins cher peut dégrader la performance globale, et l'équilibre entre coût initial et performance long terme guide les choix techniques. Par conséquent, cette optimisation multi-critères justifie l'utilisation d'outils d'aide à la décision spécialisés.

La sensibilité de la rentabilité au CAPEX suit une relation linéaire directe. Ainsi, une réduction de 10% du CAPEX améliore la Valeur Actuelle Nette (VAN) de 15% à 20%. Cette amplification provient de l'effet de levier de l'investissement initial sur l'ensemble des flux, et justifie la priorité accordée à l'optimisation des coûts d'investissement dans les stratégies de développement.

 #### Impact des charges d'exploitation sur la performance long terme

Les charges d'exploitation (OPEX) exercent un impact cumulatif significatif sur la rentabilité long terme, et leur influence s'accroît avec la durée de vie du projet selon un effet d'accumulation. L'optimisation de ces charges constitue un levier de performance souvent sous-estimé, et leur maîtrise conditionne la viabilité économique sur l'ensemble de la période d'exploitation prévue.

La structure des charges d'exploitation intègre plusieurs postes récurrents aux évolutions spécifiques. D'une part, la maintenance préventive et curative représente 1,2% à 1,8% du CAPEX annuellement, cette proportion variant selon la qualité des équipements initiaux et les conditions d'exploitation. D'autre part, l'assurance multirisque ajoute 0,25% à 0,35% du montant de l'investissement par an, les tarifs dépendant de la localisation géographique et des garanties souscrites.

Le contrôle et la surveillance à distance nécessitent 0,15% à 0,25% du CAPEX annuellement. Ces coûts incluent les systèmes de monitoring et l'abonnement aux services de supervision. La gestion administrative et commerciale représente 1,5% à 3,5% du chiffre d'affaires selon la complexité. Cette variabilité dépend du nombre de participants et des modalités de facturation retenues.

Les charges spécifiques à l'autoconsommation collective majorent ces coûts de base significativement. La gestion de la Personne Morale Organisatrice (PMO) nécessite des compétences juridiques spécialisées. La facturation individuelle aux participants génère des coûts administratifs proportionnels au nombre. La gestion des clés de répartition et le suivi des consommations complexifient les processus. Ces surcoûts représentent 4% à 8% des charges d'exploitation totales selon la taille.

L'évolution temporelle des charges d'exploitation suit généralement l'inflation générale. Certains postes présentent des dynamiques spécifiques selon leur nature. Les coûts de maintenance tendent à augmenter avec l'âge des équipements. Les charges administratives peuvent bénéficier d'économies d'échelle avec la croissance. L'automatisation des processus réduit progressivement les coûts de gestion humaine.

L'optimisation des OPEX passe par plusieurs leviers d'action complémentaires. La mutualisation des coûts de gestion entre projets permet des économies d'échelle substantielles. L'automatisation des processus administratifs réduit les charges de personnel dédiées. L'utilisation d'outils logiciels spécialisés améliore l'efficacité opérationnelle. La contractualisation de maintenance globale optimise les coûts techniques.

La sensibilité de la rentabilité aux OPEX présente un effet cumulatif sur la durée. Une réduction de 10% des OPEX améliore la VAN de 8% à 12%. Cette amélioration varie selon la durée de vie considérée et le taux d'actualisation. L'effet s'amplifie avec l'allongement de la durée d'exploitation prévue.

 Quel rôle jouent la dégradation et la performance technique dans l'équation économique ?

La dégradation des équipements photovoltaïques influence directement la production énergétique sur la durée. Cette dégradation suit des lois physiques établies selon les technologies utilisées. Son impact économique nécessite une modélisation précise pour l'évaluation de rentabilité. Cette modélisation guide les choix technologiques et les stratégies de maintenance préventive.

Les modules photovoltaïques présentent une dégradation annuelle moyenne de 0,5% à 0,8% selon les technologies. Le silicium monocristallin affiche une dégradation inférieure à 0,6% par an généralement. Le silicium polycristallin présente une dégradation de 0,6% à 0,8% annuellement. Les technologies couches minces peuvent atteindre 0,8% à 1,2% selon les conditions d'exploitation. Cette variabilité influence le choix technologique selon l'horizon d'investissement.

Les onduleurs présentent une durée de vie généralement inférieure aux modules photovoltaïques. Leur remplacement intervient typiquement après 12 à 15 ans d'exploitation. Ce remplacement représente un coût significatif à provisionner dans l'analyse économique. Les onduleurs string nécessitent un remplacement complet généralement. Les micro-onduleurs permettent un remplacement unitaire réduisant les coûts ponctuels.
La performance technique globale dépend également des conditions d'exploitation et de maintenance. L'encrassement des modules réduit la performance de 2% à 8% selon l'environnement. Le nettoyage régulier maintient la performance optimale mais génère des coûts. L'ombrage partiel dégrade significativement la production selon la technologie d'onduleur. Ces facteurs environnementaux influencent la performance prévisionnelle.
L'évolution technologique améliore continuellement les performances et la durabilité des équipements. Les garanties constructeurs s'étendent désormais sur 25 ans pour les modules. Cette extension améliore la sécurité financière des projets long terme. Elle permet d'envisager des durées d'amortissement allongées améliorant la rentabilité.
La modélisation de la dégradation nécessite une approche probabiliste intégrant les incertitudes. Les conditions climatiques locales influencent les taux de dégradation observés. L'exposition aux UV, les variations de température et l'humidité accélèrent le vieillissement. Cette variabilité géographique justifie l'utilisation de bases de données climatiques précises.
L'impact économique de la dégradation s'évalue via la perte de revenus cumulée. Une dégradation de 0,5% par an représente une perte de 10% de production sur 20 ans. Cette perte influence directement les revenus et donc la rentabilité du projet. Une modélisation précise de cette dégradation améliore la fiabilité des prévisions financières.
L'optimisation de la performance technique passe par plusieurs leviers identifiés. Le choix de composants de qualité supérieure réduit la dégradation long terme. La maintenance préventive préserve la performance optimale dans la durée. La surveillance continue permet la détection précoce des dysfonctionnements. Ces investissements en qualité et maintenance s'amortissent via l'amélioration de performance.
 #### Évolution des prix de l'électricité et viabilité économique

L'évolution des prix de l'électricité constitue un paramètre externe majeur influençant la rentabilité. Cette évolution détermine la compétitivité de l'autoconsommation face aux tarifs réglementés. Son caractère imprévisible nécessite une analyse de sensibilité et de scénarios multiples. Cette analyse guide les stratégies de couverture du risque prix.
Les tarifs réglementés de vente évoluent selon plusieurs facteurs structurels et conjoncturels. L'évolution des coûts de production de l'électricité influence les tarifs de base. Les investissements dans les réseaux de transport et distribution répercutent leurs coûts. Les taxes et contributions évoluent selon les politiques publiques énergétiques. Cette multifactorialité complexifie la prévision des évolutions tarifaires.
L'analyse historique révèle une tendance haussière des tarifs réglementés sur la période 2010-2024. La Commission de Régulation de l'Énergie (CRE, 2024) quantifie cette augmentation à 4,2% par an en moyenne. Cette progression dépasse l'inflation générale de 1,8 point annuellement. Elle améliore mécaniquement la compétitivité de l'autoconsommation collective selon l'effet de ciseaux.

La récente volatilité des marchés énergétiques européens amplifie l'incertitude sur les évolutions futures. La crise énergétique de 2022-2023 a démontré l'exposition aux chocs externes. Les mécanismes de bouclier tarifaire limitent temporairement la répercussion sur les consommateurs. Ces mécanismes créent cependant une dette publique différant les ajustements tarifaires.
L'impact de l'évolution des prix sur la rentabilité de l'autoconsommation suit une relation directe. Une augmentation de 1% des tarifs réglementés améliore la VAN de 1,5% à 2,5%. Cette amplification provient de l'effet sur l'ensemble des flux de revenus futurs. Elle justifie l'intérêt économique de l'autoconsommation dans un contexte haussier.
La modélisation de cette évolution nécessite l'élaboration de scénarios contrastés selon les hypothèses macroéconomiques. Un scénario conservateur table sur une progression de 2,5% par an. Un scénario médian prévoit une augmentation de 3,5% annuellement. Un scénario volontariste anticipe une hausse de 4,5% par an. Cette approche par scénarios encadre l'incertitude et guide la prise de décision.
L'optimisation face à cette incertitude passe par plusieurs stratégies de gestion du risque. La diversification des revenus entre autoconsommation et vente réseau réduit l'exposition. Les contrats d'achat long terme sécurisent une partie des revenus futurs. L'indexation des prix de vente aux participants limite le risque de change. Ces mécanismes de couverture améliorent la prévisibilité des flux financiers.
La sensibilité différentielle selon les projets guide les stratégies d'adaptation spécifiques. Les projets à fort taux d'autoconsommation bénéficient davantage des hausses tarifaires. Les projets orientés vente réseau sont moins sensibles à cette évolution. Cette différenciation influence les choix de dimensionnement et de développement selon les anticipations.
La surveillance continue de ces évolutions constitue un facteur clé de gestion opérationnelle. Les outils d'aide à la décision doivent intégrer cette variabilité en temps réel. L'adaptation des stratégies commerciales selon les évolutions observées optimise la performance. Cette réactivité constitue un avantage concurrentiel pour les acteurs bien équipés.

 #### Prix de vente et enjeu central de rentabilité

La détermination du prix de vente de l'électricité aux participants constitue l'enjeu central de rentabilité. Ce paramètre doit équilibrer viabilité économique du projet et attractivité pour les consommateurs. Cette optimisation multi-contraintes nécessite une approche méthodologique rigoureuse. Elle conditionne le succès commercial et la performance financière des projets développés.

 #### Positionnement par rapport aux tarifs réglementés

Le positionnement tarifaire par rapport aux tarifs réglementés détermine l'attractivité commerciale du projet, et cette attractivité conditionne la capacité de recrutement des participants nécessaires. Le positionnement doit créer une valeur perçue suffisante tout en préservant la marge. Par conséquent, cette équation complexe nécessite une analyse fine des composantes tarifaires et des perceptions clients.
Le Tarif Réglementé de Vente (TRV) résidentiel constitue la référence concurrentielle principale. Il s'établit à 25,16 c€/kWh toutes taxes comprises en 2025 selon la CRE. Ce tarif intègre l'ensemble des composantes réglementaires et fiscales applicables. Sa décomposition révèle la structure des coûts supportés par les consommateurs. Cette analyse guide le positionnement concurrentiel optimal.

La décomposition du TRV révèle plusieurs composantes aux évolutions différenciées. L'énergie représente 35% du tarif total selon les dernières analyses. Les réseaux de transport et distribution constituent 30% du montant facturé. Les taxes et contributions publiques ajoutent 35% au coût final. Cette répartition évolue selon les politiques énergétiques et les besoins d'investissement réseau.
Le positionnement optimal vise généralement une décote de 10% à 25% par rapport au TRV. Cette décote assure une attractivité suffisante pour motiver l'adhésion des participants. Elle préserve simultanément une marge permettant la viabilité du projet développé. La décote exacte dépend de la stratégie commerciale et de la concurrence locale.
L'évolution différentielle entre coûts de production et TRV crée des opportunités d'optimisation. D'une part, la baisse des coûts photovoltaïques améliore mécaniquement les marges possibles, et d'autre part, l'augmentation des tarifs réglementés élargit l'espace de positionnement commercial. Cette dynamique favorable structure l'attractivité croissante de l'autoconsommation collective.
La segmentation de la clientèle influence le positionnement tarifaire selon les sensibilités prix. Ainsi, les particuliers privilégient souvent la simplicité sur l'optimisation maximale des coûts, tandis que les entreprises analysent plus finement l'équation économique proposée. Par ailleurs, les collectivités intègrent des critères environnementaux et sociaux dans leur évaluation. Cette segmentation guide l'adaptation de l'offre et du positionnement.
L'analyse de la concurrence locale affine le positionnement selon l'environnement concurrentiel. Les offres d'électricité verte des fournisseurs alternatifs constituent une référence. Leur positionnement tarifaire influence la perception de valeur des consommateurs. La différenciation par l'origine locale de la production crée une valeur ajoutée spécifique.
La communication du positionnement nécessite une pédagogie adaptée aux différents publics. La mise en évidence des économies réalisées facilite la compréhension de l'intérêt. La démonstration de l'impact environnemental renforce l'attractivité pour les consommateurs sensibilisés. Cette communication influence l'acceptation du positionnement proposé.

 Quels mécanismes d'optimisation algorithmique peuvent maximiser la rentabilité ?

L'optimisation algorithmique du prix de vente permet de maximiser la rentabilité sous contraintes multiples. Cette approche dépasse l'intuition pour identifier mathématiquement les configurations optimales, et intègre simultanément les contraintes techniques, économiques et commerciales du projet. Par conséquent, cette sophistication améliore significativement la performance par rapport aux approches manuelles.
La formalisation mathématique du problème d'optimisation intègre plusieurs variables et contraintes identifiées. La fonction objectif vise à maximiser la Valeur Actuelle Nette (VAN) du projet. Les variables de décision incluent le prix de vente, le dimensionnement et la répartition. Les contraintes portent sur l'attractivité commerciale, la réglementation et la faisabilité technique.
L'algorithme d'optimisation explore l'espace des solutions selon une méthode heuristique performante. Les algorithmes génétiques permettent l'exploration de solutions complexes non-linéaires. Les méthodes de gradient optimisent localement les solutions identifiées. L'hybridation de ces approches améliore la robustesse et la rapidité de convergence.

La modélisation de l'attractivité commerciale intègre des fonctions de demande selon les segments. La sensibilité prix varie selon le type de participant et sa situation énergétique. Les particuliers présentent une élasticité-prix modérée selon les études comportementales. Les entreprises affichent une sensibilité plus élevée selon leurs contraintes de compétitivité.
L'intégration des contraintes réglementaires limite l'espace d'optimisation selon les règles applicables. Le prix de vente ne peut dépasser le tarif réglementé selon la réglementation. Il doit couvrir les coûts de production pour assurer la viabilité. Ces contraintes bornent l'optimisation et garantissent la conformité réglementaire.
L'optimisation multi-objectifs intègre des critères autres que la rentabilité financière pure. L'impact environnemental peut être intégré via des coefficients de pondération. L'acceptabilité sociale influence les choix selon les contextes territoriaux. Cette approche élargie améliore la robustesse des solutions dans la durée.
La validation des solutions optimisées nécessite des tests de sensibilité aux paramètres incertains. Les variations des coûts d'investissement testent la robustesse des configurations. L'évolution des tarifs réglementés évalue la stabilité des solutions. Cette validation améliore la confiance dans les recommandations algorithmiques.
L'implémentation opérationnelle de l'optimisation nécessite des interfaces utilisateur adaptées. La complexité algorithmique doit être masquée aux utilisateurs non-experts. Les résultats doivent être présentés de manière pédagogique et actionnable. Cette ergonomie conditionne l'adoption et l'utilisation effective des outils développés.

 #### Intégration des spécificités du marché français

L'intégration des spécificités françaises dans l'optimisation nécessite une connaissance approfondie du contexte réglementaire. Ces spécificités influencent directement les contraintes et opportunités d'optimisation applicables. Leur prise en compte différencie les solutions locales des approches internationales généralistes. Cette spécialisation constitue un avantage concurrentiel pour les outils dédiés au marché français.
La réglementation française de l'autoconsommation collective impose des contraintes spécifiques d'optimisation. Le périmètre géographique limite les participants selon des règles de proximité. Les seuils de puissance bornent la taille des projets selon les catégories réglementaires. Ces contraintes doivent être intégrées comme conditions impératives dans l'optimisation.
La fiscalité française présente des spécificités impactant directement l'équation économique d'optimisation. La suppression récente de l'accise modifie les équilibres selon une évolution majeure. La TVA à taux réduit pour certaines installations influence les coûts. Ces paramètres fiscaux doivent être actualisés en temps réel pour maintenir la pertinence.
Les tarifs réglementés français suivent une structure tarifaire spécifique selon les segments de clientèle. Les tarifs résidentiels intègrent une progressivité selon les niveaux de consommation. Les tarifs professionnels différencient puissance souscrite et énergie consommée. Cette complexité tarifaire nécessite une modélisation précise pour l'optimisation.

L'écosystème d'acteurs français influence les contraintes commerciales et techniques applicables. Enedis structure l'interface technique avec des procédures standardisées nationales. EDF obligation d'achat définit les conditions de valorisation du surplus. Ces contraintes institutionnelles bornent l'espace d'optimisation selon les règles nationales.
Les profils de consommation français présentent des caractéristiques culturelles et climatiques spécifiques. La saisonnalité de la consommation électrique suit les variations climatiques nationales. Les habitudes de consommation diffèrent selon les régions et les types d'habitat. Cette variabilité doit être intégrée dans la modélisation d'optimisation.
La prise en compte de l'évolution réglementaire future améliore la robustesse de l'optimisation. Les projets de modification du cadre législatif influencent les anticipations. L'harmonisation européenne des réglementations peut modifier les contraintes nationales. Cette prospective réglementaire guide les choix d'optimisation long terme.
L'adaptation culturelle de l'optimisation facilite l'acceptation par les utilisateurs français. La terminologie technique doit respecter les usages professionnels nationaux. Les unités et conventions de calcul suivent les standards français établis. Cette adaptation améliore la compréhension et l'adoption des outils développés.

 Quelle synthèse des besoins guide la définition du cahier des charges fonctionnel ?

L'analyse technico-économique conduite révèle des besoins structurants pour l'optimisation des projets d'autoconsommation collective. Cette analyse guide la définition d'un cahier des charges fonctionnel intégrant l'ensemble des contraintes identifiées. La synthèse de ces besoins oriente la conception d'un outil d'aide à la décision adapté. Cette synthèse assure la cohérence entre analyse préliminaire et spécifications techniques futures.

 Quels besoins fonctionnels prioritaires structurent les exigences utilisateurs ?

L'identification des besoins fonctionnels prioritaires résulte de l'analyse des contraintes et opportunités sectorielles. Ces besoins structurent les exigences utilisateurs selon une hiérarchisation de l'importance opérationnelle. Leur satisfaction conditionne l'adoption et l'utilisation effective des outils développés. Cette priorisation guide l'allocation des ressources de développement selon la valeur ajoutée.
Le premier besoin fonctionnel concerne l'optimisation automatisée des paramètres technico-économiques selon une approche intégrée. Cette optimisation doit déterminer le dimensionnement optimal des installations selon les contraintes locales. Elle doit calculer le prix de vente maximisant la rentabilité sous contraintes réglementaires. Cette automatisation libère les utilisateurs des calculs complexes et améliore la qualité des analyses.
Le deuxième besoin porte sur la modélisation financière avancée intégrant les spécificités françaises. Cette modélisation doit calculer les indicateurs de rentabilité standards selon les méthodes reconnues. Elle doit intégrer la fiscalité française dans ses évolutions récentes. La génération de scenarios multiples doit faciliter l'analyse de sensibilité. Cette sophistication financière répond aux exigences des investisseurs et financeurs.

Le troisième besoin concerne l'actualisation continue des paramètres réglementaires et fiscaux français. Cette actualisation doit intégrer automatiquement les évolutions normatives impactant les projets. Elle doit maintenir la cohérence des calculs avec le cadre légal applicable. Cette fiabilité réglementaire conditionne la qualité juridique des analyses produites. Elle constitue un facteur critique de confiance pour les utilisateurs professionnels.
Le quatrième besoin porte sur la génération automatisée de rapports professionnels adaptés aux différents publics. Ces rapports doivent répondre aux attentes des investisseurs selon les standards financiers. Ils doivent faciliter les présentations commerciales auprès des prospects. La documentation technique doit respecter les exigences administratives. Cette diversification des livrables répond à la multiplicité des parties prenantes impliquées.
Le cinquième besoin concerne l'intégration d'outils de prospection et de qualification commerciale territoriale. Ces outils doivent identifier les opportunités de projets selon les critères techniques et économiques. Ils doivent prioriser les efforts commerciaux selon le potentiel de rentabilité. Cette dimension commerciale amont optimise l'allocation des ressources de développement. Elle améliore la performance commerciale des porteurs de projets.
La satisfaction de ces besoins fonctionnels nécessite une architecture logicielle modulaire et évolutive. Chaque besoin correspond à un module spécialisé aux interfaces définies. L'intégration entre modules assure la cohérence d'ensemble selon une approche systémique. Cette modularité facilite la maintenance et l'évolution future selon les besoins émergents.

 Quelles exigences techniques et architecturales découlent de l'analyse fonctionnelle ?

Les exigences techniques dérivées de l'analyse fonctionnelle imposent des contraintes d'architecture significatives. Ces contraintes visent à assurer la performance, la fiabilité et l'évolutivité de la solution, et l'architecture technique doit supporter la complexité fonctionnelle tout en maintenant l'utilisabilité. Par conséquent, cette conception constitue un enjeu critique pour le succès opérationnel de la plateforme.
L'exigence de performance nécessite une architecture optimisée pour les calculs d'optimisation complexes. En effet, les algorithmes d'optimisation multi-contraintes nécessitent une puissance de calcul importante, et l'objectif de temps de réponse inférieur à 10 secondes guide les choix techniques. Cette performance conditionne l'acceptabilité pour un usage interactif en contexte professionnel.
L'exigence de fiabilité impose la mise en œuvre de mécanismes de validation robustes. La validation des données d'entrée doit détecter les erreurs et incohérences. La vérification de cohérence des résultats doit identifier les anomalies de calcul. La traçabilité des calculs doit permettre l'audit et la justification des résultats. Cette fiabilité est critique dans un contexte professionnel engageant la responsabilité.
L'exigence d'évolutivité nécessite une architecture modulaire facilitant les modifications futures. L'ajout de nouvelles fonctionnalités doit être possible sans remise en cause de l'existant. Cette modularité doit également faciliter l'adaptation aux évolutions réglementaires françaises. L'isolation des paramètres normatifs dans des modules spécialisés facilite cette adaptation.
L'exigence d'interopérabilité impose la capacité d'échange avec les systèmes d'information existants. L'import de données clients depuis les systèmes Customer Relationship Management (CRM) doit être facilité. L'export de résultats vers les outils de reporting externes doit être standardisé. Cette interopérabilité améliore l'intégration dans les workflows professionnels établis.

L'exigence de sécurité protège les données sensibles des utilisateurs selon les standards requis. La protection des données personnelles doit respecter le Règlement Général sur la Protection des Données (RGPD). L'authentification et l'autorisation doivent contrôler l'accès selon les profils utilisateurs. Cette sécurité conditionne la confiance et l'adoption par les utilisateurs professionnels.
L'exigence de scalabilité permet l'adaptation à la croissance du nombre d'utilisateurs. L'architecture doit supporter l'augmentation des charges sans dégradation des performances. Cette scalabilité facilite le déploiement interne et l'utilisation simultanée par plusieurs équipes. Elle conditionne l'efficacité opérationnelle de la plateforme dans un contexte de croissance.
L'implémentation de ces exigences nécessite des choix technologiques adaptés aux contraintes identifiées. Les technologies cloud facilitent la scalabilité et la maintenance centralisée. Les bases de données performantes supportent les calculs complexes d'optimisation. Cette sélection technologique influence directement la capacité à satisfaire les exigences techniques.

 #### Spécifications d'ergonomie et diversification des acteurs

La diversification des acteurs de l'autoconsommation collective impose des exigences d'ergonomie renforcées. Cette diversification inclut des utilisateurs aux niveaux d'expertise variables selon leur origine professionnelle, et l'accessibilité de la solution aux non-spécialistes devient un facteur critique d'adoption. Cette accessibilité doit préserver la sophistication technique nécessaire aux experts selon une approche équilibrée.
La conception d'interfaces adaptées aux différents profils utilisateurs nécessite une segmentation fine des besoins. Les experts techniques requièrent un accès complet aux paramètres et réglages avancés. Les commerciaux privilégient la rapidité d'utilisation et la clarté des résultats. Les décideurs demandent des synthèses exécutives et des visualisations impactantes. Cette segmentation guide la conception d'interfaces spécialisées selon les rôles.
L'approche progressive de complexité facilite l'apprentissage pour les utilisateurs novices. Les fonctionnalités de base doivent être accessibles sans formation approfondie selon une approche intuitive. Les fonctionnalités avancées restent disponibles pour les utilisateurs expérimentés. Cette progressivité évite l'effet de rejet tout en préservant la richesse fonctionnelle.
La personnalisation de l'interface selon les préférences utilisateurs améliore l'ergonomie d'usage. Les tableaux de bord doivent être configurables selon les indicateurs prioritaires. Les rapports doivent être adaptables selon les besoins de communication spécifiques. Cette personnalisation améliore l'efficacité d'utilisation et l'appropriation de l'outil.
L'aide contextuelle intégrée facilite l'apprentissage et l'utilisation autonome de la plateforme. Cette aide doit expliquer les concepts techniques aux non-spécialistes selon une approche pédagogique. Elle doit guider les utilisateurs dans les processus complexes d'optimisation. Cette assistance améliore l'autonomie d'utilisation et réduit les besoins de formation externe.
La validation utilisateur avant finalisation assure l'adéquation ergonomique aux besoins réels. Cette validation doit impliquer des représentants de chaque profil d'utilisateur identifié. Elle doit tester l'utilisabilité dans des conditions d'usage réelles. Cette validation itérative améliore la qualité ergonomique et l'acceptation finale.

La gestion des droits d'accès doit permettre une granularité fine d'adaptation organisationnelle. Cette gestion doit s'adapter aux différentes structures depuis les travailleurs indépendants jusqu'aux grandes entreprises. Elle doit permettre le cloisonnement interne selon les besoins de confidentialité. Cette flexibilité facilite l'adoption par des organisations aux structures variées.
Cette synthèse des besoins constitue le socle conceptuel pour la conception de la plateforme OptimPV. Elle assure la cohérence entre l'analyse stratégique du secteur et les choix de développement technologique, et cette cohérence garantit l'adéquation de la solution aux enjeux réels du marché français.

## Questionnements critiques et enjeux de validation à résoudre

L'analyse conduite révèle cependant des interrogations majeures qui devront être traitées dans la validation opérationnelle d'OptimPV. Ces questionnements, issus de l'observation terrain des opérations d'ACC existantes, constituent autant de défis à relever pour démontrer la pertinence de l'approche développée.

### La problématique des coûts de transaction spécifiques aux ACC multi-acteurs

L'étude approfondie des opérations multi-acteurs révèle que "l'ACC nécessite des formes d'intermédiation assez développées, qui génèrent des coûts de transaction propres, d'un montant plus ou moins élevé" correspondant aux "différentes tâches que la PMO doit effectuer, notamment autour du traitement des données" (rapport HAL, 2022). Contrairement aux ACC patrimoniales où ces coûts sont internalisés par la collectivité, les ACC multi-acteurs supportent des coûts d'intermédiation externes significatifs : négociation commerciale, gestion des relations multi-parties, optimisation des paramètres économiques, et production de rapports différenciés selon les parties prenantes.

**Question critique pour la partie 3 :** Comment OptimPV peut-il justifier sa valeur ajoutée spécifiquement pour les ACC multi-acteurs face à ces coûts de transaction élevés ? L'automatisation des tâches de modélisation et d'optimisation peut-elle réellement réduire ces coûts d'intermédiation ou libérer du temps pour les aspects relationnels à plus forte valeur ajoutée ?

### Le décalage d'échelle entre sophistication technique et réalité de terrain

Les données du marché révèlent une moyenne de 11 consommateurs par opération d'ACC toutes catégories confondues (1150 consommateurs pour 102 opérations). Cependant, cette moyenne masque des réalités très différentes : les ACC patrimoniales ont souvent moins de 5 consommateurs (sites municipaux), tandis que les ACC multi-acteurs peuvent atteindre 20 à 50 consommateurs, justifiant des outils d'optimisation plus sophistiqués. Les retours terrain sur les opérations multi-acteurs montrent des difficultés spécifiques à la gestion commerciale et à l'optimisation économique.

**Question critique pour la partie 3 :** Comment démontrer que le ROI d'OptimPV est positif sur un portefeuille d'ACC multi-acteurs, compte tenu de leur taille plus importante et de leurs enjeux d'optimisation spécifiques ? L'automatisation des tâches complexes de modélisation et d'optimisation justifie-t-elle l'investissement en développement interne ?

### Le hiatus entre motivations financières et motivations territoriales réelles

L'analyse des motivations révèle une différenciation claire selon le type d'opération. Les ACC patrimoniales privilégient l'"exemplarité territoriale" et l'"efficacité énergétique comme fil conducteur". En revanche, les ACC multi-acteurs, développées par des acteurs privés, intègrent nécessairement des objectifs de rentabilité financière tout en répondant aux attentes territoriales des participants.

**Question critique pour la partie 3 :** Comment OptimPV peut-il intégrer les dimensions territoriales et sociales dans ses algorithmes d'optimisation pour les ACC multi-acteurs ? L'approche centrée sur l'optimisation de la VAN et du TRI peut-elle être enrichie de critères non-financiers pour mieux correspondre aux attentes des participants ?

### La viabilité économique du modèle OptimPV sur un marché de niche

Le marché français des ACC multi-acteurs représente environ 33% des 102 opérations actives fin 2022, soit approximativement 34 opérations. Avec une croissance projetée du secteur, ce segment pourrait atteindre 100 à 200 opérations d'ici 2030, créant un marché suffisant pour justifier des outils spécialisés.

**Question critique pour la partie 3 :** Comment démontrer que le développement d'OptimPV est rentable pour un portefeuille de 10 à 20 ACC multi-acteurs sur 5 ans ? L'amortissement des coûts de développement sur ce volume d'opérations justifie-t-il l'investissement par rapport à des solutions externes ou des approches manuelles ?

### L'inadéquation entre complexité algorithmique et besoins opérationnels réels

Les difficultés identifiées varient selon le type d'ACC. Pour les ACC patrimoniales, elles concernent principalement le "manque de main d'œuvre locale" et la "méconnaissance du dispositif". Pour les ACC multi-acteurs, les défis portent davantage sur l'optimisation technico-économique, la structuration financière, la négociation multi-parties, et la production de reportings différenciés selon les parties prenantes.

**Question critique pour la partie 3 :** Les fonctionnalités avancées d'OptimPV (algorithmes génétiques, optimisation multi-contraintes) répondent-elles spécifiquement aux besoins des ACC multi-acteurs ou constituent-elles de la sophistication excessive ? Comment démontrer que l'automatisation de l'optimisation technico-économique génère une valeur supérieure aux approches manuelles pour ce segment spécifique ?

Ces questionnements critiques constituent le fil conducteur de la validation empirique présentée en partie 3. Ils orientent l'approche méthodologique retenue et guident l'évaluation de la valeur ajoutée réelle d'OptimPV dans le contexte spécifique des ACC multi-acteurs.

Par conséquent, ils déterminent les critères de succès et les métriques d'évaluation qui permettront de démontrer - ou d'infirmer - la pertinence de l'approche développée face aux enjeux réels de ce segment de marché spécialisé.


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

Python avec Pandas permet la vectorisation native des calculs ACC, divisant par 10 les temps de calcul grâce aux opérations matricielles optimisées. De plus, la gestion native des DataFrames multi-indexés permet de traiter simultanément les données temporelles, les profils participants et les métriques financières dans une structure unifiée. Par ailleurs, l'intégration transparente avec les APIs (PVGIS, Cadastre, DPE) automatise la collecte de données sans risque d'erreur de transcription. Enfin, la parallélisation native des simulations Monte Carlo divise par 10 les temps de calcul.

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

L'optimisation algorithmique d'OptimPV identifie systématiquement une zone d'équilibre entre 12 et 13 c€/kWh HT où la probabilité d'acceptation client et la rentabilité projet sont simultanément maximisées. En dessous de 12 c€/kWh HT, la marge devient insuffisante avec un TRI inférieur à 6%, rendant le projet non finançable. Au-dessus de 13 c€/kWh HT, le gain consommateur devient insuffisant (moins de 25% vs tarif EDF), générant un taux de refus supérieur à 40%.

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

La gestion de trésorerie optimisée nécessite une granularité temporelle adaptée. La complexité de la granularité mensuelle versus annuelle s'explique par les exigences spécifiques de La modélisation financière photovoltaïque exige une granularité mensuelle sur 240 périodes. Pourquoi ? D'abord, la production varie fortement selon les saisons avec un ratio été/hiver de 3 pour 1. Ensuite, les panneaux se dégradent de 0,5% par an nécessitant un ajustement mensuel. De plus, les banques imposent des remboursements mensuels avec intérêts sur capital restant dû. La TVA se déclare mensuellement avec des délais de récupération spécifiques. Enfin, la trésorerie doit rester positive chaque mois pour éviter les découverts coûteux. Le débogage de ces flux de trésorerie a nécessité plusieurs semaines d'analyse approfondie. Chaque interdépendance cachait des pièges comme les décalages TVA, la saisonnalité de production et le timing des facturations.

La nécessité d'une granularité mensuelle conduit à structurer deux piliers comptables interconnectés. OptimPV génère deux tableaux financiers complémentaires sur 240 mois. Pourquoi deux tableaux distincts ? Ils répondent à deux questions vitales différentes.

- **Compte de résultat mensuel** : Répond à "Le projet est-il rentable ?" Suit la rentabilité comptable avec revenus (vente d'énergie, prime ACC sur 5 ans), charges d'exploitation (maintenance 606€/an, assurance 303€/an, gestion 505€/an), charges financières (intérêts décroissants), amortissements linéaires sur 20 ans. Résultat : vision comptable de la performance avec résultat net après IS. Les banques exigent ce tableau pour valider la viabilité économique.

- **Tableau de flux de trésorerie** : Répond à "Y aura-t-il assez de liquidités chaque mois ?" Traduit la rentabilité en cash disponible. Intègre les flux opérationnels (résultat net + amortissements - variation BFR avec créances 30 jours), flux d'investissement (CAPEX initial, remplacement onduleur année 10), flux de financement (apports, remboursements mensuels). Résultat : trésorerie réelle disponible chaque mois. Les banques scrutent ce tableau pour détecter tout risque de découvert.

Ces deux visions sont cruciales. En effet, un projet peut afficher un bénéfice comptable tout en manquant de liquidités. Le plan de financement (capital restant dû, DSCR) et le BFR sont intégrés dans ces tableaux, pas séparés. Cette double approche évite les pièges classiques où la rentabilité cache une crise de trésorerie.

Cette double approche répond aux exigences spécifiques des financeurs bancaires. Au-delà de ces deux tableaux, les banques imposent une complexité supplémentaire. Elles exigent simultanément un **tableau annuel agrégé** (20 lignes) pour vérifier les covenants bancaires comme le DSCR, ET un **tableau mensuel détaillé** (240 lignes) pour s'assurer qu'aucun découvert n'apparaît en cours d'année. L'agrégation mensuel→annuel devient alors un casse-tête technique car certains éléments s'additionnent (CA, charges via `resample('Y').sum()`), d'autres se moyennent (ratios DSCR), et d'autres prennent la valeur finale (capital restant dû). Le calcul du DSCR annuel suit la formule bancaire standard $DSCR_{annuel} = \frac{EBITDA_{annuel} - IS_{payé}}{Service_{dette}}$, avec gestion des cas limites (division par zéro si remboursement anticipé). Cette double comptabilité, impossible à gérer correctement dans Excel, justifie l'architecture sophistiquée d'OptimPV qui maintient automatiquement la cohérence entre les deux niveaux de granularité.

Le défi majeur réside dans le maintien de la cohérence inter-tableaux sur 240 mois. Maintenir la cohérence entre compte de résultat et flux de trésorerie sur 240 périodes constitue un défi algorithmique majeur. Chaque modification déclenche des cascades de recalculs. Modifier le taux d'intérêt impacte les charges financières, les remboursements, le DSCR et l'IS. Une erreur d'arrondi au mois 1 peut créer des milliers d'euros d'écart au mois 240. L'analyse a révélé des bugs subtils où les arrondis TVA créaient 0,01€ d'écart mensuel, cumulant 2,40€ sur 20 ans. Insignifiant ? Les auditeurs bancaires rejettent tout écart. 

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

**Explication pédagogique des simulations Monte Carlo avec distributions gaussiennes :**

Les simulations Monte Carlo testent la robustesse du projet face aux incertitudes. Le principe : répéter 1000 fois le calcul en faisant varier aléatoirement les paramètres critiques (production, consommation, OPEX) selon des **distributions gaussiennes** (courbe en cloche).

Une distribution gaussienne $\mathcal{N}(\mu, \sigma)$ signifie que :
- 68% des valeurs tombent entre μ-σ et μ+σ (±1 écart-type)
- 95% entre μ-2σ et μ+2σ (±2 écarts-types)
- 99,7% entre μ-3σ et μ+3σ (±3 écarts-types)

Exemple concret : Production annuelle moyenne μ = 100 000 kWh, écart-type σ = 5 000 kWh
- 68% des simulations : production entre 95 000 et 105 000 kWh
- 95% des simulations : production entre 90 000 et 110 000 kWh
- Cas extrêmes (0,3%) : production < 85 000 ou > 115 000 kWh

**Limitation importante :** Les distributions gaussiennes sous-estiment les événements extrêmes (queues de distribution). En réalité, les risques majeurs (défaillance onduleur, grêle destructrice, faillite participant) suivent plutôt des lois à queues épaisses (Pareto, log-normale). Le modèle gaussien peut donc sous-estimer le risque réel.

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

**Résultat :** Solution efficace pour 0€ de licence vs solutions commerciales coûteuses offrant des performances similaires pour ce type de problème. OptimPV privilégie l'open-source (pas de dépendance commerciale), la suffisance (L-BFGS-B résout la grande majorité des cas), et l'efficacité économique pour un outil interne de R&D.

#### L'innovation par l'intégration systémique plutôt que l'invention

**Redéfinir l'innovation en ingénierie énergétique :** OptimPV ne prétend pas révolutionner les mathématiques de l'optimisation mais démontrer que l'innovation en ingénierie énergétique réside dans l'intégration intelligente de composants existants pour résoudre un problème industriel non adressé. L'assemblage de l'algorithme de Brent (1973), L-BFGS-B (1989), APIs publiques françaises et Streamlit crée une synergie unique spécifiquement adaptée aux contraintes de l'ACC française.

Cette approche d'innovation par intégration génère une valeur supérieure à la somme des composants individuels. La barrière à l'entrée principale réside dans la nécessité de comprendre simultanément la fiscalité française BIC, les mécanismes TURPE avec leurs seuils, l'optimisation non-linéaire sous contraintes multiples et les workflows spécifiques de l'ACC, ce qui nécessite une expertise transversale approfondie. OptimPV encode cette expertise dans un système automatisé, transformant un savoir tacite dispersé en processus explicite reproductible.

L'absence de solution commerciale satisfaisante pour le marché ACC français démontre que le défi n'est pas l'invention de nouveaux algorithmes mais l'orchestration cohérente de technologies existantes. Cette orchestration nécessite une compréhension profonde du domaine métier que les éditeurs généralistes internationaux ne possèdent pas et que les acteurs français n'ont pas jugé prioritaire de développer pour un marché encore émergent.

**Problèmes critiques découverts en production :** Le développement d'OptimPV a révélé des pièges algorithmiques inattendus. Le plus sournois concernait les projets à fort levier (90% dette). L'optimiseur convergeait vers des prix absurdes (25 c€/kWh HT) car il maximisait la VAN equity sur une base quasi-nulle (1000€ de fonds propres). Solution : détection automatique des cas d'equity < 1000€ et bascule sur VAN projet comme fonction objectif.

La gestion des discontinuités tarifaires créait des oscillations infinies. L'algorithme hésitait entre 35,9 et 36,1 kVA, basculant constamment autour du seuil critique. L'optimiseur ne convergeait jamais, épuisant les 200 itérations. Solution : introduction d'une zone morte de ±0,5 kVA autour des seuils critiques pour stabiliser la convergence.

Les erreurs d'arrondis TVA semblaient négligeables mais s'accumulaient. Un écart de 0,01€ mensuel créait 2,40€ de différence après 240 mois. Les auditeurs bancaires rejetaient systématiquement ces "petits" écarts, exigeant une cohérence parfaite au centime près. Solution : reconciliation automatique mensuelle entre compte de résultat et trésorerie, avec alerte si écart > 0,01€.

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

*Figure 4.1 : Architecture d'intégration des APIs publiques françaises (Cadastre IGN, PVGIS, BD TOPO, DPE ADEME, Open Data Enedis) avec pipeline de traitement en 5 étapes et système de scoring multi-critères. Le gain de performance atteint 97% par rapport aux méthodes manuelles Excel.*

#### Comment automatiser l'analyse territoriale par intégration multi-API ?

OptimPV interroge 4 APIs publiques pour automatiser la prospection ACC. L'intégration technique représente un défi considérable en raison de l'hétérogénéité des données : l'API Cadastre renvoie du GeoJSON avec des coordonnées Lambert-93, PVGIS fournit du JSON avec des données horaires en WGS84, la BD TOPO délivre du XML ou Shapefile avec des métadonnées attributaires complexes, et l'API DPE retourne du CSV avec des adresses textuelles nécessitant un géocodage. Chaque source utilise des formats différents, des systèmes de projection distincts et des logiques de requêtage spécifiques qui doivent être harmonisés.

#### Pourquoi privilégier les APIs publiques françaises aux solutions commerciales ?

**Problématique du choix des sources de données :** L'automatisation de la prospection ACC nécessite des données spécifiques : surfaces cadastrales précises au m², hauteurs de bâtiments, historique d'irradiation solaire sur 20 ans, et diagnostics énergétiques certifiés. Face à ce besoin, deux options s'offrent : les APIs commerciales internationales (Google Maps, HERE, OpenWeatherMap) ou les bases de données publiques françaises (IGN, PVGIS, ADEME). L'analyse comparative révèle que, pour le contexte spécifique de l'ACC française, les solutions publiques offrent paradoxalement une meilleure adéquation technique malgré leur gratuité.

**Analyse comparative des alternatives commerciales :** Les solutions commerciales présentent des atouts indéniables (mises à jour temps réel, support professionnel, SLA garantis) mais révèlent des limites spécifiques pour l'ACC française. D'une part, Google Solar API excelle dans la détection des masques proches grâce à son modèle 3D urbain, identifiant automatiquement les ombres portées des immeubles voisins - fonctionnalité absente des APIs publiques françaises. Néanmoins, son coût (0,005€/requête géocodage, 0,007€/requête bâtiment) génèrerait environ 500€ mensuels pour 1000 prospects. Plus limitant encore : l'absence de données cadastrales officielles françaises et l'indisponibilité du service Solar API en France, réservé aux marchés US et quelques pays européens. D'autre part, HERE Maps (450€/mois) offre une excellente couverture urbaine mais l'analyse terrain révèle des lacunes significatives en zones rurales où se développent pourtant de nombreux projets ACC. Par ailleurs, OpenWeatherMap Solar (300$/mois) fournit des données météo de qualité mais avec une granularité spatiale moins fine que PVGIS et sans l'historique de 20 ans validé par le Joint Research Centre européen, référence exigée par les banques françaises. Enfin, Enedis DataConnect propose des données réseau précieuses mais ses délais contractuels (3-6 mois justifiés par les enjeux de sécurité) et sa tarification opaque compliquent l'intégration rapide.

**Avantages spécifiques des APIs publiques françaises :** L'API Cadastre IGN fournit les limites parcellaires officielles utilisées pour les actes notariés et les autorisations d'urbanisme - précision variable selon l'ancienneté des relevés (de métrique à décamétrique) mais juridiquement opposable. Google Maps offre une meilleure résolution visuelle mais ses contours automatiques ne constituent pas une référence légale pour les dossiers administratifs français. La gratuité des APIs publiques reste un avantage significatif face aux 500€ mensuels des alternatives, particulièrement en phase de prototypage. Les mises à jour du cadastre suivent les déclarations officielles avec des délais variables (quelques mois en urbain, parfois années en rural), mais reflètent les divisions parcellaires légales nécessaires aux montages ACC.

**Reconnaissance institutionnelle de PVGIS :** PVGIS, développé par le Joint Research Centre européen, bénéficie d'une reconnaissance forte auprès des banques françaises habituées à cette source dans les business plans photovoltaïques. Bien que des alternatives commerciales comme SolarGIS ou Meteonorm soient également acceptées, PVGIS reste la référence gratuite la plus citée dans les dossiers de financement. Sa résolution de 5 kilomètres (couvrant 25 km²) peut sembler grossière mais l'irradiation solaire varie peu à cette échelle, contrairement aux masques locaux qui nécessitent une analyse fine - distinction importante entre météorologie régionale et ombrages ponctuels.

**Complémentarité des bases publiques françaises :** La BD TOPO IGN recense la majorité des bâtiments français avec leurs caractéristiques principales, malgré des lacunes sur les constructions très récentes ou non déclarées. Ces métadonnées structurées (hauteur, usage, année) facilitent les analyses automatisées, avantage sur l'extraction manuelle depuis Street View. La base DPE ADEME, bien que couvrant seulement 30% du parc immobilier (principalement transactions récentes), fournit des consommations certifiées utiles pour estimer les besoins énergétiques des prospects ayant vendu ou loué récemment - échantillon biaisé mais exploitable pour les premières estimations.

**Impact économique et stratégique de cette architecture :** Le choix pragmatique des APIs publiques, malgré leurs limitations reconnues, génère une économie de 1500 à 2000€ mensuels cruciale en phase de développement. Au-delà de la perfection des données, c'est leur statut officiel qui constitue l'avantage décisif en facilitant les démarches administratives (cadastre pour les autorisations, PVGIS reconnu par les banques). L'implémentation d'un cache intelligent compense partiellement les lacunes en conservant les données enrichies progressivement.

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

**Méthode d'estimation automatisée via l'orchestration d'APIs :** Le Solar Simulator orchestre automatiquement plusieurs APIs pour estimer la puissance installable sans intervention manuelle. L'API Cadastre fournit automatiquement les coordonnées GPS et la surface du bâtiment, la BD TOPO transmet la hauteur et l'orientation probable, puis ces données sont directement envoyées à PVGIS qui calcule la puissance installable optimale. Tout se fait en cascade automatique : l'utilisateur entre simplement une adresse, et l'outil interroge successivement les APIs pour collecter et transmettre les paramètres nécessaires. PVGIS retourne alors la puissance installable en tenant compte de l'irradiation locale, des pertes systèmes et du ratio surface/puissance standard. Pour affiner l'estimation, un coefficient de 0,7 à 0,8 est appliqué sur la surface brute pour tenir compte des obstacles typiques (cheminées, PAC, velux) - méthode empirique validée sur les 120 installations de référence. Les panneaux Jinko Tiger Neo 450W bifaciaux (1,77m × 1,134m, rendement 22,3%) servent de base de calcul, choix validé par le retour d'expérience de la filiale allemande qui exploite plusieurs centrales ACC sans incident technique depuis 17 ans.

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

**Dimension technique :** évalue la surface utilisable du site principal (toiture du producteur), l'orientation optimale par rapport au soleil, et l'absence d'obstacles majeurs. Mais surtout, elle analyse le potentiel d'extension : combien de toitures supplémentaires dans le rayon de 2 km pourraient accueillir des panneaux si le projet initial réussit ? Cette vision prospective identifie les sites pouvant évoluer de 100 kWc initial à 500 kWc en phase 2, maximisant le retour sur investissement commercial.

**Dimension économique :** analyse le ratio production/consommation locale et calcule la rentabilité prévisionnelle via l'indicateur LCOE intégré. Le ratio d'autoconsommation potentiel s'exprime par :

$R_{auto} = \min\left(1, \frac{Prod_{estimée}}{Conso_{locale}}\right)$

Cette évaluation économique automatique permet d'identifier les configurations les plus prometteuses financièrement et d'orienter prioritairement les efforts commerciaux.

**Dimension commerciale :** évalue la typologie des clients potentiels, leur accessibilité pour la prospection, et le potentiel de développement ultérieur selon une grille de critères comportementaux issus des retours d'expérience sectoriels.

#### Comment l'interface transforme-t-elle les données en décisions opérationnelles ?

Les trois dimensions de scoring (technique, économique, commerciale) génèrent un volume important de données qui nécessite une interface de visualisation adaptée pour faciliter la prise de décision. La **Figure 4.2** présente l'interface du module de prospection d'OptimPV déployée sur le territoire de la Communauté d'Agglomération Sophia Antipolis.

![Figure 4.2 : Interface de prospection territoriale](https://image.noelshack.com/fichiers/2025/36/1/1756722581-carte.png)

*Figure 4.2 : Capture d'écran du module de prospection OptimPV analysant 330 sites potentiels répartis sur 6 communes (Mougins, Grasse, Valbonne, Biot, Cannes, Mouans-Sartoux). L'exemple détaillé montre la parcelle cadastrale n°134 à Biot, identifiant un lotissement de 39 logements. L'encadré rouge synthétise les métriques automatiquement extraites : surface cadastrale totale, nombre de toitures exploitables, et données DPE disponibles. L'intégration avec Google Maps permet la validation visuelle des surfaces réellement exploitables, combinant ainsi analyse automatique et expertise professionnelle.*

**Workflow d'analyse hybride automatique-expert :** L'interface illustre la complémentarité entre automatisation algorithmique et validation humaine. Le système identifie automatiquement les 330 points d'intérêt via l'analyse des données de consommation agrégées. Pour chaque parcelle, comme la n°134 présentée, l'API cadastrale extrait la surface totale des toitures (ici l'ensemble du lotissement). L'intégration cartographique permet ensuite au professionnel de discriminer visuellement les toitures réellement exploitables de celles présentant des contraintes techniques (orientation nord, obstacles, état de la couverture). Cette approche hybride garantit une qualification précise tout en maintenant l'efficacité du processus de prospection.


### 4.2. Comment organiser le suivi commercial des projets multi-participants ?

#### Quelle gestion multi-participants pour respecter les contraintes réglementaires ?

**La réalité terrain de l'ACC : obtenir 50 signatures dans un immeuble relève de l'exploit.** Car le principal frein n'est pas technique mais humain. Dans une copropriété de 50 appartements, convaincre tous les occupants de signer nécessite 6 à 12 mois de négociation. Entre les absents, les opposants par principe et les indécis chroniques, le taux d'adhésion plafonne à 60-70%. Un seul copropriétaire procédurier peut bloquer le projet en assemblée générale.

Au-delà des signatures, l'accord d'Enedis constitue le second verrou. Le gestionnaire vérifie la capacité disponible au poste de transformation : un projet de 180 kWc nécessitant 260 kVA peut saturer le poste, imposant des travaux de renforcement facturés 50 000€. Cette surprise tue régulièrement des projets économiquement viables. Le module de suivi commercial d'OptimPV intègre ces contraintes réelles en trackant simultanément le taux d'adhésion, le statut Enedis et la capacité réseau disponible.

**Orchestration des phases critiques du projet ACC :** Le module de suivi commercial structure le chaos apparent en 5 phases jalonnées : (1) Prospection initiale avec scoring automatique, (2) Constitution du collectif avec suivi du taux d'adhésion, (3) Validation technique Enedis et capacité réseau, (4) Bouclage financier avec tous les participants, (5) Contractualisation et mise en service. Chaque phase intègre des seuils go/no-go : minimum 70% d'adhésion pour passer en phase 3, accord Enedis obligatoire pour la phase 4. Cette structuration évite d'investir des ressources commerciales sur des projets voués à l'échec.

Ce pipeline commercial spécialisé ACC présente des taux d'attrition typiques : 100 prospects génèrent 20 projets étudiés, 5 projets validés techniquement, et 1 à 2 installations réalisées. Cette pyramide de conversion guide l'allocation des ressources commerciales.

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

La gestion automatisée de ces provisions évite leur oubli, erreur fréquente qui peut compromettre l'obtention d'un financement bancaire. Le module treasury_validator vérifie la cohérence des flux mais ne compare pas encore aux seuils spécifiques de chaque banque - évolution prévue pour une version ultérieure.

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

**Cas normal** : Quand le projet a des remboursements de dette (service dette > 0), le DSCR se calcule normalement. Un DSCR de 1,5 signifie que le projet génère 1,5 fois plus de cash que nécessaire pour rembourser la dette - situation saine.

**Cas sans dette** : Si le service de dette est nul (projet autofinancé ou dette intégralement remboursée) mais que le projet génère du cash (CFADS > 0), le code retourne "infini". Cela signifie une capacité de remboursement illimitée puisqu'il n'y a rien à rembourser. C'est contre-intuitif mais mathématiquement correct.

**Cas sans activité** : Quand ni cash ni dette n'existent (projet en phase de développement ou arrêté), le code retourne NaN (Not a Number). Cela évite de donner un ratio qui n'aurait aucun sens économique.

Cette gestion empêche le programme de planter sur une division par zéro tout en fournissant aux banquiers des indicateurs qu'ils peuvent interpréter selon le contexte du projet.

Le système vérifie la cohérence des flux mais n'intègre pas encore les alertes automatiques sur les seuils bancaires (DSCR < 1,2) ni le calcul du LLCR - améliorations identifiées pour les versions futures.

La correction automatique propose des suggestions d'optimisation du cash management : arbitrages entre placements court terme et remboursements anticipés, optimisation des échéanciers selon les flux prévisionnels, et recommandations de refinancement le cas échéant.

Ces validations automatiques éliminent les erreurs coûteuses : un DSCR sous 1,2 non détecté peut faire échouer un financement après 3 mois de négociation. OptimPV évite ces échecs en alertant immédiatement sur les déviations, permettant de corriger le tir avant soumission aux banques.



## Conclusion : Performance validée et limitations assumées

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

L'absence de batteries constitue la lacune fonctionnelle la plus pénalisante. Les aides régionales exigent maintenant 80% d'autoconsommation minimum, seuil inatteignable sans stockage pour les profils résidentiels standards. Un foyer consomme principalement le soir (18h-22h) quand le solaire ne produit plus, créant un décalage production/consommation que seules les batteries peuvent combler. L'impact financier est majeur : ajout de 150-200 €/kWh de CAPEX batteries (soit 15-20k€ pour 100 kWh), modification des flux de trésorerie avec remplacement des batteries tous les 10-12 ans, amélioration du taux d'autoconsommation de 15-25% selon les profils.

L'intégration du stockage permettrait d'atteindre systématiquement les 80% d'autoconsommation fixés comme seuil minimum de viabilité sur les projets ACC. Sans batteries, le plafonnement s'établit à 60-65% sur les meilleurs cas, compromettant l'éligibilité aux aides et la rentabilité globale. Cette contrainte force actuellement à refuser des projets techniquement réalisables mais économiquement non viables sans stockage.

L'optimisation devient multidimensionnelle : quelle capacité de stockage installer ? Quelle stratégie de charge/décharge adopter ? Comment arbitrer entre autoconsommation maximale et durée de vie des batteries ? Ces questions nécessitent des algorithmes d'optimisation dynamique que le framework actuel ne supporte pas. L'amortissement accéléré des batteries prévu par la Loi de Finances 2026 ajoutera une complexité fiscale supplémentaire.

**Limitation 2 - Validations bancaires et alertes manquantes :**

Le calcul du DSCR existe mais sans système d'alerte. Un DSCR passant sous 1,2 devrait déclencher une notification immédiate car c'est le seuil minimal exigé par toutes les banques. Le LLCR (Loan Life Coverage Ratio) n'est pas calculé alors qu'il est systématiquement demandé pour les financements de projet. Les ratios de solvabilité (fonds propres/dette, couverture d'intérêts) ne sont pas surveillés.

Chaque établissement financier impose ses propres exigences. Le DSCR minimal varie de 1,2 à 1,35 selon les banques, les provisions oscillent entre 3% et 5% du CAPEX, et les ratios de fonds propres s'échelonnent de 20% à 30%. Sans base de données des exigences par établissement et système de validation automatique, l'utilisateur doit vérifier manuellement chaque covenant, source d'erreurs et de rejets de dossiers.

**Limitation 3 - Intelligence prospection territoriale embryonnaire :**

Le module de prospection ACC identifie les sites potentiels mais manque d'intelligence avancée. L'absence de détection automatique des masques proches (immeubles voisins, arbres) via Google Solar API génère des surestimations de 20-30% de la production. L'analyse ne considère pas l'évolution urbaine : un terrain vague aujourd'hui peut devenir un immeuble demain, créant de l'ombrage fatal au projet.

L'optimisation des périmètres ACC reste manuelle. Avec la limite réglementaire de 2 km, comment définir le cercle optimal ? Faut-il centrer sur le producteur ou décaler vers une zone de forte consommation ? Comment identifier les "ancres" de consommation (supermarchés, bureaux) garantissant l'absorption de la production ? Le machine learning sur les patterns de consommation IRIS pourrait prédire les meilleurs périmètres, mais n'est pas implémenté.

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

L'analyse du code révèle que le module `facturation/forecasting.py` existe mais n'implémente que des moyennes mobiles basiques sans modèles prédictifs avancés. Les données PVGIS historiques sur 20 ans ne sont exploitées que par moyenne simple alors qu'un modèle ARIMA ou LSTM pourrait capturer les tendances saisonnières.

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

### De la théorie à la pratique : le projet Euro plomberie Piscine

Les concepts théoriques et algorithmes développés trouvent leur validation dans l'application concrète. La Partie III présentera l'étude détaillée du projet **Euro plomberie Piscine**, un cas réel de déploiement ACC commercial qui a abouti à une levée de fonds réussie.

Ce projet regroupe 5 magasins sur la Côte d'Azur, chacun disposant de plus de 1000 m² de surface de toiture exploitable. L'investissement total dépasse le demi-million d'euros, nécessitant une modélisation financière rigoureuse pour convaincre les investisseurs institutionnels. Cette complexité multi-sites illustre parfaitement les défis que OptimPV permet de résoudre.

La Partie III analysera en détail le modèle économique retenu, les résultats des calculs d'optimisation, et la structuration du montage financier. Plus important encore, l'analyse portera sur les problèmes terrain rencontrés durant le développement du projet. Ces réalités opérationnelles - négociations avec Enedis, contraintes administratives, ajustements réglementaires en cours de route - constituent les vrais défis de l'ACC commercial.

Cette étude de cas démontrera comment OptimPV a permis de traiter efficacement l'analyse complexe de 5 sites simultanés, transformant des semaines de calculs manuels approximatifs en une optimisation précise et documentée. Les écarts entre modélisation initiale et réalité finale révéleront les apprentissages essentiels pour tout développeur de projet ACC.

Le cas Europlomberie Piscine permettra de valider l'applicabilité réelle d'OptimPV : capacité à traiter des projets multi-sites complexes, fiabilité des calculs financiers sur 20 ans, et gain de temps effectif par rapport aux méthodes manuelles. Cette confrontation au terrain révélera les forces et faiblesses de l'outil développé.