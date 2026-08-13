from __future__ import annotations

from collections import Counter
from datetime import datetime


def _parse_dt(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value))
    except ValueError:
        return None


def _to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _matches(value, match: str) -> bool:
    if match == "*":
        return True
    values = {v.strip() for v in match.split(",")}
    return str(value) in values


def _count_match(records: list[dict], cfg: dict) -> int:
    field = cfg["field"]
    rows = records
    if "filter_field" in cfg:
        rows = [
            r
            for r in rows
            if str(r.get(cfg["filter_field"])) == str(cfg["filter_match"])
        ]
    return sum(1 for r in rows if _matches(r.get(field), cfg["match"]))


def ratio_pct(records: list[dict], cfg: dict):
    num = _count_match(records, cfg["numerator"])
    den = _count_match(records, cfg["denominator"])
    return round(num / den * 100, 2) if den else None


def ratio_pct_columns(records: list[dict], cfg: dict):
    num_field, den_field = cfg["numerator_field"], cfg["denominator_field"]
    if cfg.get("aggregation", "last") == "sum":
        num = sum(_to_float(r.get(num_field)) or 0 for r in records)
        den = sum(_to_float(r.get(den_field)) or 0 for r in records)
    else:
        if not records:
            return None
        num = _to_float(records[-1].get(num_field))
        den = _to_float(records[-1].get(den_field))
    return round(num / den * 100, 2) if den else None


def ratio_pct_group(records: list[dict], cfg: dict):
    values = {v.strip() for v in cfg["match"].split(",")}
    detected = sum(1 for r in records if str(r.get(cfg["group_field"])) in values)
    total = len(records)
    return round(detected / total * 100, 2) if total else None


def top_value(records: list[dict], cfg: dict):
    field = cfg["field"]
    weight_field = cfg.get("weight_field")
    if weight_field:
        totals: dict = {}
        for r in records:
            key = r.get(field)
            totals[key] = totals.get(key, 0) + (_to_float(r.get(weight_field)) or 0)
        return max(totals, key=totals.get) if totals else None
    counts = Counter(r.get(field) for r in records)
    return counts.most_common(1)[0][0] if counts else None


def sum_per_period(records: list[dict], cfg: dict):
    field = cfg["field"]
    total = sum(_to_float(r.get(field)) or 0 for r in records)

    duration_seconds = cfg.get("period_minutes", 60) * 60
    dates = [d for d in (_parse_dt(r.get("date_heure")) for r in records) if d]
    if dates:
        span = (max(dates) - min(dates)).total_seconds()
        if span > 0:
            duration_seconds = span

    if duration_seconds <= 0:
        return None
    mbps = (total * 8 / 1_000_000) / duration_seconds
    return round(mbps, 2)


def average(records: list[dict], cfg: dict):
    values = [
        v for v in (_to_float(r.get(cfg["field"])) for r in records) if v is not None
    ]
    return round(sum(values) / len(values), 2) if values else None


def average_duration(records: list[dict], cfg: dict):
    unit = cfg.get("unit", "minutes")
    divisor = {"seconds": 1, "minutes": 60, "hours": 3600}.get(unit, 60)

    deltas = []
    for r in records:
        start = _parse_dt(r.get(cfg["start_field"]))
        end = _parse_dt(r.get(cfg["end_field"]))
        if start and end:
            deltas.append((end - start).total_seconds())

    return round((sum(deltas) / len(deltas)) / divisor, 2) if deltas else None


def last_value(records: list[dict], cfg: dict):
    return records[-1].get(cfg["field"]) if records else None


def confusion_metric(records: list[dict], cfg: dict):
    tp = fn = tn = fp = 0
    for r in records:
        truth = str(r.get(cfg["truth_field"]))
        pred = str(r.get(cfg["prediction_field"]))
        if truth == "ATTAQUE" and pred == "ATTAQUE":
            tp += 1
        elif truth == "ATTAQUE":
            fn += 1
        elif pred == "ATTAQUE":
            fp += 1
        else:
            tn += 1

    tpr = tp / (tp + fn) if (tp + fn) else None
    tnr = tn / (tn + fp) if (tn + fp) else None

    metric = cfg.get("metric", "TPR")
    if metric == "TPR":
        return round(tpr * 100, 2) if tpr is not None else None
    if metric == "BALANCED_ACCURACY":
        if tpr is None or tnr is None:
            return None
        return round((tpr + tnr) / 2 * 100, 2)
    raise ValueError(f"Métrique de confusion inconnue : {metric}")


OPERATIONS = {
    "ratio_pct": ratio_pct,
    "ratio_pct_columns": ratio_pct_columns,
    "ratio_pct_group": ratio_pct_group,
    "top_value": top_value,
    "sum_per_period": sum_per_period,
    "average": average,
    "average_duration": average_duration,
    "last_value": last_value,
    "confusion_metric": confusion_metric,
}


def compute(op: str, records: list[dict], cfg: dict):
    if op not in OPERATIONS:
        raise ValueError(
            f"Opération '{op}' inconnue. Disponibles : {', '.join(sorted(OPERATIONS))}"
        )
    return OPERATIONS[op](records, cfg)
