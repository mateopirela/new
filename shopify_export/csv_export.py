"""Genera CSV importables en Shopify (Productos > Importar).

Notas sobre Shopify:
  - El import nativo de productos NO asigna colecciones. Por eso cada producto
    lleva en `Tags` el nombre de la oportunidad y `coleccion:<handle>`, de modo
    que luego puedas crear *colecciones automáticas (smart collections)* por
    etiqueta con un par de clics. (El sync por Admin API sí crea las colecciones.)
  - Los precios van en la moneda de la tienda (configúrala en COP).
"""
from __future__ import annotations

import csv
import os

from .config import ShopifySettings
from .products import Collection

# Columnas estándar de la plantilla de importación de productos de Shopify.
COLUMNS = [
    "Handle", "Title", "Body (HTML)", "Vendor", "Product Category", "Type", "Tags",
    "Published", "Option1 Name", "Option1 Value", "Variant SKU",
    "Variant Inventory Tracker", "Variant Inventory Qty", "Variant Inventory Policy",
    "Variant Fulfillment Service", "Variant Price", "Variant Compare At Price",
    "Variant Requires Shipping", "Variant Taxable", "Image Src", "Image Position",
    "Image Alt Text", "SEO Title", "SEO Description", "Status",
]


def _row(col: Collection, product, settings: ShopifySettings) -> dict:
    published = "TRUE" if settings.product_status == "active" else "FALSE"
    return {
        "Handle": product.handle,
        "Title": product.title,
        "Body (HTML)": product.body_html,
        "Vendor": settings.vendor,
        "Product Category": col.category_label,
        "Type": col.category_label,
        "Tags": ", ".join(product.tags),
        "Published": published,
        "Option1 Name": "Title",
        "Option1 Value": "Default Title",
        "Variant SKU": product.sku,
        "Variant Inventory Tracker": "shopify",
        "Variant Inventory Qty": settings.inventory_qty,
        "Variant Inventory Policy": "deny",
        "Variant Fulfillment Service": "manual",
        "Variant Price": f"{product.price}.00",
        "Variant Compare At Price": f"{product.compare_at}.00",
        "Variant Requires Shipping": "TRUE",
        "Variant Taxable": "TRUE",
        "Image Src": "",          # sin imagen real: añádela en Shopify o vía proveedor
        "Image Position": "",
        "Image Alt Text": product.title,
        "SEO Title": f"{product.title} | {col.title}",
        "SEO Description": f"Compra {product.title} en tendencia. {col.description}"[:320],
        "Status": settings.product_status,
    }


def write_csv(path: str, collections: list[Collection], settings: ShopifySettings) -> int:
    """Escribe un CSV con todos los productos. Devuelve el nº de filas."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    rows = 0
    with open(path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=COLUMNS)
        writer.writeheader()
        for col in collections:
            for product in col.products:
                writer.writerow(_row(col, product, settings))
                rows += 1
    return rows


def write_all(collections: list[Collection], settings: ShopifySettings) -> dict:
    """Escribe el CSV global y uno por colección. Devuelve un resumen."""
    out_dir = settings.output_dir
    os.makedirs(out_dir, exist_ok=True)
    total = write_csv(os.path.join(out_dir, "productos.csv"), collections, settings)
    per_collection = {}
    for col in collections:
        path = os.path.join(out_dir, f"{col.handle}.csv")
        per_collection[col.handle] = write_csv(path, [col], settings)
    return {"total_products": total, "collections": per_collection}
