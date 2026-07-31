from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[2]
RAW_DATA_PATH = ROOT_DIR / "data" / "raw" / "hosix_rehospitalisation_dataset_riche.csv"
PROCESSED_DATA_PATH = ROOT_DIR / "data" / "processed" / "rehospitalisation_clean.csv"


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df.columns = [col.strip().lower() for col in df.columns]

    for col in ["date_entree", "date_sortie"]:
        df[col] = pd.to_datetime(df[col], errors="coerce")

    if "duree_sejour" in df.columns:
        df["duree_sejour"] = pd.to_numeric(df["duree_sejour"], errors="coerce")
    else:
        df["duree_sejour"] = (df["date_sortie"] - df["date_entree"]).dt.days

    yes_no_cols = [
        "diabete",
        "hypertension",
        "cardiopathie",
        "dialyse",
        "passage_labo",
        "passage_cardio",
        "complications",
        "infection",
        "rehospitalise_30j",
    ]

    for col in yes_no_cols:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype(str)
                .str.lower()
                .str.strip()
                .map({"oui": 1, "non": 0})
            )

    if "sexe" in df.columns:
        df["sexe"] = (
            df["sexe"]
            .astype(str)
            .str.upper()
            .str.strip()
            .map({"H": 1, "F": 0})
        )

    numeric_cols = [
        "age",
        "duree_sejour",
        "creatinine_mg_l",
        "uree_g_l",
        "potassium_mmol_l",
        "sodium_mmol_l",
        "hemoglobine_g_dl",
        "crp_mg_l",
        "albumine_g_l",
        "dfg_ml_min",
        "nb_hospitalisations_precedentes",
        "duree_hospitalisation_precedente_moy",
        "delai_depuis_derniere_hosp_jours",
        "nombre_analyses_labo",
        "score_risque_clinique",
        "delai_rehospitalisation_jours",
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df["duree_hospitalisation_precedente_moy"] = df[
        "duree_hospitalisation_precedente_moy"
    ].fillna(0)

    df["delai_depuis_derniere_hosp_jours"] = df[
        "delai_depuis_derniere_hosp_jours"
    ].fillna(999)

    df["delai_rehospitalisation_jours"] = df[
        "delai_rehospitalisation_jours"
    ].fillna(0)

    df = df.dropna(subset=["age", "date_entree", "date_sortie", "rehospitalise_30j"])

    return df


def main() -> None:
    df = pd.read_csv(RAW_DATA_PATH)
    clean_df = clean_data(df)

    PROCESSED_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    clean_df.to_csv(PROCESSED_DATA_PATH, index=False, encoding="utf-8-sig")

    print("Données nettoyées sauvegardées avec succès")
    print(PROCESSED_DATA_PATH)
    print(clean_df.shape)


if __name__ == "__main__":
    main()