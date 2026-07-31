import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "La variable DATABASE_URL est absente du fichier .env"
    )


def get_engine() -> Engine:
    """Créer et retourner le moteur de connexion PostgreSQL."""
    return create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
    )


def test_database_connection() -> bool:
    """Tester la connexion à PostgreSQL."""
    engine = get_engine()

    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        return result.scalar_one() == 1


if __name__ == "__main__":
    if test_database_connection():
        print("CONNEXION POSTGRESQL OK")
