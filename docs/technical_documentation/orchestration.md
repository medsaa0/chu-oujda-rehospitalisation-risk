# Orchestration Prefect (Étape 11)

## Objectif

Automatiser l'enchaînement complet du pipeline Data Engineering avec
Prefect, sans dupliquer la logique déjà écrite aux Étapes 5 à 10.

## Flow

`orchestration/prefect_flows/pipeline_flow.py` définit le flow
`hospital-readmission-pipeline`, composé de six tâches qui appellent
directement les fonctions Python existantes :

```text
ingestion (Etape 5)
    -> validation (Etape 6)
        -> etl (Etape 7 : nettoyage, transformation, PostgreSQL)
            -> feature_engineering (Etape 8)
                -> data_warehouse (Etape 9)
                    -> data_marts (Etape 10)
```

Chaque tâche reçoit en argument le résultat de la précédente
(`depends_on`) uniquement pour **forcer l'ordre d'exécution** dans le
graphe Prefect ; les données circulent en réalité par PostgreSQL et par
les fichiers Parquet, exactement comme lors d'une exécution manuelle
étape par étape.

## Gestion des erreurs et relance

- Chaque tâche est configurée avec `retries=2` et
  `retry_delay_seconds=30` : un échec transitoire (ex. PostgreSQL pas
  encore prêt) est automatiquement retenté.
- Si une tâche échoue après ses tentatives, le flow s'arrête : les
  tâches suivantes ne s'exécutent pas (pas de Data Warehouse construit
  sur des données invalides).
- Un hook `on_failure` (`notify_on_failure`) journalise clairement
  l'échec du run. Un vrai canal de notification (email, Slack, Teams)
  peut y être branché en production ; cela demande des identifiants
  externes hors du périmètre pédagogique de ce projet.

## Journalisation

Prefect journalise chaque tâche (début, fin, état, durée) via
`get_run_logger()`, en plus des loggers Python existants de chaque
module (`src.utils.logging_config`). L'historique des runs est
consultable dans l'UI Prefect (`prefect server start`).

## Exécution

Run unique (utilisé aussi en local/CI) :

```bash
python -m orchestration.prefect_flows.pipeline_flow
```

Déploiement planifié (bloquant, sert le flow selon une expression cron) :

```bash
python -m orchestration.prefect_flows.pipeline_flow --serve --cron "0 3 * * *"
```

## Prérequis

- PostgreSQL démarré (`docker compose up -d`).
- `data/source/diabetic_data.csv` présent (voir Étape 5).

## Limite connue

Prefect a besoin d'un serveur (temporaire en local si `PREFECT_API_URL`
n'est pas défini, ou dédié via `prefect server start` /
`prefect cloud login` en production) pour suivre l'état des runs.
