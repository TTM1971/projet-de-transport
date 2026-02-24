FROM node:18-alpine

WORKDIR /app

# Copier les fichiers de dépendances
COPY package*.json ./

# Installer les dépendances
RUN npm install

# Copier le reste du code
COPY . .

# Exposer le port
EXPOSE 3000

# Variables d'environnement pour React
ENV CHOKIDAR_USEPOLLING=true
ENV WATCHPACK_POLLING=true

# Démarrer l'application en mode développement
# Utiliser DANGEROUSLY_DISABLE_HOST_CHECK pour accepter les connexions depuis l'extérieur du conteneur
ENV DANGEROUSLY_DISABLE_HOST_CHECK=true
CMD ["npm", "start"]
