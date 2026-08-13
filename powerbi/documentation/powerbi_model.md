# Guide du modèle Power BI (Étapes 14-16)

## Portée de ce document

Ce guide prépare tout ce qu'il faut pour construire le modèle Power BI :
sources à connecter, relations, mesures DAX, sécurité, optimisation.
La construction elle-même se fait dans **Power BI Desktop**, une
application graphique Windows, à faire manuellement en suivant les
étapes ci-dessous.

---

## 1. Connexion à PostgreSQL

`Accueil > Obtenir les données > Base de données PostgreSQL`

- Serveur : `localhost:5433` (voir `.env` / `docker-compose.yml`)
- Base : `readmission_dw`
- Mode : **Import** (le volume — environ 100 000 hospitalisations — reste
  largement gérable en import ; DirectQuery n'est pas nécessaire).

## 2. Tables à importer

Importer directement les tables du **Data Warehouse** (`warehouse.*`),
pas les vues `marts.*` : les marts sont dénormalisées (utiles pour du
SQL direct ou un export rapide) alors que le modèle en étoile
`warehouse.dim_*` / `warehouse.fact_*` permet à Power BI de gérer
lui-même les relations et l'agrégation, ce qui est plus performant et
plus flexible pour le DAX.

| Table | Rôle |
|---|---|
| `warehouse.dim_patient` | Dimension |
| `warehouse.dim_admission_type` | Dimension |
| `warehouse.dim_discharge_disposition` | Dimension |
| `warehouse.dim_admission_source` | Dimension |
| `warehouse.dim_diagnosis` | Dimension |
| `warehouse.dim_medication` | Dimension |
| `warehouse.dim_date` | Table calendrier (voir §4) |
| `warehouse.fact_hospitalization` | Fait |
| `warehouse.fact_readmission` | Fait |
| `warehouse.fact_medication_usage` | Fait (bridge) |

## 3. Relations et cardinalités

| De | Vers | Cardinalité | Sens du filtre |
|---|---|---|---|
| `fact_hospitalization.patient_key` | `dim_patient.patient_key` | N:1 | Unique |
| `fact_hospitalization.admission_type_id` | `dim_admission_type.admission_type_id` | N:1 | Unique |
| `fact_hospitalization.discharge_disposition_id` | `dim_discharge_disposition.discharge_disposition_id` | N:1 | Unique |
| `fact_hospitalization.admission_source_id` | `dim_admission_source.admission_source_id` | N:1 | Unique |
| `fact_hospitalization.diag_1_key` | `dim_diagnosis.diagnosis_key` | N:1 | Unique (relation active) |
| `fact_hospitalization.diag_2_key` | `dim_diagnosis.diagnosis_key` | N:1 | **Inactive** (même dimension, activer avec `USERELATIONSHIP`) |
| `fact_hospitalization.diag_3_key` | `dim_diagnosis.diagnosis_key` | N:1 | **Inactive** (idem) |
| `fact_readmission.encounter_key` | `fact_hospitalization.encounter_key` | 1:1 | Unique |
| `fact_medication_usage.encounter_key` | `fact_hospitalization.encounter_key` | N:1 | Unique |
| `fact_medication_usage.medication_key` | `dim_medication.medication_key` | N:1 | Unique |

`dim_diagnosis` étant reliée trois fois à `fact_hospitalization`
(diag_1/2/3), c'est une **dimension à rôles multiples** (voir README,
Étape 16) : seule la relation `diag_1_key` reste active par défaut ;
les mesures qui ont besoin de `diag_2`/`diag_3` utilisent
`USERELATIONSHIP` explicitement.

## 4. Table calendrier

`warehouse.dim_date` est une table calendrier **technique**, non reliée
par clé étrangère aux faits (le dataset ne contient aucune date
d'hospitalisation réelle — voir
`docs/architecture/data_warehouse_model.md`). Dans Power BI :

1. Importer `dim_date` comme table déconnectée.
2. `Modélisation > Marquer comme table de dates` sur `full_date`.
3. Désactiver la détection automatique des dates
   (`Fichier > Options > Chargement des données > Relations`), pour
   éviter que Power BI crée ses propres tables de dates cachées.
4. Utiliser cette table pour **apprendre** les fonctions de Time
   Intelligence DAX (Étape 16), pas pour analyser les hospitalisations
   par date réelle — cette limite doit être rappelée dans le rapport
   final.

## 5. Hiérarchies recommandées

- `dim_date` : `year_number > quarter_number > month_name > full_date`
- `dim_patient` : regrouper `first_age_bracket` dans une hiérarchie
  d'âge si besoin d'un drill-down démographique.

## 6. Colonnes techniques à masquer

Masquer dans toutes les tables : les clés de substitution utilisées
uniquement pour les relations (`patient_key`, `diagnosis_key`,
`medication_key`, `encounter_key` une fois les relations créées) et
les colonnes `loaded_at`.

---

## 7. Dictionnaire de mesures DAX

Les formules ci-dessous reprennent le catalogue de
`docs/business/kpis.md`. À créer sous
`fact_readmission`/`fact_hospitalization`, organisées en dossiers de
mesures (`Activité`, `Réhospitalisation`, `Qualité`).

```dax
Nombre Hospitalisations =
COUNTROWS ( fact_hospitalization )

Nombre Patients Uniques =
DISTINCTCOUNT ( fact_hospitalization[patient_key] )

Taux Réhospitalisation Global =
DIVIDE (
    SUM ( fact_readmission[readmitted_flag] ),
    COUNTROWS ( fact_readmission )
)

Taux Réhospitalisation 30 Jours =
DIVIDE (
    SUM ( fact_readmission[readmitted_30_days] ),
    COUNTROWS ( fact_readmission )
)

Durée Moyenne Séjour =
AVERAGE ( fact_hospitalization[time_in_hospital] )

Nombre Moyen Médicaments =
AVERAGE ( fact_hospitalization[num_medications] )

Nombre Moyen Diagnostics =
AVERAGE ( fact_hospitalization[number_diagnoses] )

Taux Utilisation Insuline =
AVERAGE ( fact_readmission[insulin_prescribed] )

Taux Réhospitalisation Diag2 =
CALCULATE (
    [Taux Réhospitalisation 30 Jours],
    USERELATIONSHIP ( fact_hospitalization[diag_2_key], dim_diagnosis[diagnosis_key] )
)

Patients à Risque =
CALCULATE (
    [Nombre Patients Uniques],
    fact_readmission[is_frequent_patient] = 1
)
```

## 8. Interactivité (Étape 16)

- **Drill-through** : depuis `mart_readmission`/`fact_readmission` vers
  une page « Détail hospitalisation » filtrée sur `encounter_key`.
- **Bookmarks** : un bookmark par dashboard pour réinitialiser les
  filtres (« Vue globale »).
- **Field parameters** : un paramètre de champ pour basculer entre
  `readmitted_flag` et `readmitted_30_days` dans les mêmes visuels.
- **Tooltips personnalisés** : une page-infobulle miniature affichant
  `Taux Réhospitalisation 30 Jours` par `diagnosis_group`.

## 9. Sécurité (Row-Level Security)

Exemple de rôle `Responsable Spécialité`, filtrant
`fact_hospitalization` (via `medical_specialty`, colonne disponible en
important aussi `staging.hospital_encounters_curated` si un filtre par
spécialité est nécessaire — sinon utiliser `dim_admission_type` comme
filtre illustratif) :

```dax
[medical_specialty] = USERPRINCIPALNAME()
```

À adapter selon un vrai référentiel utilisateurs↔service en production ;
ce dataset public ne contient pas d'identifiants utilisateurs réels,
donc la démonstration RLS reste pédagogique.

## 10. Optimisation (Performance Analyzer)

- Préférer les mesures DAX aux colonnes calculées (déjà fait : tout le
  calcul est en amont dans `src/features` et `warehouse.fact_*`).
- Masquer les clés techniques (§6) pour réduire la taille du modèle.
- Vérifier la taille du modèle via `Outil de gestion des mesures externes`
  ou `Fichier > Options > Statistiques du modèle`.
- Utiliser l'onglet **Performance Analyzer** pour chaque visuel avant
  publication.

## 11. Rafraîchissement et passerelle

PostgreSQL tournant en local (Docker), utiliser la **passerelle de
données locale (mode personnel)** pour tout rafraîchissement planifié
après publication sur le service Power BI. Étapes :

1. Installer *On-premises data gateway (personal mode)*.
2. Déclarer la source `localhost:5433` / `readmission_dw`.
3. Planifier le rafraîchissement après chaque exécution du pipeline
   Prefect (Étape 11) — dans l'idéal, ajouter un déclenchement du
   rafraîchissement Power BI comme dernière tâche du flow.

---

## Livrables couverts par ce document

- ✅ Modèle recommandé (dimensions/faits à importer, relations, cardinalités)
- ✅ Table calendrier (prête : `warehouse.dim_date`)
- ✅ Dictionnaire de mesures DAX
- ✅ Guide RLS
- ✅ Guide d'optimisation et de rafraîchissement
- ⬜ Fichier `.pbix` et dashboards eux-mêmes : à construire dans Power BI
  Desktop en suivant ce guide (étape manuelle, hors du périmètre
  automatisable de ce dépôt).
