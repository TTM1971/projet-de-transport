from __future__ import annotations

"""
Sécurité applicative : réduction des risques XSS (en-têtes) et CSRF (origine + CORS strict).

Notes :
- L’API utilise un JWT dans le header Authorization (pas en cookie) : le CSRF « classique »
  (formulaire cross-site avec cookie de session) ne s’applique pas de la même façon.
- La validation d’origine en complément du CORS renforce la défense pour les navigateurs.
"""
import os
from typing import List

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


def _parse_origins() -> List[str]:
    raw = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000,http://frontend:3000",
    )
    return [o.strip() for o in raw.split(",") if o.strip()]


ALLOWED_ORIGINS = _parse_origins()
STRICT_ORIGIN = os.getenv("SECURITY_STRICT_ORIGIN", "false").lower() in ("1", "true", "yes")

UNSAFE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})

# Requêtes mutantes sans Origin attendu (CLI, intégrations) — désactivé si STRICT_ORIGIN
ALLOW_MISSING_ORIGIN = os.getenv("SECURITY_ALLOW_MISSING_ORIGIN", "true").lower() in (
    "1",
    "true",
    "yes",
)


def _path_skips_origin_check(path: str) -> bool:
    """Endpoints publics ou préflight : ne pas bloquer."""
    if path == "/":
        return True
    if path.startswith("/docs") or path.startswith("/redoc"):
        return True
    if path in ("/openapi.json", "/favicon.ico"):
        return True
    # Connexion / inscription : pas de JWT encore ; le navigateur envoie quand même Origin
    if path.startswith("/auth/login") or path.startswith("/auth/register"):
        return True
    return False


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    En-têtes anti-XSS / clickjacking / fuite d’infos.
    Pour une API JSON, la CSP limite surtout l’usage accidentel de la réponse comme « page ».
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), camera=(), geolocation=(), microphone=(), payment=()"
        )
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        return response


class OriginEnforcementMiddleware(BaseHTTPMiddleware):
    """
    Si SECURITY_STRICT_ORIGIN=true : pour POST/PUT/PATCH/DELETE, l’en-tête Origin (si présent)
    doit être dans la liste CORS_ORIGINS. Complète la protection CORS côté serveur.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        if not STRICT_ORIGIN:
            return await call_next(request)

        if request.method == "OPTIONS":
            return await call_next(request)

        if request.method not in UNSAFE_METHODS:
            return await call_next(request)

        path = request.url.path
        if _path_skips_origin_check(path):
            return await call_next(request)

        origin = request.headers.get("origin")
        if not origin:
            if ALLOW_MISSING_ORIGIN:
                return await call_next(request)
            return JSONResponse(
                status_code=403,
                content={"detail": "En-tête Origin requis pour cette méthode."},
            )

        if origin not in ALLOWED_ORIGINS:
            return JSONResponse(
                status_code=403,
                content={"detail": "Origine non autorisée."},
            )

        return await call_next(request)
