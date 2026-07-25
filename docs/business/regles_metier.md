# Règles métier

## Objectif

Les règles métier définissent les conditions à respecter pour garantir la cohérence et la qualité des données utilisées dans le projet.

---

## Règle 1 — Réhospitalisation

Un patient est considéré comme réhospitalisé lorsque la variable **readmitted** indique :

- `<30` : réhospitalisation en moins de 30 jours
- `>30` : réhospitalisation après 30 jours

Pour le modèle prédictif, la cible sera :

- 1 : patient réhospitalisé en moins de 30 jours
- 0 : patient non réhospitalisé en moins de 30 jours

---

## Règle 2 — Hospitalisation

Chaque enregistrement du dataset représente une hospitalisation unique.

La colonne `encounter_id` doit être unique.

---

## Règle 3 — Patient

Un même patient peut posséder plusieurs hospitalisations.

La colonne `patient_nbr` permet d'identifier un patient de manière anonyme.

---

## Règle 4 — Durée du séjour

La durée d'hospitalisation doit être supérieure à zéro.

---

## Règle 5 — Valeurs manquantes

Les valeurs manquantes devront être identifiées, analysées et traitées avant le chargement dans le Data Warehouse.

---

## Règle 6 — Qualité des données

Toutes les colonnes devront respecter leur type de données attendu.

Les doublons et les incohérences devront être détectés avant toute analyse.

---

## Règle 7 — Confidentialité

Le dataset utilisé est public et anonymisé.

Aucune donnée ne permet d'identifier directement un patient.

---

## Règle 8 — Décision médicale

Les analyses et les prédictions réalisées dans ce projet constituent une aide à la décision.

Elles ne remplacent jamais l'avis d'un professionnel de santé.

---

## Règle 9 — Périmètre des analyses

Les résultats concernent uniquement le dataset étudié.

Ils ne doivent pas être généralisés à d'autres établissements hospitaliers sans validation.