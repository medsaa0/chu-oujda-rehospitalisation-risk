# Dictionnaire des données

## Description générale

Le dataset « Diabetes 130-US Hospitals for Years 1999–2008 »
contient des hospitalisations de patients diabétiques.

Chaque ligne représente une hospitalisation unique.

- `encounter_id` identifie le séjour ;
- `patient_nbr` identifie le patient ;
- `readmitted` indique le statut de réhospitalisation.

---

## Structure des colonnes

| Colonne | Type source | Type métier | Description | Valeurs principales | Traitement prévu |
|---|---|---|---|---|---|
| encounter_id | Entier | Identifiant | Identifiant unique du séjour | Valeur unique | Conserver |
| patient_nbr | Entier | Identifiant patient | Identifiant anonyme du patient | Peut apparaître plusieurs fois | Conserver |
| race | Texte | Catégorie | Groupe racial déclaré | Caucasian, AfricanAmerican, Asian, Hispanic, Other | Gérer les valeurs manquantes |
| gender | Texte | Catégorie | Sexe du patient | Male, Female, Unknown/Invalid | Contrôler les valeurs rares |
| age | Texte | Catégorie ordonnée | Tranche d’âge | [0-10), [10-20), etc. | Créer une tranche ordonnée |
| weight | Texte | Catégorie ordonnée | Tranche de poids | [0-25), [25-50), etc. | Étudier le taux de valeurs manquantes |
| admission_type_id | Entier | Catégorie codée | Type d’admission | Codes numériques | Joindre avec IDS_mapping |
| discharge_disposition_id | Entier | Catégorie codée | Type de sortie | Codes numériques | Joindre avec IDS_mapping |
| admission_source_id | Entier | Catégorie codée | Source de l’admission | Codes numériques | Joindre avec IDS_mapping |
| time_in_hospital | Entier | Mesure | Durée du séjour en jours | Valeurs positives | Contrôler les limites |
| num_lab_procedures | Entier | Mesure | Nombre de procédures de laboratoire | Valeurs positives ou nulles | Conserver |
| num_procedures | Entier | Mesure | Nombre de procédures médicales | Valeurs positives ou nulles | Conserver |
| num_medications | Entier | Mesure | Nombre de médicaments prescrits | Valeurs positives | Conserver |
| number_outpatient | Entier | Mesure | Nombre de consultations externes précédentes | Valeurs positives ou nulles | Conserver |
| number_emergency | Entier | Mesure | Nombre de passages aux urgences précédents | Valeurs positives ou nulles | Conserver |
| number_inpatient | Entier | Mesure | Nombre d’hospitalisations précédentes | Valeurs positives ou nulles | Conserver |
| diag_1 | Texte | Diagnostic | Diagnostic principal | Codes ICD | Regrouper par famille |
| diag_2 | Texte | Diagnostic | Deuxième diagnostic | Codes ICD | Regrouper par famille |
| diag_3 | Texte | Diagnostic | Troisième diagnostic | Codes ICD | Regrouper par famille |
| number_diagnoses | Entier | Mesure | Nombre de diagnostics enregistrés | Valeurs positives | Conserver |
| max_glu_serum | Texte | Catégorie | Résultat du test de glucose | None, Norm, >200, >300 | Normaliser |
| A1Cresult | Texte | Catégorie | Résultat du test HbA1c | None, Norm, >7, >8 | Normaliser |
| insulin | Texte | Catégorie | Évolution du dosage d’insuline | No, Steady, Up, Down | Conserver |
| change | Texte | Booléen métier | Indique un changement de traitement | Ch, No | Convertir en booléen |
| diabetesMed | Texte | Booléen métier | Présence d’un traitement contre le diabète | Yes, No | Convertir en booléen |
| readmitted | Texte | Cible | Statut de réhospitalisation | <30, >30, NO | Créer la cible binaire |