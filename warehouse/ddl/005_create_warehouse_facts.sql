CREATE TABLE IF NOT EXISTS warehouse.fact_hospitalization (
    encounter_key BIGINT PRIMARY KEY,
    patient_key BIGINT NOT NULL REFERENCES warehouse.dim_patient (patient_key),
    admission_type_id INTEGER REFERENCES warehouse.dim_admission_type (admission_type_id),
    discharge_disposition_id INTEGER REFERENCES warehouse.dim_discharge_disposition (discharge_disposition_id),
    admission_source_id INTEGER REFERENCES warehouse.dim_admission_source (admission_source_id),
    diag_1_key INTEGER REFERENCES warehouse.dim_diagnosis (diagnosis_key),
    diag_2_key INTEGER REFERENCES warehouse.dim_diagnosis (diagnosis_key),
    diag_3_key INTEGER REFERENCES warehouse.dim_diagnosis (diagnosis_key),
    time_in_hospital INTEGER NOT NULL,
    num_lab_procedures INTEGER NOT NULL,
    num_procedures INTEGER NOT NULL,
    num_medications INTEGER NOT NULL,
    number_diagnoses INTEGER NOT NULL,
    total_previous_visits INTEGER NOT NULL,
    healthcare_utilization_score INTEGER NOT NULL,
    patient_complexity_score INTEGER NOT NULL,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_fact_hospitalization_patient_key
    ON warehouse.fact_hospitalization (patient_key);

CREATE TABLE IF NOT EXISTS warehouse.fact_readmission (
    encounter_key BIGINT PRIMARY KEY
        REFERENCES warehouse.fact_hospitalization (encounter_key),
    readmitted TEXT NOT NULL,
    readmitted_30_days SMALLINT NOT NULL,
    readmitted_flag SMALLINT NOT NULL,
    is_frequent_patient SMALLINT NOT NULL,
    insulin_prescribed SMALLINT NOT NULL,
    high_medication_burden_flag SMALLINT NOT NULL,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_fact_readmission_readmitted_30_days
    ON warehouse.fact_readmission (readmitted_30_days);

CREATE TABLE IF NOT EXISTS warehouse.fact_medication_usage (
    fact_medication_usage_id BIGSERIAL PRIMARY KEY,
    encounter_key BIGINT NOT NULL
        REFERENCES warehouse.fact_hospitalization (encounter_key),
    medication_key INTEGER NOT NULL
        REFERENCES warehouse.dim_medication (medication_key),
    status TEXT NOT NULL,
    dosage_changed SMALLINT NOT NULL
);

COMMENT ON TABLE warehouse.fact_medication_usage IS
    'Table de faits (bridge) au grain encounter x medicament. Ne '
    'contient que les medicaments effectivement prescrits '
    '(status != ''No''), pour rester exploitable en volume tout en '
    'permettant le Mart Medicaments (Etape 10).';

CREATE INDEX IF NOT EXISTS ix_fact_medication_usage_encounter_key
    ON warehouse.fact_medication_usage (encounter_key);

CREATE INDEX IF NOT EXISTS ix_fact_medication_usage_medication_key
    ON warehouse.fact_medication_usage (medication_key);
