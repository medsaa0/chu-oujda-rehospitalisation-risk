CREATE TABLE IF NOT EXISTS ingestion_history (
    id BIGSERIAL PRIMARY KEY,
    source_file_name VARCHAR(255) NOT NULL,
    source_path TEXT NOT NULL,
    landing_path TEXT,
    raw_path TEXT,
    sha256 VARCHAR(64) NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    row_count BIGINT,
    column_count INTEGER,
    status VARCHAR(20) NOT NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMPTZ,
    error_message TEXT
);