# Génération de données (mise à jour)

L’ancien script **`generate_full_year_data.py`** (génération massives sur plusieurs années, contexte Cameroun) **n’est plus utilisé**.

## Jeu de données actuel : Canada

Pour réinitialiser les données d’exploitation et charger un jeu cohérent (lignes, destinations, bus, chauffeurs, départs sur 14 jours) :

```bash
cd backend
python scripts/seed_canada_test_data.py
```

Ou :

```bash
python run_seed.py
```

Prérequis : PostgreSQL démarré, variables d’environnement comme pour l’application (`DB_HOST`, etc.).

Si vous lancez encore `python generate_full_year_data.py`, le script affiche uniquement un rappel d’utiliser les commandes ci-dessus.
