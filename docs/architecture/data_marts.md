# Data Marts (Étape 10)

## Objectif

Fournir des vues PostgreSQL prêtes à connecter à Power BI, spécialisées
par thème métier, construites au-dessus du schéma `warehouse` (Étape 9).

Schéma PostgreSQL : `marts`. Créées par
`warehouse/ddl/006_create_marts_views.sql`, exécuté via
`python -m src.warehouse.build_marts`.

Ce sont des **vues** (pas des tables matérialisées) : elles reflètent
toujours l'état courant du Data Warehouse sans étape de rafraîchissement
supplémentaire.

---

## `marts.mart_patients`

Grain : un patient. Alimente le **Dashboard 2 — Patient Analysis**.

Colonnes clés : `gender`, `race`, `first_age_bracket`, `total_encounters`,
`is_frequent_patient_ever`, `readmitted_30_days_count`.

## `marts.mart_hospitalizations`

Grain : une hospitalisation, dénormalisée avec les libellés d'admission
et de sortie. Alimente le **Dashboard 3 — Hospitalization Analysis**.

## `marts.mart_readmission`

Grain : une hospitalisation, avec démographie, diagnostic principal
regroupé et indicateurs de réhospitalisation. Alimente le
**Dashboard 4 — Readmission Analysis**.

## `marts.mart_diagnostics`

Grain : un code diagnostic principal (`diag_1`). Agrège le nombre
d'hospitalisations, de patients distincts et le taux de réhospitalisation
à 30 jours par diagnostic. Alimente le **Dashboard 5 — Clinical Analysis**.

## `marts.mart_medications`

Grain : un médicament. Agrège le nombre de prescriptions, de changements
de dosage et le taux de réhospitalisation associé. Alimente le
**Dashboard 5 — Clinical Analysis**.

Remarque : `examide` et `citoglipton` sont absents de ce mart car ils
valent `No` pour toutes les hospitalisations du dataset (aucune
prescription observée).

## `marts.mart_quality` et `marts.mart_quality_violations`

Grain : une exécution de contrôle qualité (Étape 6), respectivement une
violation de règle par exécution. Alimentent le **Dashboard 6 — Data
Quality**.

---

## Vérification

`src/warehouse/build_marts.py` compte les lignes de chaque vue après
création. Les tests d'intégration `tests/integration/test_marts.py`
vérifient la cohérence des volumes avec `warehouse.*` (nécessitent
PostgreSQL démarré et le pipeline déjà exécuté).

## Prérequis d'exécution

```bash
python -m src.warehouse.build_warehouse
python -m src.warehouse.build_marts
```
