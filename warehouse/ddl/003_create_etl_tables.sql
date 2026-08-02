CREATE SCHEMA IF NOT EXISTS staging;

CREATE TABLE IF NOT EXISTS etl_runs (
    id BIGSERIAL PRIMARY KEY,

    source_clean_file_name VARCHAR(255) NOT NULL,
    source_clean_path TEXT NOT NULL,
    curated_path TEXT,

    target_schema VARCHAR(63) NOT NULL,
    target_table VARCHAR(63) NOT NULL,

    status VARCHAR(20) NOT NULL,

    input_rows BIGINT,
    output_rows BIGINT,
    duplicates_removed BIGINT,

    source_columns INTEGER,
    output_columns INTEGER,

    duckdb_row_count BIGINT,
    postgres_row_count BIGINT,

    report_path TEXT,

    started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMPTZ,

    error_message TEXT
);