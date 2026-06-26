"""Construye productos y colecciones de Shopify a partir del informe.

Cada *oportunidad* del informe se convierte en una *colección* de Shopify, y
cada *idea de producto* dentro de ella en un *producto* con su precio en COP.
"""
from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field

# Rangos de precio (COP) y metadatos por categoría del informe.
CATEGORY_PRICING: dict[str, tuple[int, int]] = {
    "tech": (49900, 259900),
    "beauty": (24900, 129900),
    "home": (39900, 299900),
    "fitness": (29900, 159900),
    "fashion": (29900, 149900),
    "baby_pets": (24900, 119900),
    "seasonal": (19900, 99900),
    "gaming": (49900, 349900),
    "default": (29900, 149900),
}


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def _hash32(s: str) -> int:
    """FNV-1a de 32 bits (precios deterministas por nombre)."""
    h = 0x811C9DC5
    for ch in s:
        h ^= ord(ch)
        h = (h * 0x01000193) & 0xFFFFFFFF
    return h


def price_for(category_key: str, seed: str) -> int:
    lo, hi = CATEGORY_PRICING.get(category_key, CATEGORY_PRICING["default"])
    raw = lo + (_hash32(seed) % (hi - lo))
    # Redondeo a terminación .900 (precio psicológico habitual en CO).
    return max(lo, round(raw / 1000) * 1000 - 100)


@dataclass
class Product:
    title: str
    handle: str
    body_html: str
    price: int
    compare_at: int
    sku: str
    tags: list[str]


@dataclass
class Collection:
    title: str            # nombre de la oportunidad
    handle: str
    description: str
    category_key: str
    category_label: str
    score: int
    products: list[Product] = field(default_factory=list)


def _body_html(product_name: str, term: str, label: str, score: int) -> str:
    return (
        f"<p><strong>{product_name}</strong> es uno de los productos más buscados "
        f"en la categoría de {label.lower()} en este momento.</p>"
        f"<p>Aprovecha la tendencia de <em>\"{term}\"</em> (potencial de demanda "
        f"{score}/100). Envío a todo el país y pago contra entrega disponible.</p>"
        f"<ul><li>Producto en tendencia</li><li>Stock listo para despacho</li>"
        f"<li>Garantía de satisfacción</li></ul>"
    )


def build_collection(opp: dict) -> Collection:
    term = (opp.get("term") or "").strip()
    cat_key = opp.get("category_key", "default")
    cat_label = opp.get("category_label", "General")
    score = int(opp.get("score", 0))
    col_handle = slugify(term)

    ideas = opp.get("product_ideas") or [term]
    base_tags = [term, cat_label, "tendencia"]
    products: list[Product] = []
    seen: set[str] = set()
    for idea in ideas:
        handle = slugify(idea)
        if not handle or handle in seen:
            continue
        seen.add(handle)
        price = price_for(cat_key, idea + term)
        compare_at = round(price * 1.6 / 1000) * 1000 - 100
        sku = f"{col_handle[:8].upper()}-{_hash32(idea) % 100000:05d}"
        products.append(Product(
            title=idea,
            handle=handle,
            body_html=_body_html(idea, term, cat_label, score),
            price=price,
            compare_at=compare_at,
            sku=sku,
            tags=base_tags + [f"coleccion:{col_handle}"],
        ))

    return Collection(
        title=term[:1].upper() + term[1:],
        handle=col_handle,
        description=opp.get("rationale", ""),
        category_key=cat_key,
        category_label=cat_label,
        score=score,
        products=products,
    )


def load_collections(report_json: str, region_code: str = "", limit: int = 10) -> list[Collection]:
    with open(report_json, encoding="utf-8") as fh:
        report = json.load(fh)

    regions = report.get("regions", [])
    region = None
    if region_code:
        region = next((r for r in regions if r.get("code") == region_code), None)
    region = region or (regions[0] if regions else None)
    if not region:
        return []

    cols: list[Collection] = []
    seen: set[str] = set()
    for opp in region.get("opportunities", []):
        col = build_collection(opp)
        if not col.handle or col.handle in seen or not col.products:
            continue
        seen.add(col.handle)
        cols.append(col)
        if len(cols) >= limit:
            break
    return cols
