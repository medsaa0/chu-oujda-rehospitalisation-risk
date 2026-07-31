from src.utils.paths import REQUIRED_DIRECTORIES


def test_required_directories_exist() -> None:
    missing_directories = [
        str(directory)
        for directory in REQUIRED_DIRECTORIES
        if not directory.exists()
    ]

    assert not missing_directories, (
        f"Dossiers manquants : {missing_directories}"
    )
