# Orchestration de la collecte des indicateurs de niveau N0 (technique).

from __future__ import annotations

import json
import logging
from pathlib import Path

from django.utils import timezone

from dashboard.models import Indicator, IndicatorMeasurement

from . import formulas
from .client import FileServerError, NormalizedLogsClient

logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"

SOURCES = ["firewall", "edr", "passerelle_mail", "vpn", "mfa", "waf", "pam"]


def load_template(source: str) -> dict:
    with open(TEMPLATES_DIR / f"{source}.json", "r", encoding="utf-8") as fh:
        return json.load(fh)


def _save_measurement(indicator_name: str, solution_name: str, value) -> bool:
    """Retrouve l'Indicator (niveau N0, solution donnée) et enregistre la
    mesure. Retourne True si enregistrée, False si ignorée (indicateur
    introuvable ou valeur non numérique)."""
    if value is None:
        logger.info(
            "Valeur non calculable pour '%s' (%s) — ignorée.",
            indicator_name,
            solution_name,
        )
        return False

    if not isinstance(value, (int, float)):
        logger.warning(
            "Valeur non numérique pour '%s' (%s) = %r — IndicatorMeasurement.value "
            "est un DecimalField, cet indicateur ne peut pas être stocké tel quel.",
            indicator_name,
            solution_name,
            value,
        )
        return False

    try:
        indicator = Indicator.objects.get(
            name=indicator_name, level="N0", solution__name=solution_name
        )
    except Indicator.DoesNotExist:
        logger.warning(
            "Indicateur introuvable en base : name=%r, level=N0, solution=%r "
            "(vérifier la cohérence avec le référentiel KPI/KRI).",
            indicator_name,
            solution_name,
        )
        return False

    IndicatorMeasurement.objects.create(
        indicator=indicator, value=value, calculated_at=timezone.now()
    )
    return True


# Traite une source ; retourne le nombre de mesures enregistrées.
def collect_source(client: NormalizedLogsClient, source: str) -> int:
    template = load_template(source)

    try:
        payload = client.fetch_latest(source)
    except FileServerError as exc:
        logger.error("Authentification refusée par la VM pour '%s' : %s", source, exc)
        return 0
    except Exception as exc:
        logger.error("Erreur réseau vers la VM pour '%s' : %s", source, exc)
        return 0

    if payload is None:
        return 0

    records = payload["records"]
    saved = 0
    for indicator_cfg in template["indicators"]:
        try:
            value = formulas.compute(indicator_cfg["op"], records, indicator_cfg)
        except Exception as exc:
            logger.error(
                "Échec du calcul de '%s' (source=%s) : %s",
                indicator_cfg["name"],
                source,
                exc,
            )
            continue

        if _save_measurement(indicator_cfg["name"], template["source"], value):
            saved += 1

    return saved


def collect_all(client: NormalizedLogsClient, sources: list[str] | None = None) -> int:
    total = 0
    for source in sources or SOURCES:
        total += collect_source(client, source)
    return total
