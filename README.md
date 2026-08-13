# Plateforme Data Engineering et BI pour l’analyse des réhospitalisations

Ce projet consiste à concevoir une plateforme complète de **Data Engineering, Data Analysis et Business Intelligence** dédiée à l’analyse des données hospitalières et au suivi du risque de réhospitalisation.

Le projet utilise le dataset public **Diabetes 130-US Hospitals for Years 1999–2008**, contenant des données d’hospitalisation de patients diabétiques provenant de plusieurs hôpitaux américains.

L’objectif principal est de construire une chaîne de traitement complète :

```text
CSV
 ↓
Ingestion
 ↓
Validation des données
 ↓
Nettoyage et transformation
 ↓
Stockage Parquet
 ↓
Data Warehouse PostgreSQL
 ↓
Data Marts
 ↓
Analyse des données
 ↓
Dashboards Power BI
 ↓
Modèle prédictif
 ↓
API et déploiement
```

---

# Roadmap du projet

## Phase 1 — Compréhension métier

### Étape 1 — Analyse du besoin métier

#### Objectif

Comprendre les besoins des médecins, des responsables hospitaliers et des équipes de gestion afin de définir les indicateurs nécessaires au suivi des hospitalisations et des réhospitalisations.

#### Travail à réaliser

* identifier les utilisateurs de la plateforme ;
* comprendre les besoins métiers ;
* définir les principales problématiques ;
* définir les indicateurs de performance ;
* définir les objectifs du projet ;
* définir les limites du système.

#### Utilisateurs concernés

* médecins ;
* responsables hospitaliers ;
* responsables de services ;
* analystes de données ;
* direction du CHU ;
* administrateurs de la plateforme.

#### Livrables

* cahier des charges ;
* définition des besoins métiers ;
* liste des KPIs ;
* architecture fonctionnelle ;
* description du périmètre du projet.

---

### Étape 2 — Étude du dataset

#### Objectif

Analyser complètement le dataset afin de comprendre sa structure, ses variables et ses limites.

#### Dataset utilisé

```text
Diabetes 130-US Hospitals for Years 1999–2008
```

Le dataset contient des informations sur :

* les patients ;
* les admissions ;
* les diagnostics ;
* les médicaments ;
* les examens médicaux ;
* les hospitalisations précédentes ;
* la durée de séjour ;
* la réhospitalisation.

La variable cible principale est :

```text
readmitted
```

Elle indique si un patient a été réhospitalisé :

* en moins de 30 jours ;
* après plus de 30 jours ;
* jamais réhospitalisé.

#### Travail à réaliser

* comprendre chaque variable ;
* identifier les types de données ;
* analyser les valeurs manquantes ;
* détecter les doublons ;
* analyser les valeurs uniques ;
* identifier les incohérences ;
* étudier la distribution des variables ;
* comprendre la variable cible ;
* analyser la qualité globale du dataset.

#### Outils

* Python ;
* Polars ;
* Pandas ;
* Jupyter Notebook ;
* Matplotlib ;
* Plotly.

#### Livrables

* dictionnaire des données ;
* notebook d’exploration ;
* rapport de qualité initial ;
* statistiques descriptives ;
* rapport d’analyse du dataset.

---

# Phase 2 — Data Engineering

## Étape 3 — Conception de l’architecture Data Engineering

#### Objectif

Concevoir une architecture claire, professionnelle et évolutive pour gérer les différentes étapes du traitement des données.

#### Architecture prévue

```text
Source CSV
   ↓
Landing Zone
   ↓
Raw Layer
   ↓
Clean Layer
   ↓
Curated Layer
   ↓
Data Warehouse PostgreSQL
   ↓
Data Marts
   ↓
Power BI
```

#### Couches de données

### Landing Zone

Zone d’arrivée des fichiers CSV originaux.

Les fichiers sont conservés sans modification afin de garantir leur traçabilité.

### Raw Layer

Contient les données brutes importées depuis les fichiers CSV.

### Clean Layer

Contient les données nettoyées et validées.

### Curated Layer

Contient les données enrichies, transformées et prêtes pour l’analyse.

### Data Warehouse

Stockage centralisé des données structurées dans PostgreSQL.

### Data Marts

Tables spécialisées destinées à Power BI et aux analyses métiers.

#### Livrables

* diagramme d’architecture ;
* description des différentes couches ;
* choix des technologies ;
* flux de circulation des données.

---

## Étape 4 — Mise en place du projet

#### Objectif

Créer une structure professionnelle pour organiser le code, les données, les pipelines et la documentation.

#### Structure proposée

```text
hospital-readmission-data-platform/
│
├── data/
│   ├── landing/
│   ├── raw/
│   ├── clean/
│   ├── curated/
│   └── quarantine/
│
├── notebooks/
│   ├── 01_data_discovery.ipynb
│   ├── 02_data_quality.ipynb
│   ├── 03_exploratory_analysis.ipynb
│   └── 04_modeling.ipynb
│
├── src/
│   ├── ingestion/
│   ├── validation/
│   ├── transformation/
│   ├── loading/
│   ├── features/
│   ├── quality/
│   └── utils/
│
├── warehouse/
│   ├── ddl/
│   ├── dimensions/
│   ├── facts/
│   ├── marts/
│   └── queries/
│
├── orchestration/
│   └── prefect_flows/
│
├── ml/
│   ├── training/
│   ├── evaluation/
│   ├── prediction/
│   └── models/
│
├── api/
│   └── app/
│
├── powerbi/
│   ├── reports/
│   ├── screenshots/
│   └── documentation/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── data_quality/
│
├── docs/
│   ├── architecture/
│   ├── data_dictionary/
│   └── technical_documentation/
│
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

#### Outils à configurer

* Git ;
* GitHub ;
* Python ;
* environnement virtuel ;
* Docker ;
* Docker Compose ;
* PostgreSQL ;
* Power BI Desktop.

#### Livrables

* dépôt GitHub ;
* structure complète du projet ;
* environnement Python ;
* base PostgreSQL ;
* fichiers de configuration ;
* premier README.

---

## Étape 5 — Ingestion des données

#### Objectif

Créer un pipeline capable de charger automatiquement les fichiers CSV dans la plateforme.

#### Fonctionnalités

* détecter les nouveaux fichiers ;
* vérifier leur présence ;
* vérifier leur extension ;
* vérifier leur nom ;
* contrôler leur taille ;
* calculer leur empreinte ;
* éviter les doublons d’import ;
* enregistrer la date d’import ;
* conserver les fichiers originaux ;
* journaliser chaque exécution.

#### Outils

* Python ;
* Polars ;
* pathlib ;
* logging ;
* hashlib.

#### Exemple de flux

```text
diabetic_data.csv
        ↓
Vérification du fichier
        ↓
Calcul de l’empreinte
        ↓
Copie dans la Landing Zone
        ↓
Lecture avec Polars
        ↓
Enregistrement dans la Raw Layer
```

#### Livrables

* script d’ingestion ;
* table de suivi des imports ;
* fichiers de logs ;
* gestion des erreurs.

---

## Étape 6 — Contrôle qualité des données

#### Objectif

Mettre en place une couche de validation afin de garantir que les données utilisées sont fiables.

#### Contrôles techniques

* présence des colonnes obligatoires ;
* types de données ;
* formats ;
* valeurs nulles ;
* doublons ;
* unicité des identifiants ;
* cohérence des catégories ;
* valeurs hors limites ;
* lignes incomplètes.

#### Contrôles métiers

* durée de séjour positive ;
* nombre de médicaments non négatif ;
* nombre de diagnostics cohérent ;
* âge dans une catégorie valide ;
* statut de réhospitalisation valide ;
* sexe et race dans les catégories attendues.

#### Gestion des erreurs

Les lignes non valides seront envoyées dans :

```text
data/quarantine/
```

Chaque ligne rejetée devra contenir :

* la valeur invalide ;
* la colonne concernée ;
* la règle non respectée ;
* la date du rejet ;
* le motif du rejet.

#### Outils

* Pandera ;
* Polars ;
* Python ;
* logging.

#### Livrables

* schéma de validation ;
* rapport automatique de qualité ;
* données valides ;
* données rejetées ;
* tableau de suivi des erreurs.

---

## Étape 7 — Pipeline ETL

#### Objectif

Construire le pipeline principal de transformation des données.

#### Processus ETL

```text
Extraction
    ↓
Transformation
    ↓
Chargement
```

### Extraction

* lire les fichiers CSV ;
* récupérer les données brutes ;
* contrôler les fichiers disponibles.

### Transformation

* remplacer les valeurs incorrectes ;
* gérer les valeurs manquantes ;
* supprimer les doublons ;
* convertir les types ;
* normaliser les catégories ;
* nettoyer les diagnostics ;
* préparer les médicaments ;
* créer de nouvelles variables ;
* calculer des indicateurs.

### Chargement

* sauvegarder les données nettoyées ;
* convertir les données en Parquet ;
* charger les données dans PostgreSQL ;
* alimenter les tables analytiques.

#### Outils

* Python ;
* Polars ;
* DuckDB ;
* PostgreSQL ;
* Parquet.

#### Livrables

* pipeline ETL ;
* scripts de transformation ;
* fichiers Parquet ;
* tables PostgreSQL ;
* logs d’exécution.

---

## Étape 8 — Feature Engineering

#### Objectif

Créer des variables utiles pour l’analyse, les KPIs et le futur modèle de Machine Learning.

#### Variables possibles

* réhospitalisation en moins de 30 jours ;
* catégorie d’âge ;
* durée de séjour ;
* nombre total de visites ;
* nombre total d’hospitalisations précédentes ;
* nombre de visites en urgence ;
* nombre de consultations externes ;
* nombre total de médicaments ;
* nombre de changements de médicaments ;
* présence d’un traitement à l’insuline ;
* nombre de diagnostics ;
* niveau de complexité du patient ;
* groupe de diagnostic principal ;
* score d’utilisation des soins ;
* indicateur de patient fréquent ;
* indicateur de risque de réhospitalisation.

#### Exemples

```text
total_previous_visits =
number_outpatient
+ number_emergency
+ number_inpatient
```

```text
readmitted_30_days =
1 si readmitted = "<30"
0 sinon
```

#### Livrables

* table de features ;
* dictionnaire des variables créées ;
* règles de calcul ;
* tests des features.

---

## Étape 9 — Data Warehouse PostgreSQL

#### Objectif

Créer une base décisionnelle structurée selon un modèle en étoile.

#### Dimensions proposées

### DimPatient

Contient :

* identifiant patient ;
* sexe ;
* race ;
* tranche d’âge.

### DimDate

Contient :

* date ;
* jour ;
* mois ;
* trimestre ;
* année ;
* jour de la semaine.

Le dataset ne contient pas de date hospitalière exacte. Une dimension temporelle simulée ou technique pourra être créée uniquement pour l’apprentissage BI, avec cette limite clairement documentée.

### DimAdmission

Contient :

* type d’admission ;
* source d’admission ;
* mode de sortie ;
* description des catégories.

### DimDiagnostic

Contient :

* code diagnostic ;
* groupe diagnostic ;
* description ;
* catégorie médicale.

### DimMedication

Contient :

* médicament ;
* statut ;
* changement ;
* prescription.

### DimPayer

Contient :

* type de couverture ;
* code payeur ;
* catégorie.

#### Tables de faits

### FactHospitalization

Contient :

* identifiant du séjour ;
* patient ;
* admission ;
* durée du séjour ;
* nombre de procédures ;
* nombre de médicaments ;
* nombre de diagnostics ;
* visites précédentes.

### FactReadmission

Contient :

* identifiant du séjour ;
* statut de réhospitalisation ;
* réhospitalisation à moins de 30 jours ;
* réhospitalisation après 30 jours ;
* indicateurs de risque.

#### Modèle simplifié

```text
DimPatient
     |
DimAdmission
     |
DimDiagnostic
     |
DimMedication
     |
FactHospitalization
     |
FactReadmission
```

#### Outils

* PostgreSQL ;
* SQL ;
* SQLAlchemy ;
* Alembic ;
* DBeaver ou pgAdmin.

#### Livrables

* schéma du Data Warehouse ;
* scripts SQL ;
* tables de dimensions ;
* tables de faits ;
* documentation du modèle en étoile.

---

## Étape 10 — Construction des Data Marts

#### Objectif

Créer des tables analytiques spécialisées destinées aux différents dashboards Power BI.

#### Data Marts proposés

### Mart Patients

Contient :

* nombre de patients ;
* répartition par âge ;
* répartition par sexe ;
* répartition par race ;
* profils les plus fréquents.

### Mart Hospitalisations

Contient :

* nombre total d’hospitalisations ;
* durée moyenne de séjour ;
* type d’admission ;
* source d’admission ;
* type de sortie.

### Mart Réhospitalisation

Contient :

* taux de réhospitalisation ;
* retour en moins de 30 jours ;
* retour après 30 jours ;
* facteurs liés à la réhospitalisation.

### Mart Diagnostics

Contient :

* diagnostics principaux ;
* groupes de diagnostics ;
* nombre de patients par diagnostic ;
* taux de réhospitalisation par diagnostic.

### Mart Médicaments

Contient :

* médicaments utilisés ;
* évolution des traitements ;
* usage de l’insuline ;
* réhospitalisation selon le traitement.

### Mart Qualité

Contient :

* taux de valeurs manquantes ;
* lignes rejetées ;
* doublons ;
* erreurs de type ;
* qualité par colonne ;
* qualité par import.

#### Livrables

* requêtes SQL ;
* vues PostgreSQL ;
* tables agrégées ;
* documentation des Data Marts.

---

## Étape 11 — Orchestration des pipelines

#### Objectif

Automatiser l’ensemble de la chaîne de traitement avec Prefect.

#### Pipeline automatisé

```text
Détection du CSV
        ↓
Ingestion
        ↓
Validation
        ↓
Nettoyage
        ↓
Transformation
        ↓
Conversion Parquet
        ↓
Chargement PostgreSQL
        ↓
Mise à jour du Data Warehouse
        ↓
Mise à jour des Data Marts
        ↓
Rapport de qualité
        ↓
Rafraîchissement Power BI
```

#### Fonctionnalités

* planification des traitements ;
* relance après échec ;
* gestion des erreurs ;
* journalisation ;
* suivi de l’état des tâches ;
* notification en cas d’échec ;
* suivi de la durée d’exécution.

#### Outils

* Prefect ;
* Python ;
* PostgreSQL ;
* logging.

#### Livrables

* flows Prefect ;
* tâches réutilisables ;
* planning d’exécution ;
* logs d’orchestration ;
* documentation du pipeline.

---

# Phase 3 — Data Analysis

## Étape 12 — Analyse exploratoire avancée

#### Objectif

Réaliser une analyse complète des données afin d’identifier les tendances, les anomalies et les facteurs liés aux réhospitalisations.

#### Axes d’analyse

* répartition des patients par âge ;
* répartition par sexe ;
* durée des hospitalisations ;
* nombre de médicaments ;
* nombre de procédures ;
* diagnostics les plus fréquents ;
* taux de réhospitalisation ;
* patients ayant plusieurs admissions ;
* impact du nombre de visites précédentes ;
* relation entre traitements et réhospitalisation ;
* relation entre durée de séjour et réhospitalisation ;
* relation entre type d’admission et réhospitalisation.

#### Outils

* SQL ;
* Python ;
* Pandas ;
* Polars ;
* Matplotlib ;
* Plotly ;
* Jupyter Notebook.

#### Livrables

* notebook d’analyse ;
* rapport analytique ;
* graphiques ;
* recommandations ;
* principales conclusions.

---

## Étape 13 — Définition des KPIs métier

#### Objectif

Définir les indicateurs qui seront utilisés dans les dashboards Power BI.

#### KPIs généraux

* nombre total d’hospitalisations ;
* nombre total de patients ;
* nombre total de réhospitalisations ;
* taux global de réhospitalisation ;
* taux de réhospitalisation à moins de 30 jours ;
* durée moyenne de séjour ;
* nombre moyen de médicaments ;
* nombre moyen de diagnostics ;
* nombre moyen de procédures.

#### KPIs patients

* patients par tranche d’âge ;
* patients par sexe ;
* patients par race ;
* patients avec plusieurs admissions ;
* patients considérés à risque.

#### KPIs hospitalisations

* hospitalisations par type d’admission ;
* hospitalisations par source d’admission ;
* durée moyenne par groupe de patients ;
* répartition selon le type de sortie.

#### KPIs diagnostics

* diagnostics les plus fréquents ;
* taux de réhospitalisation par diagnostic ;
* diagnostics associés aux séjours longs.

#### KPIs médicaments

* médicaments les plus utilisés ;
* patients sous insuline ;
* modifications de traitements ;
* réhospitalisation selon le traitement.

#### KPIs qualité

* taux de complétude ;
* taux de valeurs manquantes ;
* nombre de doublons ;
* nombre de lignes rejetées ;
* nombre d’anomalies ;
* score global de qualité.

#### Remarque importante

Le dataset ne contient pas de coût réel. Aucun KPI financier réel ne sera calculé sans données fiables. Un coût estimé ne pourra être ajouté que comme simulation pédagogique clairement identifiée.

---

# Phase 4 — Power BI

## Étape 14 — Construction du modèle Power BI

#### Objectif

Connecter Power BI au Data Warehouse PostgreSQL et créer un modèle analytique performant.

#### Travail à réaliser

* connecter Power BI à PostgreSQL ;
* importer les dimensions ;
* importer les tables de faits ;
* importer les Data Marts ;
* créer les relations ;
* configurer les cardinalités ;
* créer une table calendrier ;
* créer les hiérarchies ;
* masquer les colonnes techniques ;
* définir les formats ;
* créer les mesures DAX ;
* organiser les mesures dans des dossiers.

#### Modèle recommandé

```text
Dimensions
   ↓
Tables de faits
   ↓
Mesures DAX
   ↓
Dashboards
```

#### Bonnes pratiques

* utiliser un modèle en étoile ;
* éviter les relations plusieurs-à-plusieurs inutiles ;
* limiter les colonnes calculées ;
* privilégier les mesures DAX ;
* utiliser des noms compréhensibles ;
* cacher les clés techniques ;
* désactiver les dates automatiques ;
* utiliser une table calendrier unique.

#### Livrables

* modèle Power BI ;
* relations documentées ;
* table calendrier ;
* dictionnaire des mesures ;
* documentation du modèle.

---

## Étape 15 — Développement des dashboards Power BI

#### Objectif

Créer plusieurs dashboards professionnels adaptés aux différents utilisateurs.

---

### Dashboard 1 — Executive Overview

#### Objectif

Présenter une vue globale de la situation hospitalière.

#### Contenu

* nombre total de patients ;
* nombre total d’hospitalisations ;
* taux de réhospitalisation ;
* taux de réhospitalisation à moins de 30 jours ;
* durée moyenne de séjour ;
* nombre moyen de médicaments ;
* évolution des principaux indicateurs ;
* principaux diagnostics ;
* profils les plus à risque.

#### Utilisateurs

* direction ;
* responsables hospitaliers ;
* responsables de services.

---

### Dashboard 2 — Patient Analysis

#### Objectif

Analyser les caractéristiques des patients.

#### Contenu

* patients par âge ;
* patients par sexe ;
* patients par race ;
* patients selon le nombre d’admissions ;
* patients selon les visites précédentes ;
* segmentation des profils ;
* filtres par catégorie.

#### Fonctionnalités

* slicers ;
* drill-down ;
* tooltips ;
* drill-through vers le détail d’un patient pseudonymisé.

---

### Dashboard 3 — Hospitalization Analysis

#### Objectif

Analyser les hospitalisations et la durée des séjours.

#### Contenu

* nombre d’hospitalisations ;
* durée moyenne de séjour ;
* hospitalisations par type d’admission ;
* hospitalisations par source ;
* hospitalisations par type de sortie ;
* durée selon le profil patient ;
* nombre de procédures ;
* nombre de diagnostics.

---

### Dashboard 4 — Readmission Analysis

#### Objectif

Analyser les réhospitalisations et leurs principaux facteurs.

#### Contenu

* taux global de réhospitalisation ;
* réhospitalisation en moins de 30 jours ;
* réhospitalisation après 30 jours ;
* réhospitalisation par âge ;
* réhospitalisation par sexe ;
* réhospitalisation par diagnostic ;
* réhospitalisation par traitement ;
* réhospitalisation selon la durée du séjour ;
* patients ayant plusieurs visites précédentes.

#### Fonctionnalités

* comparaison entre patients réhospitalisés et non réhospitalisés ;
* analyse des facteurs ;
* filtres avancés ;
* navigation vers les autres dashboards.

---

### Dashboard 5 — Clinical Analysis

#### Objectif

Analyser les diagnostics, médicaments et traitements.

#### Contenu

* diagnostics les plus fréquents ;
* diagnostics associés à la réhospitalisation ;
* médicaments les plus utilisés ;
* usage de l’insuline ;
* changement de traitement ;
* examens réalisés ;
* procédures médicales ;
* nombre de diagnostics par patient.

---

### Dashboard 6 — Data Quality

#### Objectif

Suivre la qualité des données traitées par les pipelines.

#### Contenu

* nombre de fichiers importés ;
* nombre de lignes valides ;
* nombre de lignes rejetées ;
* taux de valeurs manquantes ;
* doublons détectés ;
* erreurs par colonne ;
* erreurs par règle ;
* évolution du score de qualité ;
* historique des imports.

#### Utilisateurs

* Data Engineer ;
* Data Analyst ;
* administrateur.

---

### Dashboard 7 — Pipeline Monitoring

#### Objectif

Suivre l’exécution des pipelines Data Engineering.

#### Contenu

* dernière exécution ;
* statut du pipeline ;
* durée de traitement ;
* nombre de lignes traitées ;
* nombre d’erreurs ;
* étapes réussies ;
* étapes échouées ;
* historique des exécutions ;
* fraîcheur des données.

---

## Étape 16 — Maîtrise avancée de Power BI

#### Objectif

Améliorer les performances, l’interactivité et la sécurité des rapports.

#### Power Query

Maîtriser :

* connexion à PostgreSQL ;
* nettoyage des données ;
* changement des types ;
* fusion des requêtes ;
* ajout de colonnes ;
* paramètres ;
* requêtes de référence ;
* requêtes intermédiaires ;
* query folding.

#### DAX

Maîtriser :

* `CALCULATE` ;
* `FILTER` ;
* `DIVIDE` ;
* `DISTINCTCOUNT` ;
* `SUMX` ;
* `AVERAGEX` ;
* `COUNTROWS` ;
* `ALL` ;
* `ALLSELECTED` ;
* `REMOVEFILTERS` ;
* `RELATED` ;
* `USERELATIONSHIP` ;
* `SWITCH` ;
* fonctions temporelles.

#### Modélisation

Maîtriser :

* modèle en étoile ;
* relations ;
* cardinalité ;
* direction de filtrage ;
* dimensions conformes ;
* table calendrier ;
* hiérarchies ;
* dimensions à rôles multiples.

#### Interactivité

Maîtriser :

* drill-down ;
* drill-through ;
* bookmarks ;
* boutons ;
* tooltips personnalisés ;
* navigation entre pages ;
* paramètres What-if ;
* field parameters ;
* filtres synchronisés.

#### Sécurité

Mettre en place :

* Row-Level Security ;
* rôles utilisateurs ;
* filtres par service ;
* accès limité aux données ;
* masquage des informations sensibles.

#### Optimisation

* réduire le nombre de colonnes ;
* limiter les visuels ;
* optimiser les mesures DAX ;
* éviter les colonnes calculées inutiles ;
* améliorer le modèle ;
* utiliser Performance Analyzer ;
* vérifier la taille du modèle ;
* utiliser des agrégations.

#### Rafraîchissement

* configurer le rafraîchissement ;
* préparer la passerelle Power BI ;
* gérer les paramètres ;
* contrôler la fraîcheur ;
* documenter la procédure de mise à jour.

#### Livrables

* rapports optimisés ;
* mesures DAX documentées ;
* sécurité RLS ;
* guide utilisateur ;
* guide de maintenance Power BI.

---

# Phase 5 — Machine Learning

## Étape 17 — Modèle prédictif de réhospitalisation

#### Objectif

Construire un modèle permettant d’estimer la probabilité de réhospitalisation à moins de 30 jours.

#### Préparation de la cible

```text
1 = patient réhospitalisé en moins de 30 jours
0 = patient non réhospitalisé en moins de 30 jours
```

#### Modèles à comparer

* Logistic Regression ;
* Random Forest ;
* XGBoost.

#### Métriques

* précision ;
* recall ;
* F1-score ;
* ROC-AUC ;
* PR-AUC ;
* matrice de confusion ;
* spécificité ;
* sensibilité.

#### Travail à réaliser

* préparer les variables ;
* gérer les catégories ;
* gérer les valeurs manquantes ;
* séparer les données ;
* entraîner les modèles ;
* comparer les résultats ;
* sélectionner le meilleur modèle ;
* expliquer les prédictions ;
* enregistrer les scores dans PostgreSQL.

#### Intégration Power BI

Power BI pourra afficher :

* score de risque ;
* catégorie de risque ;
* principaux facteurs ;
* nombre de patients à risque ;
* distribution des probabilités ;
* comparaison entre risque estimé et résultat réel.

#### Livrables

* modèle entraîné ;
* rapport d’évaluation ;
* pipeline de prédiction ;
* table des prédictions ;
* dashboard de risque.

---

# Phase 6 — Industrialisation

## Étape 18 — Développement de l’API

#### Objectif

Créer une API permettant d’exposer les données, les indicateurs et les prédictions.

#### Technologie

```text
FastAPI
```

#### Endpoints possibles

```text
GET /health
GET /api/kpis
GET /api/patients
GET /api/hospitalizations
GET /api/readmissions
GET /api/data-quality
GET /api/pipeline-runs
POST /api/predict
```

#### Fonctionnalités

* consulter les KPIs ;
* récupérer les données analytiques ;
* lancer une prédiction ;
* consulter les métriques ;
* vérifier l’état du système.

#### Livrables

* API FastAPI ;
* documentation Swagger ;
* tests ;
* gestion des erreurs ;
* endpoints sécurisés.

---

## Étape 19 — Conteneurisation

#### Objectif

Créer un environnement reproductible avec Docker.

#### Services à conteneuriser

* PostgreSQL ;
* pipeline ETL ;
* API FastAPI ;
* Prefect ;
* outils de suivi.

#### Exemple

```text
docker compose up -d
```

#### Livrables

* Dockerfile ;
* docker-compose.yml ;
* volumes ;
* variables d’environnement ;
* documentation de lancement.

---

## Étape 20 — Tests, documentation et finalisation

#### Tests à réaliser

* tests d’ingestion ;
* tests de validation ;
* tests de transformation ;
* tests SQL ;
* tests du Data Warehouse ;
* tests des Data Marts ;
* tests du pipeline Prefect ;
* tests de l’API ;
* tests du modèle ;
* tests des mesures Power BI.

#### Documentation technique

* architecture ;
* structure du projet ;
* installation ;
* configuration ;
* description des pipelines ;
* description du Data Warehouse ;
* description des Data Marts ;
* description des dashboards ;
* documentation API.

#### Documentation fonctionnelle

* besoins métiers ;
* utilisateurs ;
* KPIs ;
* règles de gestion ;
* utilisation des dashboards ;
* interprétation des indicateurs.

#### Livrables finaux

* dépôt GitHub ;
* pipeline Data Engineering ;
* Data Warehouse PostgreSQL ;
* Data Marts ;
* dashboards Power BI ;
* modèle prédictif ;
* API FastAPI ;
* environnement Docker ;
* documentation technique ;
* rapport final ;
* présentation de soutenance.

---

# État actuel du projet

```text
Étape 1 — Analyse du besoin métier ✅
        ↓
Étape 2 — Étude du dataset ✅
        ↓
Étape 3 — Architecture Data Engineering ✅
        ↓
Étape 4 — Initialisation du projet ✅
        ↓
Étape 5 — Ingestion des données ✅
        ↓
Étape 6 — Contrôle qualité ✅
        ↓
Étape 7 — Pipeline ETL ✅
        ↓
Étape 8 — Feature Engineering ✅
        ↓
Étape 9 — Data Warehouse ✅
        ↓
Étape 10 — Data Marts ✅
        ↓
Étape 11 — Orchestration Prefect ✅
        ↓
Étape 12 — Analyse exploratoire avancée ✅
        ↓
Étape 13 — KPIs métier ✅
        ↓
Étape 14 — Modèle Power BI ✅ (guide détaillé fourni, construction manuelle dans Power BI Desktop)
        ↓
Étape 15 — Dashboards Power BI ✅ (guide détaillé fourni, construction manuelle dans Power BI Desktop)
        ↓
Étape 16 — Optimisation Power BI ✅ (guide fourni)
        ↓
Étape 17 — Machine Learning ✅
        ↓
Étape 18 — API FastAPI ✅
        ↓
Étape 19 — Dockerisation ✅
        ↓
Étape 20 — Tests et documentation ✅
```

## Résumé de ce qui est construit

- **Pipeline de données** (`src/`, `orchestration/`) : ingestion,
  contrôle qualité, ETL, Feature Engineering, chargement PostgreSQL,
  entièrement orchestré par un flow Prefect
  (`orchestration/prefect_flows/pipeline_flow.py`).
- **Data Warehouse** (`warehouse/`) : modèle en étoile PostgreSQL
  (schéma `warehouse`), 7 Data Marts (schéma `marts`) prêts pour la BI.
- **Modèle prédictif** (`ml/`) : comparaison Logistic
  Regression / Random Forest / XGBoost, suivi MLflow, scoring vers
  `warehouse.fact_prediction`.
- **API** (`api/`) : FastAPI exposant KPIs, Data Marts et prédictions
  (`/docs` pour la documentation interactive).
- **Conteneurisation** (`Dockerfile`, `docker-compose.yml`) : services
  `postgres`, `api`, `pipeline`, `mlflow`.
- **Power BI** (`powerbi/documentation/`) : le modèle, les mesures DAX
  et les 7 dashboards sont documentés en détail (référence
  `powerbi_model.md` + guide pas-à-pas
  `guide_powerbi_desktop.md`/`.pdf`), à construire manuellement dans
  Power BI Desktop (application graphique non pilotable depuis ce dépôt).
- **Tests** (`tests/`) : unitaires, intégration (base réelle) et
  qualité des données — voir `pytest` (62+ tests).
- **Documentation** : technique (`docs/technical_documentation/`),
  fonctionnelle et KPIs (`docs/business/`), architecture
  (`docs/architecture/`).

## Limites connues du projet

- Les probabilités du modèle prédictif ne sont pas calibrées (seuils de
  risque par quantile plutôt que par probabilité absolue, voir
  `docs/technical_documentation/ml_model.md`).
- `dim_date` est une table calendrier technique, non reliée aux faits
  (le dataset ne contient pas de date d'hospitalisation réelle).
- Les attributs de `dim_patient` (âge, sexe, race) reflètent la première
  hospitalisation connue du patient (simplification Type 1).
- Aucun KPI financier réel : le dataset ne contient pas de coût.
- Power BI Desktop étant une application graphique Windows, les
  dashboards eux-mêmes doivent être construits manuellement en suivant
  `powerbi/documentation/guide_powerbi_desktop.pdf`.

---

# Stack technique

## Data Engineering

* Python ;
* Polars ;
* Pandera ;
* DuckDB ;
* Parquet ;
* PostgreSQL ;
* SQLAlchemy ;
* Alembic ;
* Prefect ;
* Docker ;
* Git ;
* GitHub.

## Data Analysis

* SQL ;
* Pandas ;
* Polars ;
* Jupyter Notebook ;
* Matplotlib ;
* Plotly ;
* statistiques descriptives ;
* analyse exploratoire ;
* définition des KPIs.

## Business Intelligence

* Power BI Desktop ;
* Power Query ;
* DAX ;
* modèle en étoile ;
* dashboards interactifs ;
* drill-through ;
* bookmarks ;
* tooltips ;
* Row-Level Security ;
* Performance Analyzer ;
* passerelle de données ;
* rafraîchissement.

## Machine Learning

* Scikit-learn ;
* XGBoost ;
* Imbalanced-learn ;
* SHAP ;
* MLflow.

## Développement et industrialisation

* FastAPI ;
* Pydantic ;
* Pytest ;
* Docker Compose ;
* logging ;
* documentation Swagger.

---

# Compétences acquises à la fin du projet

## Data Engineering

* ingestion de fichiers CSV ;
* construction de pipelines ETL ;
* contrôle qualité des données ;
* gestion des erreurs ;
* stockage Parquet ;
* automatisation des traitements ;
* orchestration avec Prefect ;
* modélisation dimensionnelle ;
* création d’un Data Warehouse ;
* construction de Data Marts ;
* SQL avancé ;
* PostgreSQL ;
* Docker ;
* tests de pipelines ;
* monitoring.

## Data Analysis

* compréhension métier ;
* exploration des données ;
* statistiques descriptives ;
* détection des tendances ;
* définition des KPIs ;
* interprétation des résultats ;
* communication des insights ;
* création de rapports analytiques.

## Power BI

* connexion à PostgreSQL ;
* Power Query ;
* DAX ;
* modèle en étoile ;
* relations ;
* mesures ;
* colonnes calculées ;
* table calendrier ;
* hiérarchies ;
* KPIs ;
* dashboards interactifs ;
* drill-down ;
* drill-through ;
* bookmarks ;
* tooltips ;
* field parameters ;
* RLS ;
* optimisation ;
* publication ;
* rafraîchissement ;
* passerelle de données.

## Machine Learning

* préparation des données ;
* classification ;
* comparaison de modèles ;
* évaluation ;
* gestion du déséquilibre ;
* explicabilité ;
* intégration des prédictions dans Power BI.

## Développement

* FastAPI ;
* API REST ;
* tests ;
* Docker ;
* documentation ;
* Git ;
* GitHub.

---

# Résultat final attendu

À la fin du projet, la plateforme devra permettre de :

* ingérer automatiquement les fichiers hospitaliers ;
* contrôler leur qualité ;
* nettoyer et transformer les données ;
* stocker les données dans un Data Warehouse ;
* construire plusieurs Data Marts ;
* automatiser les pipelines ;
* analyser les hospitalisations ;
* mesurer les taux de réhospitalisation ;
* visualiser les résultats dans Power BI ;
* identifier les facteurs de risque ;
* prédire le risque de réhospitalisation ;
* exposer les résultats via une API ;
* suivre la qualité des données et les pipelines.

Le projet doit mettre en valeur un profil complet :

```text
Data Engineer
+
Data Analyst
+
Power BI Developer
+
Machine Learning Engineer junior
```
