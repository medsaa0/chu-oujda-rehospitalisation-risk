# Pipeline ETL

## Objectif

Le pipeline ETL transforme les données hospitalières validées en données
propres, typées et prêtes pour leur exploitation dans PostgreSQL.

## Source

Le pipeline utilise le fichier Parquet validé le plus récent présent dans :

`data/clean/`

## Transformations appliquées

- conservation des colonnes attendues ;
- remplacement des chaînes vides et de `?` par des valeurs nulles ;
- suppression des doublons résiduels ;
- conversion des colonnes numériques en entiers ;
- remplacement des valeurs descriptives absentes par `Unknown` ;
- nettoyage et normalisation des codes diagnostics ;
- normalisation des colonnes de médicaments ;
- remplacement des tirets dans les noms de colonnes par des underscores ;
- ajout de métadonnées techniques ETL.

Les diagnostics absents restent nulls. Le pipeline n'invente jamais un
diagnostic médical.

## Sortie Parquet

Le fichier final est enregistré dans :

`data/curated/`

## Vérification DuckDB

DuckDB vérifie :

- le nombre de lignes du fichier Curated ;
- l'unicité de `encounter_id`.

## Chargement PostgreSQL

Les données sont chargées dans :

`staging.hospital_encounters_curated`

La table est remplacée à chaque exécution afin d'éviter les doublons de
chargement.

## Suivi

Chaque exécution est enregistrée dans :

`etl_runs`

Les logs sont disponibles dans :

- `logs/etl_transformation.log`
- `logs/etl_loading.log`
- `logs/etl_pipeline.log`

Le rapport de la dernière exécution est enregistré dans :

`reports/etl/etl_report_latest.json`

## Limite de cette étape

Cette étape ne crée pas encore les variables analytiques ou prédictives.
Le Feature Engineering sera réalisé dans l'étape suivante.