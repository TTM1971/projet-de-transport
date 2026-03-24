"""
Constantes de référence pour la conformité de base (Canada).
Les règles exactes varient par province/territoire — valider avec RH / juridique en production.
"""

# Fuseau horaire par défaut pour l'exploitation (Ontario / Québec — ajustable par site)
DEFAULT_TIMEZONE = "America/Toronto"

# Durée maximale d'un quart saisi (heures) — repère prudent pour détection d'anomalies
MAX_SHIFT_HOURS = 13.0

# Au-delà de cette durée de travail continu, une pause devrait être planifiée (repère Ontario 5h)
HOURS_BEFORE_BREAK_RECOMMENDED = 5.0
RECOMMENDED_BREAK_MINUTES = 30
