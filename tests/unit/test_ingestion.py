from pathlib import Path

import pytest

from src.ingestion.ingest_csv import (
    calculate_sha256,
    validate_source_file,
)


def test_calculate_sha256(tmp_path: Path) -> None:
    test_file = tmp_path / "test.txt"
    test_file.write_bytes(b"abc")

    result = calculate_sha256(test_file)

    assert result == (
        "ba7816bf8f01cfea414140de5dae2223"
        "b00361a396177a9cb410ff61f20015ad"
    )


def test_validate_source_file_accepts_valid_file(
    tmp_path: Path,
) -> None:
    test_file = tmp_path / "diabetic_data.csv"
    test_file.write_text(
        "encounter_id,patient_nbr\n1,10\n",
        encoding="utf-8",
    )

    result = validate_source_file(test_file)

    assert result > 0


def test_validate_source_file_rejects_wrong_name(
    tmp_path: Path,
) -> None:
    test_file = tmp_path / "wrong_name.csv"
    test_file.write_text(
        "id\n1\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Nom invalide"):
        validate_source_file(test_file)


def test_validate_source_file_rejects_empty_file(
    tmp_path: Path,
) -> None:
    test_file = tmp_path / "diabetic_data.csv"
    test_file.touch()

    with pytest.raises(ValueError, match="vide"):
        validate_source_file(test_file)