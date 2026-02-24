# Projet de Transport Collectif

Application web de gestion de transport collectif avec billetterie, suivi de flotte et gestion d'atelier.

##  Prérequis

### Option 1 : Avec Docker (Recommandé)
- [Docker](https://www.docker.com/get-started) (version 20.10+)
- [Docker Compose](https://docs.docker.com/compose/install/) (version 2.0+)

### Option 2 : Sans Docker (Développement local)
- Python 3.11+
- Node.js 16+ et npm
- PostgreSQL 14+

---

##  Démarrage rapide avec Docker (Recommandé)

### 1. Démarrer tous les services

```bash
# À la racine du projet
docker-compose up --build
```

Cette commande va :
- ✅ Démarrer PostgreSQL (port 5432)
- ✅ Démarrer MinIO (ports 9000, 9001)
- ✅ Construire et démarrer le backend FastAPI (port 8000)
- ✅ Construire et démarrer le frontend React (port 3000)

**Note** : Le frontend est maintenant géré par Docker ! Plus besoin de le démarrer séparément.

### 3. Accéder aux services

- **API Backend** : http://localhost:8000
- **Documentation API** : http://localhost:8000/docs (Swagger UI)
- **Frontend** : http://localhost:3000
- **MinIO Console** : http://localhost:9001 (minioadmin / minioadmin)

---

##  Démarrage sans Docker (Développement local)


### 2. Configurer le backend

```bash
cd backend

# Activer l'environnement virtuel (si existant)
# Sur Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Sur Windows CMD:
venv\Scripts\activate.bat
# Sur Linux/Mac:
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Modifier database.py pour utiliser localhost au lieu de 'database'
# DATABASE_URL = "postgresql://user:password@localhost:5432/transport_db"
```

**Note** : Modifiez `backend/database.py` ligne 6 :
```python
DATABASE_URL = "postgresql://user:password@localhost:5432/transport_db"
```

### 3. Démarrer le backend

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Démarrer le frontend

```bash
cd frontend
npm install
npm start
```


##  Commandes Docker utiles

```bash
# Démarrer en arrière-plan
docker-compose up -d

# Voir les logs
docker-compose logs -f

# Arrêter les services
docker-compose down

# Reconstruire les images
docker-compose build --no-cache

# Accéder au conteneur backend
docker-compose exec backend bash

# Accéder à PostgreSQL
docker-compose exec database psql -U user -d transport_db
```

---

##  Structure du projet

```
projet-de-transport/
├── backend/              # API FastAPI
│   ├── auth/            # Authentification JWT
│   ├── models/          # Modèles SQLAlchemy
│   ├── routes/          # Routes API
│   ├── schemas/         # Schémas Pydantic
│   └── main.py          # Point d'entrée
├── frontend/            # Application React
│   └── src/
│       ├── pages/       # Pages de l'application
│       └── components/  # Composants réutilisables
├── database/            # Données PostgreSQL (volume Docker)
├── ingestion_pipeline/  # Pipeline d'ingestion de données
└── docker-compose.yml   # Configuration Docker
```

---

## Notes importantes

1. **Base de données** : Les données PostgreSQL sont persistées dans `./database/data/`
2. **MinIO** : Utilisé pour le stockage d'objets (pipeline d'ingestion)
3. **Variables d'environnement** : Pour la production, créez un fichier `.env` avec vos configurations
4. **Ports** : Assurez-vous que les ports 3000, 5432, 8000, 9000, 9001 sont disponibles

---
