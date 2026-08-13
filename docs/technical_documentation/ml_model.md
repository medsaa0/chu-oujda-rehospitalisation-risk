# Modèle prédictif de réhospitalisation (Étape 17)

## Objectif

Estimer la probabilité qu'une hospitalisation soit suivie d'une
réhospitalisation à moins de 30 jours (`readmitted_30_days`, Étape 8).

## Périmètre d'entraînement

Les hospitalisations dont la sortie correspond à un **décès ou une
sortie en hospice** (`discharge_disposition_id` ∈ `{11, 13, 14, 19, 20, 21}`,
voir `data/source/IDS_mapping.csv`) sont **exclues** : un patient décédé
ne peut pas être réhospitalisé, et les inclure biaiserait le modèle vers
une prédiction triviale. C'est la pratique standard sur ce dataset
(cf. Strack et al., 2014).

## Variables utilisées

Numériques : `time_in_hospital`, `num_lab_procedures`, `num_procedures`,
`num_medications`, `number_diagnoses`, `age_midpoint`,
`total_previous_visits`, `healthcare_utilization_score`,
`patient_complexity_score`, `active_medications_count`,
`medication_dosage_changes_count`.

Catégorielles (encodage One-Hot) : `gender`, `race`, `admission_type_id`,
`discharge_disposition_id`, `admission_source_id`, `max_glu_serum`,
`a1c_result`, `change`, `diabetesmed`, `insulin_prescribed`,
`diag_1_group`.

## Modèles comparés

`ml/training/train_models.py` entraîne et compare, avec
`class_weight="balanced"` (Logistic Regression, Random Forest) ou
`scale_pos_weight` (XGBoost) pour compenser le déséquilibre de classes
(~11 % de cas positifs) :

- Logistic Regression
- Random Forest (300 arbres, profondeur 12)
- XGBoost (300 arbres, profondeur 6, learning rate 0.05)

Le meilleur modèle (ROC-AUC le plus élevé sur le jeu de test, 20 %,
stratifié) est sauvegardé dans `ml/models/best_model.joblib` (pipeline
complet : prétraitement + modèle).

## Résultats (dernière exécution locale)

Voir `reports/ml/model_evaluation_latest.json` pour le détail complet.
Ordre de grandeur observé (cohérent avec la littérature publiée sur ce
dataset, qui rapporte généralement un ROC-AUC entre 0.65 et 0.69 pour
cette tâche) :

| Modèle | ROC-AUC | F1 | Précision | Rappel |
|---|---|---|---|---|
| Logistic Regression | ~0.65 | ~0.26 | ~0.18 | ~0.54 |
| Random Forest | ~0.66 | ~0.27 | ~0.18 | ~0.54 |
| XGBoost (retenu) | ~0.66 | ~0.27 | ~0.18 | ~0.56 |

## Suivi MLflow

Chaque run (par modèle) journalise ses hyperparamètres, ses métriques
et l'artefact du pipeline dans l'expérience
`hospital_readmission_30_days` (dossier local `mlruns/`, non versionné).
Consultable avec :

```bash
mlflow ui
```

## Scoring et table des prédictions

`ml/prediction/predict.py` charge `best_model.joblib`, score toutes les
hospitalisations éligibles et écrit le résultat dans
`warehouse.fact_prediction` (`encounter_key`, `predicted_probability`,
`predicted_risk_category`, `model_name`, `predicted_at`).

### Catégories de risque : seuils par quantile, pas par probabilité fixe

`class_weight="balanced"` et `scale_pos_weight` améliorent le
**classement** (ROC-AUC) mais **décalibrent** la probabilité prédite
(elle ne s'interprète plus comme une vraie probabilité absolue). Un
seuil fixe (ex. `probabilité >= 0.30` → risque élevé) serait donc
trompeur : en pratique, la majorité des scores dépassait ce seuil.

`categorize_risk()` utilise donc des **seuils par quantile** de la
population scorée : les 80 % de probabilité la plus basse sont classés
`Low`, les 15 % suivants `Medium`, les 5 % les plus élevés `High`. Ce
choix garde une répartition informative et exploitable dans les
dashboards, indépendamment de la calibration absolue des probabilités.

### Vérification de la valeur prédictive

Le taux réel de réhospitalisation à 30 jours par catégorie prédite
(dernière exécution locale) confirme un pouvoir discriminant net :

| Catégorie | Hospitalisations | Taux réel de réhospitalisation à 30 jours |
|---|---|---|
| Low | ~79 500 | ~7.6 % |
| Medium | ~14 900 | ~20.5 % |
| High | ~5 000 | ~44.0 % |

## Commandes

```bash
python -m ml.training.train_models
python -m ml.prediction.predict
```

Prérequis : Étapes 7 et 8 déjà exécutées (tables `staging.*` peuplées).

## Limites connues

- Les probabilités de `predicted_probability` ne sont pas calibrées
  (voir ci-dessus) : à utiliser pour le classement/la catégorisation,
  pas comme une probabilité clinique absolue.
- Aucune explicabilité (SHAP) n'est encore intégrée malgré sa présence
  dans `requirements.txt` ; c'est une amélioration possible pour une
  itération future du projet.
