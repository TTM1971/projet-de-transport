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
├── nginx/                    # Nginx (reverse proxy dev + conf prod statique)
├── database/data/            # Données PostgreSQL persistées
├── ingestion_pipeline/data/  # Données MinIO persistées
├── docker-compose.yml        # Développement (React en mode dev sur :3000)
├── docker-compose.prod.yml   # Production locale : build statique servi par Nginx
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

- **Application (recommandé, via Nginx)** : [http://localhost](http://localhost) — l’API est appelée en `/api/...` depuis le navigateur.
- Frontend direct (dev) : [http://localhost:3000](http://localhost:3000) — avec `setupProxy`, les appels `/api` sont aussi relayés vers le backend.
- API directe : [http://localhost:8000](http://localhost:8000)
- Swagger : [http://localhost:8000/docs](http://localhost:8000/docs)
- MinIO Console : [http://localhost:9001](http://localhost:9001) (minioadmin / minioadmin)

### Nginx

Le service `nginx` écoute sur le **port 80** et :

- sert l’interface React en proxy vers `frontend:3000` ;
- expose l’API sous **`/api/`** (le préfixe est retiré avant d’atteindre FastAPI : `/api/auth/login` → `/auth/login`).

Fichiers : `nginx/nginx.conf`, `nginx/conf.d/transport.conf`. Exemple TLS : `nginx/ssl.conf.example`.

En local **sans Docker**, si vous lancez `npm start` dans `frontend/`, définissez dans `.env.development.local` par exemple `PROXY_BACKEND=http://127.0.0.1:8000` pour que `/api` pointe vers votre backend local.

### Production locale (fichiers statiques + Nginx)

Pour servir le **build** React depuis Nginx (sans serveur de dev sur le port 3000) et un backend **sans** `--reload` :

```bash
docker compose -f docker-compose.prod.yml up --build -d
```

- Application : [http://localhost](http://localhost) (même schéma `/api/...`).
- Le service `frontend-build` copie une fois le résultat de `npm run build` dans un volume partagé avec Nginx ; la config utilisée est `nginx/conf.d/transport.static.conf`.
- Le backend est lancé avec **Gunicorn** et **2** workers **Uvicorn** (`uvicorn.workers.UvicornWorker`) ; modifiez l’argument `-w` dans `docker-compose.prod.yml` si besoin.
- Arrêt : `docker compose -f docker-compose.prod.yml down` (le volume nommé `frontend_dist` peut être supprimé avec `down -v` pour forcer un rebuild front au prochain démarrage).

Sur un **serveur de production**, adaptez `CORS_ORIGINS`, TLS (`nginx/ssl.conf.example`), et évitez d’exposer les ports internes (8000, 5432) publiquement si ce n’est pas nécessaire.

## Jeu de donnees de test Canada

Pour reinitialiser les donnees metier avec le jeu de test:

```bash
cd backend
python scripts/seed_canada_test_data.py
```

Ce seed:
- supprime les donnees d'exploitation existantes (departs, lignes, destinations, etc.)
- regenere des donnees de test coherentes pour le Canada
- cree ou reinitialise les **comptes de demo** (memes identifiants que sur la page de connexion : `admin` / `admin123`, etc.)

Avec Docker, depuis la racine du depot : `docker compose exec backend python scripts/seed_canada_test_data.py`

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
# Stack développement (défaut)
docker compose up --build -d

# Stack production locale (statique + Nginx)
docker compose -f docker-compose.prod.yml up --build -d

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

### Smoke checks (après déploiement)

L’API expose :

- `GET /health` — liveness (processus OK, sans test base) ;
- `GET /health/ready` — readiness (requête `SELECT 1` sur PostgreSQL).

Derrière Nginx : `/api/health` et `/api/health/ready` (réécriture vers le backend).

Script Python (sans dépendance supplémentaire), à lancer une fois la stack joignable :

```bash
python scripts/smoke_checks.py
```

Variables utiles : `SMOKE_BASE_URL` (ex. `http://localhost`), `SMOKE_API_PREFIX` (défaut `/api` ; vide pour tester l’API directement sur le port 8000), `SMOKE_SKIP_FRONTEND=1` si vous ne servez pas d’UI sur la base URL. Code de sortie `0` si tout passe, `1` sinon (adapté CI / pipeline).

Sous PowerShell, API directe sans préfixe :

```powershell
$env:SMOKE_BASE_URL = "http://127.0.0.1:8000"
$env:SMOKE_API_PREFIX = ""
python scripts/smoke_checks.py
```

**GitHub Actions** : le workflow `.github/workflows/smoke.yml` lance `docker compose -f docker-compose.prod.yml up --build`, attend les endpoints `/api/health` et `/api/health/ready`, puis exécute `python3 scripts/smoke_checks.py`. Déclenché sur les **pull requests**, sur les **push** vers `main` ou `master`, et **manuellement** (onglet Actions → « Smoke tests » → Run workflow).

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

- **Backend unhealthy** / logs : `password authentication failed for user "user"` : les données dans `database/data/` viennent d’une init PostgreSQL avec un **autre** mot de passe que `DB_PASSWORD` dans le compose. **Option A** — réinitialiser le rôle (depuis la machine hôte, base déjà démarrée) :
  ```bash
  docker compose exec database psql -U user -d transport_db -c "ALTER USER \"user\" WITH PASSWORD 'password';"
  ```
  Remplacez `password` par la valeur de `DB_PASSWORD` dans votre `docker-compose.yml` si vous l’avez changée. Puis `docker compose restart backend`. **Option B** — repartir sur une base vide : `docker compose down`, vider ou supprimer `database/data/`, puis `docker compose up -d` (**perte de toutes les données locales**).
- 504 / `ERR_EMPTY_RESPONSE` sur `/api/...` : verifier que le backend est **healthy** (`docker compose ps`), consulter `docker compose logs -f backend`. Le `docker-compose.yml` lance l’API **sans** `--reload` par défaut (le reload sur volume évite les redémarrages intempestifs) ; tester l’API : `http://localhost:8000/health` ou `http://localhost/api/health` via Nginx.
- Si l'UI ne charge pas: verifier `docker compose ps` puis `docker compose logs -f`.
- Si l'API renvoie des erreurs CORS/Origin: verifier les variables de `backend/.env.example`.
- Si les donnees semblent incoherentes: relancer le seed Canada puis rafraichir l'application.

## Mise en production et PostgreSQL

En developpement, la base est deja **PostgreSQL** (conteneur `database` dans `docker-compose.yml`).  
En production, vous creez une **base PostgreSQL dediee** (managed : RDS, Azure Database, Neon, Supabase, etc. ou serveur VPS avec PostgreSQL).

### Etapes generales

1. Creer une base PostgreSQL + un utilisateur avec droits sur cette base.
2. Definir les variables cote backend :
   - soit `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `DB_PORT` ;
   - soit une seule `DATABASE_URL` au format `postgresql://user:pass@hote:5432/nom_base` ;
   - pour la plupart des offres cloud, ajouter `PGSSLMODE=require` (voir `backend/.env.example`).
3. Deployer l’API : au premier demarrage, `main.py` execute `Base.metadata.create_all()` puis `ensure_schema_compat()` pour aligner le schema.
4. Migrer les donnees si besoin depuis votre environnement actuel (voir ci-dessous).
5. En production : activer `SECURITY_STRICT_ORIGIN=true`, renseigner `CORS_ORIGINS` avec l’URL du frontend, et `TRUSTED_HOSTS` avec le nom d’hote de l’API.

### Exporter puis importer les donnees (pg_dump / pg_restore)

Sur la machine qui a acces a l’ancienne base (ex. Docker local) :

```bash
docker compose exec -T database pg_dump -U user -d transport_db -Fc -f /tmp/transport.dump
docker compose cp database:/tmp/transport.dump ./transport.dump
```

Sur la machine qui peut joindre la base de production (remplacer les parametres) :

```bash
pg_restore -h VOTRE_HOTE -U VOTRE_USER -d VOTRE_DB --no-owner --clean --if-exists transport.dump
```

Si vous preferez un SQL brut :

```bash
docker compose exec -T database pg_dump -U user -d transport_db --no-owner > transport.sql
psql -h VOTRE_HOTE -U VOTRE_USER -d VOTRE_DB -f transport.sql
```

En cas de base de production **vide** et sans besoin de conserver l’historique, vous pouvez aussi ne pas restaurer de dump et recharger uniquement le seed :  
`python backend/scripts/seed_canada_test_data.py` (a lancer depuis un environnement configure pour pointer vers la prod, avec precautions).
