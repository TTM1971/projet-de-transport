/**
 * Base URL des appels Axios.
 *
 * En développement sur le navigateur, utiliser toujours un chemin relatif `/api` :
 * le proxy (setupProxy / Nginx) relaie vers le backend. Ne jamais mettre
 * REACT_APP_API_URL=http://backend:8000 — ce nom n'existe que dans Docker (ERR_NAME_NOT_RESOLVED).
 */
function normalizeApiBase() {
  let v = (process.env.REACT_APP_API_URL ?? '/api').trim();
  if (!v) v = '/api';

  if (typeof window !== 'undefined') {
    // URL absolue vers le service Docker "backend" : invalide dans le navigateur
    if (/^https?:\/\/backend(?::\d+)?(\/|$)/i.test(v)) {
      return '/api';
    }
  }

  // "api" ou "api/foo" sans schéma → forcer un chemin absolu depuis l'origine
  if (!v.includes('://')) {
    return v.startsWith('/') ? v : `/${v}`;
  }

  return v;
}

const API_URL = normalizeApiBase();

export default API_URL;
