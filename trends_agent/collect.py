"""Recolección de datos de tendencias desde Google Trends.

Fuentes (todas gratuitas):
  1. Feed RSS "Trending Now"  -> tendencias del día con tráfico aproximado y
     noticias relacionadas, por país.   (fuente primaria, robusta)
  2. pytrends.interest_by_region        -> desglose geográfico interno
     (departamentos / estados) para las tendencias top.  (best-effort)

El diseño es defensivo: si una fuente falla o devuelve vacío, el resto del
informe se sigue generando con lo disponible.
"""
from __future__ import annotations

import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

import requests

from .config import Region, Settings

RSS_URL = "https://trends.google.com/trending/rss?geo={geo}"
HT_NS = "{https://trends.google.com/trending/rss}"
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)


@dataclass
class NewsItem:
    title: str
    url: str
    source: str


@dataclass
class Trend:
    term: str
    approx_traffic: str = ""          # p.ej. "20.000+"
    traffic_value: int = 0            # versión numérica para ordenar
    rank: int = 0
    picture: str = ""
    news: list[NewsItem] = field(default_factory=list)
    # Desglose geográfico interno: {nombre_region: interes_0_100}
    geo_breakdown: dict[str, int] = field(default_factory=dict)
    related_queries: list[str] = field(default_factory=list)

    @property
    def news_titles(self) -> list[str]:
        return [n.title for n in self.news]


@dataclass
class RegionData:
    region: Region
    trends: list[Trend] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Feed RSS
# ---------------------------------------------------------------------------
def fetch_rss(geo: str, timeout: int = 30) -> bytes:
    """Descarga el feed RSS de tendencias para un país. Lanza en caso de error."""
    resp = requests.get(
        RSS_URL.format(geo=geo),
        headers={"User-Agent": USER_AGENT, "Accept": "application/rss+xml, application/xml"},
        timeout=timeout,
    )
    resp.raise_for_status()
    return resp.content


def parse_rss(xml_bytes: bytes, max_trends: int) -> list[Trend]:
    """Parsea el XML del feed RSS de Google Trends a una lista de Trend."""
    root = ET.fromstring(xml_bytes)
    trends: list[Trend] = []
    for i, item in enumerate(root.iter("item")):
        if i >= max_trends:
            break
        title = (item.findtext("title") or "").strip()
        if not title:
            continue
        approx = (item.findtext(f"{HT_NS}approx_traffic") or "").strip()
        picture = (item.findtext(f"{HT_NS}picture") or "").strip()
        news = []
        for ni in item.findall(f"{HT_NS}news_item"):
            n_title = (ni.findtext(f"{HT_NS}news_item_title") or "").strip()
            n_url = (ni.findtext(f"{HT_NS}news_item_url") or "").strip()
            n_src = (ni.findtext(f"{HT_NS}news_item_source") or "").strip()
            if n_title:
                news.append(NewsItem(n_title, n_url, n_src))
        trends.append(
            Trend(
                term=title,
                approx_traffic=approx,
                traffic_value=_traffic_to_int(approx),
                rank=i + 1,
                picture=picture,
                news=news,
            )
        )
    return trends


def _traffic_to_int(approx: str) -> int:
    """'20.000+' / '1M+' -> entero aproximado para poder ordenar."""
    if not approx:
        return 0
    s = approx.lower().replace("+", "").replace(",", "").replace(".", "").strip()
    mult = 1
    if s.endswith("m"):
        mult, s = 1_000_000, s[:-1]
    elif s.endswith("k"):
        mult, s = 1_000, s[:-1]
    try:
        return int(float(s) * mult)
    except ValueError:
        return 0


# ---------------------------------------------------------------------------
# Desglose geográfico interno (pytrends) - best effort
# ---------------------------------------------------------------------------
def enrich_geo_breakdown(trends: list[Trend], region: Region, settings: Settings) -> list[str]:
    """Añade `geo_breakdown` y `related_queries` a las tendencias top.

    Devuelve la lista de errores no fatales encontrados.
    """
    errors: list[str] = []
    try:
        from pytrends.request import TrendReq
    except Exception as exc:  # pragma: no cover - import opcional
        return [f"pytrends no disponible: {exc}"]

    try:
        pytrends = TrendReq(hl=region.hl, tz=region.tz, timeout=(10, 25))
    except Exception as exc:
        return [f"No se pudo inicializar pytrends: {exc}"]

    for trend in trends[: settings.geo_breakdown_top]:
        try:
            pytrends.build_payload([trend.term], geo=region.code, timeframe="now 7-d")
            df = pytrends.interest_by_region(resolution="REGION", inc_low_vol=True)
            if df is not None and not df.empty and trend.term in df.columns:
                col = df[trend.term].sort_values(ascending=False)
                trend.geo_breakdown = {
                    str(idx): int(val) for idx, val in col.head(5).items() if int(val) > 0
                }
            related = pytrends.related_queries().get(trend.term) or {}
            top = related.get("top")
            if top is not None and not top.empty:
                trend.related_queries = [str(q) for q in top["query"].head(6).tolist()]
        except Exception as exc:
            errors.append(f"geo/related '{trend.term}': {exc}")
        time.sleep(settings.request_delay)
    return errors


# ---------------------------------------------------------------------------
# Orquestación por región
# ---------------------------------------------------------------------------
def collect_region(region: Region, settings: Settings) -> RegionData:
    data = RegionData(region=region)
    try:
        xml_bytes = fetch_rss(region.rss_geo)
        data.trends = parse_rss(xml_bytes, settings.max_trends)
    except Exception as exc:
        data.errors.append(f"RSS '{region.rss_geo}': {exc}")
        return data

    if not data.trends:
        data.errors.append("El feed RSS no devolvió tendencias.")
        return data

    data.errors.extend(enrich_geo_breakdown(data.trends, region, settings))
    return data
