# Analyse du besoin métier

## 1. Contexte

Les établissements hospitaliers produisent un volume important de données relatives aux patients, aux admissions, aux diagnostics, aux traitements et aux hospitalisations.

Ces données sont souvent dispersées ou insuffisamment exploitées pour produire des indicateurs fiables et aider les responsables hospitaliers à suivre les réhospitalisations.

Le projet consiste à concevoir une plateforme Data Engineering et Business Intelligence permettant de centraliser, contrôler, transformer et analyser les données hospitalières.

Le dataset utilisé est « Diabetes 130-US Hospitals for Years 1999–2008 ». Il contient des données relatives aux hospitalisations de patients diabétiques dans 130 hôpitaux américains.

## 2. Problématique

Comment construire une plateforme de données fiable permettant d’analyser les hospitalisations des patients diabétiques, de mesurer les réhospitalisations et d’identifier les profils associés à un retour à l’hôpital en moins de 30 jours ?

## 3. Objectif principal

Construire une plateforme Data Engineering complète capable de transformer un fichier CSV hospitalier en données fiables, structurées et exploitables dans des dashboards Power BI.

## 4. Objectifs spécifiques

- automatiser l’ingestion du fichier CSV ;
- contrôler la qualité des données ;
- nettoyer et standardiser les variables ;
- stocker les données nettoyées au format Parquet ;
- construire un Data Warehouse PostgreSQL ;
- créer des Data Marts adaptés aux besoins analytiques ;
- automatiser les pipelines avec Prefect ;
- définir les principaux indicateurs hospitaliers ;
- créer des dashboards professionnels avec Power BI ;
- analyser les facteurs liés à la réhospitalisation ;
- développer un modèle prédictif de réhospitalisation à moins de 30 jours ;
- intégrer les prédictions dans Power BI.

## 5. Question métier principale

Quels sont les profils, les diagnostics, les traitements et les caractéristiques d’hospitalisation les plus associés à une réhospitalisation en moins de 30 jours ?

## 6. Questions métier secondaires

- Quel est le taux global de réhospitalisation ?
- Quel est le taux de réhospitalisation en moins de 30 jours ?
- Quelles tranches d’âge sont les plus concernées ?
- Existe-t-il une différence selon le sexe ou la race ?
- Quels diagnostics sont les plus associés aux réhospitalisations ?
- La durée du séjour influence-t-elle la réhospitalisation ?
- Le nombre d’hospitalisations précédentes augmente-t-il le risque ?
- Quel est l’impact du nombre de médicaments ?
- Les changements de traitement influencent-ils la réhospitalisation ?
- Quels profils de patients utilisent le plus fréquemment les services hospitaliers ?

## 7. Résultat attendu

La solution finale devra fournir :

- un pipeline Data Engineering automatisé ;
- un système de contrôle qualité ;
- un stockage en couches Landing, Raw, Clean et Curated ;
- un Data Warehouse PostgreSQL ;
- plusieurs Data Marts ;
- des dashboards Power BI ;
- un suivi de la qualité des données ;
- un suivi de l’exécution des pipelines ;
- un module prédictif de réhospitalisation.