# Guide pas-à-pas — Construction du projet Power BI Desktop

## CHU Oujda — Plateforme d'analyse du risque de réhospitalisation

Ce guide décrit, étape par étape, comment construire dans **Power BI
Desktop** le modèle, les mesures et les 7 dashboards prévus aux Étapes
14, 15 et 16 du projet, à partir du Data Warehouse PostgreSQL déjà
construit (Étapes 9 et 10).

---

## Partie 0 — Prérequis avant d'ouvrir Power BI Desktop

1. PostgreSQL doit être démarré :
   ```bash
   docker compose up -d postgres
   ```
2. Le pipeline complet doit avoir été exécuté au moins une fois, pour
   que `warehouse.*` et `marts.*` contiennent des données :
   ```bash
   python -m orchestration.prefect_flows.pipeline_flow
   ```
3. (Optionnel, pour le Dashboard de risque prédictif) Le modèle ML doit
   être entraîné :
   ```bash
   python -m ml.training.train_models
   python -m ml.prediction.predict
   ```
4. Installer **Power BI Desktop** (Microsoft Store ou
   powerbi.microsoft.com), gratuit.
5. Noter les informations de connexion (fichier `.env`) :
   - Serveur : `localhost`
   - Port : `5433`
   - Base : `readmission_dw`
   - Utilisateur : `readmission_user`
   - Mot de passe : `readmission_password`

---

## Partie 1 — Connexion à PostgreSQL

1. Ouvrir **Power BI Desktop**.
2. Ruban **Accueil** → cliquer sur **Obtenir les données**.
3. Dans la fenêtre de recherche, taper `PostgreSQL` → sélectionner
   **Base de données PostgreSQL** → **Connecter**.
4. Renseigner :
   - **Serveur** : `localhost:5433`
   - **Base de données** : `readmission_dw`
   - Mode de connectivité des données : **Import**
5. Cliquer **OK**. Si un pilote PostgreSQL (Npgsql) est demandé, suivre
   le lien d'installation proposé par Power BI, puis relancer l'étape.
6. Renseigner les identifiants (onglet **Base de données**) :
   - Utilisateur : `readmission_user`
   - Mot de passe : `readmission_password`
7. Cliquer **Connecter**.

### Sélection des tables

Dans le **Navigateur**, cocher uniquement les tables suivantes (ne pas
importer les vues `marts.*`, voir justification dans
`powerbi_model.md`) :

- `warehouse.dim_patient`
- `warehouse.dim_admission_type`
- `warehouse.dim_discharge_disposition`
- `warehouse.dim_admission_source`
- `warehouse.dim_diagnosis`
- `warehouse.dim_medication`
- `warehouse.dim_date`
- `warehouse.fact_hospitalization`
- `warehouse.fact_readmission`
- `warehouse.fact_medication_usage`
- `warehouse.fact_prediction` (si le modèle a été entraîné, Étape 17)

Cliquer **Transformer les données** (pas **Charger** directement) pour
vérifier chaque table dans l'éditeur Power Query avant import.

### Vérification rapide dans Power Query

Pour chaque table, vérifier dans le volet de droite (**Étapes
appliquées**) que les types de colonnes sont corrects (Power BI les
détecte automatiquement depuis PostgreSQL). Cliquer **Fermer et
appliquer** (ruban **Accueil**) une fois la vérification faite.

---

## Partie 2 — Construction du modèle en étoile

Basculer sur la vue **Modèle** (icône à gauche, 3 rectangles reliés).

### 2.1 Créer les relations

Pour chaque ligne du tableau ci-dessous : glisser-déposer la colonne
source sur la colonne cible dans la vue Modèle, une fenêtre
**Modifier la relation** s'ouvre.

| Glisser depuis | Déposer sur | Cardinalité à choisir | Sens du filtre |
|---|---|---|---|
| `fact_hospitalization[patient_key]` | `dim_patient[patient_key]` | Plusieurs vers un (*:1) | Unique direction (vers fact) |
| `fact_hospitalization[admission_type_id]` | `dim_admission_type[admission_type_id]` | *:1 | Unique |
| `fact_hospitalization[discharge_disposition_id]` | `dim_discharge_disposition[discharge_disposition_id]` | *:1 | Unique |
| `fact_hospitalization[admission_source_id]` | `dim_admission_source[admission_source_id]` | *:1 | Unique |
| `fact_hospitalization[diag_1_key]` | `dim_diagnosis[diagnosis_key]` | *:1 | Unique (laisser **active**) |
| `fact_hospitalization[diag_2_key]` | `dim_diagnosis[diagnosis_key]` | *:1 | Unique — Power BI la crée **inactive** (ligne pointillée) automatiquement car `dim_diagnosis` a déjà une relation active |
| `fact_hospitalization[diag_3_key]` | `dim_diagnosis[diagnosis_key]` | *:1 | idem, inactive |
| `fact_readmission[encounter_key]` | `fact_hospitalization[encounter_key]` | Un vers un (1:1) | Unique |
| `fact_medication_usage[encounter_key]` | `fact_hospitalization[encounter_key]` | *:1 | Unique |
| `fact_medication_usage[medication_key]` | `dim_medication[medication_key]` | *:1 | Unique |
| `fact_prediction[encounter_key]` (si présente) | `fact_hospitalization[encounter_key]` | 1:1 | Unique |

Cocher **Valider les données pour garantir la précision** à chaque
fenêtre de relation, puis **OK**.

### 2.2 Configurer la table calendrier (`dim_date`)

1. Cliquer sur la table `dim_date` dans le volet **Données**.
2. Ruban **Outils de table** → **Marquer comme table de dates** →
   sélectionner la colonne `full_date`.
3. **Fichier → Options et paramètres → Options → Chargement des
   données** → décocher **Détection automatique de nouvelles
   relations** et **Table de calendrier automatique** (évite les
   doublons de tables de dates cachées).

**Rappel important** : `dim_date` n'est reliée par **aucune** relation
aux tables de faits (le dataset ne contient pas de date
d'hospitalisation réelle). Elle sert uniquement à pratiquer les
fonctions de Time Intelligence DAX (Étape 16) sur une table
indépendante — ne pas essayer de la relier artificiellement à
`fact_hospitalization`.

### 2.3 Créer les hiérarchies

Sur `dim_date` : clic droit sur `year_number` → **Créer une
hiérarchie** → renommer `Hiérarchie Calendrier` → glisser `quarter_number`,
puis `month_name`, puis `full_date` dans la hiérarchie (dans cet
ordre).

### 2.4 Masquer les colonnes techniques

Dans le volet **Données**, clic droit sur chaque colonne suivante →
**Masquer dans la vue de rapport** :

- Toutes les colonnes `*_key` une fois les relations créées
  (`patient_key`, `diagnosis_key`, `medication_key`) — garder
  `encounter_key` visible si besoin de compter les lignes.
- `loaded_at` sur toutes les tables `dim_*`/`fact_*`.

---

## Partie 3 — Créer les mesures DAX

Pour **chaque** mesure ci-dessous :

1. Clic droit sur `fact_hospitalization` (ou `fact_readmission` selon
   indication) dans le volet **Données** → **Nouvelle mesure**.
2. Coller la formule dans la barre de formule.
3. Appuyer sur **Entrée**.
4. Dans le ruban **Outils de mesure**, définir le **Format** (Nombre
   entier, Pourcentage à 1 décimale, etc.) et le **Dossier d'affichage**
   indiqué entre crochets.

### Dossier [Activité]

```dax
Nombre Hospitalisations =
COUNTROWS ( fact_hospitalization )

Nombre Patients Uniques =
DISTINCTCOUNT ( fact_hospitalization[patient_key] )

Duree Moyenne Sejour =
AVERAGE ( fact_hospitalization[time_in_hospital] )

Nombre Moyen Medicaments =
AVERAGE ( fact_hospitalization[num_medications] )

Nombre Moyen Diagnostics =
AVERAGE ( fact_hospitalization[number_diagnoses] )
```

### Dossier [Réhospitalisation] (créer sur `fact_readmission`)

```dax
Taux Reheospitalisation Global =
DIVIDE (
    SUM ( fact_readmission[readmitted_flag] ),
    COUNTROWS ( fact_readmission )
)

Taux Reheospitalisation 30 Jours =
DIVIDE (
    SUM ( fact_readmission[readmitted_30_days] ),
    COUNTROWS ( fact_readmission )
)

Nombre Reheospitalisations 30 Jours =
SUM ( fact_readmission[readmitted_30_days] )

Taux Utilisation Insuline =
AVERAGE ( fact_readmission[insulin_prescribed] )

Patients a Risque Frequent =
CALCULATE (
    [Nombre Patients Uniques],
    fact_readmission[is_frequent_patient] = 1
)
```

### Dossier [Clinique] (créer sur `fact_hospitalization`)

```dax
Taux Reheospitalisation Diag2 =
CALCULATE (
    [Taux Reheospitalisation 30 Jours],
    USERELATIONSHIP ( fact_hospitalization[diag_2_key], dim_diagnosis[diagnosis_key] )
)
```

### Dossier [Prédiction] (si `fact_prediction` importée)

```dax
Nombre Patients Risque Eleve =
CALCULATE (
    DISTINCTCOUNT ( fact_prediction[encounter_key] ),
    fact_prediction[predicted_risk_category] = "High"
)

Probabilite Moyenne Predite =
AVERAGE ( fact_prediction[predicted_probability] )
```

---

## Partie 4 — Construction des 7 dashboards

Pour chaque dashboard : clic droit sur l'onglet de page en bas →
**Renommer la page** avec le nom indiqué, puis ajouter les visuels
listés (ruban **Insertion → Visuel élémentaire** ou volet
**Visualisations**).

### Dashboard 1 — Executive Overview

| Visuel | Champs |
|---|---|
| Carte (KPI) x4 | `[Nombre Hospitalisations]`, `[Nombre Patients Uniques]`, `[Taux Reheospitalisation 30 Jours]`, `[Duree Moyenne Sejour]` |
| Graphique en courbes | Axe : `dim_date[Hiérarchie Calendrier]` (pédagogique, non relié) ; Valeur : `[Nombre Hospitalisations]` |
| Graphique à barres horizontales | Axe : `dim_diagnosis[diagnosis_group]` ; Valeur : `[Nombre Hospitalisations]`, trié décroissant |
| Table | `dim_patient[first_age_bracket]`, `[Taux Reheospitalisation 30 Jours]` |

### Dashboard 2 — Patient Analysis

| Visuel | Champs |
|---|---|
| Graphique à secteurs | `dim_patient[gender]`, `[Nombre Patients Uniques]` |
| Histogramme | `dim_patient[first_age_bracket]`, `[Nombre Patients Uniques]` |
| Graphique à barres | `dim_patient[race]`, `[Nombre Patients Uniques]` |
| Table avec drill-through | Liste des patients (`patient_nbr`, `gender`, `race`, `first_age_bracket`) |
| Slicers | `gender`, `race`, `first_age_bracket` |

Pour le **drill-through** : créer une page « Détail Patient », dans le
volet **Visualisations → Drill-through**, glisser `dim_patient[patient_nbr]`.

### Dashboard 3 — Hospitalization Analysis

| Visuel | Champs |
|---|---|
| Carte | `[Nombre Hospitalisations]`, `[Duree Moyenne Sejour]` |
| Barres empilées | `dim_admission_type[admission_type_description]`, `[Nombre Hospitalisations]` |
| Barres | `dim_admission_source[admission_source_description]`, `[Nombre Hospitalisations]` |
| Barres | `dim_discharge_disposition[discharge_disposition_description]`, `[Nombre Hospitalisations]` |
| Nuage de points | `time_in_hospital` (X), `patient_complexity_score` (Y) |

### Dashboard 4 — Readmission Analysis

| Visuel | Champs |
|---|---|
| Jauge ou Carte | `[Taux Reheospitalisation 30 Jours]` |
| Barres | `dim_patient[first_age_bracket]`, `[Taux Reheospitalisation 30 Jours]` |
| Barres | `dim_patient[gender]`, `[Taux Reheospitalisation 30 Jours]` |
| Barres | `dim_diagnosis[diagnosis_group]` (relation active diag_1), `[Taux Reheospitalisation 30 Jours]` |
| Barres | `dim_admission_type[admission_type_description]`, `[Taux Reheospitalisation 30 Jours]` |
| Slicer | `total_previous_visits` (regroupé par tranche via un groupe Power BI) |

Ajouter un **bouton de navigation** (ruban **Insertion → Boutons →
Navigation vierge**) vers le Dashboard 5.

### Dashboard 5 — Clinical Analysis

| Visuel | Champs |
|---|---|
| Barres horizontales | `dim_diagnosis[diagnosis_group]`, `[Nombre Hospitalisations]` |
| Barres horizontales | `dim_diagnosis[diagnosis_group]`, `[Taux Reheospitalisation 30 Jours]` |
| Barres | `dim_medication[medication_name]`, `COUNTROWS(fact_medication_usage)` |
| Carte | `[Taux Utilisation Insuline]` |
| Table | médicaments x `dosage_changed` (sommé) |

### Dashboard 6 — Data Quality

Importer en plus (Power Query) les tables `public.data_quality_runs` et
`public.data_quality_rule_results` (mode Import, même connexion
PostgreSQL, cocher ces deux tables dans le Navigateur).

| Visuel | Champs |
|---|---|
| Carte | `total_rows`, `valid_rows`, `rejected_rows` (dernière exécution, filtrée par `MAX(started_at)`) |
| Jauge | `valid_rate_percent` |
| Table | `data_quality_rule_results` : `rule_name`, `column_name`, `violation_count` |
| Courbe | historique de `valid_rate_percent` par `started_at` |

### Dashboard 7 — Pipeline Monitoring

Importer en plus la table `public.etl_runs`.

| Visuel | Champs |
|---|---|
| Carte | dernier `status`, dernier `started_at` |
| Table | historique des runs : `status`, `input_rows`, `output_rows`, `started_at`, `finished_at` |
| Indicateur visuel (KPI) | tendance du nombre de lignes traitées dans le temps |

---

## Partie 5 — Interactivité avancée (Étape 16)

### Bookmarks

1. Régler les filtres d'une page à l'état « vue par défaut ».
2. Volet **Affichage → Signets → Ajouter**.
3. Nommer `Vue globale`.
4. Ajouter un bouton (**Insertion → Boutons**) sur chaque page,
   **Action → Type : Signet**, sélectionner `Vue globale`.

### Field parameters

1. Ruban **Modélisation → Nouveaux paramètres → Paramètre de champs**.
2. Ajouter `[Taux Reheospitalisation Global]` et
   `[Taux Reheospitalisation 30 Jours]`.
3. Nommer le paramètre `Choix Indicateur Reheospitalisation`.
4. Utiliser ce paramètre comme valeur dans les visuels du Dashboard 4
   pour permettre à l'utilisateur de basculer entre les deux mesures.

### Info-bulles personnalisées

1. Créer une nouvelle page, **Format de la page → Type de page :
   Infobulle**, taille « Petite infobulle ».
2. Ajouter un visuel carte avec `[Taux Reheospitalisation 30 Jours]`.
3. Sur les visuels du Dashboard 5, **Format du visuel → Infobulles →
   Type : Rapport**, sélectionner cette page.

---

## Partie 6 — Sécurité (Row-Level Security)

1. Ruban **Modélisation → Gérer les rôles**.
2. **Créer** → nommer `Responsable Spécialité`.
3. Sélectionner `fact_hospitalization` (ou une table important
   `medical_specialty` si nécessaire) → filtre DAX :
   ```dax
   [medical_specialty] = USERPRINCIPALNAME()
   ```
4. **Enregistrer**.
5. Pour tester : **Modélisation → Afficher en tant que rôles** →
   cocher `Responsable Spécialité` → saisir un compte de test.

*(Rappel : ce dataset public ne contient pas de vrais comptes
utilisateurs — cette démonstration RLS reste pédagogique, voir
`powerbi_model.md`.)*

---

## Partie 7 — Optimisation avant publication

1. Ruban **Affichage → Performance Analyzer → Démarrer
   l'enregistrement**, interagir avec chaque page, **Arrêter**, vérifier
   qu'aucun visuel ne dépasse ~1 seconde de rendu.
2. **Fichier → Options → Statistiques du modèle** pour vérifier la
   taille de chaque table (les tables `dim_*` doivent rester petites).
3. Supprimer toute colonne calculée non utilisée par une mesure.

---

## Partie 8 — Publication et rafraîchissement

1. Ruban **Accueil → Publier** → choisir l'espace de travail Power BI.
2. Dans le **service Power BI** (app.powerbi.com), ouvrir le jeu de
   données publié → **Paramètres → Passerelle de données** → installer
   et configurer l'**On-premises data gateway (mode personnel)** si
   PostgreSQL reste local (Docker sur votre machine).
3. **Paramètres → Planifier l'actualisation** → définir une fréquence
   cohérente avec l'orchestration Prefect (Étape 11), par exemple
   quotidienne après le passage planifié du pipeline.

---

## Récapitulatif des livrables couverts par ce guide

- ✅ Connexion PostgreSQL et sélection des tables
- ✅ Modèle en étoile complet (relations, cardinalités, dimension à
  rôles multiples `dim_diagnosis`)
- ✅ Table calendrier technique
- ✅ Hiérarchies et masquage des colonnes techniques
- ✅ Dictionnaire de mesures DAX prêtes à copier-coller
- ✅ Les 7 dashboards du README, visuel par visuel
- ✅ Interactivité (bookmarks, field parameters, tooltips, drill-through)
- ✅ Sécurité RLS
- ✅ Optimisation et publication/rafraîchissement

Ce guide, combiné à `powerbi_model.md` (référence des relations et du
catalogue de mesures), couvre l'intégralité des Étapes 14, 15 et 16 du
README — la seule action qui reste manuelle est de suivre ces clics
dans Power BI Desktop, application graphique que je ne peux pas piloter
directement.
