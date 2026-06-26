"""Configuración del exportador a Shopify."""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class ShopifySettings:
    # Informe estructurado que produce el agente 1.
    report_json: str = os.getenv("STORE_REPORT_JSON", "reports/latest.json")
    # Carpeta de salida de los CSV.
    output_dir: str = os.getenv("SHOPIFY_OUTPUT_DIR", "shopify")
    # Marca / vendor por defecto en Shopify.
    vendor: str = os.getenv("SHOPIFY_VENDOR", "Tendencias CO")
    # Nº máximo de colecciones (oportunidades) a exportar.
    max_collections: int = int(os.getenv("SHOPIFY_MAX_COLLECTIONS", "10"))
    # Región del informe a usar (código). Vacío = primera disponible.
    region_code: str = os.getenv("STORE_REGION", "")
    # Inventario inicial por producto.
    inventory_qty: int = int(os.getenv("SHOPIFY_INVENTORY_QTY", "100"))
    # Estado de los productos importados: 'active' o 'draft'.
    product_status: str = os.getenv("SHOPIFY_PRODUCT_STATUS", "draft")

    # --- Admin API (opcional) ---
    shop_domain: str | None = os.getenv("SHOPIFY_STORE") or None        # ej. mitienda.myshopify.com
    access_token: str | None = os.getenv("SHOPIFY_ACCESS_TOKEN") or None
    api_version: str = os.getenv("SHOPIFY_API_VERSION", "2024-10")

    @property
    def api_enabled(self) -> bool:
        return bool(self.shop_domain and self.access_token)
