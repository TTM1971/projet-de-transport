"""
Script pour exécuter la génération de données de test
"""
import sys
import os

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from seed_data import seed_data

if __name__ == "__main__":
    print("Démarrage de la génération de données de test...")
    seed_data()
    print("\n✅ Génération terminée !")
