#!/usr/bin/env python3
"""
Smoke checks post-déploiement : UI (Nginx), API liveness, readiness base.

Variables d'environnement :
  SMOKE_BASE_URL     URL publique (défaut: http://127.0.0.1)
  SMOKE_API_PREFIX   Préfixe API derrière Nginx (défaut: /api). Vide = API directe ex. http://127.0.0.1:8000
  SMOKE_SKIP_FRONTEND  Si 1, ne vérifie pas la page d'accueil (défaut: 0)
  SMOKE_TIMEOUT_SEC    Timeout HTTP en secondes (défaut: 15)

Exemples :
  # Stack Docker avec Nginx sur le port 80
  python scripts/smoke_checks.py

  # API seule (sans préfixe /api)
  set SMOKE_BASE_URL=http://127.0.0.1:8000
  set SMOKE_API_PREFIX=
  python scripts/smoke_checks.py
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any


def _env(name: str, default: str) -> str:
    return os.environ.get(name, default).strip()


def _bool_env(name: str, default: bool) -> bool:
    v = os.environ.get(name)
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "on")


def _join_url(base: str, *parts: str) -> str:
    b = base.rstrip("/")
    for p in parts:
        if not p:
            continue
        p = p if p.startswith("/") else f"/{p}"
        b = f"{b}{p}"
    return b


def _get_json(url: str, timeout: float) -> tuple[int, dict[str, Any]]:
    req = urllib.request.Request(url, headers={"User-Agent": "transport-smoke-checks/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
        data = json.loads(raw) if raw.strip() else {}
        return resp.status, data


def _get_text(url: str, timeout: float) -> tuple[int, str]:
    req = urllib.request.Request(url, headers={"User-Agent": "transport-smoke-checks/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode("utf-8", errors="replace")
        return resp.status, body


def main() -> int:
    base = _env("SMOKE_BASE_URL", "http://127.0.0.1")
    prefix = _env("SMOKE_API_PREFIX", "/api")
    skip_fe = _bool_env("SMOKE_SKIP_FRONTEND", False)
    try:
        timeout = float(_env("SMOKE_TIMEOUT_SEC", "15"))
    except ValueError:
        timeout = 15.0

    api_root = _join_url(base, prefix) if prefix else base.rstrip("/")

    errors: list[str] = []

    # 1) Page d'accueil (build statique ou dev)
    if not skip_fe:
        try:
            status, html = _get_text(base.rstrip("/") + "/", timeout)
            if status != 200:
                errors.append(f"frontend: HTTP {status} sur {base}/")
            elif "<html" not in html.lower() and "<!doctype" not in html.lower():
                errors.append("frontend: réponse sans HTML attendu (index SPA)")
            else:
                print(f"OK  frontend  {base}/")
        except urllib.error.HTTPError as e:
            errors.append(f"frontend: HTTP {e.code} {e.reason}")
        except urllib.error.URLError as e:
            errors.append(f"frontend: {e.reason}")
        except Exception as e:
            errors.append(f"frontend: {e}")

    # 2) Liveness API
    health_url = _join_url(api_root, "/health")
    try:
        status, data = _get_json(health_url, timeout)
        if status != 200 or data.get("status") != "ok":
            errors.append(f"health: attendu 200 + status=ok, obtenu {status} {data!r}")
        else:
            print(f"OK  health     {health_url}")
    except urllib.error.HTTPError as e:
        errors.append(f"health: HTTP {e.code}")
    except urllib.error.URLError as e:
        errors.append(f"health: {e.reason}")
    except json.JSONDecodeError as e:
        errors.append(f"health: JSON invalide ({e})")
    except Exception as e:
        errors.append(f"health: {e}")

    # 3) Readiness (PostgreSQL)
    ready_url = _join_url(api_root, "/health/ready")
    try:
        status, data = _get_json(ready_url, timeout)
        if status != 200 or data.get("status") != "ready":
            errors.append(f"ready: attendu 200 + status=ready, obtenu {status} {data!r}")
        else:
            print(f"OK  ready      {ready_url}")
    except urllib.error.HTTPError as e:
        if e.code == 503:
            errors.append("ready: base indisponible (503)")
        else:
            errors.append(f"ready: HTTP {e.code}")
    except urllib.error.URLError as e:
        errors.append(f"ready: {e.reason}")
    except json.JSONDecodeError as e:
        errors.append(f"ready: JSON invalide ({e})")
    except Exception as e:
        errors.append(f"ready: {e}")

    if errors:
        print("Échec des smoke checks:", file=sys.stderr)
        for msg in errors:
            print(f"  - {msg}", file=sys.stderr)
        return 1

    print("Tous les smoke checks ont réussi.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
