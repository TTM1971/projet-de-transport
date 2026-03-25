/**
 * Durcissement des appels API (complément CORS / bonnes pratiques anti-CSRF côté client).
 * Le JWT reste dans Authorization : en cas de XSS, un attaquant peut toujours l’utiliser —
 * d’où l’importance des en-têtes CSP côté front + pas de dangerouslySetInnerHTML.
 */
import axios from 'axios';

axios.defaults.headers.common['X-Requested-With'] = 'XMLHttpRequest';
axios.defaults.withCredentials = false;

// En dev : éviter l’overlay « Uncaught runtime errors » pour les rejets Axios non capturés (API arrêtée).
if (process.env.NODE_ENV === 'development') {
  window.addEventListener('unhandledrejection', (event) => {
    const r = event.reason;
    if (!r || typeof r !== 'object' || !r.isAxiosError) return;
    if (r.response) return;
    const code = r.code;
    const msg = (r.message || '').toLowerCase();
    if (code === 'ERR_NETWORK' || msg.includes('network error')) {
      event.preventDefault();
      // eslint-disable-next-line no-console
      console.warn(
        "[API] Impossible de joindre le backend. Démarrez l'API (ex. port 8000 : « docker compose up » ou uvicorn). " +
          'Sur :3000, vérifiez PROXY_BACKEND dans setupProxy (Docker : http://backend:8000).',
      );
    }
  });
}
