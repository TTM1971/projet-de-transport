/**
 * Normalise la clé `detail` des erreurs FastAPI / Pydantic pour affichage (string).
 * Évite "Objects are not valid as a React child" quand detail est un tableau d'objets { loc, msg, type }.
 */
export function formatApiError(detail, fallback = 'Une erreur est survenue.') {
  if (detail == null || detail === '') return fallback;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    return (
      detail
        .map((item) => {
          if (typeof item === 'string') return item;
          if (item && typeof item === 'object' && item.msg != null) {
            const loc = Array.isArray(item.loc)
              ? item.loc.filter((p) => p != null && p !== 'body').join(' · ')
              : '';
            return loc ? `${loc} : ${item.msg}` : String(item.msg);
          }
          try {
            return JSON.stringify(item);
          } catch {
            return String(item);
          }
        })
        .join(' · ') || fallback
    );
  }
  if (typeof detail === 'object') {
    if (detail.msg != null) {
      const loc = Array.isArray(detail.loc)
        ? detail.loc.filter((p) => p != null && p !== 'body').join(' · ')
        : '';
      return loc ? `${loc} : ${detail.msg}` : String(detail.msg);
    }
    try {
      return JSON.stringify(detail);
    } catch {
      return fallback;
    }
  }
  return String(detail);
}

/**
 * Message explicite pour l’écran de connexion (axios sans réponse = API arrêtée, mauvaise URL, CORS, etc.).
 */
export function formatLoginError(error, fallback = 'Erreur de connexion') {
  if (!error || !error.response) {
    const code = error?.code;
    const msg = (error?.message || '').toLowerCase();
    if (
      code === 'ERR_NETWORK' ||
      code === 'ECONNREFUSED' ||
      msg.includes('network error') ||
      msg.includes('failed to fetch')
    ) {
      return "Impossible de joindre l'API. Vérifiez que le backend tourne (Docker : « docker compose up » ou uvicorn sur le port 8000) et que l'URL de l'API est correcte.";
    }
    if (code === 'ECONNABORTED') {
      return "Délai dépassé : le serveur ne répond pas à temps.";
    }
    if (error?.message) {
      return error.message;
    }
    return fallback;
  }
  return formatApiError(error.response?.data?.detail, fallback);
}
