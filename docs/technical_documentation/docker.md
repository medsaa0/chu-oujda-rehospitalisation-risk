# Conteneurisation (Étape 19)

## Services

| Service | Rôle | Démarrage |
|---|---|---|
| `postgres` | Data Warehouse PostgreSQL | par défaut (`docker compose up -d`) |
| `api` | API FastAPI (Étape 18) | par défaut |
| `pipeline` | Exécute le flow Prefect complet (Étapes 5-10) | à la demande (`profile: pipeline`) |
| `mlflow` | Interface de suivi des entraînements (Étape 17) | à la demande (`profile: monitoring`) |

Tous les services partagent la même image (`Dockerfile` à la racine),
qui installe `requirements.txt` et embarque `api/`, `src/`, `ml/`,
`orchestration/`, `warehouse/` et `data/source/`. Seule la commande
lancée diffère par service.

## Lancement

Base + API :

```bash
docker compose up -d
```

Exécuter le pipeline complet dans un conteneur (one-off) :

```bash
docker compose --profile pipeline run --rm pipeline
```

Démarrer l'interface MLflow (`http://localhost:5000`) :

```bash
docker compose --profile monitoring up -d mlflow
```

## Variables d'environnement

Définies dans `.env` (voir `.env.example`) ; `docker-compose.yml`
surcharge `DATABASE_URL` pour les services `api`/`pipeline` afin qu'ils
utilisent le nom de service Docker `postgres` (réseau interne) plutôt
que `localhost` (utilisé lors d'une exécution en dehors de Docker).

| Variable | Défaut | Rôle |
|---|---|---|
| `POSTGRES_PORT` | `5433` | Port hôte exposé pour PostgreSQL |
| `API_PORT` | `8000` | Port hôte exposé pour l'API |
| `MLFLOW_PORT` | `5000` | Port hôte exposé pour l'UI MLflow |

## Volumes

- `postgres_data` : persistance de la base entre redémarrages.
- `./ml/models` et `./reports` montés dans `api` : le modèle entraîné
  localement (Étape 17) reste accessible à l'API sans reconstruire
  l'image.
- `./data`, `./logs`, `./reports` montés dans `pipeline` : les fichiers
  Parquet et les rapports produits par le pipeline restent visibles sur
  l'hôte.
- `./mlruns` monté dans `mlflow` : mêmes runs que ceux produits par un
  entraînement lancé localement (`python -m ml.training.train_models`).

## Ordre recommandé pour un environnement Docker complet

```bash
docker compose up -d postgres
docker compose --profile pipeline run --rm pipeline
# Entrainement du modele (hors conteneur, plus simple pour iterer) :
python -m ml.training.train_models
python -m ml.prediction.predict
docker compose up -d api
docker compose --profile monitoring up -d mlflow
```

## Limite connue

L'entraînement du modèle (`ml/training/train_models.py`) n'est pas
conteneurisé comme service à part : il est prévu pour être exécuté
ponctuellement (localement ou via `docker compose run --rm pipeline
python -m ml.training.train_models`), pas en continu, ce qui ne
justifie pas un service dédié dans `docker-compose.yml`.
