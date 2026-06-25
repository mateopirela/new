"""Capa opcional de análisis con IA (Claude).

Si hay `ANTHROPIC_API_KEY`, se le pide a Claude que redacte un análisis
estratégico más fino sobre las oportunidades de dropshipping a partir de los
datos ya recolectados y clasificados. Si no hay clave o la llamada falla, se
devuelve None y el informe usa solo el análisis heurístico.
"""
from __future__ import annotations

import json

import requests

from .analyze import Analysis
from .collect import RegionData
from .config import Settings

API_URL = "https://api.anthropic.com/v1/messages"


def generate_insight(region_data: RegionData, analyses: list[Analysis], settings: Settings) -> str | None:
    if not settings.llm_enabled:
        return None

    payload_trends = []
    for a in analyses[:15]:
        payload_trends.append({
            "termino": a.trend.term,
            "trafico": a.trend.approx_traffic,
            "categoria": a.category.label,
            "potencial_dropshipping": a.score,
            "regiones_internas": a.trend.geo_breakdown,
            "noticias": a.trend.news_titles[:2],
            "ideas_base": a.product_ideas,
        })

    prompt = (
        "Eres un analista experto en e-commerce y dropshipping para mercados de "
        f"habla hispana. Región analizada: {region_data.region.name}.\n\n"
        "Aquí tienes las tendencias de búsqueda del día (JSON) ya clasificadas:\n\n"
        f"{json.dumps(payload_trends, ensure_ascii=False, indent=2)}\n\n"
        "Escribe un análisis en español (Markdown, sin encabezado de nivel 1) con:\n"
        "1. Lectura rápida de qué está moviendo la atención hoy.\n"
        "2. Las 3-5 mejores oportunidades de producto para vender por dropshipping, "
        "con: producto concreto, por qué encaja con la tendencia, nivel de "
        "competencia estimado y ángulo de marketing.\n"
        "3. Una advertencia sobre las tendencias que NO conviene perseguir (efímeras/noticias).\n"
        "Sé concreto y accionable. Máximo ~400 palabras."
    )

    try:
        resp = requests.post(
            API_URL,
            headers={
                "x-api-key": settings.anthropic_api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": settings.anthropic_model,
                "max_tokens": 1200,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        parts = [b.get("text", "") for b in data.get("content", []) if b.get("type") == "text"]
        text = "".join(parts).strip()
        return text or None
    except Exception:
        # El informe debe generarse aunque la IA falle.
        return None
