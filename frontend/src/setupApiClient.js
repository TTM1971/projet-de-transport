/**
 * Durcissement des appels API (complément CORS / bonnes pratiques anti-CSRF côté client).
 * Le JWT reste dans Authorization : en cas de XSS, un attaquant peut toujours l’utiliser —
 * d’où l’importance des en-têtes CSP côté front + pas de dangerouslySetInnerHTML.
 */
import axios from 'axios';

axios.defaults.headers.common['X-Requested-With'] = 'XMLHttpRequest';
axios.defaults.withCredentials = false;
