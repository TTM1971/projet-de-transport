FROM python:3.11-slim

WORKDIR /app

# Mettre à jour pip et installer uniquement les dépendances essentielles d'abord
# Cela permet de mieux utiliser le cache Docker
COPY requirements.txt requirements.txt

# Installer les dépendances depuis requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Installer les dépendances optionnelles (ML/Analytics) seulement si nécessaire
# Commentées pour accélérer le build - décommentez si vous en avez besoin
# RUN pip install --no-cache-dir pandas numpy boto3 minio

# Copier le code de l'application
COPY . .

# Exposer le port
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=50s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=5).read()"

# Défaut production (workers Uvicorn) — le compose dev remplace par uvicorn --reload
CMD ["gunicorn", "main:app", "-k", "uvicorn.workers.UvicornWorker", "-w", "2", "-b", "0.0.0.0:8000", "--timeout", "120", "--graceful-timeout", "30"]
