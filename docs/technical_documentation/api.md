# API FastAPI (Étape 18)

## Lancement

```bash
uvicorn api.app.main:app --reload
```

Documentation interactive (Swagger) : `http://127.0.0.1:8000/docs`.

## Endpoints

| Méthode | Route | Description | Source |
|---|---|---|---|
| GET | `/health` | Vérifie l'API et la connexion PostgreSQL | — |
| GET | `/api/kpis` | KPIs globaux (voir `docs/business/kpis.md`) | `warehouse.fact_hospitalization` + `fact_readmission` |
| GET | `/api/patients` | Liste paginée (`limit`, `offset`, filtres `gender`/`race`) | `marts.mart_patients` |
| GET | `/api/hospitalizations` | Liste paginée | `marts.mart_hospitalizations` |
| GET | `/api/readmissions` | Liste paginée (filtre `readmitted_30_days`) | `marts.mart_readmission` |
| GET | `/api/data-quality` | Historique des contrôles qualité | `marts.mart_quality` |
| GET | `/api/pipeline-runs` | Historique des exécutions ETL | table `etl_runs` |
| POST | `/api/predict` | Score de risque de réhospitalisation à 30 jours | `ml/models/best_model.joblib` |

## Structure

```text
api/app/
├── main.py            # Application FastAPI, montage des routers
├── dependencies.py     # Moteur PostgreSQL et modele ML mis en cache
├── schemas.py           # Modeles Pydantic (requetes/reponses)
└── routers/
    ├── health.py
    ├── kpis.py
    ├── patients.py
    ├── hospitalizations.py
    ├── readmissions.py
    ├── data_quality.py
    ├── pipeline_runs.py
    └── predict.py
```

## `/api/predict`

Attend les mêmes variables que le modèle (voir
`docs/technical_documentation/ml_model.md`). Réponse `503` si le modèle
n'a pas encore été entraîné (`python -m ml.training.train_models` puis
`python -m ml.prediction.predict`), `422` si le corps de la requête ne
correspond pas au schéma attendu.

Les catégories de risque (`Low`/`Medium`/`High`) réutilisent les seuils
par quantile calculés lors du dernier scoring
(`reports/ml/prediction_report_latest.json`), pour rester cohérentes
avec `warehouse.fact_prediction`.

## Prérequis

- PostgreSQL démarré avec le pipeline exécuté au moins jusqu'à l'Étape 10
  (Data Marts) pour les endpoints de lecture.
- Modèle entraîné (Étape 17) pour `/api/predict`.

## Tests

`tests/integration/test_api.py` utilise `fastapi.testclient.TestClient`
contre la base réelle (nécessite PostgreSQL démarré et le pipeline
exécuté).
