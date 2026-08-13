# Catalogue des KPIs

## Objectif

Les indicateurs de performance (KPIs) permettent de suivre l'activité
hospitalière, d'analyser les réhospitalisations et d'aider les
responsables hospitaliers dans leur prise de décision.

Chaque KPI ci-dessous précise sa **formule de calcul** et le
**Data Mart** (Étape 10) ou la table `warehouse.*` (Étape 9) sur lequel
il s'appuie, afin de pouvoir être directement traduit en mesure DAX
dans Power BI (Étape 14).

---

## KPIs d'activité

| KPI | Formule | Source |
|---|---|---|
| Nombre total d'hospitalisations | `COUNT(encounter_key)` | `marts.mart_hospitalizations` |
| Nombre total de patients uniques | `COUNT(DISTINCT patient_key)` | `marts.mart_patients` |
| Nombre total de réhospitalisations | `SUM(readmitted_flag)` | `marts.mart_readmission` |
| Nombre de réhospitalisations à moins de 30 jours | `SUM(readmitted_30_days)` | `marts.mart_readmission` |
| Nombre moyen d'hospitalisations par patient | `COUNT(encounter_key) / COUNT(DISTINCT patient_key)` | `marts.mart_patients.total_encounters` |

---

## KPIs de réhospitalisation

| KPI | Formule | Source |
|---|---|---|
| Taux global de réhospitalisation | `AVG(readmitted_flag)` (ou `SUM(readmitted_flag) / COUNT(*)`) | `marts.mart_readmission` |
| Taux de réhospitalisation à moins de 30 jours | `AVG(readmitted_30_days)` | `marts.mart_readmission` |
| Taux de réhospitalisation après 30 jours | `AVG(readmitted_flag) - AVG(readmitted_30_days)` (statut `>30`) | `marts.mart_readmission` |
| Taux de réhospitalisation par tranche d'âge | `AVG(readmitted_30_days)` groupé par `first_age_bracket` | `marts.mart_readmission` |
| Taux de réhospitalisation par sexe | `AVG(readmitted_30_days)` groupé par `gender` | `marts.mart_readmission` |
| Taux de réhospitalisation par race | `AVG(readmitted_30_days)` groupé par `race` | `marts.mart_readmission` |

---

## KPIs liés aux hospitalisations

| KPI | Formule | Source |
|---|---|---|
| Durée moyenne du séjour | `AVG(time_in_hospital)` | `marts.mart_hospitalizations` |
| Nombre moyen de visites antérieures | `AVG(total_previous_visits)` | `marts.mart_hospitalizations` |
| Nombre moyen de procédures médicales | `AVG(num_procedures)` | `marts.mart_hospitalizations` |
| Nombre moyen d'examens de laboratoire | `AVG(num_lab_procedures)` | `marts.mart_hospitalizations` |
| Nombre moyen de médicaments prescrits | `AVG(num_medications)` | `marts.mart_hospitalizations` |
| Nombre moyen de diagnostics par patient | `AVG(number_diagnoses)` | `marts.mart_hospitalizations` |

---

## KPIs cliniques

| KPI | Formule | Source |
|---|---|---|
| Diagnostics les plus fréquents | `COUNT(*)` groupé par `diagnosis_group` (ou `diagnosis_code`), trié décroissant | `marts.mart_diagnostics` |
| Diagnostics associés aux réhospitalisations | `readmitted_30_days_rate` par `diagnosis_group`, trié décroissant | `marts.mart_diagnostics` |
| Médicaments les plus prescrits | `prescription_count` par `medication_name`, trié décroissant | `marts.mart_medications` |
| Utilisation de l'insuline | `AVG(insulin_prescribed)` | `marts.mart_readmission` |
| Évolution des traitements (changements de dosage) | `SUM(dosage_change_count)` par médicament | `marts.mart_medications` |
| Réhospitalisation selon le traitement | `readmitted_30_days_rate` par médicament | `marts.mart_medications` |

---

## KPIs de qualité des données

| KPI | Formule | Source |
|---|---|---|
| Nombre de lignes importées | `total_rows` | `marts.mart_quality` |
| Nombre de lignes valides | `valid_rows` | `marts.mart_quality` |
| Nombre de lignes rejetées | `rejected_rows` | `marts.mart_quality` |
| Taux de valeurs manquantes | voir `reports/quality/missing_values_latest.csv` | rapport qualité (Étape 6) |
| Nombre de doublons | `duplicate_rows` | `marts.mart_quality` |
| Nombre d'anomalies détectées | `total_violations` | `marts.mart_quality` |
| Score global de qualité des données | `valid_rate_percent` (`valid_rows / total_rows * 100`) | `marts.mart_quality` |

---

## KPIs des pipelines

| KPI | Formule | Source |
|---|---|---|
| Nombre d'exécutions des pipelines | `COUNT(id)` | table `etl_runs` (PostgreSQL, schéma `public`) |
| Temps moyen d'exécution | `AVG(finished_at - started_at)` | table `etl_runs` |
| Dernière exécution | `MAX(started_at)` | table `etl_runs` |
| Statut de la dernière exécution | `status` de la ligne la plus récente (`ORDER BY started_at DESC LIMIT 1`) | table `etl_runs` |
| Nombre d'erreurs détectées | `COUNT(*) FILTER (WHERE status = 'FAILED')` | table `etl_runs` |
| Fraîcheur des données | `now() - MAX(finished_at)` | table `etl_runs` |

---

## Limites connues

- Aucun KPI financier n'est calculé : le dataset ne contient pas de coût
  réel (voir README, Étape 13). Un coût simulé pourrait être ajouté
  uniquement à des fins pédagogiques et devrait être clairement identifié
  comme tel dans tout dashboard qui l'afficherait.
- Les KPIs démographiques (`gender`, `race`, `first_age_bracket`) issus de
  `dim_patient` reflètent la première hospitalisation connue du patient
  (voir `docs/architecture/data_warehouse_model.md`), pas une valeur
  garantie stable dans le temps.
