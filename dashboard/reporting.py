# Helper imports for report logo embedding.
import html
import json
from pathlib import Path

from django.conf import settings
from django.http import HttpResponse
from django.utils import timezone


STRINGS = {
    "fr": {
        "html_lang": "fr",
        "all_solutions": "Toutes les solutions",
        "brand_name": "Office National de l&apos;Électricité et de l&apos;Eau Potable",
        "brand_sub": "Direction cybersécurité · Indicateurs de pilotage",
        "generated_on": "Généré le",
        "intro": "Synthèse professionnelle des indicateurs de performance et de risque cyber.",
        "scope": "Périmètre",
        "solution": "Solution",
        "indicators": "Indicateurs",
        "col_indicator": "Indicateur",
        "col_type": "Type",
        "col_level": "Niveau",
        "col_solution": "Solution",
        "col_value": "Valeur",
        "empty": "Aucun indicateur sélectionné.",
        "confidential": "Document confidentiel · ONEE",
        "footer_tag": "Rapport KPI / KRI",
    },
    "en": {
        "html_lang": "en",
        "all_solutions": "All solutions",
        "brand_name": "National Office of Electricity and Drinking Water",
        "brand_sub": "Cybersecurity Directorate · Steering indicators",
        "generated_on": "Generated on",
        "intro": "Professional summary of cyber performance and risk indicators.",
        "scope": "Scope",
        "solution": "Solution",
        "indicators": "Indicators",
        "col_indicator": "Indicator",
        "col_type": "Type",
        "col_level": "Level",
        "col_solution": "Solution",
        "col_value": "Value",
        "empty": "No indicator selected.",
        "confidential": "Confidential document · ONEE",
        "footer_tag": "KPI / KRI Report",
    },
}


def build_payload(indicators, title, selected_kind, solution_name, language="fr"):
    lang = language if language in STRINGS else "fr"
    return {
        "title": title,
        "language": lang,
        "generated_at": timezone.now().isoformat(),
        "kind": selected_kind or "KPI + KRI",
        "solution": solution_name or STRINGS[lang]["all_solutions"],
        "indicators": [
            {
                "name": item.name,
                "type": item.kind,
                "level": item.level,
                "solution": item.solution.name if item.solution else None,
                "value": str(item.latest_value)
                if item.latest_value is not None
                else None,
                "target": str(item.target_value)
                if item.target_value is not None
                else None,
                "nature": item.nature,
            }
            for item in indicators
        ],
    }


def _logo_data_uri():
    logo_path = Path(settings.MEDIA_ROOT) / "onee.png"
    if not logo_path.exists():
        return ""
    encoded = base64.b64encode(logo_path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def _report_html(payload):
    logo = _logo_data_uri()
    t = STRINGS.get(payload.get("language", "fr"), STRINGS["fr"])
    title = html.escape(payload["title"])
    solution = html.escape(payload["solution"])
    kind = html.escape(payload["kind"])
    generated_at = html.escape(payload["generated_at"].replace("T", " ").split(".")[0])
    rows = "".join(
        f"<tr><td><strong>{html.escape(str(item['name']))}</strong></td>"
        f'<td><span class="badge">{html.escape(str(item["type"]))}</span></td>'
        f"<td>{html.escape(str(item['level']))}</td>"
        f"<td>{html.escape(str(item['solution'] or '—'))}</td>"
        f'<td class="value">{html.escape(str(item["value"] or "—"))}</td></tr>'
        for item in payload["indicators"]
    )
    return f'''<!doctype html>
<html lang="{t["html_lang"]}"><head><meta charset="utf-8"><title>{title}</title>
<style>
@page{{size:A4;margin:18mm 16mm 20mm}}*{{box-sizing:border-box}}body{{font-family:Arial,Helvetica,sans-serif;color:#183b56;margin:0;font-size:10px;line-height:1.45}}.masthead{{display:flex;justify-content:space-between;align-items:center;border-bottom:3px solid #087f8c;padding-bottom:14px;margin-bottom:28px}}.brand{{display:flex;align-items:center;gap:12px}}.brand img{{width:58px;height:58px;object-fit:contain}}.brand-name{{font-size:11px;letter-spacing:1px;font-weight:bold;color:#102a43;text-transform:uppercase}}.brand-sub{{font-size:9px;color:#637589;margin-top:3px}}.date{{text-align:right;color:#637589;font-size:9px}}h1{{font-size:25px;line-height:1.15;color:#102a43;margin:0 0 8px}}.intro{{color:#637589;margin:0 0 22px;font-size:11px}}.summary{{display:flex;gap:10px;margin:0 0 24px}}.summary-card{{flex:1;padding:12px 14px;background:#f0f8f8;border:1px solid #d7e9e8;border-radius:6px}}.summary-label{{display:block;text-transform:uppercase;font-size:8px;letter-spacing:.8px;color:#637589;margin-bottom:4px}}.summary-value{{font-size:12px;font-weight:bold;color:#087f8c}}table{{width:100%;border-collapse:collapse;margin-top:10px}}th{{background:#102a43;color:white;text-align:left;font-size:9px;text-transform:uppercase;letter-spacing:.3px;padding:9px 8px}}td{{border-bottom:1px solid #d7e1e8;padding:9px 8px;vertical-align:top}}tr:nth-child(even){{background:#f6f9fb}}.badge{{display:inline-block;background:#e4f4f3;color:#087f8c;border-radius:10px;padding:2px 6px;font-size:8px;font-weight:bold}}.value{{font-weight:bold;color:#102a43}}.footer{{margin-top:28px;border-top:1px solid #d7e1e8;padding-top:9px;color:#637589;font-size:8px;display:flex;justify-content:space-between}}
</style></head><body><header class="masthead"><div class="brand">{f'<img src="{logo}" alt="ONEE">' if logo else ""}<div><div class="brand-name">{t["brand_name"]}</div><div class="brand-sub">{t["brand_sub"]}</div></div></div><div class="date">{t["generated_on"]}<br><strong>{generated_at}</strong></div></header><main><h1>{title}</h1><p class="intro">{t["intro"]}</p><section class="summary"><div class="summary-card"><span class="summary-label">{t["scope"]}</span><span class="summary-value">{kind}</span></div><div class="summary-card"><span class="summary-label">{t["solution"]}</span><span class="summary-value">{solution}</span></div><div class="summary-card"><span class="summary-label">{t["indicators"]}</span><span class="summary-value">{len(payload["indicators"])}</span></div></section><table><thead><tr><th>{t["col_indicator"]}</th><th>{t["col_type"]}</th><th>{t["col_level"]}</th><th>{t["col_solution"]}</th><th>{t["col_value"]}</th></tr></thead><tbody>{rows or f'<tr><td colspan="5">{t["empty"]}</td></tr>'}</tbody></table></main><footer class="footer"><span>{t["confidential"]}</span><span>{t["footer_tag"]}</span></footer></body></html>'''


def export_report(payload, fmt):
    fmt = fmt.lower()
    filename = payload["title"].replace(" ", "_")
    if fmt == "json":
        response = HttpResponse(
            json.dumps(payload, ensure_ascii=False, indent=2),
            content_type="application/json; charset=utf-8",
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}.json"'
        return response

    report_html = _report_html(payload)
    if fmt == "pdf":
        try:
            from weasyprint import HTML

            content = HTML(
                string=report_html, base_url=str(settings.MEDIA_ROOT)
            ).write_pdf()
            response = HttpResponse(content, content_type="application/pdf")
        except ImportError:
            response = HttpResponse(
                report_html, content_type="text/html; charset=utf-8"
            )
    else:
        response = HttpResponse(
            report_html,
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    response["Content-Disposition"] = f'attachment; filename="{filename}.{fmt}"'
    return response
