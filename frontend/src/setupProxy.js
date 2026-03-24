/**
 * Dev : les requêtes /api/* sont proxifiées vers le backend (même réécriture que Nginx).
 * Ainsi REACT_APP_API_URL=/api fonctionne sur le port 3000 et derrière Nginx (port 80).
 */
const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function setupProxy(app) {
  // Docker Compose définit PROXY_BACKEND=http://backend:8000 ; en local sans Docker : http://127.0.0.1:8000
  const target = process.env.PROXY_BACKEND || 'http://127.0.0.1:8000';
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
