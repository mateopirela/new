"""Sincronización opcional con Shopify vía Admin API (REST).

Crea una colección personalizada por oportunidad y sus productos. Se activa solo
si están definidas SHOPIFY_STORE y SHOPIFY_ACCESS_TOKEN. No se puede probar desde
el sandbox (sin red); está pensado para ejecutarse en GitHub Actions.
"""
from __future__ import annotations

import time

import requests

from .config import ShopifySettings
from .products import Collection


class ShopifyAPI:
    def __init__(self, settings: ShopifySettings):
        self.s = settings
        self.base = f"https://{settings.shop_domain}/admin/api/{settings.api_version}"
        self.headers = {
            "X-Shopify-Access-Token": settings.access_token or "",
            "Content-Type": "application/json",
        }

    def _post(self, path: str, payload: dict) -> dict:
        resp = requests.post(f"{self.base}{path}", json=payload, headers=self.headers, timeout=30)
        # Respeta el rate-limit básico de Shopify (2 req/s en REST).
        if resp.status_code == 429:
            time.sleep(2)
            resp = requests.post(f"{self.base}{path}", json=payload, headers=self.headers, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def create_product(self, col: Collection, product) -> int:
        payload = {
            "product": {
                "title": product.title,
                "body_html": product.body_html,
                "vendor": self.s.vendor,
                "product_type": col.category_label,
                "handle": product.handle,
                "tags": ", ".join(product.tags),
                "status": self.s.product_status,
                "variants": [{
                    "price": f"{product.price}.00",
                    "compare_at_price": f"{product.compare_at}.00",
                    "sku": product.sku,
                    "inventory_management": "shopify",
                    "inventory_policy": "deny",
                }],
            }
        }
        data = self._post("/products.json", payload)
        return int(data["product"]["id"])

    def create_collection(self, col: Collection) -> int:
        payload = {"custom_collection": {"title": col.title, "body_html": col.description}}
        data = self._post("/custom_collections.json", payload)
        return int(data["custom_collection"]["id"])

    def add_to_collection(self, collection_id: int, product_id: int) -> None:
        self._post("/collects.json", {"collect": {
            "collection_id": collection_id, "product_id": product_id,
        }})


def sync(collections: list[Collection], settings: ShopifySettings) -> dict:
    """Crea colecciones y productos en Shopify. Devuelve un resumen."""
    api = ShopifyAPI(settings)
    summary = {"collections": 0, "products": 0, "errors": []}
    for col in collections:
        try:
            cid = api.create_collection(col)
            summary["collections"] += 1
        except Exception as exc:  # noqa: BLE001
            summary["errors"].append(f"colección '{col.title}': {exc}")
            continue
        for product in col.products:
            try:
                pid = api.create_product(col, product)
                api.add_to_collection(cid, pid)
                summary["products"] += 1
                time.sleep(0.6)  # margen para el rate-limit
            except Exception as exc:  # noqa: BLE001
                summary["errors"].append(f"producto '{product.title}': {exc}")
    return summary
