"""Generación del informe diario en Markdown."""
from __future__ import annotations

from .analyze import Analysis, top_opportunities
from .collect import RegionData


def _emoji_for_score(score: int) -> str:
    if score >= 75:
        return "🟢"
    if score >= 55:
        return "🟡"
    return "🔴"


def build_report(
    date_str: str,
    per_region: list[tuple[RegionData, list[Analysis], str | None]],
) -> str:
    """Construye el informe completo.

    `per_region`: lista de (datos_region, analisis, insight_ia_opcional).
    """
    region_names = ", ".join(rd.region.name for rd, _, _ in per_region)
    lines: list[str] = []
    lines.append(f"# 📊 Informe de tendencias y dropshipping — {date_str}")
    lines.append("")
    lines.append(f"**Regiones:** {region_names}  ·  **Fuente:** Google Trends (Trending Now)")
    lines.append("")
    lines.append("> Generado automáticamente por `trends_agent`. "
                 "Los potenciales de dropshipping son estimaciones heurísticas: "
                 "validar siempre proveedor, margen y competencia antes de invertir.")
    lines.append("")

    for region_data, analyses, insight in per_region:
        lines.extend(_render_region(region_data, analyses, insight))

    lines.append("---")
    lines.append("")
    lines.append("<sub>Informe diario · agente de tendencias · datos públicos de Google Trends</sub>")
    lines.append("")
    return "\n".join(lines)


def _render_region(region_data: RegionData, analyses: list[Analysis], insight: str | None) -> list[str]:
    r = region_data.region
    out: list[str] = []
    out.append(f"## 🌎 {r.name}")
    out.append("")

    if not analyses:
        out.append("_No se obtuvieron tendencias para esta región hoy._")
        out.append("")
        if region_data.errors:
            out.append("<details><summary>Detalles técnicos</summary>\n")
            for e in region_data.errors:
                out.append(f"- {e}")
            out.append("\n</details>")
            out.append("")
        return out

    # --- Tabla de tendencias del día ---
    out.append("### 🔥 Tendencias del día")
    out.append("")
    out.append("| # | Búsqueda | Tráfico aprox. | Categoría | Potencial DS |")
    out.append("|---|----------|----------------|-----------|:------------:|")
    for a in analyses:
        traffic = a.trend.approx_traffic or "—"
        out.append(
            f"| {a.trend.rank} | {a.trend.term} | {traffic} | "
            f"{a.category.label} | {_emoji_for_score(a.score)} {a.score} |"
        )
    out.append("")

    # --- Distribución geográfica interna ---
    geo_rows = [a for a in analyses if a.trend.geo_breakdown]
    if geo_rows:
        out.append("### 🗺️ Distribución geográfica interna")
        out.append("")
        out.append("Dónde se busca más cada término (interés relativo 0–100 por región):")
        out.append("")
        for a in geo_rows:
            dist = ", ".join(f"{reg} ({val})" for reg, val in a.trend.geo_breakdown.items())
            out.append(f"- **{a.trend.term}** → {dist}")
        out.append("")

    # --- Oportunidades de dropshipping ---
    opps = top_opportunities(analyses)
    out.append("### 🛒 Oportunidades de dropshipping")
    out.append("")
    if not opps:
        out.append("_Hoy las tendencias son mayormente noticias/eventos con baja intención "
                   "de compra directa. Poco encaje para producto físico._")
        out.append("")
    else:
        for a in opps:
            out.append(f"#### {_emoji_for_score(a.score)} {a.trend.term}  ·  _{a.category.label}_  ·  potencial {a.score}/100")
            out.append("")
            out.append(f"{a.rationale}")
            out.append("")
            out.append("**Productos sugeridos:**")
            for idea in a.product_ideas:
                out.append(f"- {idea}")
            if a.trend.related_queries:
                rel = ", ".join(a.trend.related_queries[:5])
                out.append("")
                out.append(f"_Búsquedas relacionadas:_ {rel}")
            out.append("")

    # --- Análisis con IA (opcional) ---
    if insight:
        out.append("### 🤖 Análisis estratégico (IA)")
        out.append("")
        out.append(insight.strip())
        out.append("")

    if region_data.errors:
        out.append("<details><summary>⚠️ Avisos técnicos no fatales</summary>\n")
        for e in region_data.errors:
            out.append(f"- {e}")
        out.append("\n</details>")
        out.append("")

    return out
