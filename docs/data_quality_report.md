# Rapport initial de qualité des données

## 1. Objectif

Ce rapport présente les principaux résultats de l’analyse
de qualité du dataset avant le développement du pipeline ETL.

---

## 2. Informations générales

- Nombre de lignes :
- Nombre de colonnes :
- Nombre d’hospitalisations uniques :
- Nombre de patients uniques :
- Nombre de lignes dupliquées :
- Variable cible : `readmitted`

---

## 3. Interprétation d’une ligne

Chaque ligne représente une hospitalisation unique.

Un même patient peut apparaître plusieurs fois lorsqu’il possède
plusieurs hospitalisations.

La colonne `encounter_id` identifie le séjour.

La colonne `patient_nbr` identifie le patient.

---

## 4. Valeurs manquantes

Les valeurs manquantes peuvent être représentées par :

- une valeur nulle ;
- le caractère `?` ;
- une catégorie `Unknown/Invalid` ;
- une valeur `None` selon la variable.

### Colonnes les plus concernées

| Colonne | Nombre de valeurs manquantes | Pourcentage | Niveau |
|---|---:|---:|---|
| weight | À compléter | À compléter | Critique |
| medical_specialty | À compléter | À compléter | Élevé |
| payer_code | À compléter | À compléter | Élevé |
| race | À compléter | À compléter | À déterminer |

---

## 5. Doublons

- Doublons exacts :
- `encounter_id` dupliqués :
- Patients ayant plusieurs hospitalisations :

Les répétitions de `patient_nbr` ne sont pas considérées comme
des doublons, car un patient peut avoir plusieurs séjours.

---

## 6. Qualité des identifiants

### `encounter_id`

- obligatoire ;
- non nul ;
- unique ;
- représente un séjour.

### `patient_nbr`

- obligatoire ;
- peut apparaître plusieurs fois ;
- représente un patient anonymisé.

---

## 7. Qualité des variables numériques

Les variables numériques analysées sont notamment :

- `time_in_hospital` ;
- `num_lab_procedures` ;
- `num_procedures` ;
- `num_medications` ;
- `number_outpatient` ;
- `number_emergency` ;
- `number_inpatient` ;
- `number_diagnoses`.

Contrôles effectués :

- valeurs négatives ;
- valeurs nulles ;
- valeurs extrêmes ;
- distributions inhabituelles.

---

## 8. Qualité des variables catégorielles

Les principales variables catégorielles sont :

- `race` ;
- `gender` ;
- `age` ;
- `medical_specialty` ;
- `max_glu_serum` ;
- `A1Cresult` ;
- `change` ;
- `diabetesMed` ;
- `readmitted`.

Contrôles effectués :

- valeurs inconnues ;
- valeurs rares ;
- cohérence des catégories ;
- catégories non attendues.

---

## 9. Variable cible

La variable `readmitted` contient :

- `<30` ;
- `>30` ;
- `NO`.

Pour le futur modèle :

- 1 : réhospitalisation en moins de 30 jours ;
- 0 : autre situation.

Le déséquilibre entre les classes devra être pris en compte
lors de la phase Machine Learning.

---

## 10. Colonnes nécessitant une attention particulière

### `weight`

Risque de forte proportion de valeurs manquantes.

### `payer_code`

Peut être fortement incomplet et peu pertinent pour certaines analyses.

### `medical_specialty`

Peut contenir de nombreuses valeurs manquantes ou rares.

### `diag_1`, `diag_2`, `diag_3`

Nécessitent un regroupement en familles de diagnostics.

### Colonnes de médicaments

Certaines colonnes peuvent être constantes ou presque toujours égales à `No`.

---

## 11. Recommandations pour le futur ETL

- conserver les fichiers sources sans modification ;
- convertir `?` en valeur nulle dans la couche Clean ;
- conserver une trace des valeurs originales ;
- enrichir les codes d’admission avec `IDS_mapping.csv` ;
- vérifier l’unicité de `encounter_id` ;
- traiter les colonnes fortement incomplètes individuellement ;
- regrouper les diagnostics par grandes familles ;
- créer une cible binaire `readmitted_30_days` ;
- convertir les variables métier booléennes ;
- créer un rapport automatique de qualité ;
- envoyer les lignes invalides vers une zone de quarantaine.

---

## 12. Conclusion

Le dataset est suffisamment riche pour construire une plateforme
Data Engineering, BI et Machine Learning.

Cependant, plusieurs transformations seront nécessaires avant son
utilisation dans le Data Warehouse et Power BI.