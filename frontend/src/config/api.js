// URL de l'API : préfixe relatif /api (Nginx + setupProxy) ou URL absolue ex. http://localhost:8000
const API_URL = process.env.REACT_APP_API_URL || '/api';

export default API_URL;
