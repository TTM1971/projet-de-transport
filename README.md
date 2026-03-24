# Projet de Transport Collectif

Application web complète de gestion d'exploitation transport:
- billetterie
- planification des chauffeurs et des équipes
- suivi flotte / maintenance
- analytics et audit
- gestion multi-villes
<img width="1299" height="592" alt="image" src="https://github.com/user-attachments/assets/a99c9455-625c-4161-8fcd-b54eefce4dbe" />

## Stack technique

- Frontend: React
- Backend: FastAPI + SQLAlchemy
- Base de données: PostgreSQL
- Orchestration locale: Docker Compose
- Stockage objet technique: MinIO

## Architecture

```
projet-de-transport/
├── frontend/                 # Interface React
├── backend/                  # API FastAPI
├── database/data/            # Données PostgreSQL persistées
├── ingestion_pipeline/data/  # Données MinIO persistées
├── docker-compose.yml
├── compose.env.example
└── README.md
```

## Prérequis

### Option recommandee: Docker

- Docker Desktop (ou moteur Docker)
- Docker Compose v2+

### Option locale sans Docker

- Python 3.11+
- Node.js 16+ et npm
- PostgreSQL 14+

## Demarrage rapide avec Docker

### 1) Configurer l'environnement Compose

Depuis la racine du projet:

```powershell
copy compose.env.example .env
```

ou sous bash:

```bash
cp compose.env.example .env
```

Le fichier `.env` active `COMPOSE_BAKE=false` pour eviter des erreurs Compose sur certaines installations.

### 2) Lancer tous les services

```bash
docker compose up --build -d
```

### 3) Verifier les services

- Frontend: [http://localhost:3000](http://localhost:3000)
- API: [http://localhost:8000](http://localhost:8000)
- Swagger: [http://localhost:8000/docs](http://localhost:8000/docs)
- MinIO Console: [http://localhost:9001](http://localhost:9001) (minioadmin / minioadmin)

## Jeu de donnees de test Canada

Pour reinitialiser les donnees metier avec le jeu de test:

```bash
cd backend
python scripts/seed_canada_test_data.py
```

Ce seed:
- supprime les donnees d'exploitation existantes (departs, lignes, destinations, etc.)
- regenere des donnees de test coherentes pour le Canada
- conserve le cadre applicatif pour les tests fonctionnels

## Lancement en local sans Docker

### Backend

```bash
cd backend
python -m venv venv
```

Activation:

- PowerShell:
```powershell
.\venv\Scripts\Activate.ps1
```
- CMD:
```cmd
venv\Scripts\activate.bat
```
- Linux/macOS:
```bash
source venv/bin/activate
```

Installation + demarrage:

```bash
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm start
```

## Variables d'environnement

### Racine

- `compose.env.example`: variables lues par Docker Compose (notamment `COMPOSE_BAKE=false`)

### Backend

- `backend/.env.example`: exemples securite/CORS
- En dev, les valeurs Docker du `docker-compose.yml` suffisent pour demarrer

## Commandes utiles

```bash
# Logs
docker compose logs -f

# Logs d'un service
docker compose logs -f backend

# Arreter
docker compose down

# Rebuild propre
docker compose build --no-cache

# Shell backend
docker compose exec backend bash

# Console postgres
docker compose exec database psql -U user -d transport_db
```

## Fonctionnalites metier principales

- Filtrage par ville et mode ville admin
- Planification chauffeurs avec prevention des conflits horaires
- Regle de pause obligatoire integree dans le blocage planning
- Desassignation d'un trajet autorisee seulement au moins 2h avant depart
- Audit admin des actions gestionnaires

## Notes importantes

- Le dossier `ingestion_pipeline/data` est monte par le service MinIO de `docker-compose.yml`.
- Les anciens scripts de lancement `scripts/docker-compose-up.*` ont ete retires et remplaces par la procedure `.env` + `docker compose up`.
- Les donnees PostgreSQL locales sont dans `database/data/` et peuvent etre volumineuses.

## Depannage rapide

- Si l'UI ne charge pas: verifier `docker compose ps` puis `docker compose logs -f`.
- Si l'API renvoie des erreurs CORS/Origin: verifier les variables de `backend/.env.example`.
- Si les donnees semblent incoherentes: relancer le seed Canada puis rafraichir l'application.
