import argparse
import hashlib
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import polars as pl
from sqlalchemy import text
from sqlalchemy.engine import Engine

from src.utils.database import get_engine
from src.utils.logging_config import get_logger
from src.utils.paths import (
    LANDING_DIR,
    RAW_DIR,
    SOURCE_DIR,
    WAREHOUSE_DIR,
    create_required_directories,
)

EXPECTED_FILENAME = "diabetic_data.csv"
HASH_CHUNK_SIZE = 1024 * 1024

logger = get_logger("ingestion")


def calculate_sha256(file_path: Path) -> str:
    """Calculer l'empreinte SHA-256 d'un fichier."""
    digest = hashlib.sha256()

    with file_path.open("rb") as file:
        while chunk := file.read(HASH_CHUNK_SIZE):
            digest.update(chunk)

    return digest.hexdigest()


def validate_source_file(file_path: Path) -> int:
    """Vérifier la présence, le nom, l'extension et la taille du fichier."""
    if not file_path.exists():
        raise FileNotFoundError(f"Fichier introuvable : {file_path}")

    if not file_path.is_file():
        raise ValueError(f"Le chemin n'est pas un fichier : {file_path}")

    if file_path.name != EXPECTED_FILENAME:
        raise ValueError(
            f"Nom invalide : {file_path.name}. "
            f"Nom attendu : {EXPECTED_FILENAME}"
        )

    if file_path.suffix.lower() != ".csv":
        raise ValueError(f"Extension invalide : {file_path.suffix}")

    file_size = file_path.stat().st_size

    if file_size == 0:
        raise ValueError(f"Le fichier est vide : {file_path}")

    return file_size


def ensure_ingestion_table(engine: Engine) -> None:
    """Créer la table de suivi des imports."""
    ddl_path = (
        WAREHOUSE_DIR
        / "ddl"
        / "001_create_ingestion_history.sql"
    )

    if not ddl_path.exists():
        raise FileNotFoundError(f"Script SQL introuvable : {ddl_path}")

    ddl_statement = ddl_path.read_text(encoding="utf-8-sig")

    with engine.begin() as connection:
        connection.exec_driver_sql(ddl_statement)


def find_successful_import(
    engine: Engine,
    file_hash: str,
) -> dict[str, Any] | None:
    """Rechercher un import déjà réussi avec la même empreinte."""
    query = text(
        """
        SELECT
            id,
            landing_path,
            raw_path,
            row_count,
            column_count
        FROM ingestion_history
        WHERE sha256 = :sha256
          AND status = 'SUCCESS'
        ORDER BY id DESC
        LIMIT 1
        """
    )

    with engine.connect() as connection:
        result = connection.execute(
            query,
            {"sha256": file_hash},
        )

        row = result.mappings().first()

    return dict(row) if row else None


def create_import_record(
    engine: Engine,
    source_path: Path,
    landing_path: Path,
    raw_path: Path,
    file_hash: str,
    file_size: int,
) -> int:
    """Créer une ligne PostgreSQL avec le statut RUNNING."""
    query = text(
        """
        INSERT INTO ingestion_history (
            source_file_name,
            source_path,
            landing_path,
            raw_path,
            sha256,
            file_size_bytes,
            status
        )
        VALUES (
            :source_file_name,
            :source_path,
            :landing_path,
            :raw_path,
            :sha256,
            :file_size_bytes,
            'RUNNING'
        )
        RETURNING id
        """
    )

    values = {
        "source_file_name": source_path.name,
        "source_path": str(source_path),
        "landing_path": str(landing_path),
        "raw_path": str(raw_path),
        "sha256": file_hash,
        "file_size_bytes": file_size,
    }

    with engine.begin() as connection:
        import_id = connection.execute(
            query,
            values,
        ).scalar_one()

    return int(import_id)


def mark_import_success(
    engine: Engine,
    import_id: int,
    row_count: int,
    column_count: int,
) -> None:
    """Enregistrer la réussite de l'import."""
    query = text(
        """
        UPDATE ingestion_history
        SET status = 'SUCCESS',
            row_count = :row_count,
            column_count = :column_count,
            finished_at = CURRENT_TIMESTAMP
        WHERE id = :import_id
        """
    )

    with engine.begin() as connection:
        connection.execute(
            query,
            {
                "import_id": import_id,
                "row_count": row_count,
                "column_count": column_count,
            },
        )


def mark_import_failed(
    engine: Engine,
    import_id: int,
    error_message: str,
) -> None:
    """Enregistrer l'échec de l'import."""
    query = text(
        """
        UPDATE ingestion_history
        SET status = 'FAILED',
            error_message = :error_message,
            finished_at = CURRENT_TIMESTAMP
        WHERE id = :import_id
        """
    )

    with engine.begin() as connection:
        connection.execute(
            query,
            {
                "import_id": import_id,
                "error_message": error_message[:4000],
            },
        )


def build_destination_paths(
    source_path: Path,
    file_hash: str,
) -> tuple[Path, Path]:
    """Construire les noms des fichiers Landing et Raw."""
    timestamp = datetime.now(timezone.utc).strftime(
        "%Y%m%dT%H%M%SZ"
    )

    landing_path = (
        LANDING_DIR
        / f"{timestamp}_{source_path.name}"
    )

    raw_path = (
        RAW_DIR
        / f"{source_path.stem}_{file_hash[:12]}.parquet"
    )

    return landing_path, raw_path


def ingest_csv(source_path: Path) -> dict[str, Any]:
    """Importer le CSV vers la Landing Zone et la Raw Layer."""
    create_required_directories()

    source_path = source_path.resolve()
    file_size = validate_source_file(source_path)
    file_hash = calculate_sha256(source_path)

    engine = get_engine()
    ensure_ingestion_table(engine)

    previous_import = find_successful_import(
        engine,
        file_hash,
    )

    if previous_import:
        logger.info(
            "Import ignoré : le fichier %s a déjà été importé "
            "avec l'identifiant %s.",
            source_path.name,
            previous_import["id"],
        )

        return {
            "status": "SKIPPED",
            "sha256": file_hash,
            "previous_import_id": previous_import["id"],
            "raw_path": previous_import["raw_path"],
        }

    landing_path, raw_path = build_destination_paths(
        source_path,
        file_hash,
    )

    import_id = create_import_record(
        engine=engine,
        source_path=source_path,
        landing_path=landing_path,
        raw_path=raw_path,
        file_hash=file_hash,
        file_size=file_size,
    )

    logger.info(
        "Début import_id=%s | fichier=%s | taille=%s octets",
        import_id,
        source_path.name,
        file_size,
    )

    try:
        shutil.copy2(
            source_path,
            landing_path,
        )

        dataframe = pl.read_csv(
            landing_path,
            infer_schema_length=0,
            try_parse_dates=False,
        )

        if dataframe.height == 0:
            raise ValueError(
                "Le fichier ne contient aucune ligne de données."
            )

        dataframe.write_parquet(
            raw_path,
            compression="zstd",
            statistics=True,
        )

        mark_import_success(
            engine=engine,
            import_id=import_id,
            row_count=dataframe.height,
            column_count=dataframe.width,
        )

        logger.info(
            "Import réussi | import_id=%s | lignes=%s | "
            "colonnes=%s | raw=%s",
            import_id,
            dataframe.height,
            dataframe.width,
            raw_path,
        )

        return {
            "status": "SUCCESS",
            "import_id": import_id,
            "sha256": file_hash,
            "file_size_bytes": file_size,
            "landing_path": str(landing_path),
            "raw_path": str(raw_path),
            "row_count": dataframe.height,
            "column_count": dataframe.width,
        }

    except Exception as error:
        if raw_path.exists():
            raw_path.unlink()

        mark_import_failed(
            engine=engine,
            import_id=import_id,
            error_message=str(error),
        )

        logger.exception(
            "Échec de l'import %s : %s",
            import_id,
            error,
        )

        raise


def parse_arguments() -> argparse.Namespace:
    """Lire les arguments de la commande."""
    parser = argparse.ArgumentParser(
        description=(
            "Importer diabetic_data.csv vers "
            "la Landing Zone et la Raw Layer."
        )
    )

    parser.add_argument(
        "--source",
        type=Path,
        default=SOURCE_DIR / EXPECTED_FILENAME,
        help="Chemin du fichier diabetic_data.csv.",
    )

    return parser.parse_args()


def main() -> None:
    """Lancer le pipeline depuis le terminal."""
    arguments = parse_arguments()
    result = ingest_csv(arguments.source)

    print()
    print("RESULTAT DE L'INGESTION")

    for key, value in result.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()