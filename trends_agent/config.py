"""Configuración del agente: regiones, parámetros y lectura de variables de entorno."""
from __future__ import annotations

import os
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Catálogo de regiones soportadas.
#
#   rss_geo        -> código de país para el feed RSS de Google Trends
#                     (https://trends.google.com/trending/rss?geo=CO)
#   pytrends_pn    -> nombre de país que usa pytrends en trending_searches()
#   hl / tz        -> idioma y huso horario para las consultas de pytrends
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Region:
    code: str          # identificador interno (ISO-2)
    name: str          # nombre legible
    rss_geo: str       # geo para el feed RSS
    pytrends_pn: str   # 'country name' para pytrends.trending_searches
    hl: str = "es-CO"
    tz: int = 300      # offset en minutos respecto a UTC (Colombia = UTC-5 -> 300)


REGIONS: dict[str, Region] = {
    "CO": Region("CO", "Colombia", "CO", "colombia", "es-CO", 300),
    "MX": Region("MX", "México", "MX", "mexico", "es-MX", 360),
    "AR": Region("AR", "Argentina", "AR", "argentina", "es-AR", 180),
    "ES": Region("ES", "España", "ES", "spain", "es-ES", -60),
    "CL": Region("CL", "Chile", "CL", "chile", "es-CL", 240),
    "PE": Region("PE", "Perú", "PE", "peru", "es-PE", 300),
    "US": Region("US", "Estados Unidos", "US", "united_states", "en-US", 300),
}


@dataclass
class Settings:
    # Regiones a analizar (por defecto Colombia).
    regions: list[str] = field(default_factory=lambda: _env_list("TRENDS_REGIONS", ["CO"]))
    # Nº máximo de tendencias a procesar por región.
    max_trends: int = int(os.getenv("TRENDS_MAX", "20"))
    # Nº de tendencias top para las que se intenta el desglose geográfico interno.
    geo_breakdown_top: int = int(os.getenv("TRENDS_GEO_TOP", "8"))
    # Carpeta de salida de los informes.
    output_dir: str = os.getenv("TRENDS_OUTPUT_DIR", "reports")
    # Análisis con IA (opcional). Si no hay clave, se usa el analizador heurístico.
    anthropic_api_key: str | None = os.getenv("ANTHROPIC_API_KEY") or None
    anthropic_model: str = os.getenv("TRENDS_LLM_MODEL", "claude-haiku-4-5-20251001")
    use_llm: bool = os.getenv("TRENDS_USE_LLM", "auto") != "off"
    # Pausa entre consultas a pytrends para evitar el rate-limit (segundos).
    request_delay: float = float(os.getenv("TRENDS_REQUEST_DELAY", "1.5"))

    def resolved_regions(self) -> list[Region]:
        out = []
        for code in self.regions:
            region = REGIONS.get(code.strip().upper())
            if region:
                out.append(region)
        return out or [REGIONS["CO"]]

    @property
    def llm_enabled(self) -> bool:
        return self.use_llm and bool(self.anthropic_api_key)


def _env_list(name: str, default: list[str]) -> list[str]:
    raw = os.getenv(name)
    if not raw:
        return list(default)
    return [p for p in (x.strip() for x in raw.split(",")) if p]
