# Modèle du Data Warehouse (Étape 9)

## Objectif

Documenter le modèle en étoile PostgreSQL construit par
`src/warehouse/build_warehouse.py` à partir des tables `staging`
(Curated + Features).

Schéma PostgreSQL : `warehouse`.

---

## Schéma en étoile

```text
dim_patient
dim_admission_type
dim_discharge_disposition
dim_admission_source
dim_diagnosis
dim_medication
        \
         \
fact_hospitalization ── fact_readmission
         \
          fact_medication_usage (bridge)

dim_date  (table calendrier technique, non reliée aux faits)
```

---

## Dimensions

### `dim_patient`

| Colonne | Description |
|---|---|
| `patient_key` | Clé de substitution |
| `patient_nbr` | Clé naturelle (identifiant patient du dataset) |
| `gender`, `race` | Démographie |
| `first_age_bracket`, `first_age_midpoint` | Tranche d'âge et point milieu |

**Limite documentée** : `gender`, `race` et l'âge sont capturés à la
**première hospitalisation connue** du patient (simplification Type 1).
Si un attribut change d'une hospitalisation à l'autre dans le dataset
source, seule la première valeur est conservée. C'est un choix
pédagogique assumé, pas une garantie clinique.

### `dim_admission_type`, `dim_discharge_disposition`, `dim_admission_source`

Correspondent conceptuellement au « DimAdmission » décrit dans le
README (type d'admission, source d'admission, mode de sortie), modélisées
comme trois petites dimensions de référence conformes issues de
`data/source/IDS_mapping.csv` — c'est l'approche standard en modélisation
dimensionnelle plutôt qu'une dimension composite artificielle.

### `dim_diagnosis`

Un code ICD-9 distinct par ligne (`diagnosis_code`), avec son
regroupement clinique (`diagnosis_group`) calculé par
`src/features/build_features.py::diagnosis_group_expr` (même règle
que la Feature `diag_x_group`, voir `docs/data_dictionary_features.md`).

### `dim_medication`

Liste fixe des 23 médicaments suivis dans le dataset (une ligne par
médicament).

### `dim_date`

Table calendrier technique couvrant 1999-2008 (années du dataset).

**Limite documentée** : le dataset ne contient aucune date
d'hospitalisation exacte. `dim_date` n'est donc **pas reliée par clé
étrangère** aux tables de faits ; elle sert uniquement de référence
pédagogique pour apprendre le Time Intelligence Power BI (Étape 16).

---

## Tables de faits

### `fact_hospitalization`

Grain : une ligne par hospitalisation (`encounter_key` = `encounter_id`).

Contient les clés étrangères vers `dim_patient`, `dim_admission_type`,
`dim_discharge_disposition`, `dim_admission_source` et jusqu'à trois
`dim_diagnosis` (`diag_1_key`, `diag_2_key`, `diag_3_key`, nullables
puisque `diag_2`/`diag_3` peuvent être absents), ainsi que les mesures
numériques du séjour (durée, procédures, médicaments, diagnostics,
visites antérieures, scores de complexité et d'utilisation issus de
l'Étape 8).

### `fact_readmission`

Grain : une ligne par hospitalisation, alignée 1:1 sur
`fact_hospitalization` via `encounter_key`. Contient le statut de
réhospitalisation et les indicateurs binaires calculés à l'Étape 8.

Séparée de `fact_hospitalization` pour isoler la variable cible et ses
dérivés, conformément au README (deux tables de faits distinctes).

### `fact_medication_usage`

Table de faits en pont (bridge) au grain **hospitalisation ×
médicament**. Ne contient que les médicaments effectivement prescrits
(`status != 'No'`), ce qui limite son volume (~120 000 lignes pour
101 763 hospitalisations) tout en permettant l'analyse détaillée par
médicament nécessaire au Mart Médicaments (Étape 10).

---

## Chargement

`src/warehouse/build_warehouse.py` :

1. crée le schéma et les tables (`warehouse/ddl/004_*.sql`, `005_*.sql`) ;
2. vide puis recharge chaque dimension et chaque fait (`TRUNCATE ... CASCADE`
   puis `INSERT ... SELECT`), ce qui rend le pipeline idempotent : chaque
   exécution reflète l'état courant de `staging` ;
3. journalise le nombre de lignes chargées par table.

Commande :

```bash
python -m src.warehouse.build_warehouse
```

Prérequis : les Étapes 7 (ETL) et 8 (Feature Engineering) doivent avoir
été exécutées, car ce script lit `staging.hospital_encounters_curated`
et `staging.hospital_encounters_features`.
