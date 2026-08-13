CREATE SCHEMA IF NOT EXISTS warehouse;

CREATE TABLE IF NOT EXISTS warehouse.dim_patient (
    patient_key BIGSERIAL PRIMARY KEY,
    patient_nbr BIGINT NOT NULL UNIQUE,
    gender TEXT,
    race TEXT,
    first_age_bracket TEXT,
    first_age_midpoint INTEGER,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE warehouse.dim_patient IS
    'Dimension patient. gender/race/age proviennent de la premiere '
    'hospitalisation connue du patient (simplification Type 1, '
    'documentee dans docs/architecture/data_engineering_architecture.md) '
    'car ces attributs peuvent varier d''une hospitalisation a l''autre '
    'dans le dataset source.';

CREATE TABLE IF NOT EXISTS warehouse.dim_admission_type (
    admission_type_id INTEGER PRIMARY KEY,
    admission_type_description TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS warehouse.dim_discharge_disposition (
    discharge_disposition_id INTEGER PRIMARY KEY,
    discharge_disposition_description TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS warehouse.dim_admission_source (
    admission_source_id INTEGER PRIMARY KEY,
    admission_source_description TEXT NOT NULL
);

COMMENT ON TABLE warehouse.dim_admission_type IS
    'Correspond au groupe "DimAdmission" du README (volet type). '
    'Source : data/source/IDS_mapping.csv.';
COMMENT ON TABLE warehouse.dim_discharge_disposition IS
    'Correspond au groupe "DimAdmission" du README (volet sortie). '
    'Source : data/source/IDS_mapping.csv.';
COMMENT ON TABLE warehouse.dim_admission_source IS
    'Correspond au groupe "DimAdmission" du README (volet source). '
    'Source : data/source/IDS_mapping.csv.';

CREATE TABLE IF NOT EXISTS warehouse.dim_diagnosis (
    diagnosis_key SERIAL PRIMARY KEY,
    diagnosis_code TEXT NOT NULL UNIQUE,
    diagnosis_group TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS warehouse.dim_medication (
    medication_key SERIAL PRIMARY KEY,
    medication_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS warehouse.dim_date (
    date_key INTEGER PRIMARY KEY,
    full_date DATE NOT NULL UNIQUE,
    day_of_month INTEGER NOT NULL,
    month_number INTEGER NOT NULL,
    month_name TEXT NOT NULL,
    quarter_number INTEGER NOT NULL,
    year_number INTEGER NOT NULL,
    day_of_week_number INTEGER NOT NULL,
    day_name TEXT NOT NULL,
    is_weekend BOOLEAN NOT NULL
);

COMMENT ON TABLE warehouse.dim_date IS
    'Table calendrier technique/pedagogique couvrant 1999-2008 (annees '
    'du dataset). Le dataset ne contient aucune date d''hospitalisation '
    'exacte : cette dimension n''est donc PAS reliee par cle etrangere '
    'aux tables de faits. Elle sert uniquement de reference pour '
    'apprendre les fonctions de Time Intelligence dans Power BI (Etape 16).';
