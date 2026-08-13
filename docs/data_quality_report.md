# Rapport automatique de qualité des données

## Informations générales

- Fichier contrôlé : `diabetic_data_0689e7ec0312.parquet`
- Date du contrôle : `2026-08-13T10:45:08.695629+00:00`
- Nombre total de lignes : **101766**
- Lignes valides : **101763**
- Lignes rejetées : **3**
- Nombre total de violations : **3**
- Doublons exacts : **0**
- Taux de lignes valides : **99.9971%**

## Résultat du contrôle

Les lignes valides sont enregistrées dans :

`C:\Users\DELL\chu-oujda-rehospitalisation-risk\data\clean\diabetic_data_0689e7ec0312_validated.parquet`

Les lignes rejetées sont enregistrées dans :

`C:\Users\DELL\chu-oujda-rehospitalisation-risk\data\quarantine\diabetic_data_0689e7ec0312_rejected.parquet`

## Violations détectées

| rule_name | column_name | rejection_reason | violation_count |
| --- | --- | --- | --- |
| invalid_category | gender | La valeur ne fait pas partie des catégories autorisées. | 3 |

## Colonnes avec le plus de valeurs manquantes

| column_name | missing_count | missing_rate_percent |
| --- | --- | --- |
| weight | 98569 | 96.8585 |
| medical_specialty | 49949 | 49.0822 |
| payer_code | 40256 | 39.5574 |
| race | 2273 | 2.2336 |
| diag_3 | 1423 | 1.3983 |
| diag_2 | 358 | 0.3518 |
| diag_1 | 21 | 0.0206 |
| encounter_id | 0 | 0.0 |
| patient_nbr | 0 | 0.0 |
| gender | 0 | 0.0 |
| age | 0 | 0.0 |
| admission_type_id | 0 | 0.0 |
| discharge_disposition_id | 0 | 0.0 |
| admission_source_id | 0 | 0.0 |
| time_in_hospital | 0 | 0.0 |

## Interprétation

Une valeur `?`, une chaîne vide ou une valeur nulle est comptée comme
manquante. Les valeurs manquantes des colonnes facultatives sont signalées
dans le rapport, mais ne provoquent pas automatiquement le rejet d'une ligne.

Les lignes rejetées pourront être corrigées ou traitées durant le pipeline
ETL. Les données de la Raw Layer ne sont jamais modifiées.
