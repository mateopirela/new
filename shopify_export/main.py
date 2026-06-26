"""Punto de entrada del agente 2 (Shopify).

Uso:
    python -m shopify_export.main            # genera los CSV de importación
    python -m shopify_export.main --sync     # además crea todo vía Admin API
                                             # (requiere SHOPIFY_STORE y _ACCESS_TOKEN)
"""
from __future__ import annotations

import sys

from . import admin_api, csv_export
from .config import ShopifySettings
from .products import load_collections


def run(do_sync: bool = False, settings: ShopifySettings | None = None) -> dict:
    settings = settings or ShopifySettings()
    cols = load_collections(settings.report_json, settings.region_code, settings.max_collections)

    if not cols:
        print("[shopify] No hay oportunidades en el informe.", file=sys.stderr)
        return {"collections": 0}

    result = csv_export.write_all(cols, settings)
    print(
        f"[shopify] {len(cols)} colecciones, {result['total_products']} productos "
        f"-> {settings.output_dir}/productos.csv (+ CSV por colección)",
        file=sys.stderr,
    )

    if do_sync:
        if not settings.api_enabled:
            print("[shopify] --sync ignorado: faltan SHOPIFY_STORE / SHOPIFY_ACCESS_TOKEN.",
                  file=sys.stderr)
        else:
            summary = admin_api.sync(cols, settings)
            print(f"[shopify] Sync API: {summary['collections']} colecciones, "
                  f"{summary['products']} productos, {len(summary['errors'])} errores.",
                  file=sys.stderr)
            for e in summary["errors"][:10]:
                print(f"   - {e}", file=sys.stderr)
            result["api"] = summary

    return result


def main() -> int:
    do_sync = "--sync" in sys.argv[1:]
    try:
        run(do_sync=do_sync)
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"[shopify] ERROR fatal: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
