from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]

DATA_DIR = ROOT_DIR / "data"

SOURCE_DIR = DATA_DIR / "source"
LANDING_DIR = DATA_DIR / "landing"
RAW_DIR = DATA_DIR / "raw"
CLEAN_DIR = DATA_DIR / "clean"
CURATED_DIR = DATA_DIR / "curated"
FEATURES_DIR = DATA_DIR / "features"
QUARANTINE_DIR = DATA_DIR / "quarantine"

LOGS_DIR = ROOT_DIR / "logs"
WAREHOUSE_DIR = ROOT_DIR / "warehouse"
MODELS_DIR = ROOT_DIR / "ml" / "models"


REQUIRED_DIRECTORIES = [
    SOURCE_DIR,
    LANDING_DIR,
    RAW_DIR,
    CLEAN_DIR,
    CURATED_DIR,
    FEATURES_DIR,
    QUARANTINE_DIR,
    LOGS_DIR,
    WAREHOUSE_DIR,
    MODELS_DIR,
]


def create_required_directories() -> None:
    """Créer les dossiers nécessaires au fonctionnement du pipeline."""
    for directory in REQUIRED_DIRECTORIES:
        directory.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    create_required_directories()

    print("Dossiers du projet :")
    for directory in REQUIRED_DIRECTORIES:
        print(f"[OK] {directory}")
