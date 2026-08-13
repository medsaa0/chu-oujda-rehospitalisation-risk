CREATE TABLE IF NOT EXISTS warehouse.fact_prediction (
    encounter_key BIGINT PRIMARY KEY
        REFERENCES warehouse.fact_hospitalization (encounter_key),
    predicted_probability DOUBLE PRECISION NOT NULL,
    predicted_risk_category TEXT NOT NULL,
    model_name TEXT NOT NULL,
    model_version TEXT,
    predicted_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE warehouse.fact_prediction IS
    'Scores du modele predictif de reheospitalisation a 30 jours '
    '(Etape 17). Les hospitalisations avec sortie deces/hospice sont '
    'exclues (voir ml/training/train_models.py), le risque de '
    'reheospitalisation n''y ayant pas de sens clinique.';

CREATE INDEX IF NOT EXISTS ix_fact_prediction_risk_category
    ON warehouse.fact_prediction (predicted_risk_category);
