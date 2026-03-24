"""
Ancien script « année complète » (données Cameroun) — supprimé.

Pour un jeu de démonstration cohérent avec le Canada :
  cd backend
  python scripts/seed_canada_test_data.py

Ou : python run_seed.py
"""
import sys


def main():
    print(
        "Le script generate_full_year_data.py (ancienne génération Cameroun) "
        "n'est plus disponible.\n\n"
        "Utilisez le jeu de données Canada :\n"
        "  cd backend\n"
        "  python scripts/seed_canada_test_data.py\n"
        "ou :\n"
        "  python run_seed.py\n"
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
