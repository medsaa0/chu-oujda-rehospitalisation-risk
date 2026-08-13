from src.utils.paths import SOURCE_DIR
from src.warehouse.build_warehouse import (
    CALENDAR_END_YEAR,
    CALENDAR_START_YEAR,
    generate_calendar_rows,
    parse_ids_mapping,
)


def test_parse_ids_mapping_splits_three_sections() -> None:
    sections = parse_ids_mapping(SOURCE_DIR / "IDS_mapping.csv")

    assert set(sections) == {
        "admission_type_id",
        "discharge_disposition_id",
        "admission_source_id",
    }

    assert len(sections["admission_type_id"]) == 8
    assert (1, "Emergency") in sections["admission_type_id"]


def test_parse_ids_mapping_discharge_disposition_has_expired() -> None:
    sections = parse_ids_mapping(SOURCE_DIR / "IDS_mapping.csv")

    discharge_rows = dict(sections["discharge_disposition_id"])

    assert discharge_rows[11] == "Expired"


def test_generate_calendar_rows_covers_full_range() -> None:
    rows = generate_calendar_rows()

    years = {row["year_number"] for row in rows}

    assert years == set(range(CALENDAR_START_YEAR, CALENDAR_END_YEAR + 1))
    assert rows[0]["full_date"].isoformat() == f"{CALENDAR_START_YEAR}-01-01"
    assert rows[-1]["full_date"].isoformat() == f"{CALENDAR_END_YEAR}-12-31"


def test_generate_calendar_rows_date_key_matches_date() -> None:
    rows = generate_calendar_rows()

    first_row = rows[0]

    assert first_row["date_key"] == 19990101
    assert first_row["day_name"] == "Friday"
    assert first_row["is_weekend"] is False
