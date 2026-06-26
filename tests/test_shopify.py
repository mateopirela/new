"""Pruebas offline del exportador a Shopify (sin red)."""
from __future__ import annotations

import csv
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shopify_export import csv_export  # noqa: E402
from shopify_export.config import ShopifySettings  # noqa: E402
from shopify_export.products import (  # noqa: E402
    build_collection, load_collections, price_for, slugify,
)

REPORT = os.path.join(os.path.dirname(__file__), "..", "reports", "latest.json")


def test_slugify():
    assert slugify("Audífonos inalámbricos / TWS") == "audifonos-inalambricos-tws"
    assert slugify("Serum facial vitamina C") == "serum-facial-vitamina-c"


def test_price_deterministic_and_ranged():
    p1 = price_for("tech", "Audífonos TWS|audífonos")
    p2 = price_for("tech", "Audífonos TWS|audífonos")
    assert p1 == p2                       # determinista
    assert 49900 <= p1 <= 259900          # dentro del rango de la categoría
    assert str(p1).endswith("900")        # terminación psicológica


def test_build_collection():
    opp = {
        "term": "audífonos inalámbricos",
        "category_key": "tech",
        "category_label": "Tecnología y gadgets",
        "score": 95,
        "rationale": "buena demanda",
        "product_ideas": ["Audífonos TWS", "Smartwatch económico", "Audífonos TWS"],
    }
    col = build_collection(opp)
    assert col.handle == "audifonos-inalambricos"
    # Se deduplican ideas repetidas.
    assert len(col.products) == 2
    p = col.products[0]
    assert p.compare_at > p.price                       # precio tachado mayor
    assert f"coleccion:{col.handle}" in p.tags          # etiqueta de colección


def test_load_collections_from_report():
    cols = load_collections(REPORT, "", 10)
    assert cols, "el informe de ejemplo debe producir colecciones"
    handles = {c.handle for c in cols}
    assert "audifonos-inalambricos" in handles
    # Las noticias (dólar) no deben generar colección.
    assert "dolar-hoy" not in handles


def test_csv_columns_and_rows():
    cols = load_collections(REPORT, "", 10)
    settings = ShopifySettings()
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "productos.csv")
        n = csv_export.write_csv(path, cols, settings)
        with open(path, encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            assert reader.fieldnames == csv_export.COLUMNS
            data = list(reader)
        assert len(data) == n
        # Estructura de una fila clave.
        first = data[0]
        assert first["Handle"]
        assert first["Variant Price"].endswith(".00")
        assert first["Option1 Value"] == "Default Title"
        assert first["Vendor"]


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
