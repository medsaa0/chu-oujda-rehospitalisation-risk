import pytest

from src.loading.load_postgres import validate_identifier


def test_accepts_simple_identifier() -> None:
    validate_identifier("hospital_encounters_curated")


def test_accepts_identifier_starting_with_underscore() -> None:
    validate_identifier("_internal_table")


@pytest.mark.parametrize(
    "identifier",
    [
        "table; DROP TABLE etl_runs;--",
        "table name",
        "table-name",
        "table.name",
        "1table",
        "",
        "table'",
    ],
)
def test_rejects_unsafe_identifiers(identifier: str) -> None:
    with pytest.raises(ValueError):
        validate_identifier(identifier)
