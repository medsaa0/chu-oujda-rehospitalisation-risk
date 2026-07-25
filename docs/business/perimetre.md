# Périmètre du projet

## Fonctionnalités incluses

Le projet couvre les fonctionnalités suivantes :

- ingestion du dataset CSV ;
- validation de la qualité des données ;
- nettoyage et transformation des données ;
- stockage des données au format Parquet ;
- conception d'un Data Warehouse PostgreSQL ;
- création de Data Marts ;
- automatisation des pipelines avec Prefect ;
- analyse exploratoire des données ;
- définition des KPIs ;
- création de dashboards Power BI ;
- développement d'un modèle prédictif de réhospitalisation ;
- développement d'une API FastAPI ;
- conteneurisation avec Docker.

---

## Fonctionnalités non incluses

Cette première version ne comprend pas :

- connexion au système HOSIX ;
- traitement des données en temps réel ;
- intégration avec les systèmes hospitaliers ;
- modification des dossiers médicaux ;
- calcul des coûts hospitaliers réels ;
- déploiement Kubernetes ;
- architecture Big Data (Spark, Kafka).

---

## Contraintes

Le projet repose sur un dataset public présentant certaines limites :

- données anonymisées ;
- données provenant d'hôpitaux américains ;
- période couverte : 1999–2008 ;
- patients diabétiques uniquement ;
- absence de certaines informations cliniques détaillées ;
- présence de valeurs manquantes dans plusieurs variables.

---

## Évolutions futures

Le projet pourra évoluer vers :

- l'intégration de données hospitalières réelles ;
- l'ajout de nouvelles sources de données ;
- le traitement de plusieurs établissements de santé ;
- le suivi en temps réel des données ;
- la surveillance automatique de la qualité des données ;
- le monitoring des pipelines ;
- l'amélioration continue du modèle prédictif.