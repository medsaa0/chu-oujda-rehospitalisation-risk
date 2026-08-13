CREATE SCHEMA IF NOT EXISTS marts;

-- Mart Patients : une ligne par patient (Dashboard 2 - Patient Analysis)
CREATE OR REPLACE VIEW marts.mart_patients AS
SELECT
    p.patient_key,
    p.patient_nbr,
    p.gender,
    p.race,
    p.first_age_bracket,
    p.first_age_midpoint,
    COUNT(h.encounter_key) AS total_encounters,
    SUM(h.total_previous_visits) AS total_previous_visits_sum,
    MAX(r.is_frequent_patient) AS is_frequent_patient_ever,
    SUM(r.readmitted_30_days) AS readmitted_30_days_count,
    SUM(r.readmitted_flag) AS readmitted_count
FROM warehouse.dim_patient p
JOIN warehouse.fact_hospitalization h ON h.patient_key = p.patient_key
JOIN warehouse.fact_readmission r ON r.encounter_key = h.encounter_key
GROUP BY
    p.patient_key, p.patient_nbr, p.gender, p.race,
    p.first_age_bracket, p.first_age_midpoint;

-- Mart Hospitalisations : une ligne par sejour (Dashboard 3 - Hospitalization Analysis)
CREATE OR REPLACE VIEW marts.mart_hospitalizations AS
SELECT
    h.encounter_key,
    h.patient_key,
    p.gender,
    p.race,
    p.first_age_bracket,
    at.admission_type_description,
    dd.discharge_disposition_description,
    ads.admission_source_description,
    h.time_in_hospital,
    h.num_lab_procedures,
    h.num_procedures,
    h.num_medications,
    h.number_diagnoses,
    h.total_previous_visits,
    h.healthcare_utilization_score,
    h.patient_complexity_score
FROM warehouse.fact_hospitalization h
JOIN warehouse.dim_patient p ON p.patient_key = h.patient_key
LEFT JOIN warehouse.dim_admission_type at
    ON at.admission_type_id = h.admission_type_id
LEFT JOIN warehouse.dim_discharge_disposition dd
    ON dd.discharge_disposition_id = h.discharge_disposition_id
LEFT JOIN warehouse.dim_admission_source ads
    ON ads.admission_source_id = h.admission_source_id;

-- Mart Reheospitalisation : une ligne par sejour, facteurs inclus (Dashboard 4)
CREATE OR REPLACE VIEW marts.mart_readmission AS
SELECT
    h.encounter_key,
    p.gender,
    p.race,
    p.first_age_bracket,
    at.admission_type_description,
    d1.diagnosis_group AS diag_1_group,
    h.time_in_hospital,
    h.total_previous_visits,
    r.readmitted,
    r.readmitted_30_days,
    r.readmitted_flag,
    r.is_frequent_patient,
    r.insulin_prescribed,
    r.high_medication_burden_flag
FROM warehouse.fact_hospitalization h
JOIN warehouse.fact_readmission r ON r.encounter_key = h.encounter_key
JOIN warehouse.dim_patient p ON p.patient_key = h.patient_key
LEFT JOIN warehouse.dim_admission_type at
    ON at.admission_type_id = h.admission_type_id
LEFT JOIN warehouse.dim_diagnosis d1 ON d1.diagnosis_key = h.diag_1_key;

-- Mart Diagnostics : une ligne par diagnostic principal (Dashboard 5)
CREATE OR REPLACE VIEW marts.mart_diagnostics AS
SELECT
    d1.diagnosis_code,
    d1.diagnosis_group,
    COUNT(h.encounter_key) AS hospitalization_count,
    COUNT(DISTINCT h.patient_key) AS patient_count,
    ROUND(AVG(r.readmitted_30_days)::numeric, 4) AS readmitted_30_days_rate,
    ROUND(AVG(h.time_in_hospital)::numeric, 2) AS avg_time_in_hospital
FROM warehouse.fact_hospitalization h
JOIN warehouse.fact_readmission r ON r.encounter_key = h.encounter_key
JOIN warehouse.dim_diagnosis d1 ON d1.diagnosis_key = h.diag_1_key
GROUP BY d1.diagnosis_code, d1.diagnosis_group;

-- Mart Medicaments : une ligne par medicament (Dashboard 5)
CREATE OR REPLACE VIEW marts.mart_medications AS
SELECT
    m.medication_name,
    COUNT(*) AS prescription_count,
    SUM(u.dosage_changed) AS dosage_change_count,
    COUNT(DISTINCT u.encounter_key) AS hospitalization_count,
    ROUND(AVG(r.readmitted_30_days)::numeric, 4) AS readmitted_30_days_rate
FROM warehouse.fact_medication_usage u
JOIN warehouse.dim_medication m ON m.medication_key = u.medication_key
JOIN warehouse.fact_readmission r ON r.encounter_key = u.encounter_key
GROUP BY m.medication_name;

-- Mart Qualite : une ligne par execution de controle qualite (Dashboard 6)
CREATE OR REPLACE VIEW marts.mart_quality AS
SELECT
    q.id AS quality_run_id,
    q.raw_file_name,
    q.status,
    q.total_rows,
    q.valid_rows,
    q.rejected_rows,
    q.total_violations,
    q.duplicate_rows,
    CASE
        WHEN q.total_rows > 0
            THEN ROUND((q.valid_rows::numeric / q.total_rows) * 100, 4)
        ELSE NULL
    END AS valid_rate_percent,
    q.started_at,
    q.finished_at
FROM data_quality_runs q;

-- Detail des violations par regle, pour le Mart Qualite (Dashboard 6)
CREATE OR REPLACE VIEW marts.mart_quality_violations AS
SELECT
    rr.quality_run_id,
    rr.rule_name,
    rr.column_name,
    rr.violation_count,
    rr.description
FROM data_quality_rule_results rr;
