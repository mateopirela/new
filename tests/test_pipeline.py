"""Pruebas offline del pipeline (sin red).

Verifican el parseo del RSS, la clasificación heurística, la detección de
oportunidades y la generación del informe Markdown.

Ejecutar:  python -m tests.test_pipeline   (o pytest)
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trends_agent import analyze, report  # noqa: E402
from trends_agent.collect import RegionData, parse_rss  # noqa: E402
from trends_agent.config import REGIONS  # noqa: E402

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "co_sample.xml")


def _load_trends():
    with open(FIXTURE, "rb") as fh:
        return parse_rss(fh.read(), max_trends=20)


def test_parse_rss():
    trends = _load_trends()
    assert len(trends) == 5
    assert trends[0].term == "audífonos inalámbricos"
    assert trends[0].traffic_value == 50000
    assert trends[0].news and "comprar" in trends[0].news[0].title.lower()
    # El evento deportivo tiene el mayor tráfico.
    assert trends[2].traffic_value == 200000


def test_classification():
    trends = _load_trends()
    analyses = analyze.analyze_region(trends)
    by_term = {a.trend.term: a for a in analyses}

    assert by_term["audífonos inalámbricos"].category.key == "tech"
    assert by_term["freidora de aire"].category.key == "home"
    assert by_term["serum facial vitamina c"].category.key == "beauty"
    assert by_term["Nacional vs Millonarios"].category.key == "sports_event"
    assert by_term["dólar hoy"].category.key == "news"

    # Producto -> oportunidad ; noticia -> no.
    assert by_term["audífonos inalámbricos"].is_opportunity
    assert by_term["serum facial vitamina c"].is_opportunity
    assert not by_term["dólar hoy"].is_opportunity


def test_buy_signal_boost():
    """El titular de audífonos incluye 'baratos' y 'dónde comprar' -> boost."""
    trends = _load_trends()
    a = analyze.analyze_trend(trends[0])
    assert a.score >= 90  # 85 base +5 tráfico +5 señal de compra


def test_top_opportunities_sorted():
    analyses = analyze.analyze_region(_load_trends())
    opps = analyze.top_opportunities(analyses)
    assert opps  # hay al menos una
    scores = [o.score for o in opps]
    assert scores == sorted(scores, reverse=True)
    assert all(o.is_opportunity for o in opps)


def test_report_generation():
    trends = _load_trends()
    analyses = analyze.analyze_region(trends)
    rd = RegionData(region=REGIONS["CO"], trends=trends)
    md = report.build_report("2026-06-25", [(rd, analyses, None)])

    assert "# 📊 Informe de tendencias" in md
    assert "Colombia" in md
    assert "audífonos inalámbricos" in md
    assert "Oportunidades de dropshipping" in md
    # La noticia del dólar no debe aparecer como oportunidad de producto.
    assert "## 🌎 Colombia" in md
    return md


def _run_all():
    passed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"  ✓ {name}")
            passed += 1
    print(f"\n{passed} pruebas OK")


if __name__ == "__main__":
    _run_all()
    # Muestra un informe de ejemplo por stdout.
    print("\n----- INFORME DE EJEMPLO -----\n")
    print(test_report_generation())
