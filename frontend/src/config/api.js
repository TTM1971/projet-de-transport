// Configuration de l'URL de l'API
// En développement, utilise localhost
// En production, peut être configuré via variable d'environnement
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export default API_URL;
