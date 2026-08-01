CREATE TABLE IF NOT EXISTS data_quality_runs (
    id BIGSERIAL PRIMARY KEY,
    raw_file_name VARCHAR(255) NOT NULL,
    raw_path TEXT NOT NULL,
    status VARCHAR(20) NOT NULL,
    total_rows BIGINT,
    valid_rows BIGINT,
    rejected_rows BIGINT,
    total_violations BIGINT,
    duplicate_rows BIGINT,
    valid_path TEXT,
    quarantine_path TEXT,
    report_path TEXT,
    started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMPTZ,
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS data_quality_rule_results (
    id BIGSERIAL PRIMARY KEY,
    quality_run_id BIGINT NOT NULL,
    rule_name VARCHAR(150) NOT NULL,
    column_name VARCHAR(150) NOT NULL,
    violation_count BIGINT NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_quality_run
        FOREIGN KEY (quality_run_id)
        REFERENCES data_quality_runs(id)
        ON DELETE CASCADE
);