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








