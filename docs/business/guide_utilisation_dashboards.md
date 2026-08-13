# Guide d'utilisation et d'interprétation des dashboards

## Objectif

Compléter `docs/business/utilisateurs.md` (qui dashboard pour qui) en
expliquant **comment lire** chaque indicateur, pour que les dashboards
Power BI restent actionnables et ne soient pas mal interprétés.

---

## Executive Overview

**À regarder en premier** : `Taux Réhospitalisation 30 Jours`. Sur ce
dataset, la valeur de référence observée est d'environ **11 %**. Une
valeur qui s'en écarte nettement (à la hausse) sur un sous-groupe filtré
mérite d'être creusée dans Readmission Analysis avant toute conclusion.

**Piège à éviter** : comparer `Nombre Hospitalisations` entre deux
périodes n'a de sens que si le volume de données importées est le
même — vérifier `Data Quality` avant de tirer une conclusion sur une
évolution.

## Patient Analysis

Sert à décrire **qui** est hospitalisé, pas à conclure sur le risque
(pour le risque, voir Readmission Analysis). La répartition par
`first_age_bracket`, `gender`, `race` reflète la première hospitalisation
connue de chaque patient (voir limite documentée dans
`docs/architecture/data_warehouse_model.md`) — un patient réapparu
plusieurs fois n'est compté qu'une fois dans ce dashboard.

## Hospitalization Analysis

`Durée Moyenne Séjour` est sensible aux valeurs extrêmes ; toujours
croiser avec la distribution complète (pas seulement la moyenne) avant
de conclure à un allongement ou raccourcissement des séjours.

## Readmission Analysis

Dashboard central du projet. Lecture recommandée :

1. Regarder le taux global.
2. Filtrer par facteur (âge, diagnostic, type d'admission, visites
   antérieures) pour identifier les sous-groupes à risque plus élevé.
3. **Ne pas confondre corrélation et causalité** : un taux plus élevé
   chez les patients à visites antérieures nombreuses ne prouve pas que
   ces visites *causent* la réhospitalisation — c'est un facteur
   associé, à interpréter avec un médecin/responsable clinique.

Si le modèle prédictif (Étape 17, `fact_prediction`) est disponible :
les catégories `Low`/`Medium`/`High` sont **relatives à la population
scorée** (seuils par quantile, voir
`docs/technical_documentation/ml_model.md`), pas des seuils cliniques
absolus. `High` signifie « parmi les 5 % les plus à risque de ce
dataset », pas « probabilité de réhospitalisation supérieure à X % ».

## Clinical Analysis

Le regroupement des diagnostics (`diagnosis_group`) est une
classification large (9 familles) à but analytique, pas un usage
clinique individuel — voir `docs/data_dictionary_features.md` pour la
table de correspondance ICD-9 complète.

## Data Quality

`Score global de qualité` (`valid_rate_percent`) proche de 100 % est
attendu (le dataset source est déjà propre). Une baisse significative
lors d'une prochaine ingestion signale un **changement de format
source**, pas une dégradation progressive normale — à investiguer
immédiatement via `marts.mart_quality_violations`.

## Pipeline Monitoring

`status = FAILED` sur le run le plus récent signifie que les autres
dashboards affichent des **données potentiellement obsolètes** (le
dernier chargement réussi). Toujours vérifier ce dashboard avant de
présenter les autres en réunion.

---

## Règles de gestion transverses

Voir `docs/business/regles_metier.md` pour les règles de calcul
détaillées (déjà rédigées à l'Étape 1) — ce guide n'en est pas une
redite, il porte sur la **lecture** des résultats, pas leur calcul.
