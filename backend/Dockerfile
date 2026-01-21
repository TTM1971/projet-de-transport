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

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
