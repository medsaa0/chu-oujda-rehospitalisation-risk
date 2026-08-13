# Dictionnaire des variables dérivées (Feature Engineering)

## Objectif

Ce document décrit les variables calculées par `src/features/build_features.py`
à partir du Parquet Curated. Ces variables alimentent les KPIs, les Data
Marts (Étape 10) et serviront de base au modèle prédictif (Étape 17).

Le module produit une table gardée par `encounter_id` : `data/features/*_features.parquet`,
puis chargée dans PostgreSQL sous `staging.hospital_encounters_features`.

---

## Variables liées à la cible

| Variable | Type | Règle de calcul | Description |
|---|---|---|---|
| `readmitted_30_days` | Int8 (0/1) | `1` si `readmitted = '<30'`, sinon `0` | Cible principale du modèle prédictif (Étape 17) |
| `readmitted_flag` | Int8 (0/1) | `1` si `readmitted != 'NO'`, sinon `0` | Réhospitalisation, quel que soit le délai |

## Variables démographiques

| Variable | Type | Règle de calcul | Description |
|---|---|---|---|
| `age_midpoint` | Int32 | Point milieu de la tranche `age` (ex. `[50-60)` → `55`) | Permet des calculs statistiques et des corrélations sur l'âge |

## Variables d'utilisation des soins

| Variable | Type | Règle de calcul | Description |
|---|---|---|---|
| `total_previous_visits` | Int64 | `number_outpatient + number_emergency + number_inpatient` | Nombre total de visites antérieures, tous types confondus |
| `healthcare_utilization_score` | Int64 | `total_previous_visits + time_in_hospital` | Score simple d'utilisation globale des soins |
| `is_frequent_patient` | Int8 (0/1) | `1` si `total_previous_visits >= 3`, sinon `0` | Seuil pédagogique documenté ici ; indicateur utilisé dans les dashboards, pas dans le modèle ML |

## Variables médicamenteuses

| Variable | Type | Règle de calcul | Description |
|---|---|---|---|
| `active_medications_count` | Int64 | Nombre de colonnes médicament (parmi les 23) différentes de `No` | Nombre de traitements actifs pendant le séjour |
| `medication_dosage_changes_count` | Int64 | Nombre de colonnes médicament valant `Up` ou `Down` | Nombre de changements de dosage |
| `insulin_prescribed` | Int8 (0/1) | `1` si `insulin != 'No'`, sinon `0` | Présence d'un traitement à l'insuline |
| `high_medication_burden_flag` | Int8 (0/1) | `1` si `num_medications >= 15`, sinon `0` | Seuil pédagogique documenté ici ; charge médicamenteuse élevée |

## Variables cliniques

| Variable | Type | Règle de calcul | Description |
|---|---|---|---|
| `diag_1_group` | String | Regroupement ICD-9 (voir ci-dessous) | Famille clinique du diagnostic principal |
| `diag_2_group` | String | Regroupement ICD-9 | Famille clinique du deuxième diagnostic |
| `diag_3_group` | String | Regroupement ICD-9 | Famille clinique du troisième diagnostic |
| `patient_complexity_score` | Int64 | `num_medications + num_procedures + number_diagnoses + time_in_hospital` | Score composite de complexité du séjour |

### Regroupement des diagnostics (ICD-9)

Classification issue de la littérature de référence sur ce dataset
(Strack et al., 2014), utilisée telle quelle pour rester comparable
aux études publiées :

| Famille | Codes ICD-9 |
|---|---|
| Diabetes | `250.xx` |
| Circulatory | `390–459`, `785` |
| Respiratory | `460–519`, `786` |
| Digestive | `520–579`, `787` |
| Injury | `800–999` |
| Musculoskeletal | `710–739` |
| Genitourinary | `580–629`, `788` |
| Neoplasms | `140–239` |
| Other | tout le reste (dont les codes `V` et `E`, et les diagnostics manquants) |

---

## Tests

Les règles ci-dessus sont couvertes par `tests/unit/test_features.py`.

## Limites connues

- Les seuils `is_frequent_patient` et `high_medication_burden_flag` sont des
  choix pédagogiques simples, pas des seuils cliniquement validés.
- Le regroupement diagnostic ne couvre pas la totalité des sous-classifications
  ICD-9 ; les codes non listés tombent dans `Other`, ce qui est le comportement
  attendu et documenté par la littérature de référence.
