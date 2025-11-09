# PAGES LIMINAIRES

## 📝 TODO : TABLE DES MATIÈRES + TABLE DES ILLUSTRATIONS
*[À insérer ici - réalisée par l'auteur]*

---

## GLOSSAIRE

**ACC (Autoconsommation Collective)** : Partage local d'électricité photovoltaïque entre participants.

**AMB (Alpes-Maritimes Bureau d'études)** : Société d'installations électriques.

**API** : Interface de Programmation d'Application.

**Aurora Solar** : Logiciel de dimensionnement photovoltaïque.

**Brent (Méthode de)** : Algorithme d'optimisation numérique.

**BT/HT** : Basse Tension/Haute Tension.

**Cadastre** : Service de géolocalisation parcellaire français.

**Cannes ABA Gestion** : Projet pilote OptimPV.

**CRE** : Commission de Régulation de l'Énergie.

**DevOps** : Développement et déploiement logiciel.

**DPE** : Diagnostic de Performance Énergétique.

**EaaS (Energy as a Service)** : Financement énergétique sans investissement initial.

**Enedis** : Gestionnaire du réseau électrique français.

**EPCI** : Établissement Public de Coopération Intercommunale.

**EPIC** : Établissement Public à caractère Industriel et Commercial.

**EPP (Euro Plomberie-Piscine)** : Entreprise antiboise partenaire OptimPV.

**Excel** : Tableur Microsoft.

**HAL** : Archive ouverte française.

**IRR** : Voir TRI.

**L-BFGS-B** : Algorithme d'optimisation SciPy.

**LCOE** : Levelized Cost of Energy.

**LTECV** : Loi de Transition Énergétique pour la Croissance Verte.

**MIRR** : Modified Internal Rate of Return.

**Monte Carlo** : Méthode statistique par simulations.

**NextJS** : Framework React.

**NPV** : Voir VAN.

**NumPy** : Bibliothèque Python calcul numérique.

**OptimPV** : Plateforme d'optimisation photovoltaïque ACC.

**PACA** : Provence-Alpes-Côte d'Azur.

**Pandas** : Bibliothèque Python manipulation données.

**PDL/PRM** : Point De Livraison/Point Référence Mesure.

**PMO** : Personne Morale Organisatrice.

**PPE** : Programmation Pluriannuelle de l'Énergie.

**PVGIS** : Service européen données irradiation solaire.

**PVsyst** : Logiciel simulation photovoltaïque.

**Python** : Langage de programmation.

**React** : Bibliothèque JavaScript interfaces utilisateur.

**REST** : Architecture échange données web.

**SciPy** : Bibliothèque Python calcul scientifique.

**Streamlit** : Framework Python applications web.

**TRI** : Taux de Rentabilité Interne.

**TURPE** : Tarif d'Utilisation des Réseaux Publics d'Électricité.

**VAN** : Valeur Actualisée Nette.

**WACC** : Weighted Average Cost of Capital.

---

## REMERCIEMENTS

Je tiens à exprimer ma reconnaissance envers toutes les personnes qui ont contribué à la réalisation de cette thèse professionnelle.

Mes remerciements s'adressent en premier lieu à **Ludwig di Giovani**, CEO d'AMB, pour sa confiance et son accompagnement dans le développement d'OptimPV. Son expertise financière des projets énergétiques et sa vision stratégique de l'autoconsommation collective ont été déterminantes dans l'orientation de ce travail de recherche appliquée.

Je remercie **Yoann Mabrito**, directeur du bureau d'études d'AMB, pour son encadrement technique rigoureux et ses conseils méthodologiques. Sa connaissance approfondie des enjeux énergétiques et réglementaires a enrichi ma compréhension des spécificités du marché français.

Ma gratitude va également à **Patrick Chambon**, chargé d'affaires ENR, ainsi qu'à l'équipe technique du bureau d'études - **Pierre-Yves** et **Mathieu** - pour leur accueil et leur contribution à ma montée en compétences sur les technologies photovoltaïques.

Je souhaite remercier **Euro Plomberie-Piscine** et sa direction pour avoir accepté de servir de cas d'étude concret à cette recherche, permettant une validation empirique des développements théoriques sur données réelles.

Mes remerciements vont enfin à mon tuteur académique pour son suivi pédagogique et ses orientations méthodologiques qui ont contribué à la rigueur scientifique de ce travail.

---

## RÉSUMÉ

Les développeurs de projets photovoltaïques font face à un défi récurrent : comment structurer financièrement une installation en autoconsommation collective pour satisfaire des acteurs aux intérêts divergents ? Un producteur cherche à maximiser ses revenus, des consommateurs veulent réduire leur facture, et des investisseurs exigent un retour sur investissement attractif. Cette équation à multiples inconnues freine souvent le développement de projets pourtant techniquement viables.

L'analyse manuelle de ces projets, généralement réalisée sur Excel, prend plusieurs jours et ne permet d'explorer qu'un nombre limité de scénarios. Les erreurs de calcul sont fréquentes et l'optimisation reste approximative. De plus, chaque modification de paramètre nécessite de recalculer l'ensemble des tableaux financiers sur 20 ans.

Le travail réalisé durant cette mission a consisté à développer OptimPV, une plateforme web automatisant l'analyse financière complète de ces projets. L'outil calcule instantanément les indicateurs clés (NPV, TRI, payback) pour chaque participant, teste automatiquement des milliers de combinaisons de paramètres pour identifier la configuration optimale, et génère des rapports professionnels adaptés à chaque interlocuteur.

L'utilisation d'OptimPV sur des projets réels a permis d'identifier des configurations augmentant la rentabilité moyenne de 15%, tout en réduisant le temps d'analyse de 3 jours à 2 heures. Plusieurs projets initialement jugés non-rentables ont pu être restructurés et validés grâce aux optimisations proposées par l'outil.

**Mots-clés :** photovoltaïque, autoconsommation collective, optimisation financière, aide à la décision, automatisation

---

## ABSTRACT

Solar project developers face a recurring challenge: how to financially structure a collective self-consumption installation to satisfy stakeholders with diverging interests? A producer seeks to maximize revenue, consumers want to reduce their energy bills, and investors demand attractive returns on investment. This multi-variable equation often hinders the development of projects that are otherwise technically viable.

Manual analysis of these projects, typically performed in Excel, takes several days and only allows exploration of a limited number of scenarios. Calculation errors are frequent and optimization remains approximate. Moreover, each parameter modification requires recalculating all financial tables over a 20-year period.

The work carried out during this mission consisted of developing OptimPV, a web platform that automates the complete financial analysis of these projects. The tool instantly calculates key indicators (NPV, IRR, payback) for each participant, automatically tests thousands of parameter combinations to identify the optimal configuration, and generates professional reports tailored to each stakeholder.

Using OptimPV on real projects has identified configurations that increase average profitability by 15%, while reducing analysis time from 3 days to 2 hours. Several projects initially deemed unprofitable were successfully restructured and validated thanks to the optimizations proposed by the tool.

**Keywords:** photovoltaic, collective self-consumption, financial optimization, decision support, automation

---

# CONTEXTE PROFESSIONNEL ET PRÉSENTATION DE L'ENTREPRISE

## 1. AMB : Expertise technique et positionnement stratégique

### 1.1. Évolution stratégique et positionnement concurrentiel

Azureen mouginouse batiment, est une société à responsabilité limitée immatriculée sous le SIREN 392762548, constitue depuis 1993 un acteur référent dans l'écosystème des installations électriques françaises. Fondée par Éric Chambon selon une approche artisanale privilégiant proximité et réactivité opérationnelle, l'entreprise a connu une évolution organisationnelle significative, passant d'une structure unipersonnelle à une organisation de 25 à 35 collaborateurs spécialisés.

L'analyse de cette trajectoire révèle une stratégie de diversification progressive, l'entreprise élargissant son périmètre d'intervention des secteurs résidentiel et tertiaire vers les marchés industriels et collectivités territoriales. Cette expansion s'appuie sur un ancrage territorial fort dans le département des Alpes-Maritimes, avec des références établies à Nice, Mougins et Cannes.

Le rachat de décembre 2024 par Idéal Storm, avec la participation majoritaire de Ludwig di Giovani, s'inscrit dans une logique de consolidation sectorielle. Cette opération génère un effet de levier stratégique, permettant l'accès à des ressources financières et techniques renforcées, tout en préservant l'expertise locale développée sur trois décennies.

Les performances économiques témoignent de la solidité du modèle : avec un chiffre d'affaires 2024 s'établissant à 4 millions d'euros, AMB confirme sa position d'acteur structurant sur le marché régional des solutions technologiques pour le bâtiment. Cette performance s'appuie sur une offre intégrée couvrant l'ensemble de la chaîne de valeur : études techniques, installation, mise en service et maintenance opérationnelle.



### 1.2. Infrastructure opérationnelle et implantation géographique

L'organisation spatiale d'AMB s'articule autour d'un site unique de 400 m² situé au 423 chemin de la Nartassière à Mouans-Sartoux (06370), regroupant l'intégralité des fonctions supports : bureaux d'études, espaces administratifs et zone de stockage technique. Cette centralisation fonctionnelle optimise la coordination des activités tout en permettant une gestion rationalisée des flux logistiques et informationnels.

Cette implantation géographique stratégique au cœur des Alpes-Maritimes positionne AMB à équidistance des principaux bassins économiques régionaux, facilitant les interventions sur l'ensemble du territoire départemental et garantissant des temps de réaction optimisés pour les opérations de maintenance et dépannage.

### 1.3. Domaines d'expertise technique et segmentation de marché

L'analyse du portefeuille d'activités révèle une spécialisation technique multidisciplinaire, structurée autour de cinq axes d'expertise complémentaires générant des synergies opérationnelles significatives.

Les installations électriques courants forts (BT/HT) constituent le cœur métier historique, avec une expertise reconnue dans la conception et réalisation de distributions électriques complexes respectant les exigences normatives NFC 15-100. Cette compétence fondamentale s'articule avec les systèmes courants faibles (réseaux informatiques, téléphonie) pour proposer une approche intégrée des infrastructures numériques du bâtiment.

Le pôle sécurité développe des solutions techniques spécialisées : détection intrusion, contrôle d'accès biométrique, et systèmes de détection incendie conformes aux réglementations ERP. Cette expertise sécuritaire répond aux enjeux croissants de protection des biens et personnes dans les secteurs tertiaire et industriel.

L'expertise mobilité électrique positionne AMB sur le marché émergent des infrastructures de recharge, avec des installations jusqu'à 22,5 kVA répondant aux standards techniques IRVE (Infrastructure de Recharge de Véhicules Électriques). Cette spécialisation s'inscrit dans la transition énergétique et l'évolution des usages de mobilité.

Enfin, les services de maintenance préventive et corrective garantissent la continuité opérationnelle des installations sur leur cycle de vie complet, générant des revenus récurrents et renforçant la fidélisation client à long terme.



### 1.4. Organisation fonctionnelle et structure managériale

L'architecture organisationnelle d'AMB révèle une structure de 30 collaborateurs répartis selon une logique de spécialisation métier, garantissant l'efficacité opérationnelle et la qualité des prestations délivrées. Cette organisation matricielle combine expertise technique approfondie et transversalité des compétences, créant les conditions d'une approche projet intégrée.
  


Figure 1 : Organigramme de la société

## 2. Architecture du bureau d'études : cœur technique de l'expertise AMB

### 2.1. Positionnement stratégique et gouvernance technique

L'analyse structurelle du bureau d'études révèle une organisation stratifiée articulée autour de pôles d'expertise complémentaires, sous la direction technique de Yoann Mabrito. Cette fonction de direction technique hybride intègre supervision des études techniques, coordination projet et interface client, optimisant ainsi les flux informationnels entre conception technique et exigences commerciales.

Dans une volonté de renforcer son offre dans le domaine des énergies renouvelables, AMB a récemment mis en place un service dédié aux ENR, spécialisé notamment dans les installations photovoltaïques et les solutions énergétiques durables. Ce service est piloté par Ludwig DI Giovani et Patrick Chambon, qui en assurent conjointement la gestion et le développement. Patrick Chambon, en qualité de chargé d'affaires, assure le suivi des projets, la relation client et la coordination des études techniques.

Le bureau d'études est également composé de trois techniciens spécialisés dans leur domaine respectif. Pierre-Yves, expert en courants forts, prend en charge les études et le dimensionnement des installations électriques. Mathieu, spécialisé en courants faibles, se consacre à la conception des systèmes de sécurité, de contrôle d'accès et des réseaux de communication. L'ingénieur d'études intervient sur le dimensionnement des installations électriques et photovoltaïques, en réalisant à la fois l'étude technique et financière des projets, au-delà d'une approche purement économique comme les PPA. Cette fonction participe également à la conception des plans et schémas électriques.

L'ensemble des équipes du bureau d'études travaille en collaboration étroite avec Ludwig DI Giovani, qui occupe un double rôle de chargé d'affaires et de dirigeant de l'entreprise. Son implication directe dans la gestion des projets permet d'assurer une supervision technique rigoureuse et d'orienter les prises de décisions stratégiques.

Le bureau d’études joue un rôle central dans le bon déroulement des projets en assurant des études techniques précises et conformes aux normes en vigueur. Il intervient à différentes étapes, de la phase de conception à la mise en œuvre des installations, et se voit confier plusieurs missions essentielles.
Tout d’abord, il assure la conception et la réalisation des études techniques, notamment à travers la modélisation des systèmes électriques, la réalisation des études d’éclairage avec Dialux et la création des plans et schémas électriques sur AutoCAD. Le bureau d’études a également la charge du dimensionnement des installations électriques et photovoltaïques, en intégrant des solutions adaptées aux besoins spécifiques de chaque projet.
Le respect des normes et des réglementations en vigueur constitue un enjeu majeur. À ce titre, le bureau d'études élabore les notes de calculs nécessaires afin de garantir la conformité des installations, notamment avec la norme NFC 15-100 et les réglementations spécifiques au secteur.
Dans une logique d’accompagnement des équipes sur le terrain, il assure un support technique aux équipes travaux, en mettant à disposition des plans d’exécution détaillés et des documents techniques, permettant ainsi de garantir la bonne réalisation des chantiers.
L’intégration de solutions innovantes fait également partie des missions du bureau d’études, en particulier dans le cadre du service ENR, qui vise à optimiser la performance énergétique des bâtiments et à développer des solutions basées sur les énergies renouvelables et les nouvelles technologies.

Par ailleurs, la modélisation 3D représente un levier essentiel, tant d’un point de vue technique que commercial. Grâce à l’utilisation des logiciels Autodesk AutoCAD et Revit, le bureau d’études conçoit des maquettes détaillées, facilitant la visualisation des projets et permettant de proposer aux clients une représentation claire et précise des installations envisagées.
Enfin, l’une des missions fondamentales du bureau d’études consiste à analyser et suivre les projets en cours, en recueillant les retours des conducteurs de travaux afin de fournir à la direction des éléments d’aide à la décision. Cette démarche vise à assurer une gestion optimisée des projets et à garantir un niveau élevé de satisfaction client.

Grâce à cette organisation structurée et à l’expertise de chaque membre de l’équipe, le bureau d’études d’AMB est en mesure de répondre aux exigences des clients en proposant des solutions innovantes, performantes et conformes aux standards les plus élevés du secteur.
L'intégration au sein du service ENR a été marquée par une évolution constante et une montée en compétences significative. L'ingénieur d'études a débuté en tant que projeteur, permettant d'acquérir une solide base technique et de se familiariser avec les exigences du bureau d'études. Cette progression a conduit à une évolution vers un poste d'ingénieur bureau d'études spécialisé dans les énergies renouvelables.

Tout au long de cette période de trois années, l'opportunité d'explorer de nouveaux aspects du métier a permis de perfectionner les connaissances et de se spécialiser davantage. Les capacités en dimensionnement électrique et photovoltaïque, en conception de plans et en gestion de projet ont été renforcées, tout en développant une approche approfondie de l'optimisation énergétique. Cette fonction a également permis d'améliorer la communication et la collaboration avec les conducteurs de travaux, les chargés d'affaires et les autres membres du bureau d'études.

Aujourd'hui, cette expérience s'oriente vers un nouveau défi professionnel avec la participation active au développement du nouveau service ENR de l'entreprise. Ce secteur en pleine expansion représente une opportunité d'application des compétences acquises tout en explorant des technologies innovantes dans le domaine des énergies renouvelables et du photovoltaïque. Cette fonction consiste à assurer les études techniques et à contribuer à la structuration et à la croissance de cette nouvelle activité, en collaboration étroite avec Ludwig DI Giovani et Patrick Chambon.

Cette progression témoigne d'un engagement vers l'évolution continue et l'apport d'une valeur ajoutée à l'entreprise. Elle illustre également la capacité d'adaptation aux nouvelles exigences du secteur et l'investissement dans des projets ambitieux, contribuant activement à la transition énergétique et à l'optimisation des solutions énergétiques proposées par AMB.
 

Dans le cadre du développement du nouveau service ENR d'AMB, la mission confiée consiste à concevoir et développer OptimPV, une solution logicielle dédiée aux projets photovoltaïques, en collaboration avec Euro Plomberie-Piscine comme partenaire de validation terrain.

## 2. Présentation de la mission

### 2.1 Mission et planning de développement

La mission s'échelonne sur l'année académique 2024-2025, en alternance avec les périodes en entreprise AMB.

Le développement d'OptimPV s'articule autour de jalons chronologiques précis, correspondant aux périodes d'alternance et aux besoins opérationnels identifiés.

L'intégration au service ENR d'AMB (15 novembre 2024) marque le début du projet, permettant l'immersion dans l'écosystème professionnel et l'identification des enjeux métier. Cette phase initiale facilite la compréhension des processus internes et des attentes client.

L'analyse approfondie du marché de l'autoconsommation collective (janvier-février 2025) constitue la base documentaire du projet. Cette recherche permet d'identifier les lacunes du marché et de définir les spécifications fonctionnelles d'OptimPV selon les besoins sectoriels.

La conception de la plateforme (juillet 2025) précède le développement du cœur applicatif (juin 2025), avec l'implémentation progressive des modules spécialisés : prospection géographique (juillet), simulations Monte Carlo (août), et intégration des dispositifs d'aide PACA (août).

Le partenariat avec Euro Plomberie-Piscine, initié en août 2025, offre un cas d'étude concret pour valider les fonctionnalités développées sur un projet d'autoconsommation collective de 200 kWc destiné à 24 consommateurs antibois.

Cette approche itérative permet de combiner formation théorique et application pratique, avec une validation continue des développements sur des projets réels.

![Planning de développement OptimPV](https://image.noelshack.com/fichiers/2025/37/3/1757496202-projet-sans-titre-1.png)
*Figure 4 : Planning de développement d'OptimPV - Jalons chronologiques et phases de réalisation*








 Analyse du marché de l'autoconsommation collective et développement d'une plateforme intégrée d'aide à la décision pour l'optimisation technico-économique des projets photovoltaïques : Le cas OptimPV

## Introduction Générale

### Problématique et enjeux de l'autoconsommation collective

L'autoconsommation collective d'électricité (ACC) constitue une modalité émergente de la décentralisation énergétique française. Définie par l'article L.315-2 du Code de l'énergie, cette pratique permet à plusieurs producteurs et consommateurs de partager localement l'électricité produite via une personne morale organisatrice (PMO). Le marché français présente une dynamique de croissance soutenue : 1 111 opérations actives en juin 2025 contre 102 fin 2022, représentant 10 644 consommateurs, 1 694 producteurs et 161 MW de puissance installée, avec une progression de 144% sur l'année 2024-2025.

Néanmoins, cette croissance s'accompagne de défis opérationnels spécifiques selon la typologie des projets. Les développeurs de projets d'ACC multi-acteurs, segment représentant environ 33% des opérations, font face à des enjeux d'optimisation technico-économique distincts des ACC patrimoniales. Contrairement à ces dernières qui appliquent généralement un prix au coût technique (LCOE), les ACC multi-acteurs requièrent une optimisation fine du prix de vente permettant d'équilibrer la rentabilité du porteur de projet et l'attractivité commerciale pour les consommateurs.

Cette optimisation présente une complexité particulière dans un contexte réglementaire et fiscal en évolution. La suppression de l'accise sur l'électricité depuis mars 2025, les modifications des seuils de puissance autorisée, et l'imbrication des mécanismes tarifaires (TURPE, TVA différentielle) génèrent un environnement d'analyse où les paramètres évoluent fréquemment. Par ailleurs, l'analyse des pratiques actuelles révèle une inadéquation entre la sophistication croissante des projets et les outils d'analyse utilisés, majoritairement basés sur des tableurs Excel atteignant leurs limites techniques face à la volumétrie des données à traiter (5,2 millions de points sur 20 ans pour un projet standard).

L'hypothèse de recherche examine si une approche algorithmique spécialisée peut améliorer significativement l'efficacité opérationnelle de ces analyses. OptimPV se différencie des solutions existantes (PVsyst, Aurora Solar, outils propriétaires) par son architecture modulaire évolutive et ses algorithmes d'optimisation intégrant nativement les spécificités réglementaires françaises. En outre, cette recherche évalue la viabilité d'un modèle économique associé : l'Energy as a Service (EaaS) combiné à l'ACC, permettant aux entreprises d'accéder au photovoltaïque sans mobilisation de capitaux initiaux.

### Démarche et structuration du mémoire

Cette recherche appliquée examine la valeur ajoutée d'OptimPV dans le contexte des ACC multi-acteurs. La démarche s'articule autour de trois axes complémentaires : diagnostic sectoriel, développement technique, et validation empirique.

La première partie présente l'analyse stratégique du secteur photovoltaïque français, avec une attention particulière portée au marché de l'autoconsommation collective et à l'identification des inefficiences opérationnelles. Cette analyse segmente le marché selon les typologies de PMO et caractérise les besoins d'optimisation spécifiques, établissant le cahier des charges fonctionnel de la solution développée.

La deuxième partie détaille la conception et le développement de la plateforme OptimPV. L'architecture modulaire développée sépare le moteur de calcul financier du module d'adaptation réglementaire, permettant une évolutivité face aux mutations législatives. Les algorithmes d'optimisation implémentés (méthode de Brent, simulations Monte Carlo) traitent l'optimisation sous contraintes multiples. La validation technique s'appuie sur le projet réel Cannes ABA Gestion, quantifiant les gains de performance obtenus.

La troisième partie présente la validation opérationnelle par l'étude de faisabilité Euro Plomberie-Piscine. Cette entreprise familiale multi-sites (467 MWh/an) constitue le terrain d'application du modèle EaaS+ACC développé. L'analyse examine la viabilité économique du projet (201,6 kWc, 269 MWh/an) selon les perspectives opérateur et client, validant l'hypothèse de différenciation par l'optimisation algorithmique. La robustesse des projections est évaluée par simulation Monte Carlo sur 1000 scénarios.

Ainsi, cette structuration permet d'examiner la transformation d'un besoin de marché identifié en solution technique opérationnelle, puis sa validation dans des conditions réelles d'application.



## Partie I : Analyse Stratégique du Secteur Photovoltaïque

### Chapitre 1 : Le Marché de l'Autoconsommation Collective en France

L'autoconsommation collective française s'inscrit dans un cadre réglementaire structuré dont la maîtrise conditionne la viabilité des projets. Cette analyse détaille les spécificités du marché français et identifie les segments présentant des besoins d'optimisation technico-économique.

![Figure 1.0 : Principe de fonctionnement de l'autoconsommation collective](https://terresolaire.com/wp-content/uploads/2025/03/autoconsocollective_Schema-2.jpg)
*Figure 1.0 : Schéma de principe de l'autoconsommation collective illustrant le partage local d'électricité photovoltaïque entre producteurs et consommateurs dans le respect du périmètre géographique réglementaire (Source : Terre Solaire, 2025)*

L'analyse de ce marché nécessite d'examiner successivement trois dimensions structurantes : le cadre réglementaire et ses évolutions récentes, l'écosystème d'acteurs et leurs interactions, puis la segmentation par modèles de PMO qui détermine les besoins d'optimisation spécifiques.

#### Cadre réglementaire : opportunités et contraintes du marché
La maîtrise de ce cadre constitue un prérequis essentiel pour le développement de projets viables. D'une part, l'analyse révèle une progression législative favorable au développement du secteur, mais d'autre part, des contraintes structurelles maintenues influencent directement les modèles économiques applicables.

##### L'évolution législative depuis 2015 : structuration progressive du marché
L'autoconsommation collective trouve ses fondements juridiques dans la loi de transition énergétique pour la croissance verte (LTECV) de 2015. En effet, cette loi a introduit ce concept innovant dans le droit français. L'article L.315-2 du Code de l'énergie définit précisément ce dispositif ﹕ "L'opération d'autoconsommation est collective lorsque la fourniture d'électricité est effectuée entre un ou plusieurs producteurs et un ou plusieurs consommateurs finals liés entre eux au sein d'une personne morale et dont les points de soutirage et d'injection sont situés dans le même bâtiment, y compris des immeubles résidentiels" (rapport HAL, 2022). 

La France a privilégié dès 2016 la création d'une structure juridique spécifique : la Personne Morale Organisatrice (PMO). Cette entité assure l'interface entre les participants au projet et le gestionnaire du réseau de distribution. Sa nature juridique demeure flexible : société de droit privé, association ou personne morale de droit public.

La PMO remplit un rôle d'identification administrative des relations contractuelles auprès d'Enedis et du fournisseur de complément, sans pour autant définir la qualification juridique précise des rapports entre producteurs et consommateurs.
Par la suite, l'ordonnance de 2016 et le décret de 2017 ont précisé les modalités techniques et administratives, établissant trois types d'opérations d'ACC selon le périmètre géographique :

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
L'impact de cette évolution dépasse la simple augmentation quantitative des seuils autorisés. En effet, elle traduit une volonté politique d'accélération du déploiement des énergies renouvelables décentralisées, dans un contexte de croissance soutenue du marché. L'évolution historique témoignait déjà d'une dynamique positive : 41 opérations actives fin novembre 2020, 55 fin mai 2021, pour atteindre 102 opérations actives en juin 2022, soit une progression de +149% en 18 mois (rapport HAL, 2022), dépassant l'objectif PPE 2020 de 50 opérations à l'horizon 2023. Cette croissance historique n'était cependant qu'un prélude à l'explosion qui allait suivre.

##### L'accélération historique de 2024-2025 : un changement d'échelle vers 2030

Jamais l'autoconsommation collective n'avait connu une telle accélération en l'espace d'un an. Les données publiées par Enedis à juin 2025 sont sans appel : le modèle change d'échelle, franchissant un cap historique et confirmant son rôle central dans la transition énergétique française.

**Structure du marché français :** L'évolution des données trimestrielles Enedis révèle une accélération continue depuis mars 2021. De 50 opérations en mars 2021, le secteur atteint 1 111 opérations en juin 2025, soit une croissance de +2 122% en 4 ans. La progression s'intensifie particulièrement depuis 2024 : +144% entre juin 2024 (454 opérations) et juin 2025 (1 111 opérations) - un rythme sans précédent.

![Tableau de répartition des opérations d'autoconsommation collective actives](https://image.noelshack.com/fichiers/2025/36/1/1756737995-tableau-de-r-partition-des-op-rations-d-autoconsommation-collective-actives-maille-enedis.png)
*Figure 1.2 : Évolution trimestrielle des opérations d'autoconsommation collective (mars 2021 - juin 2025). La progression exponentielle témoigne de l'impact des assouplissements réglementaires successifs, culminant avec l'explosion de 2024-2025 (Source : Enedis, 2025)*

La puissance installée cumulée atteint 161 MW en juin 2025, contre 38 MW seulement 12 mois plus tôt (+320%). Cette montée en puissance s'accompagne d'une structuration du marché : 1 700 producteurs partagent désormais leur électricité avec plus de 10 600 consommateurs. La taille moyenne des opérations s'établit à 145 kVA, témoignant d'une montée en puissance significative par rapport aux 52 kVA observés en juin 2022.

Cette progression exceptionnelle confirme l'impact des mesures réglementaires récentes (arrêté périmètre, exonération d'accise pour ACC, simplifications administratives) et valide le potentiel de développement du secteur. Pour les opérations multi-acteurs représentant environ 33% de ce total, soit approximativement 370 opérations fin 2025 (contre ~34 fin 2022), l'enjeu d'optimisation technico-économique devient considérable et justifie pleinement le développement d'outils spécialisés comme OptimPV.

**Perspectives 2030 : un marché au potentiel considérable malgré l'absence d'objectifs officiels.** Cette dynamique de croissance contraste paradoxalement avec l'absence d'objectifs ACC quantifiés dans la Programmation Pluriannuelle de l'Énergie (PPE3, 2024-2025). Contrairement à l'Espagne qui vise explicitement 9 GW d'autoconsommation collective d'ici 2030 via sa "Hoja de Ruta del Autoconsumo", la France privilégie une approche non directive, se contentant de mesures facilitatrices sans cibles chiffrées.

Le projet PPE3, mis en concertation en novembre 2024, fixe un objectif global de 54 GW photovoltaïques en 2030 (rythme de 5,5 à 7 GW/an) mais souligne qu'"il ne semble pas pertinent de fixer un objectif de développement de l'autoconsommation en tant que tel". Cette position gouvernementale laisse le marché ACC évoluer selon sa dynamique propre, alimentée par les assouplissements réglementaires successifs.

Pourtant, une extrapolation prudente révèle un potentiel de développement considérable. Si l'ACC représentait seulement 3% du parc photovoltaïque français en 2030, cela équivaudrait à 1,6 GW d'autoconsommation collective, soit une multiplication par dix par rapport aux 161 MW actuels. Un scénario à 5% porterait ce potentiel à 2,7 GW, représentant une multiplication par dix-sept. Ce "gap" entre la situation actuelle et le potentiel 2030 met en évidence l'ampleur du marché émergent et l'opportunité de développement pour des solutions d'optimisation spécialisées.

**Typologie des PMO :** Bien que les données détaillées par type de PMO pour 2025 ne soient pas encore disponibles, l'analyse historique révèle que les collectivités territoriales dominaient massivement le portage de projets, représentant plus des deux tiers des opérations d'ACC en mai 2022 (rapport HAL, 2022). Cette prédominance s'explique par le développement d'ACC "patrimoniales", où le consommateur et le producteur constituent une même personne morale disposant de PRM/PDL distincts. Les PMO constituées sous forme de sociétés et EPIC représentaient 18% des opérations. L'explosion récente du marché (×10 en 4 ans) suggère une diversification probable de cette répartition, avec l'émergence accélérée de trois formes de PMO distinctes : ACC "patrimoniale", ACC "bailleur social" et ACC "multi-acteurs/communauté".

La capacité d'évolution du cadre normatif français justifie les nouvelles ambitions réglementaires pour 2025.

 Quelles contraintes géographiques et dérogations spécifiques encadrent les projets ?

La réglementation française impose des contraintes géographiques strictes visant plusieurs objectifs complémentaires. D'une part, ces contraintes préservent l'efficacité du réseau électrique selon les principes techniques établis, et d'autre part, elles maximisent les bénéfices de la consommation locale pour les participants. Ainsi, la règle générale impose un périmètre maximal de 2 kilomètres entre lieux de production et de consommation.
Une dérogation spécifique permet l'extension à 20 kilomètres pour les zones rurales. Adaptée aux spécificités des territoires moins denses, cette mesure facilite le développement de projets dans les territoires où la densité démographique limite les opportunités. L'application de cette dérogation nécessite une justification technique et économique selon les critères établis.
L'arrêté du 21 février 2025 introduit une innovation majeure concernant les dérogations publiques. Une dérogation spécifique s'applique aux projets portés par des communes ou des établissements publics de coopération intercommunale (EPCI) à fiscalité propre. 
Cette dérogation s'active lorsque l'ensemble des participants sont des organismes publics. Les entités exerçant une mission de service public peuvent également en bénéficier.
Dans ce cadre dérogatoire, la puissance cumulée peut atteindre jusqu'à 10 MW selon les dispositions spécifiques. Le périmètre de partage peut s'étendre à l'ensemble du territoire de l'EPCI concerné. Cette extension géographique facilite significativement le développement de projets territoriaux d'envergure. 
Elle illustre la volonté des pouvoirs publics de favoriser l'émergence de projets publics structurants.
L'analyse des critères cumulatifs révèle cependant des exigences administratives importantes. Ces contraintes procédurales peuvent constituer un frein pour certains porteurs de projets. La nécessité de justifier le caractère public de tous les participants peut compliquer la structuration juridique. La vérification du respect des critères nécessite un accompagnement juridique spécialisé.

Au-delà de ces évolutions des seuils et périmètres autorisés, la transformation la plus significative du secteur résulte des modifications fiscales récentes qui redéfinissent fondamentalement l'équation économique des projets.

#### La révolution fiscale : transformation de l'économie des projets

L'évolution la plus structurante pour l'économie de l'autoconsommation collective concerne la révolution fiscale récente. L'article 21 du Projet de loi de finances 2025, adopté le 6 février via le recours au 49.3, modifie profondément la fiscalité applicable. Cette réforme aligne le régime fiscal de l'autoconsommation collective sur celui de l'autoconsommation individuelle. L'alignement concerne les installations inférieures à 1 MW selon les seuils définis.
Concrètement, cette réforme entraîne la suppression de l'accise sur l'électricité pour ces installations. L'accise représentait une taxe de 33,7 €/MWh qui pénalisait significativement les projets collectifs. Depuis le 1er mars 2025, ce tarif est officiellement fixé à 0 €/MWh. L'article 75 de la loi de finances pour 2025 formalise cette suppression (République Française, 2025).

Cette mesure représente un avantage concurrentiel considérable pour l'autoconsommation collective. Les projets peuvent désormais proposer des prix plus attractifs aux consommateurs participants. L'élimination de cette taxation améliore directement la compétitivité face aux tarifs réglementés standards. Cette amélioration facilite le développement de projets et accélère l'adoption par les consommateurs participants.
L'impact économique de cette suppression est quantifiable et significatif. Les projets d'autoconsommation collective peuvent proposer une baisse d'environ 25% du prix de l'électricité. Cette réduction concerne les consommateurs participants selon les simulations économiques réalisées. Cette amélioration renforce l'attractivité économique du modèle considérablement. Elle accélère potentiellement le déploiement selon les prévisions de marché établies.
Parallèlement aux évolutions fiscales, le Tarif d'Utilisation des Réseaux Publics d'Électricité (TURPE) a fait l'objet d'adaptations spécifiques. La Commission de Régulation de l'Énergie a introduit en mai 2018 une formule tarifaire optionnelle destinée aux participants d'opérations d'ACC, créant une distinction entre flux autoproduits et alloproduits (rapport HAL, 2022). Cette adaptation technique reconnaît les spécificités économiques de l'autoconsommation collective tout en préservant les principes de solidarité tarifaire du système électrique français.

Au-delà de ces adaptations actuelles, l'ACC présente un potentiel de réponse aux enjeux de congestion locale du réseau électrique. La décentralisation de la production permet de traiter des problématiques territoriales spécifiques en évitant les flux longue distance, créant une valeur ajoutée pour les gestionnaires de réseau. Les évolutions envisagées du TURPE vers une part variable accrue visent à inciter à la réduction de la consommation aux heures de pointe, ouvrant de nouveaux axes d'optimisation pour les outils d'aide à la décision.

Cette évolution illustre l'importance de la veille réglementaire pour les acteurs du secteur. Les outils d'analyse doivent intégrer rapidement ces évolutions pour maintenir leur pertinence, créant un avantage opérationnel décisif pour les développeurs réactifs.

L'application concrète de ces évolutions réglementaires et fiscales dépend de l'organisation des acteurs qui les mettent en œuvre sur le terrain. L'analyse de cet écosystème institutionnel et de ses interactions opérationnelles devient donc nécessaire.

#### L'écosystème d'acteurs et les rôles institutionnels

L'autoconsommation collective implique un écosystème multi-acteurs aux rôles différenciés et interconnectés. La Figure 1.3 schématise cette organisation institutionnelle, plaçant la Personne Morale Organisatrice (PMO) au centre du dispositif.

![Schéma de fonctionnement d'une opération d'ACC](https://i0.wp.com/sgge.fr/wp-content/uploads/2021/10/partagelec.png?resize=768%2C417&ssl=1)
*Figure 1.3 : Écosystème d'acteurs et flux contractuels d'une opération d'autoconsommation collective. La PMO (Personne Morale Organisatrice) centralise les relations : convention Enedis, contrats de vente avec consommateurs, gestion administrative et financière, contrats de construction/maintenance (Source : SGGE, 2021)*

Au cœur de toute opération, la PMO constitue l'élément central structurant, ayant "pour mission principale de servir d'interface entre les acteurs (producteurs et consommateurs) et le gestionnaire du réseau de distribution, concluant une convention d'autoconsommation collective" (rapport HAL, 2022). Elle coordonne les flux énergétiques et informationnels entre :

- **Les participants internes** : producteur(s) et consommateur(s) liés par contrat onéreux ou non
- **Le gestionnaire de réseau** : principalement Enedis assurant mesure et distribution
- **L'acheteur de surplus** : valorisation de l'excédent de production
- **Le fournisseur de complément** : approvisionnement de l'énergie manquante

Cette configuration multi-acteurs génère des enjeux de coordination que la plateforme OptimPV vise à automatiser et optimiser.

**Évolution des modèles de PMO :** Le cadre initial de 2016 a progressivement évolué vers trois configurations distinctes. Pour les bailleurs sociaux, un cadre juridique spécifique a été créé en 2019 via la loi relative à l'énergie et au climat : le bailleur social devient directement la PMO, l'information sur la présence d'une opération d'ACC étant assurée à la conclusion du contrat de location. Le locataire peut librement décider de ne pas participer à l'opération et peut également la quitter à tout moment (rapport HAL, 2022). Cette simplification répond aux spécificités de ce segment de marché et facilite considérablement le montage de projets.
Le gestionnaire de réseau de distribution, principalement Enedis, joue un rôle technique crucial. Il assure le raccordement des installations selon les normes techniques établies. 

Cette mesure nécessite une infrastructure spécifique : chaque site de production et de consommation doit disposer d'un point de livraison distinct (PDL pour la consommation, PRM pour la production) équipé de compteurs communicants Linky. L'obtention de ces points de livraison constitue souvent le goulot d'étranglement dans le développement des projets, les délais Enedis pouvant atteindre 6 à 12 mois selon la complexité du raccordement. Cette contrainte temporelle influence directement la planification des projets et leur modèle économique.

La répartition de l'électricité produite localement suit les directives de la PMO, basée sur les données de mesure transmises automatiquement par les compteurs. Cette répartition respecte les clés de répartition contractuellement définies entre les participants.
L'arrêté du 10 juillet 2024 a simplifié significativement les obligations administratives. Les collectivités territoriales bénéficient particulièrement de ces dispositions. Il n'est pas nécessaire de constituer de budget annexe pour les projets respectant certains critères. La constitution de régie n'est également pas obligatoire dans ces cas précis. Cette exemption s'applique tant que la puissance cumulée ne dépasse pas 1 MW.
Cette simplification administrative encourage l'engagement des collectivités dans le développement territorial. Elle réduit les coûts administratifs et facilite la prise de décision politique. L'élimination de contraintes procédurales accélère les délais de mise en œuvre. Cette facilitation répond aux demandes exprimées par les associations d'élus locaux.
L'analyse de l'écosystème révèle l'émergence d'acteurs spécialisés dans l'accompagnement technique et juridique, développant progressivement une expertise spécifique à l'autoconsommation collective. Cette spécialisation témoigne de la structuration graduelle de la filière économique et facilite simultanément l'accès au marché pour les porteurs de projets non-experts.

Par conséquent, cette structuration crée une chaîne de valeur spécialisée permettant la professionnalisation du secteur, tout en favorisant l'établissement de standards techniques et commerciaux homogènes sur le territoire national.

### Synthèse des modèles de PMO : segmentation du marché et périmètre d'OptimPV

L'évolution réglementaire a conduit à l'émergence de trois formes de PMO distinctes, inscrites dans le modèle de convention d'autoconsommation collective, présentant des enjeux d'optimisation radicalement différents (rapport HAL, 2022) :

#### **ACC "patrimoniale" : optimisation technique sans enjeu commercial**

Les opérations patrimoniales représentaient historiquement 67% des ACC françaises selon les données Enedis de 2022. Dans ce modèle, le consommateur et le producteur constituent une même personne morale (typiquement collectivités territoriales) disposant de PRM/PDL distincts. La commune installe des panneaux photovoltaïques sur un site (mairie, école) et consomme l'électricité produite sur d'autres sites communaux (éclairage public, équipements municipaux). Avec l'explosion du marché depuis 2024, cette répartition évolue probablement vers une diversification des modèles.

**Spécificités économiques :** L'objectif n'est pas la rentabilité commerciale mais l'optimisation budgétaire interne. Le prix de l'électricité échangée correspond au coût technique de production (LCOE - Levelized Cost of Energy) sans marge commerciale. La collectivité cherche à réduire sa facture énergétique globale en mutualisant sa production entre ses différents sites de consommation.

**Besoins d'optimisation limités :** Ce modèle ne présente aucun enjeu d'optimisation de prix de vente puisqu'il n'y a pas de transaction commerciale. Les outils nécessaires relèvent davantage de la gestion technique (dimensionnement, suivi de production) que de l'optimisation économique sophistiquée.

#### **ACC "bailleur social" : modèle intermédiaire à gouvernance simplifiée**

**Enjeux de volatilité des participants :** L'un des défis structurels des ACC réside dans la gestion de la liberté d'adhésion et de retrait des participants. Cette volatilité génère des coûts opérationnels et affecte la rentabilité économique selon les variations du nombre de membres.

Pour les bailleurs sociaux, cette problématique s'avère particulièrement sensible du fait de la rotation naturelle des locataires. La loi relative à l'énergie et au climat de 2019 a créé un cadre juridique spécifique : le bailleur social devient directement PMO et informe de l'existence de l'ACC lors de la signature du bail. Le locataire conserve sa liberté de choix de fournisseur et peut refuser de participer ou quitter l'opération à tout moment.

Ce modèle représente une part croissante des opérations mais conserve une logique sociale plutôt que commerciale. L'optimisation porte principalement sur l'équité de répartition et la réduction des charges locatives.

#### **ACC "multi-acteurs/communauté" : segment cible d'OptimPV**

Les opérations multi-acteurs, bien que minoritaires en nombre (environ 33% des opérations), constituent le segment présentant les enjeux d'optimisation technico-économique les plus avancés. Dans ce modèle, un développeur privé (SPV) installe une production photovoltaïque et vend l'électricité à des consommateurs tiers (particuliers, entreprises, collectivités).

**Enjeux d'optimisation cruciaux :** Contrairement aux ACC patrimoniales, ces projets nécessitent une optimisation fine du prix de vente pour équilibrer rentabilité du porteur de projet et attractivité pour les consommateurs. Le prix doit se positionner entre le coût de production (seuil de viabilité) et les tarifs réglementés (seuil d'attractivité), tout en intégrant les spécificités fiscales et réglementaires.

**Stratégies de déploiement :** Ces opérations peuvent débuter en configuration restreinte (périmètre d'un même bâtiment) pour constituer un socle de consommation stable, avant extension géographique vers d'autres participants aux profils complémentaires. Cette approche progressive permet d'optimiser le foisonnement des courbes de charge tout en maîtrisant les risques de développement. Le cas d'étude ABA gestion analysé en partie 2 illustre cette stratégie d'optimisation par diversification des profils de consommation.

**Gouvernance multi-parties :** La multiplicité des parties prenantes aux intérêts divergents (investisseurs, consommateurs, PMO) nécessite des outils d'aide à la décision avancés pour identifier les configurations gagnant-gagnant.

#### **Périmètre et justification d'OptimPV**

**OptimPV cible exclusivement les ACC multi-acteurs**, seul segment présentant des besoins réels d'optimisation algorithmique des paramètres technico-économiques. Les ACC patrimoniales, bien que majoritaires en nombre, ne constituent pas un marché pertinent pour des outils d'optimisation commerciale avancés.

Bien que réduisant le marché adressable, cette focalisation améliore sa pertinence. Elle justifie le développement d'une solution spécialisée sur les enjeux spécifiques de ce segment : optimisation de prix, modélisation financière multi-parties, gestion des clés de répartition avancées, et aide à la négociation commerciale.

Cette analyse de la segmentation du marché permet d'identifier les freins opérationnels spécifiques aux ACC multi-acteurs qui justifient le développement d'outils d'optimisation dédiés.

### Identification des freins : justification du développement d'OptimPV

L'analyse des retours d'expérience révèle cependant des coûts de transaction significatifs inhérents aux opérations d'ACC. Comme l'identifie le rapport HAL (2022) ﹕ "Contrairement aux autres dispositifs de production décentralisée d'énergie, l'ACC nécessite des formes d'intermédiation assez développées, qui génèrent des coûts de transaction propres, d'un montant plus ou moins élevé. Ils correspondent aux différentes tâches que la PMO doit effectuer, notamment autour du traitement des données, pour faire fonctionner l'opération, c'est-à-dire assurer une mise en relation des producteurs et consommateurs qui soit efficace aux plans technique, économique et organisationnel".

Les défis opérationnels, amplifiés par la multiplicité des paramètres technico-économiques et l'évolution réglementaire constante, justifie le développement de la plateforme OptimPV. L'automatisation et l'optimisation de ces processus de gestion constituent un enjeu majeur pour la viabilité économique des projets, particulièrement pour les opérations de taille modeste qui dominent le marché français.

 Quels modèles économiques structurent les flux de revenus et de coûts ?

L'économie de l'autoconsommation collective repose sur des modèles financiers structurés articulant multiples flux. Ces modèles intègrent des structures de revenus diversifiées et des postes de coûts spécifiques, et l'optimisation de ces modèles constitue l'enjeu central de la rentabilité des projets. L'optimisation nécessite une compréhension fine des mécanismes économiques sous-jacents selon l'analyse financière menée.

 #### Structure des revenus : autoconsommation et valorisation du surplus

Les revenus d'un projet d'autoconsommation collective se décomposent en deux flux principaux distincts. D'une part, les économies générées par l'autoconsommation locale constituent le premier flux de valeur, et d'autre part, la valorisation du surplus de production via la vente au réseau forme le second flux. Cette dualité structure l'ensemble du modèle économique et guide les stratégies d'optimisation.

L'électricité produite localement se substitue à l'électricité du réseau facturée aux tarifs réglementés. L'avantage économique dépend de l'écart entre le coût de production local et le prix réseau, qui intègre le tarif de base, la Contribution au Service Public de l'Électricité (CSPE de 2,25 c€/kWh en 2025) et la Taxe sur la Consommation Finale d'Électricité (TCFE variable selon les collectivités). Le Tarif Réglementé de Vente résidentiel s'établit à 25,16 c€/kWh toutes taxes comprises en 2025.

À l'inverse, l'évolution récente des tarifs de rachat du surplus révèle un effondrement dramatique de la valorisation. Les mécanismes d'obligation d'achat d'EDF offrent désormais des tarifs variables selon la puissance : 4,00 c€/kWh pour les installations de 0 à 9 kWc (chute de 69% depuis 2023-2024), 7,31 c€/kWh pour 9 à 100 kWc, et proche de 0 c€/kWh au-delà de 100 kWc où l'obligation d'achat disparaît totalement. Ces tarifs évoluent trimestriellement selon les mécanismes de dégressivité de la CRE.

L'écart considérable entre ces deux valorisations - 25,16 c€/kWh pour l'autoconsommation contre 4-7 c€/kWh pour le surplus - rend l'optimisation du taux d'autoconsommation particulièrement cruciale. Cette différence de valorisation de 1 à 6 justifie une analyse fine des profils de consommation et des stratégies de dimensionnement adaptées aux spécificités de chaque projet.

Cette valorisation du surplus présente cependant une rupture critique au seuil de 100 kWc : au-delà, l'absence d'obligation d'achat réduit drastiquement la valorisation du surplus, incitant les développeurs à sous-dimensionner les installations. Cette contrainte génère un gâchis énergétique en n'exploitant pas le potentiel maximal des toitures disponibles, les opérations étant dimensionnées sur la consommation en base plutôt que sur le potentiel de production optimal.

L'optimisation du ratio autoconsommation/surplus constitue un levier économique majeur. Si un taux d'autoconsommation élevé maximise les économies directes pour les participants, le surdimensionnement pour augmenter l'autoconsommation peut cependant dégrader la rentabilité globale. L'équilibre optimal dépend des profils de consommation et des caractéristiques techniques spécifiques. Par conséquent, cette optimisation nécessite des outils de simulation performants pour identifier les configurations optimales.

 Quelle structure de coûts caractérise les projets d'autoconsommation collective ?

La structure de coûts des projets d'autoconsommation collective intègre plusieurs postes spécifiques distincts. Généralement, les coûts d'investissement initial (CAPEX) représentent le poste le plus significatif, tandis que les charges d'exploitation annuelles (OPEX) impactent la rentabilité sur la durée de vie. En outre, les coûts de structure spécifiques à l'autoconsommation collective s'ajoutent aux postes traditionnels.
Les coûts d'investissement se décomposent en plusieurs sous-ensembles techniques identifiés. D'une part, les modules photovoltaïques représentent environ 30% du CAPEX total selon les études de marché récentes. Parallèlement, les onduleurs et équipements électriques constituent 15% de l'investissement initial, tandis que la structure porteuse et l'installation représentent 25% du coût total. De plus, les raccordements électriques et les compteurs spécialisés ajoutent 20% au montant global. Enfin, les études et frais de développement complètent avec 10% de l'investissement total.
Par ailleurs, l'évolution des coûts d'investissement suit une tendance baissière constante depuis 2010. En effet, l'Agence Internationale de l'Énergie (AIE) quantifie cette baisse à 65% sur la période 2010-2024. Cette réduction provient principalement de la diminution du coût des modules photovoltaïques, mais également de l'amélioration des rendements de production qui contribue à cette optimisation économique. Ainsi, les économies d'échelle dans la production industrielle expliquent en partie cette évolution favorable.
Les charges d'exploitation annuelles intègrent plusieurs postes récurrents spécifiques. La maintenance préventive et curative représente environ 1,5% du CAPEX annuellement. L'assurance multirisque ajoute 0,3% du montant de l'investissement initial. Le contrôle et la surveillance à distance nécessitent 0,2% du CAPEX par an. La gestion administrative et commerciale représente entre 2% et 4% du chiffre d'affaires. Ces charges varient selon la taille et les spécificités du projet développé.
Les coûts spécifiques à l'autoconsommation collective révèlent des enjeux particuliers identifiés par le rapport HAL (2022). Ces coûts de transaction comprennent deux composantes distinctes : d'une part la gestion administrative (facturation, suivi des données de consommation, gestion des clés de répartition), et d'autre part "l'animation de l'opération" qui consiste à "constituer et entretenir le collectif".

La dimension relationnelle s'avère critique pour les ACC multi-acteurs. Le rapport HAL souligne que cette animation nécessite de "générer, dans le temps, de la confiance, de la crédibilité, de la simplicité et à gérer le risque d'échec potentiel pour le collectif". Ces coûts relationnels incluent la négociation commerciale initiale, la résolution des conflits de facturation, la communication régulière avec les participants, et la production de rapports différenciés selon les parties prenantes (investisseurs, consommateurs, autorités).

L'analyse terrain révèle que ces coûts de gestion représentent généralement entre 8% et 15% des charges d'exploitation totales pour les ACC multi-acteurs, soit significativement plus que les 5% à 10% des ACC patrimoniales. Cet écart s'explique par les spécificités des relations multi-parties et la nécessité de maintenir l'engagement des consommateurs sur la durée de vie du projet.

L'optimisation de cette structure de coûts constitue un levier de compétitivité majeur pour les développeurs d'ACC multi-acteurs. La mutualisation des coûts de gestion entre plusieurs projets permet des économies d'échelle substantielles. L'automatisation des processus administratifs réduit les charges de personnel dédiées à la gestion opérationnelle. 

Concernant les coûts relationnels, leur réduction passe par la standardisation et la clarification des processus de communication. Des rapports automatisés et personnalisés selon les parties prenantes réduisent les besoins d'accompagnement individuel. La transparence des données de consommation et de facturation, facilitée par des logiciels spécialisés, diminue les sources de conflit et maintient la confiance dans la durée. Cette optimisation des aspects relationnels s'avère particulièrement critique pour la viabilité économique des projets de taille modeste où ces coûts fixes pèsent davantage.

### Les clés de répartition : un paramètre d'optimisation sous-exploité

Au-delà de l'optimisation des coûts et du prix de vente, la méthode de partage de l'énergie produite constitue un levier d'optimisation sociale souvent négligé. L'analyse des données Enedis révèle que 80% des opérations utilisent la clé de répartition "par défaut", qui répartit automatiquement l'énergie au prorata des consommations mesurées par les compteurs Linky (rapport HAL, 2022). Cette prédominance s'explique par sa simplicité administrative : aucune négociation contractuelle n'est nécessaire, la répartition s'effectue automatiquement selon les données de consommation réelle.

Les clés "dynamiques" (15%) et "statiques" (5%) restent sous-exploitées malgré leur potentiel d'optimisation sociale. Leur faible adoption résulte des exigences contractuelles qu'elles imposent : définir des critères de priorisation nécessite des négociations entre participants et une gestion administrative plus sophistiquée que la simple répartition automatique.

![Figure 1.4 : Répartition schématique des flux énergétiques](https://image.noelshack.com/fichiers/2025/36/1/1756736501-figure-1-3-repartition-flux.png)
*Figure 1.4 : Comparaison des trois méthodes de répartition appliquées aux mêmes participants (logement social, PME locale, résidence secondaire). La clé dynamique permet une optimisation sociale en priorisant le logement social, illustrant le potentiel des méthodes alternatives.*

L'enjeu d'optimisation sociale dépasse la simple répartition énergétique. Les clés dynamiques permettent de traduire contractuellement des objectifs territoriaux, comme privilégier les logements sociaux face aux résidences secondaires, ou soutenir les PME locales dans leur développement. Cette dimension sociale, absente de la clé par défaut, nécessite cependant une gouvernance plus élaborée et des outils d'aide à la décision pour identifier les configurations optimales selon le contexte local.

L'impact économique du choix de la clé de répartition varie selon la configuration du projet et les profils des participants. Une optimisation algorithmique de ce paramètre, intégrée à la plateforme OptimPV, permettrait d'identifier la méthode de répartition maximisant la satisfaction collective tout en respectant l'équité entre participants. L'expertise technique offre un avantage opérationnel aux projets utilisant des outils d'optimisation avancés.

### Le lien entre autoconsommation collective et sobriété énergétique

Au-delà de l'optimisation technico-économique, l'analyse des opérations d'ACC révèle une dimension souvent sous-estimée dans les modélisations financières : l'efficacité énergétique. Le rapport HAL identifie que cette dimension constitue un élément commun très présent dans l'ensemble des opérations d'ACC, servant parfois de fil conducteur pour certaines initiatives.

Cette double finalité - économique et comportementale - s'avère particulièrement prégnante dans les projets portés par les collectivités territoriales et les bailleurs sociaux. D'une part, ces acteurs recherchent une optimisation des coûts énergétiques pour leurs usagers. D'autre part, ils utilisent l'ACC comme un outil pédagogique pour rendre les participants "acteurs de leur propre consommation" et les inciter à réduire leur consommation globale.

L'intégration de cette dimension dans les outils d'optimisation comme OptimPV ouvre des perspectives fonctionnelles spécifiques. Les modules de suivi et de reporting sur les économies d'énergie réalisées permettent de quantifier l'impact comportemental. Les outils de simulation du "gain de sobriété" potentiel enrichissent l'analyse de rentabilité en intégrant les bénéfices environnementaux. Les fonctionnalités de communication facilitent l'animation communautaire autour d'objectifs partagés de réduction de la consommation.

Cette approche intégrée distingue l'optimisation technique de la simple maximisation de production. Elle reconnaît que l'enjeu n'est pas seulement de mieux produire, mais aussi de mieux consommer. Une telle approche intégrée différencie les plateformes d'optimisation de nouvelle génération.

 #### Impact des mécanismes tarifaires et fiscaux sur la rentabilité

Les mécanismes tarifaires et fiscaux exercent une influence déterminante sur la rentabilité des projets. Leur évolution récente modifie substantiellement les équilibres économiques établis précédemment. La compréhension fine de ces mécanismes conditionne l'optimisation des modèles d'affaires. Cette maîtrise devient un facteur clé de succès pour les porteurs de projets.
La suppression de l'accise sur l'électricité constitue l'évolution fiscale la plus structurante récente. Effective depuis le 1er mars 2025, elle élimine une charge de 33,7 €/MWh. L'impact sur la compétitivité des projets d'autoconsommation collective est considérable selon les simulations réalisées. Cette mesure permet une réduction du prix de vente de l'électricité d'environ 3,4 c€/kWh. L'attractivité pour les consommateurs participants s'améliore ainsi directement.
Les tarifs réglementés de vente d'électricité constituent la référence concurrentielle principale. Le Tarif Réglementé de Vente (TRV) résidentiel s'établit à 25,16 c€/kWh toutes taxes comprises en 2025. Ce tarif intègre l'ensemble des composantes tarifaires et fiscales applicables. L'évolution de ce tarif influence directement la compétitivité de l'autoconsommation collective. Une augmentation du TRV améliore mécaniquement l'attractivité des projets décentralisés.
L'optimisation fiscale des structures juridiques constitue un levier additionnel de performance. Le choix de la forme juridique de la PMO influence la fiscalité applicable. Les structures associatives bénéficient d'exonérations spécifiques sous certaines conditions. Les sociétés commerciales supportent l'impôt sur les sociétés au taux de 25%. Cette différenciation guide le choix de structuration juridique selon les objectifs poursuivis.
La Taxe sur la Valeur Ajoutée (TVA) s'applique différemment selon la nature des opérations. Les ventes d'électricité sont soumises au taux réduit de 5,5% pour les installations inférieures à 3 kW. Le taux normal de 20% s'applique pour les puissances supérieures selon la réglementation. Les modèles économiques et choix de dimensionnement en dépendent directement. L'optimisation de la TVA nécessite une structuration juridique et technique cohérente.

La déductibilité de la TVA sur les investissements dépend du statut fiscal de la PMO. Les structures assujetties peuvent récupérer la TVA sur les équipements et prestations. Cette récupération améliore significativement l'économie du projet selon les simulations financières. Elle représente 20% du montant de l'investissement initial hors taxes. L'économie substantielle justifie souvent le choix d'un statut assujetti malgré les contraintes administratives.

 Quels facteurs déterminent l'équilibre économique des projets ?

L'équilibre économique des projets d'autoconsommation collective résulte de l'articulation délicate entre revenus et charges. Plusieurs facteurs clés déterminent cet équilibre selon une sensibilité variable. L'identification et la hiérarchisation de ces facteurs orientent les stratégies d'optimisation. Cette analyse guide les décisions de conception et de dimensionnement des installations.
Le prix de vente de l'électricité aux participants constitue le paramètre d'équilibre central. Ce prix doit assurer la viabilité économique du projet tout en restant attractif, et se positionne généralement entre le coût de production et le tarif réglementé. L'écart avec le tarif réglementé détermine l'attractivité pour les consommateurs, tandis que la marge par rapport au coût de production conditionne la rentabilité du porteur de projet.
Le taux d'autoconsommation influence directement les revenus du projet selon un effet multiplicateur. Si un taux élevé maximise la valorisation de la production au prix de vente négocié, un taux faible nécessite une valorisation importante du surplus au tarif d'obligation d'achat. L'optimisation de ce taux passe par l'adéquation entre profils de production et de consommation, cette adéquation dépendant de la saisonnalité et des habitudes de consommation des participants.
La durée de vie économique du projet détermine la répartition des charges d'investissement. Une durée de 20 ans constitue généralement la référence pour l'amortissement comptable. Les garanties constructeurs s'étendent sur 25 ans pour les modules photovoltaïques actuels. Cette extension de garantie améliore la sécurité financière et facilite l'obtention de financements. Elle permet également d'envisager des modèles économiques sur durées plus longues.
Le coût du financement impacte significativement la rentabilité selon le mode retenu. Si un financement par fonds propres évite les charges financières, il immobilise cependant les capitaux. À l'inverse, le recours à l'emprunt génère des intérêts mais optimise la rentabilité des capitaux propres. Les taux d'intérêt actuels pour les projets d'énergies renouvelables varient entre 3% et 5%, cette variation dépendant de la qualité du porteur de projet et des garanties offertes.
L'optimisation de ces paramètres nécessite des outils de simulation et d'aide à la décision performants. L'interdépendance entre variables complique l'identification manuelle des configurations optimales, justifiant le recours à des logiciels spécialisés pour l'exploration de scénarios et l'optimisation multi-critères.

**Cette conclusion sur la nécessité d'outils avancés amène naturellement à examiner l'offre existante sur le marché.** L'analyse des solutions disponibles permettra d'identifier les lacunes et de définir les spécifications d'OptimPV pour répondre aux besoins spécifiques des ACC multi-acteurs.

### Chapitre 2 : Analyse des Outils Existants et Spécifications d'OptimPV

Le marché des outils d'aide à la décision pour les projets photovoltaïques présente une segmentation importante. Cette segmentation reflète la diversité des acteurs et des besoins selon l'analyse menée. Or, les solutions existantes présentent des limitations significatives pour l'autoconsommation collective française, et ces lacunes justifient le développement d'une solution spécialisée interne.

 Quelles solutions académiques et institutionnelles structurent l'offre actuelle ?

Les solutions académiques et institutionnelles constituent un segment important de l'offre d'outils d'analyse. Ces solutions, développées par les organismes de recherche, offrent généralement une sophistication technique élevée. Ainsi, l'Institut National de l'Énergie Solaire (INES) propose des outils de dimensionnement reconnus par la profession, tandis que le Centre Scientifique et Technique du Bâtiment (CSTB) développe des logiciels de simulation énergétique spécialisés.
L'outil PVsyst constitue la référence internationale pour la simulation photovoltaïque selon les retours professionnels. Développé par l'Université de Genève, il intègre des modèles physiques avancés, et sa base de données météorologiques couvre l'ensemble du territoire français avec précision. Les fonctionnalités de simulation permettent une modélisation fine des performances techniques, tandis que l'exportation de rapports détaillés facilite la documentation des projets pour les investisseurs.
Cependant, PVsyst présente des limitations importantes pour les ACC multi-acteurs françaises. D'une part, l'outil ne traite pas spécifiquement les contraintes réglementaires françaises, et la modélisation économique reste généraliste sans prendre en compte les spécificités fiscales. D'autre part, il ne propose aucune fonctionnalité pour gérer les coûts relationnels identifiés par le rapport HAL : génération de rapports différenciés, outils de communication avec les parties prenantes, ou suivi de la satisfaction des participants. L'interface utilisateur technique nécessite une formation approfondie, et le coût de licence élevé limite l'accessibilité pour les développeurs de projets de taille modeste.
L'Agence de l'Environnement et de la Maîtrise de l'Énergie (ADEME) propose des outils gratuits accessibles en ligne. Ces outils visent à démocratiser l'accès à l'analyse technique selon la mission de l'agence. Cependant, leur simplicité limite la finesse d'analyse nécessaire pour les projets professionnels. La mise à jour des paramètres réglementaires suit les évolutions avec retard. L'absence d'intégration avec d'autres outils complique l'utilisation dans les workflows professionnels.
Les solutions académiques privilégient généralement la précision technique sur l'utilisabilité opérationnelle. Cette orientation répond aux besoins de recherche mais limite l'adoption par les praticiens. L'interface utilisateur souvent technique constitue une barrière à l'adoption généralisée. L'inadaptation aux contraintes opérationnelles des entreprises limite leur diffusion professionnelle significativement.

 #### Solutions commerciales et écosystème concurrentiel

L'analyse du marché des outils photovoltaïques révèle une segmentation complexe structurée autour de trois catégories d'acteurs aux stratégies distinctes : les éditeurs logiciels traditionnels proposant des solutions commerciales généralistes, les opérateurs "Energy as a Service" développant des plateformes internes propriétaires, et enfin les solutions spécialisées émergentes dédiées à l'autoconsommation collective. Cette tripartition révèle des approches radicalement différentes face aux enjeux spécifiques des ACC multi-acteurs.

##### Solutions logicielles commerciales traditionnelles

Les solutions commerciales développées par des éditeurs logiciels privés structurent une part croissante du marché, bénéficiant d'investissements significatifs dans l'ergonomie et l'intégration aux processus commerciaux. Ces solutions présentent généralement une supériorité ergonomique par rapport aux outils académiques, facilitant ainsi leur adoption par les professionnels.

Parmi les acteurs dominants, la société allemande Valentin Software développe PV*SOL, positionné comme concurrent direct de PVsyst. Cet outil intègre des fonctionnalités avancées de dimensionnement et d'analyse économique, tandis que son interface modernisée facilite la prise en main pour les non-spécialistes. Par ailleurs, la génération automatique de rapports commerciaux accélère significativement les processus de vente. Toutefois, le coût élevé des licences limite l'accessibilité pour les petites structures de développement.

Concernant l'offre française, celle-ci demeure limitée sur ce segment spécialisé. D'une part, la société Tecsol propose des outils spécialisés mais exclusivement destinés aux bureaux d'études experts, nécessitant une expertise technique approfondie. D'autre part, l'entreprise Sunology développe des calculateurs simplifiés orientés vers l'autoconsommation individuelle. Ces solutions françaises présentent cependant une lacune majeure : aucune ne traite spécifiquement l'autoconsommation collective avec ses spécificités réglementaires complexes.

Parallèlement, l'émergence de solutions SaaS (Software as a Service) transforme progressivement les modèles économiques du secteur. Ces plateformes cloud réduisent les coûts d'acquisition initiaux tout en facilitant les mises à jour réglementaires. Ainsi, la société norvégienne Glint Solar propose une plateforme d'analyse géographique et technique, tandis que l'outil américain HelioScope de Folsom Labs se spécialise dans la conception d'installations complexes. Néanmoins, ces solutions internationales présentent un défaut structurel : elles ne prennent pas en compte les spécificités du marché français, créant un décalage entre sophistication technique et applicabilité opérationnelle locale.

##### Écosystème des opérateurs "Energy as a Service" : un modèle d'innovation propriétaire

Parallèlement à cette offre logicielle traditionnelle, l'essor du modèle "Energy as a Service" (EaaS) a fait émerger un écosystème structurellement différent d'opérateurs développant des plateformes internes sophistiquées exclusivement destinées à leurs propres opérations. Cette analyse révèle un paradoxe significatif : malgré des investissements considérables dans l'innovation technologique, aucun de ces acteurs ne commercialise ses outils vers l'externe, créant un gap de marché structurel.

Engie occupe une position dominante sur le marché français de l'EaaS, s'appuyant sur des plateformes internes d'une sophistication technique remarquable pour déployer son offre "My Power TPE/PME" et ses PPA "Greenfield". L'opérateur revendique des économies atteignant 36 000€/an pour ses clients PME via des engagements contractuels de 15 à 20 ans. Ces outils internes intègrent des fonctionnalités avancées de dimensionnement automatisé, de surveillance télémétrique et de génération différenciée de rapports selon les parties prenantes. Cependant, cette expertise technologique reste inaccessible aux développeurs externes, les plateformes demeurant strictement propriétaires.

Dans une dynamique similaire, TotalEnergies déploie une stratégie d'intégration verticale à l'échelle industrielle, ayant contracté plus de 1,5 GW de PPAs avec 600+ clients en 2024, dont 1,1 GW déjà opérationnels. L'opérateur mobilise des outils propriétaires couvrant l'ensemble de la chaîne de valeur, du développement au financement et à l'exploitation, comme l'illustrent des réalisations d'envergure telles que le carport de 12,3 MWc de l'aéroport JFK ou la centrale flottante de 31 MWc en Belgique. Cette intégration complète, depuis la production de modules jusqu'à la commercialisation d'énergie, confère à TotalEnergies des capacités d'optimisation exceptionnelles mais non partagées.

GreenYellow, ancienne filiale du groupe Casino devenue acteur indépendant, illustre parfaitement la spécialisation sectorielle dans le "Photovoltaic as a Service" (PVaaS). L'entreprise a orchestré une transformation stratégique significative, basculant de 70-80% de projets en vente totale vers 70-80% d'autoconsommation suite à la crise énergétique. L'exemple du déploiement Decathlon en Pologne (3 MW répartis sur 14 magasins, contrat 15 ans, production 3 GWh/an) démontre les capacités de gestion centralisée multi-sites via des outils internes propriétaires.

Cette tendance s'étend aux acteurs émergents européens, comme UrbanVolt en Irlande et au Royaume-Uni, qui revendique 400+ installations déployées via des contrats "solar & lighting as a service" de 10-15 ans. Cette entreprise cible spécifiquement les PME industrielles et logistiques en proposant des tarifs structurellement inférieurs aux tarifs réseau traditionnels.

Le constat qui émerge de cette analyse est critique pour l'écosystème : l'ensemble de ces acteurs développent des solutions technologiques sophistiquées mais adoptent systématiquement des stratégies propriétaires sans commercialisation externe. Cette approche génère un cercle vicieux où chaque nouveau développeur d'ACC doit recréer ab initio ses propres processus et outils d'optimisation, multipliant les coûts de développement et ralentissant la croissance sectorielle.

##### Solutions spécialisées autoconsommation collective : l'émergence d'un marché de niche

Face à ces deux premiers segments, le marché des solutions spécifiquement dédiées à l'autoconsommation collective présente un paysage radicalement différent, caractérisé par sa jeunesse et sa forte spécialisation. Cette analyse révèle l'émergence progressive d'acteurs innovants mais également les limites structurelles du marché actuel.

Enogrid constitue l'unique acteur français véritablement spécialisé dans l'outillage de l'autoconsommation collective. Fondée en 2018, cette entreprise édite trois plateformes complémentaires : EnoLab pour la simulation de projets, EnoPower pour la conception de répartition des flux, et "Mon Énergie Collective" pour le suivi opérationnel des consommations. Avec 35 employés et 350+ projets accompagnés, Enogrid a démontré sa capacité à structurer ce marché émergent. Les levées de fonds successives (1,1 M€ en 2023 auprès d'Engie et Schneider Electric, puis 1,4 M€ via financement participatif en 2025) valident le potentiel économique de ce segment. Toutefois, l'offre d'Enogrid présente des limitations significatives : les solutions se limitent à des abonnements SaaS de gestion administrative sans intégrer les dimensions cruciales de financement et d'optimisation algorithmique des paramètres économiques.

SerenyCalas illustre parfaitement le paradoxe du marché ACC en révélant l'ampleur du gap concurrentiel existant. Cette SAS créée en 2018, spécialisée dans le développement opérationnel d'ACC multi-acteurs, a réalisé une croissance exceptionnelle en multipliant ses effectifs par cinq (de 6 à 30 salariés) entre 2018 et 2025. Cette progression témoigne de la demande latente pour des services spécialisés ACC. Cependant, SerenyCalas reproduit le modèle propriétaire observé chez les grands opérateurs EaaS : l'entreprise développe exclusivement des outils internes pour ses propres opérations, sans aucune commercialisation externe. Cette stratégie confirme l'existence d'une lacune structurelle dans l'offre d'outils commerciaux accessibles aux développeurs d'ACC indépendants.

L'analyse de ces trois segments concurrentiels fait émerger un constat paradoxal : malgré l'explosion du marché ACC (×10 en 4 ans selon les données Enedis), l'écosystème d'outils demeure sous-développé et fragmenté. D'une part, les solutions commerciales traditionnelles adoptent une approche généraliste inadaptée aux spécificités réglementaires françaises. D'autre part, les acteurs les plus innovants conservent jalousement leurs développements technologiques sans créer d'économies d'échelle via la commercialisation. Enfin, les rares solutions spécialisées ACC restent limitées dans leur périmètre fonctionnel.

Cette triple inadéquation - généralisme des outils internationaux, propriétarisme des plateformes EaaS, et spécialisation limitée des solutions dédiées - crée des opportunités de marché significatives pour une solution intégrée combinant expertise réglementaire française, sophistication algorithmique et accessibilité commerciale. Cette lacune justifie le développement d'OptimPV comme première solution commerciale intégrant l'ensemble de la chaîne de valeur ACC : prospection géographique, optimisation algorithmique, modélisation financière multi-parties et gestion des aspects relationnels spécifiques aux projets multi-acteurs.

#### Quels besoins non couverts créent des opportunités de différenciation ?

L'identification des besoins non couverts par les solutions existantes révèle plusieurs opportunités significatives. La première concerne l'intégration complète de la chaîne de valeur selon une approche holistique. Aucune solution actuelle ne propose une intégration depuis la prospection géographique jusqu'à la facturation. Cette lacune oblige les développeurs de projets à utiliser multiples outils sans cohérence. L'intégration complète permet une optimisation des processus internes et une réduction des coûts de développement.
La seconde opportunité porte sur la spécialisation française et l'intégration temps réel des évolutions réglementaires. Les récentes modifications du cadre fiscal et réglementaire nécessitent une adaptation rapide. La suppression de l'accise effective depuis mars 2025 illustre cette nécessité d'adaptation. Les outils actuels présentent des délais de mise à jour incompatibles avec la réactivité commerciale. Une solution spécialisée pourrait intégrer automatiquement les évolutions normatives françaises.
La troisième opportunité concerne l'optimisation automatisée des paramètres économiques selon une approche algorithmique. La détermination du prix de vente optimal nécessite une optimisation multi-contraintes avancée. Cette optimisation doit maximiser la rentabilité tout en respectant les contraintes réglementaires. Elle doit également maintenir l'attractivité pour les consommateurs participants. Aucune solution existante ne traite cette problématique d'optimisation de manière satisfaisante.
La quatrième opportunité porte sur l'accessibilité pour les non-spécialistes selon une approche démocratisante. Le développement de l'autoconsommation collective implique une diversification des acteurs. Les collectivités territoriales entrent sur le marché sans expertise technique approfondie. Les PME et particuliers porteurs de projets manquent souvent de compétences spécialisées. Les outils actuels requièrent un niveau de spécialisation élevé constituant une barrière.
La cinquième opportunité concerne la gestion des aspects relationnels spécifiques aux ACC multi-acteurs. Le rapport HAL identifie la nécessité de "générer, dans le temps, de la confiance, de la crédibilité, de la simplicité" pour maintenir l'engagement des participants. Cette dimension relationnelle nécessite des outils de communication adaptés : génération automatisée de rapports personnalisés selon les parties prenantes, tableaux de bord transparents sur les performances individuelles et collectives, et outils de suivi de satisfaction des participants. Les dossiers techniques pour les autorités administratives nécessitent un format spécifique, les présentations commerciales pour les prospects doivent être attractives et simplifiées, les rapports financiers pour les investisseurs exigent un niveau de détail élevé. Cette gestion multidimensionnelle des relations parties prenantes n'est traitée par aucune solution existante.
La sixième opportunité porte sur l'intégration d'outils de prospection et de qualification commerciale géographique. L'identification des opportunités de projets nécessite une analyse territoriale fine. La priorisation des efforts commerciaux selon le potentiel économique optimise les ressources. Cette dimension commerciale en amont n'est pas intégrée dans les outils techniques existants. L'intégration complète faciliterait l'identification et la conversion des prospects qualifiés.

 Quelle approche de développement assure une spécialisation technique durable ?

L'approche de développement retenue pour OptimPV s'appuie sur quatre piliers techniques complémentaires. Cette approche multi-dimensionnelle assure une spécialisation opérationnelle durable selon l'analyse conduite. L'articulation cohérente de ces piliers crée une expertise interne difficilement reproductible.
Le premier pilier concerne l'intégration fonctionnelle complète de la prospection à la facturation. Cette approche répond directement aux besoins exprimés par les professionnels de simplification. L'optimisation des workflows via une interface unique améliore l'efficacité opérationnelle. La réduction du nombre d'outils nécessaires diminue les coûts informatiques et de formation. Cette intégration constitue un avantage concurrentiel difficile à reproduire rapidement.
Le second pilier porte sur la spécialisation française et l'actualisation continue des paramètres normatifs. La plateforme intègre nativement les spécificités du marché français selon une approche dédiée. Les mécanismes de mise à jour automatisée maintiennent la cohérence avec l'évolution réglementaire. Cette spécialisation crée une expertise interne adaptée au contexte français. Elle constitue un avantage opérationnel par rapport aux outils généralistes.
Le troisième pilier concerne l'optimisation algorithmique des paramètres économiques via des fonctionnalités avancées. L'optimisation automatique du prix de vente maximise la rentabilité sous contraintes multiples. Cette capacité d'optimisation différencie OptimPV des approches purement descriptives concurrentes. Elle apporte une valeur ajoutée mesurable et démontrable pour les utilisateurs. Cette sophistication technique constitue un avantage compétitif durable.

Le quatrième pilier porte sur l'accessibilité et l'ergonomie comme avantage concurrentiel décisif. L'interface graphique intuitive d'OptimPV constitue un gain de productivité majeur par rapport aux approches manuelles sur tableur Excel couramment utilisées dans le secteur. Elle permet aux bureaux d'études d'accéder à des fonctionnalités d'optimisation avancées sans formation spécialisée prolongée, tout en conservant la sophistication technique nécessaire aux experts. Cette ergonomie facilite l'adoption interne et accélère les processus de développement de projets.
Cette approche de développement s'appuie sur des spécialisations techniques et fonctionnelles adaptées aux besoins internes. L'intégration complète nécessite des développements conséquents et une connaissance approfondie du métier. Cette combinaison d'expertise technique et sectorielle constitue un atout opérationnel durable pour la solution développée.

Il convient cependant de souligner que le développement d'OptimPV présente une dépendance réglementaire forte inhérente au secteur de l'autoconsommation collective. Les évolutions fréquentes du cadre normatif (suppression d'accise, modification des seuils TURPE, évolution des périmètres géographiques) nécessitent une capacité d'adaptation continue de l'outil. Cette dépendance constitue un risque opérationnel qui doit être anticipé par des mécanismes de veille réglementaire et des architectures logicielles modulaires permettant une mise à jour rapide des paramètres de calcul.

 Chapitre 3 : Analyse Technico-Économique et Leviers d'Optimisation

 Quels paramètres clés déterminent la performance des projets photovoltaïques ?
L'optimisation technico-économique des projets photovoltaïques nécessite une compréhension fine de l'influence des différents paramètres. Cette analyse de sensibilité permet d'identifier les leviers d'action prioritaires selon leur impact relatif, et l'orientation des efforts d'optimisation vers les variables les plus impactantes améliore l'efficacité des démarches. Par conséquent, cette hiérarchisation guide les stratégies de développement et les choix techniques fondamentaux.
 #### Structure des coûts d'investissement et impact sur la rentabilité

Les coûts d'investissement (CAPEX) constituent le poste le plus significatif dans l'économie des projets photovoltaïques. Ils présentent la plus forte sensibilité sur les indicateurs de rentabilité selon l'analyse financière menée, et l'optimisation de ces coûts représente le levier principal d'amélioration de la performance économique. Cette optimisation nécessite une décomposition précise des différents postes pour identifier les opportunités.
La structure détaillée des coûts d'investissement révèle plusieurs postes aux évolutions différenciées. Les modules photovoltaïques représentent 35% à 45% du CAPEX total selon les technologies retenues. Cette proportion varie selon le type de cellules (silicium monocristallin, polycristallin ou couches minces). Les onduleurs et équipements électriques constituent 12% à 18% de l'investissement initial. La structure porteuse et l'installation représentent 20% à 30% du coût total selon les spécificités.
Les raccordements électriques et comptages spécialisés ajoutent 8% à 15% au montant global. Cette variation dépend de la distance au point de raccordement et des spécificités techniques. Les études, développement et frais annexes complètent avec 8% à 12% de l'investissement total. Ces frais incluent les études d'ingénierie, les autorisations administratives et l'accompagnement juridique nécessaire.
L'évolution temporelle de ces coûts suit des trajectoires différenciées selon les composants. L'Agence Internationale de l'Énergie (AIE, 2024) quantifie la baisse des modules à 85% sur la période 2010-2024. Cette réduction massive provient des économies d'échelle dans la production asiatique. L'amélioration des rendements contribue également à cette optimisation par unité de puissance installée.

Les coûts d'installation et de raccordement suivent une évolution moins favorable. Ces postes intègrent principalement de la main-d'œuvre locale aux coûts stables. L'amélioration de la productivité compense partiellement l'inflation des coûts salariaux. Les gains proviennent de la standardisation des procédures et de l'expérience des installateurs.

L'optimisation du CAPEX nécessite une approche globale intégrant tous les postes simultanément. En effet, la recherche du composant le moins cher peut dégrader la performance globale, et l'équilibre entre coût initial et performance long terme guide les choix techniques. Par conséquent, cette optimisation multi-critères justifie l'utilisation d'outils d'aide à la décision spécialisés.

La sensibilité de la rentabilité au CAPEX suit une relation linéaire directe. Ainsi, une réduction de 10% du CAPEX améliore la Valeur Actuelle Nette (VAN) de 15% à 20%. Cette amplification provient de l'effet de levier de l'investissement initial sur l'ensemble des flux, et justifie la priorité accordée à l'optimisation des coûts d'investissement dans les stratégies de développement.

 #### Impact des charges d'exploitation sur la performance long terme

Les charges d'exploitation (OPEX) exercent un impact cumulatif significatif sur la rentabilité long terme, et leur influence s'accroît avec la durée de vie du projet selon un effet d'accumulation. L'optimisation de ces charges constitue un levier de performance souvent sous-estimé, et leur maîtrise conditionne la viabilité économique sur l'ensemble de la période d'exploitation prévue.

La structure des charges d'exploitation intègre plusieurs postes récurrents aux évolutions spécifiques. D'une part, la maintenance préventive et curative représente 1,2% à 1,8% du CAPEX annuellement, cette proportion variant selon la qualité des équipements initiaux et les conditions d'exploitation. D'autre part, l'assurance multirisque ajoute 0,25% à 0,35% du montant de l'investissement par an, les tarifs dépendant de la localisation géographique et des garanties souscrites.

Le contrôle et la surveillance à distance nécessitent 0,15% à 0,25% du CAPEX annuellement. Ces coûts incluent les systèmes de monitoring et l'abonnement aux services de supervision. La gestion administrative et commerciale représente 1,5% à 3,5% du chiffre d'affaires selon les spécificités. Cette variabilité dépend du nombre de participants et des modalités de facturation retenues.

Les charges spécifiques à l'autoconsommation collective majorent ces coûts de base significativement. La gestion de la Personne Morale Organisatrice (PMO) nécessite des compétences juridiques spécialisées. La facturation individuelle aux participants génère des coûts administratifs proportionnels au nombre. La gestion des clés de répartition et le suivi des consommations alourdissent les processus. Ces surcoûts représentent 4% à 8% des charges d'exploitation totales selon la taille.

L'évolution temporelle des charges d'exploitation suit généralement l'inflation générale. Certains postes présentent des dynamiques spécifiques selon leur nature. Les coûts de maintenance tendent à augmenter avec l'âge des équipements. Les charges administratives peuvent bénéficier d'économies d'échelle avec la croissance. L'automatisation des processus réduit progressivement les coûts de gestion humaine.

L'optimisation des OPEX passe par plusieurs leviers d'action complémentaires. La mutualisation des coûts de gestion entre projets permet des économies d'échelle substantielles. L'automatisation des processus administratifs réduit les charges de personnel dédiées. Les logiciels spécialisés améliorent l'efficacité opérationnelle. La contractualisation de maintenance globale optimise les coûts techniques.

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
Les tarifs réglementés de vente évoluent selon plusieurs facteurs structurels et conjoncturels. L'évolution des coûts de production de l'électricité influence les tarifs de base. Les investissements dans les réseaux de transport et distribution répercutent leurs coûts. Les taxes et contributions évoluent selon les politiques publiques énergétiques. Cette multifactorialité complique la prévision des évolutions tarifaires.
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

Le positionnement tarifaire par rapport aux tarifs réglementés détermine l'attractivité commerciale du projet, et cette attractivité conditionne la capacité de recrutement des participants nécessaires. Le positionnement doit créer une valeur perçue suffisante tout en préservant la marge. Par conséquent, cette équation délicate nécessite une analyse fine des composantes tarifaires et des perceptions clients.
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
L'algorithme d'optimisation explore l'espace des solutions selon une méthode heuristique performante. Les algorithmes génétiques permettent l'exploration de solutions avancées non-linéaires. Les méthodes de gradient optimisent localement les solutions identifiées. L'hybridation de ces approches améliore la robustesse et la rapidité de convergence.

La modélisation de l'attractivité commerciale intègre des fonctions de demande selon les segments. La sensibilité prix varie selon le type de participant et sa situation énergétique. Les particuliers présentent une élasticité-prix modérée selon les études comportementales. Les entreprises affichent une sensibilité plus élevée selon leurs contraintes de compétitivité.
L'intégration des contraintes réglementaires limite l'espace d'optimisation selon les règles applicables. Le prix de vente ne peut dépasser le tarif réglementé selon la réglementation. Il doit couvrir les coûts de production pour assurer la viabilité. Ces contraintes bornent l'optimisation et garantissent la conformité réglementaire.
L'optimisation multi-objectifs intègre des critères autres que la rentabilité financière pure. L'impact environnemental peut être intégré via des coefficients de pondération. L'acceptabilité sociale influence les choix selon les contextes territoriaux. Cette approche élargie améliore la robustesse des solutions dans la durée.
La validation des solutions optimisées nécessite des tests de sensibilité aux paramètres incertains. Les variations des coûts d'investissement testent la robustesse des configurations. L'évolution des tarifs réglementés évalue la stabilité des solutions. Cette validation améliore la confiance dans les recommandations algorithmiques.
L'implémentation opérationnelle de l'optimisation nécessite des interfaces utilisateur adaptées. La sophistication algorithmique doit être masquée aux utilisateurs non-experts. Les résultats doivent être présentés de manière pédagogique et actionnable. Cette ergonomie conditionne l'adoption et l'utilisation effective des outils développés.

 #### Intégration des spécificités du marché français

L'intégration des spécificités françaises dans l'optimisation nécessite une connaissance approfondie du contexte réglementaire. Ces spécificités influencent directement les contraintes et opportunités d'optimisation applicables. Leur prise en compte différencie les solutions locales des approches internationales généralistes. Cette spécialisation constitue un avantage concurrentiel pour les outils dédiés au marché français.
La réglementation française de l'autoconsommation collective impose des contraintes spécifiques d'optimisation. Le périmètre géographique limite les participants selon des règles de proximité. Les seuils de puissance bornent la taille des projets selon les catégories réglementaires. Ces contraintes doivent être intégrées comme conditions impératives dans l'optimisation.
La fiscalité française présente des spécificités impactant directement l'équation économique d'optimisation. La suppression récente de l'accise modifie les équilibres selon une évolution majeure. La TVA à taux réduit pour certaines installations influence les coûts. Ces paramètres fiscaux doivent être actualisés en temps réel pour maintenir la pertinence.
Les tarifs réglementés français suivent une structure tarifaire spécifique selon les segments de clientèle. Les tarifs résidentiels intègrent une progressivité selon les niveaux de consommation. Les tarifs professionnels différencient puissance souscrite et énergie consommée. Cette structure tarifaire nécessite une modélisation précise pour l'optimisation.

L'écosystème d'acteurs français influence les contraintes commerciales et techniques applicables. Enedis structure l'interface technique avec des procédures standardisées nationales. EDF obligation d'achat définit les conditions de valorisation du surplus. Ces contraintes institutionnelles bornent l'espace d'optimisation selon les règles nationales.
Les profils de consommation français présentent des caractéristiques culturelles et climatiques spécifiques. La saisonnalité de la consommation électrique suit les variations climatiques nationales. Les habitudes de consommation diffèrent selon les régions et les types d'habitat. Cette variabilité doit être intégrée dans la modélisation d'optimisation.
La prise en compte de l'évolution réglementaire future améliore la robustesse de l'optimisation. Les projets de modification du cadre législatif influencent les anticipations. L'harmonisation européenne des réglementations peut modifier les contraintes nationales. Cette prospective réglementaire guide les choix d'optimisation long terme.
L'adaptation culturelle de l'optimisation facilite l'acceptation par les utilisateurs français. La terminologie technique doit respecter les usages professionnels nationaux. Les unités et conventions de calcul suivent les standards français établis. Cette adaptation améliore la compréhension et l'adoption des outils développés.

 Quelle synthèse des besoins guide la définition du cahier des charges fonctionnel ?

L'analyse technico-économique conduite révèle des besoins structurants pour l'optimisation des projets d'autoconsommation collective. Cette analyse guide la définition d'un cahier des charges fonctionnel intégrant l'ensemble des contraintes identifiées. La synthèse de ces besoins oriente la conception d'un outil d'aide à la décision adapté. Cette synthèse assure la cohérence entre analyse préliminaire et spécifications techniques futures.

 Quels besoins fonctionnels prioritaires structurent les exigences utilisateurs ?

L'identification des besoins fonctionnels prioritaires résulte de l'analyse des contraintes et opportunités sectorielles. Ces besoins structurent les exigences utilisateurs selon une hiérarchisation de l'importance opérationnelle. Leur satisfaction conditionne l'adoption et l'utilisation effective des outils développés. Cette priorisation guide l'allocation des ressources de développement selon la valeur ajoutée.
Le premier besoin fonctionnel concerne l'optimisation automatisée des paramètres technico-économiques selon une approche intégrée. Cette optimisation doit déterminer le dimensionnement optimal des installations selon les contraintes locales. Elle doit calculer le prix de vente maximisant la rentabilité sous contraintes réglementaires. Cette automatisation libère les utilisateurs des calculs avancés et améliore la qualité des analyses.
Le deuxième besoin porte sur la modélisation financière avancée intégrant les spécificités françaises. Cette modélisation doit calculer les indicateurs de rentabilité standards selon les méthodes reconnues. Elle doit intégrer la fiscalité française dans ses évolutions récentes. La génération de scenarios multiples doit faciliter l'analyse de sensibilité. Cette sophistication financière répond aux exigences des investisseurs et financeurs.

Le troisième besoin concerne l'actualisation continue des paramètres réglementaires et fiscaux français. Cette actualisation doit intégrer automatiquement les évolutions normatives impactant les projets. Elle doit maintenir la cohérence des calculs avec le cadre légal applicable. Cette fiabilité réglementaire conditionne la qualité juridique des analyses produites. Elle constitue un facteur critique de confiance pour les utilisateurs professionnels.
Le quatrième besoin porte sur la génération automatisée de rapports professionnels adaptés aux différents publics. Ces rapports doivent répondre aux attentes des investisseurs selon les standards financiers. Ils doivent faciliter les présentations commerciales auprès des prospects. La documentation technique doit respecter les exigences administratives. Cette diversification des livrables répond à la multiplicité des parties prenantes impliquées.
Le cinquième besoin concerne l'intégration d'outils de prospection et de qualification commerciale territoriale. Ces outils doivent identifier les opportunités de projets selon les critères techniques et économiques. Ils doivent prioriser les efforts commerciaux selon le potentiel de rentabilité. Cette dimension commerciale amont optimise l'allocation des ressources de développement. Elle améliore la performance commerciale des porteurs de projets.
La satisfaction de ces besoins fonctionnels nécessite une architecture logicielle modulaire et évolutive. Chaque besoin correspond à un module spécialisé aux interfaces définies. L'intégration entre modules assure la cohérence d'ensemble selon une approche systémique. Cette modularité facilite la maintenance et l'évolution future selon les besoins émergents.

 Quelles exigences techniques et architecturales découlent de l'analyse fonctionnelle ?

Les exigences techniques dérivées de l'analyse fonctionnelle imposent des contraintes d'architecture significatives. Ces contraintes visent à assurer la performance, la fiabilité et l'évolutivité de la solution, et l'architecture technique doit supporter la richesse fonctionnelle tout en maintenant l'utilisabilité. Par conséquent, cette conception constitue un enjeu critique pour le succès opérationnel de la plateforme.
L'exigence de performance nécessite une architecture optimisée pour les calculs d'optimisation avancés. En effet, les algorithmes d'optimisation multi-contraintes nécessitent une puissance de calcul importante, et l'objectif de temps de réponse inférieur à 10 secondes guide les choix techniques. Cette performance conditionne l'acceptabilité pour un usage interactif en contexte professionnel.
L'exigence de fiabilité impose la mise en œuvre de mécanismes de validation robustes. La validation des données d'entrée doit détecter les erreurs et incohérences. La vérification de cohérence des résultats doit identifier les anomalies de calcul. La traçabilité des calculs doit permettre l'audit et la justification des résultats. Cette fiabilité est critique dans un contexte professionnel engageant la responsabilité.
L'exigence d'évolutivité nécessite une architecture modulaire facilitant les modifications futures. L'ajout de nouvelles fonctionnalités doit être possible sans remise en cause de l'existant. Cette modularité doit également faciliter l'adaptation aux évolutions réglementaires françaises. L'isolation des paramètres normatifs dans des modules spécialisés facilite cette adaptation.
L'exigence d'interopérabilité impose la capacité d'échange avec les systèmes d'information existants. L'import de données clients depuis les systèmes Customer Relationship Management (CRM) doit être facilité. L'export de résultats vers les outils de reporting externes doit être standardisé. Cette interopérabilité améliore l'intégration dans les workflows professionnels établis.

L'exigence de sécurité protège les données sensibles des utilisateurs selon les standards requis. La protection des données personnelles doit respecter le Règlement Général sur la Protection des Données (RGPD). L'authentification et l'autorisation doivent contrôler l'accès selon les profils utilisateurs. Cette sécurité conditionne la confiance et l'adoption par les utilisateurs professionnels.
L'exigence de scalabilité permet l'adaptation à la croissance du nombre d'utilisateurs. L'architecture doit supporter l'augmentation des charges sans dégradation des performances. Cette scalabilité facilite le déploiement interne et l'utilisation simultanée par plusieurs équipes. Elle conditionne l'efficacité opérationnelle de la plateforme dans un contexte de croissance.
L'implémentation de ces exigences nécessite des choix technologiques adaptés aux contraintes identifiées. Les technologies cloud facilitent la scalabilité et la maintenance centralisée. Les bases de données performantes supportent les calculs intensifs d'optimisation. Cette sélection technologique influence directement la capacité à satisfaire les exigences techniques.

 #### Spécifications d'ergonomie et diversification des acteurs

La diversification des acteurs de l'autoconsommation collective impose des exigences d'ergonomie renforcées. Cette diversification inclut des utilisateurs aux niveaux d'expertise variables selon leur origine professionnelle, et l'accessibilité de la solution aux non-spécialistes devient un facteur critique d'adoption. Cette accessibilité doit préserver la sophistication technique nécessaire aux experts selon une approche équilibrée.
La conception d'interfaces adaptées aux différents profils utilisateurs nécessite une segmentation fine des besoins. Les experts techniques requièrent un accès complet aux paramètres et réglages avancés. Les commerciaux privilégient la rapidité d'utilisation et la clarté des résultats. Les décideurs demandent des synthèses exécutives et des visualisations impactantes. Cette segmentation guide la conception d'interfaces spécialisées selon les rôles.
L'approche progressive de difficulté facilite l'apprentissage pour les utilisateurs novices. Les fonctionnalités de base doivent être accessibles sans formation approfondie selon une approche intuitive. Les fonctionnalités avancées restent disponibles pour les utilisateurs expérimentés. Cette progressivité évite l'effet de rejet tout en préservant la richesse fonctionnelle.
La personnalisation de l'interface selon les préférences utilisateurs améliore l'ergonomie d'usage. Les tableaux de bord doivent être configurables selon les indicateurs prioritaires. Les rapports doivent être adaptables selon les besoins de communication spécifiques. Cette personnalisation améliore l'efficacité d'utilisation et l'appropriation de l'outil.
L'aide contextuelle intégrée facilite l'apprentissage et l'utilisation autonome de la plateforme. Cette aide doit expliquer les concepts techniques aux non-spécialistes selon une approche pédagogique. Elle doit guider les utilisateurs dans les processus avancés d'optimisation. Cette assistance améliore l'autonomie d'utilisation et réduit les besoins de formation externe.
La validation utilisateur avant finalisation assure l'adéquation ergonomique aux besoins réels. Cette validation doit impliquer des représentants de chaque profil d'utilisateur identifié. Elle doit tester l'utilisabilité dans des conditions d'usage réelles. Cette validation itérative améliore la qualité ergonomique et l'acceptation finale.

La gestion des droits d'accès doit permettre une granularité fine d'adaptation organisationnelle. Cette gestion doit s'adapter aux différentes structures depuis les travailleurs indépendants jusqu'aux grandes entreprises. Elle doit permettre le cloisonnement interne selon les besoins de confidentialité. Cette flexibilité facilite l'adoption par des organisations aux structures variées.
Cette synthèse des besoins constitue le socle conceptuel pour la conception de la plateforme OptimPV. Elle assure la cohérence entre l'analyse stratégique du secteur et les choix de développement technologique, et cette cohérence garantit l'adéquation de la solution aux enjeux réels du marché français.

## Synthèse

L'analyse stratégique du secteur photovoltaïque français révèle une transformation structurelle de l'autoconsommation collective, caractérisée par une croissance exceptionnelle de +2 122% en quatre ans pour atteindre 1 111 opérations actives en juin 2025. Cette évolution témoigne de la maturité émergente d'un marché longtemps expérimental, désormais structuré autour de trois segments aux besoins différenciés.

La segmentation des ACC selon les typologies de PMO confirme des logiques économiques distinctes. Les ACC patrimoniales (67% du marché) privilégient une approche de coût technique dans une logique d'exemplarité territoriale, tandis que les ACC multi-acteurs (33% des opérations, soit environ 370 projets en 2025) nécessitent une optimisation fine entre rentabilité opérateur et attractivité commerciale. Cette différenciation, amplifiée par les évolutions réglementaires récentes, génère des besoins d'optimisation algorithmique spécifiques au segment multi-acteurs.

L'analyse concurrentielle révèle un paradoxe sectoriel : malgré des investissements technologiques considérables des grands opérateurs EaaS, aucune solution commerciale ne répond spécifiquement aux besoins d'optimisation intégrée des ACC multi-acteurs. Cette lacune résulte de stratégies propriétaires systématiques créant des inefficiences sectorielles où chaque développeur reconstitue individuellement ses processus d'analyse.

L'identification des leviers d'optimisation technico-économique confirme trois paramètres critiques : l'optimisation du prix de vente sous contraintes multiples, la maximisation du ratio autoconsommation/surplus, et l'intégration temps réel des évolutions réglementaires françaises. Ces leviers, combinés aux coûts de transaction spécifiques aux ACC multi-acteurs, justifient le développement d'une approche algorithmique spécialisée.

Le positionnement concurrentiel OptimPV sur l'intersection EaaS + ACC + optimisation algorithmique confirme l'existence d'une niche défendable, renforcée par la barrière à l'entrée constituée par la complexité réglementaire française. Cette position unique permet d'envisager une différenciation viable basée sur la transparence tarifaire, l'ancrage territorial et l'absence d'investissement client.

Néanmoins, cette analyse stratégique soulève des interrogations critiques qui conditionnent la validation opérationnelle de l'approche développée.

## Questionnements critiques et enjeux de validation à résoudre

L'analyse conduite révèle cependant des interrogations majeures qui devront être traitées dans la validation opérationnelle d'OptimPV. Ces questionnements, issus de l'observation terrain des opérations d'ACC existantes, constituent autant de défis à relever pour démontrer la pertinence de l'approche développée.

### La problématique des coûts de transaction spécifiques aux ACC multi-acteurs

L'étude approfondie des opérations multi-acteurs révèle que "l'ACC nécessite des formes d'intermédiation assez développées, qui génèrent des coûts de transaction propres, d'un montant plus ou moins élevé" correspondant aux "différentes tâches que la PMO doit effectuer, notamment autour du traitement des données" (rapport HAL, 2022). Contrairement aux ACC patrimoniales où ces coûts sont internalisés par la collectivité, les ACC multi-acteurs supportent des coûts d'intermédiation externes significatifs : négociation commerciale, gestion des relations multi-parties, optimisation des paramètres économiques, et production de rapports différenciés selon les parties prenantes.

**Enjeu de justification économique :** Comment OptimPV peut-il justifier sa valeur ajoutée spécifiquement pour les ACC multi-acteurs face à ces coûts de transaction élevés ? L'automatisation des tâches de modélisation et d'optimisation peut-elle réellement réduire ces coûts d'intermédiation ou libérer du temps pour les aspects relationnels à plus forte valeur ajoutée ?

### Le décalage d'échelle entre sophistication technique et réalité de terrain

Les données du marché révèlent une moyenne de 11 consommateurs par opération d'ACC toutes catégories confondues (1150 consommateurs pour 102 opérations). Cependant, cette moyenne masque des réalités très différentes : les ACC patrimoniales ont souvent moins de 5 consommateurs (sites municipaux), tandis que les ACC multi-acteurs peuvent atteindre 20 à 50 consommateurs, justifiant des outils d'optimisation plus avancés. Les retours terrain sur les opérations multi-acteurs montrent des difficultés spécifiques à la gestion commerciale et à l'optimisation économique.

**Validation de la performance économique :** Le ROI d'OptimPV s'avère-t-il positif sur un portefeuille d'ACC multi-acteurs, compte tenu de leur taille plus importante et de leurs enjeux d'optimisation spécifiques ? L'automatisation des tâches techniques de modélisation et d'optimisation justifie-t-elle l'investissement en développement interne ?

### L'écart entre motivations financières et motivations territoriales réelles

L'analyse des motivations révèle une différenciation claire selon le type d'opération. Les ACC patrimoniales privilégient "l'exemplarité territoriale" et "l'efficacité énergétique comme fil conducteur". Par ailleurs, les ACC multi-acteurs, développées par des acteurs privés, intègrent nécessairement des objectifs de rentabilité financière tout en répondant aux attentes territoriales des participants.

**Défi d'intégration multi-critères :** Dans quelle mesure OptimPV peut-il intégrer les dimensions territoriales et sociales dans ses algorithmes d'optimisation pour les ACC multi-acteurs ? L'approche centrée sur l'optimisation de la VAN et du TRI peut-elle être enrichie de critères non-financiers pour mieux correspondre aux attentes des participants ?

### La viabilité économique du modèle OptimPV sur un marché de niche

Le marché français des ACC multi-acteurs représentait environ 33% des 102 opérations actives fin 2022, soit approximativement 34 opérations. Avec l'explosion observée depuis 2024, ce segment atteint désormais environ 370 opérations en 2025, et pourrait dépasser 1 000 à 1 500 opérations d'ici 2030 selon la tendance actuelle, créant un marché substantiel qui justifie pleinement le développement d'outils internes spécialisés comme OptimPV pour les bureaux d'études.

**Question critique pour la partie 3 :** Comment démontrer que le développement d'OptimPV est rentable sur un marché désormais substantiel de 370 opérations multi-acteurs en 2025 ? L'amortissement des coûts de développement sur ce volume d'opérations en forte croissance justifie-t-il l'investissement par rapport à des solutions externes ou des approches manuelles ?

### L'inadéquation entre sophistication algorithmique et besoins opérationnels réels

Les difficultés identifiées varient selon le type d'ACC. Pour les ACC patrimoniales, elles concernent principalement le "manque de main d'œuvre locale" et la "méconnaissance du dispositif". Pour les ACC multi-acteurs, les défis portent davantage sur l'optimisation technico-économique, la structuration financière, la négociation multi-parties, et la production de reportings différenciés selon les parties prenantes.

**Enjeu de validation empirique :** Les fonctionnalités avancées d'OptimPV (algorithmes génétiques, optimisation multi-contraintes) répondent-elles spécifiquement aux besoins des ACC multi-acteurs ou constituent-elles de la sophistication excessive ? L'automatisation de l'optimisation technico-économique génère-t-elle une valeur supérieure aux approches manuelles pour ce segment spécifique ?

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

## Chapitre 11 : Solutions Techniques Envisagées pour l'Écosystème Digital

Ces besoins fonctionnels clairement identifiés par l'expérience EPP nécessitent une approche technique structurée pour transformer OptimPV d'un outil d'étude en plateforme d'accompagnement complet. Avant de concevoir une architecture adaptée, il convient d'analyser l'écosystème des solutions existantes afin de positionner efficacement les développements envisagés.

### 11.1. Applications de suivi post-installation : un marché sous-développé

**Quelles solutions existent pour le monitoring opérationnel des projets ACC ?**

Contrairement aux outils de conception analysés en Partie 1 (OptimPV, Enogrid, SerenyCalas), l'écosystème d'applications dédiées au suivi opérationnel post-installation demeure particulièrement sous-développé. Cette lacune se révèle critique car les dirigeants d'entreprises multi-sites perdent toute visibilité une fois leur projet ACC mis en service.

L'analyse spécifique des applications de monitoring révèle des tentatives partielles inadaptées aux besoins dirigeants. MySmartBattery développée par Saft se limite exclusivement au stockage résidentiel sans vision consolidée entreprise. Enerplan Monitor propose une interface technique uniquement, inadaptée aux besoins de pilotage stratégique des dirigeants. Linky Connect d'Enedis traite les données site par site sans intégrer la consolidation multi-sites pourtant essentielle aux entreprises comme EPP.

Il convient de souligner que ces solutions ne sont pas développées spécifiquement pour l'autoconsommation collective, mais plutôt pour le monitoring énergétique généraliste, expliquant leur inadéquation aux spécificités ACC multi-acteurs.

Par ailleurs, l'absence de solutions commerciales spécialisées ACC peut sembler paradoxale compte tenu du dynamisme du marché. Cette situation s'explique vraisemblablement par l'existence de plateformes internes propriétaires chez les grands opérateurs EaaS (Total Énergies, Engie, EDF Renouvelables). Ces outils, développés pour leurs propres opérations et non commercialisés, créent une asymétrie concurrentielle défavorable aux développeurs indépendants qui ne peuvent accéder à ces technologies.

Cette carence spécifique au monitoring post-installation contraste avec l'écosystème plus développé des outils de conception. Elle crée une rupture dans l'accompagnement des dirigeants, confirmant l'opportunité stratégique pour un module complémentaire à OptimPV répondant à ce besoin non satisfait.

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

L'application serait proposée gratuitement selon une logique économique stratégique : optimiser naturellement les comportements de consommation pour maximiser l'autoconsommation collective sans intervention manuelle de l'opérateur. Cette approche s'inspire des retours d'expérience du secteur photovoltaïque où le monitoring en temps réel génère une modification comportementale spontanée des utilisateurs.

La gamification énergétique induit des réflexes d'optimisation : "Ah, là j'ai de la production solaire, je vais allumer mon four maintenant" ou "Super, c'est le moment de faire tourner mon lave-linge". Ces micro-décisions quotidiennes, multipliées sur 640 consommateurs dans la boucle ACC, augmentent mécaniquement le taux d'autoconsommation collective sans campagne de sensibilisation coûteuse.

Pour l'opérateur, cette gratuité stratégique génère un retour sur investissement indirect mais mesurable : chaque point d'autoconsommation supplémentaire améliore la rentabilité du projet EPP en réduisant le surplus non valorisé. L'application gratuite devient ainsi un levier d'optimisation opérationnelle déguisé en service client.

#### Roadmap de développement

**Quelle stratégie de développement séquencé pour cette application ?**

La roadmap de développement s'articulerait sur trois phases permettant une validation progressive des fonctionnalités et une montée en charge maîtrisée.

La Phase 1 de 6 mois développerait un MVP Dashboard web responsive incluant les fonctionnalités essentielles (économies, comparaisons), l'intégration API Linky via Enedis et les tests sur Euro Plomberie avec 28 utilisateurs pilotes sélectionnés.

La Phase 2 de 12 mois étendrait le développement vers une application mobile native iOS/Android intégrant les notifications push et le mode hors-ligne, ainsi que la gamification avancée et les challenges inter-sites.

La Phase 3 de 18 mois introduirait l'intelligence artificielle prédictive avec des recommandations personnalisées d'optimisation, la prédiction de consommation/production sur 7 jours et la détection automatique d'anomalies, transformant l'application en assistant intelligent de l'autoconsommation collective.

Cette roadmap technologique ambitieuse s'appuie sur la validation préalable des performances OptimPV que confirme concrètement l'étude de cas Euro Plomberie-Piscine, permettant d'envisager sereinement cette évolution vers un écosystème digital complet.

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

Cette validation méthodologique confirme la viabilité théorique et calculatoire du concept OptimPV développé en Partie 2 et sa capacité à répondre efficacement aux enjeux concurrentiels identifiés en Partie 1. L'étude de cas Euro Plomberie-Piscine, bien que reposant sur un échantillon unique, démontre par ses résultats que l'innovation OptimPV EaaS+ACC constitue une réponse théoriquement pertinente et différenciée aux besoins du marché français de l'autoconsommation collective.

Néanmoins, bien que les projections soient encourageantes avec une probabilité de succès de 72,7%, la mise en œuvre opérationnelle nécessitera une vigilance constante pour maintenir les performances prévisionnelles. L'expérience terrain EPP révèle déjà des écarts entre modélisation théorique et réalité opérationnelle, notamment sur la complexité administrative sous-estimée et les coûts cachés non anticipés. Ces décalages, inhérents à tout projet innovant, exigeront des adaptations méthodologiques et des ajustements stratégiques réguliers.

La trajectoire d'industrialisation identifiée, bien que prometteuse, demeure conditionnée à la capacité d'OptimPV à s'adapter aux surprises opérationnelles inévitables des phases de déploiement. Le maintien des marges de rentabilité projetées nécessitera une amélioration continue des processus d'estimation, une meilleure anticipation des contraintes terrain, et une réactivité commerciale face aux évolutions concurrentielles accélérées observées sur des marchés dynamiques comme la région PACA. Cette approche prudente et adaptative constitue la condition sine qua non de transformation du concept validé en succès industriel durable.