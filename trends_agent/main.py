"""Punto de entrada del agente: recolecta, analiza y escribe el informe diario.

Uso:
    python -m trends_agent.main              # usa la fecha de hoy (UTC)
    python -m trends_agent.main 2026-06-25   # fecha concreta (para el nombre)
    TRENDS_REGIONS=CO,MX python -m trends_agent.main
"""
from __future__ import annotations

import datetime as dt
import json
import os
import sys

from . import analyze, collect, report
from .config import Settings
from .llm import generate_insight


def _today_iso() -> str:
    # datetime.now() está disponible en ejecución normal (no en este sandbox de build).
    return dt.datetime.utcnow().strftime("%Y-%m-%d")


def run(date_str: str | None = None, settings: Settings | None = None) -> str:
    settings = settings or Settings()
    date_str = date_str or _today_iso()

    per_region = []
    for region in settings.resolved_regions():
        print(f"[trends] Recolectando {region.name} ({region.rss_geo})...", file=sys.stderr)
        region_data = collect.collect_region(region, settings)
        analyses = analyze.analyze_region(region_data.trends)
        insight = generate_insight(region_data, analyses, settings)
        if insight:
            print(f"[trends] Análisis IA generado para {region.name}.", file=sys.stderr)
        per_region.append((region_data, analyses, insight))

    md = report.build_report(date_str, per_region)
    payload = report.report_payload(date_str, per_region)

    os.makedirs(settings.output_dir, exist_ok=True)
    out_path = os.path.join(settings.output_dir, f"{date_str}.md")
    json_path = os.path.join(settings.output_dir, f"{date_str}.json")
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(md)
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)

    # Copias "latest" siempre apuntando al informe más reciente.
    with open(os.path.join(settings.output_dir, "latest.md"), "w", encoding="utf-8") as fh:
        fh.write(md)
    with open(os.path.join(settings.output_dir, "latest.json"), "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)

    print(f"[trends] Informe escrito en {out_path} (+ JSON)", file=sys.stderr)
    return out_path


def main() -> int:
    date_str = sys.argv[1] if len(sys.argv) > 1 else None
    try:
        run(date_str)
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"[trends] ERROR fatal: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
