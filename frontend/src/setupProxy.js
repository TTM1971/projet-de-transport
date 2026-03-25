/**
 * Dev : les requêtes /api/* sont proxifiées vers le backend (même réécriture que Nginx).
 * Ainsi REACT_APP_API_URL=/api fonctionne sur le port 3000 et derrière Nginx (port 80).
 */
const fs = require('fs');
const path = require('path');
const { createProxyMiddleware } = require('http-proxy-middleware');

function loadEnvFiles() {
  try {
    // Même logique que CRA : .env.local puis .env (ne remplace pas les vars déjà définies par l’OS / Docker)
    require('dotenv').config({ path: path.join(__dirname, '..', '.env.local') });
    require('dotenv').config({ path: path.join(__dirname, '..', '.env.development.local') });
    require('dotenv').config({ path: path.join(__dirname, '..', '.env') });
  } catch (_) {
    /* dotenv optionnel si résolution échoue */
  }
}

function resolveProxyTarget() {
  loadEnvFiles();
  let target = process.env.PROXY_BACKEND || 'http://127.0.0.1:8000';

  // Dans un conteneur Docker, 127.0.0.1 / localhost = le conteneur lui-même, pas le backend.
  // Le fichier .env du poste (127.0.0.1:8000) casse le proxy si on monte ./frontend dans le conteneur.
  const inDocker = fs.existsSync('/.dockerenv');
  if (inDocker && /127\.0\.0\.1|localhost/i.test(target)) {
    target = 'http://backend:8000';
    // eslint-disable-next-line no-console
    console.info('[setupProxy] Docker détecté : PROXY_BACKEND forcé vers http://backend:8000');
  }
  return target;
}

module.exports = function setupProxy(app) {
  const target = resolveProxyTarget();
  // eslint-disable-next-line no-console
  console.info('[setupProxy] /api ->', target);
  // proxyTimeout / timeout : défaut ~120 s → 504 sur analytics/planning lourds
  const tenMinutes = 600_000;
  app.use(
    '/api',
    createProxyMiddleware({
      target,
      changeOrigin: true,
      pathRewrite: { '^/api': '' },
      proxyTimeout: tenMinutes,
      timeout: tenMinutes,
    }),
  );
};
