# 📊 Agente de tendencias y oportunidades de dropshipping

Agente que **cada día** analiza las búsquedas más populares en Google Trends,
muestra **cómo se distribuyen geográficamente** dentro del país y genera un
**informe en Markdown** con qué está en tendencia y **qué productos se pueden
vender por dropshipping** en cada región.

Foco actual: **🇨🇴 Colombia** (configurable a otros mercados).

---

## ¿Cómo funciona?

```
Google Trends RSS  ──►  collect.py   (tendencias del día + tráfico + noticias)
        │
        ├─ pytrends ─►  interest_by_region   (desglose por departamentos)
        │               related_queries      (búsquedas relacionadas)
        ▼
   analyze.py   ──►  clasifica por categoría y estima potencial dropshipping (0-100)
        ▼
   llm.py (opcional, Claude)  ──►  análisis estratégico redactado
        ▼
   report.py    ──►  reports/AAAA-MM-DD.md  +  reports/latest.md
```

1. **Recolección** — feed RSS *Trending Now* de Google Trends (gratis, sin API key).
2. **Distribución geográfica** — para las tendencias top, `pytrends` calcula en
   qué regiones/departamentos se busca más cada término.
3. **Análisis dropshipping** — clasificador heurístico por categorías
   (tecnología, belleza, hogar, fitness, moda, mascotas…) que estima el
   potencial y sugiere productos concretos vendibles.
4. **Análisis con IA (opcional)** — si defines `ANTHROPIC_API_KEY`, Claude
   redacta recomendaciones estratégicas más finas. Sin clave, funciona igual
   con el motor heurístico.
5. **Informe** — Markdown versionado en `reports/`.

> ⚠️ **Importante sobre la red:** Google Trends **no es accesible** desde el
> sandbox de desarrollo de Claude (la política de egreso lo bloquea). Por eso
> el agente está pensado para ejecutarse en **GitHub Actions**, donde sí hay
> acceso a internet. El fetch real ocurre en el cron diario.

---

## Ejecución

### Local

```bash
pip install -r requirements.txt
python -m trends_agent.main            # informe de hoy para Colombia
TRENDS_REGIONS=CO,MX python -m trends_agent.main
```

### Automática (GitHub Actions)

El workflow [`.github/workflows/daily-trends.yml`](.github/workflows/daily-trends.yml)
corre **todos los días a las 12:00 UTC (07:00 Colombia)**, genera el informe y
lo commitea en `reports/`. También se puede lanzar a mano desde la pestaña
**Actions → Informe diario de tendencias → Run workflow**.

Para activar el análisis con IA: añade el secret `ANTHROPIC_API_KEY` en
*Settings → Secrets and variables → Actions*.

---

## Configuración (variables de entorno)

| Variable | Por defecto | Descripción |
|----------|-------------|-------------|
| `TRENDS_REGIONS` | `CO` | Regiones a analizar (`CO,MX,AR,ES,CL,PE,US`). |
| `TRENDS_MAX` | `20` | Nº máximo de tendencias por región. |
| `TRENDS_GEO_TOP` | `8` | Nº de tendencias top con desglose geográfico. |
| `TRENDS_OUTPUT_DIR` | `reports` | Carpeta de salida. |
| `TRENDS_USE_LLM` | `auto` | `off` para desactivar la IA aunque haya clave. |
| `TRENDS_LLM_MODEL` | `claude-haiku-4-5-20251001` | Modelo de Claude a usar. |
| `ANTHROPIC_API_KEY` | — | Clave para el análisis con IA (opcional). |

---

## Pruebas

```bash
python -m tests.test_pipeline     # pruebas offline con datos de muestra
```

Las pruebas no tocan la red: usan un feed RSS de ejemplo en
`tests/fixtures/`.

---

## Estructura

```
trends_agent/
  config.py     catálogo de regiones y ajustes
  collect.py    descarga y parseo de Google Trends (+ geo con pytrends)
  analyze.py    clasificación heurística y oportunidades de dropshipping
  llm.py        análisis estratégico opcional con Claude
  report.py     generación del informe Markdown
  main.py       orquestación / entrypoint
shopify_export/
  config.py     ajustes (vendor, estado, credenciales API)
  products.py   oportunidades -> colecciones y productos (precios COP)
  csv_export.py CSV importables en Shopify
  admin_api.py  sync opcional vía Shopify Admin API
  main.py       orquestación / entrypoint
.github/workflows/daily-trends.yml   cron diario (agente 1 + agente 2)
reports/        informes generados (AAAA-MM-DD.md + .json + latest.*)
shopify/        CSV generados (productos.csv + uno por colección)
tests/          pruebas offline + fixtures
```

---

## 🛍️ Agente 2 — Exportador a Shopify

Un segundo agente lee el informe estructurado (`reports/latest.json`) y vuelca
las oportunidades a **Shopify**: cada **oportunidad** se convierte en una
**colección** y cada **idea de producto** en un **producto** con su precio en COP.

```
reports/latest.json  ──►  shopify_export  ──►  shopify/productos.csv      (importable en Shopify)
                                               shopify/<oportunidad>.csv   (un CSV por colección)
                                          └──► (opcional) Admin API: crea colecciones + productos
```

Dos vías, según lo que tengas listo:

| Vía | Requiere | Cuándo |
|-----|----------|--------|
| **CSV de importación** | nada | Empezar ya: *Shopify → Productos → Importar*. |
| **Admin API (auto)** | `SHOPIFY_STORE` + `SHOPIFY_ACCESS_TOKEN` | Sync diario sin intervención. |

### Generar los CSV (local)

```bash
pip install -r requirements.txt
python -m shopify_export.main            # genera shopify/*.csv
python -m shopify_export.main --sync     # además crea todo vía Admin API
```

### Configuración (entorno / Variables y Secrets del repo)

| Variable | Por defecto | Descripción |
|----------|-------------|-------------|
| `SHOPIFY_VENDOR` | `Tendencias CO` | Nombre del *vendor* en Shopify. |
| `SHOPIFY_PRODUCT_STATUS` | `draft` | `draft` o `active` al importar/crear. |
| `SHOPIFY_INVENTORY_QTY` | `100` | Inventario inicial por producto. |
| `SHOPIFY_MAX_COLLECTIONS` | `10` | Máx. oportunidades a exportar. |
| `STORE_REGION` | (1ª del informe) | Región del informe a usar. |
| `SHOPIFY_STORE` *(secret)* | — | Dominio `mitienda.myshopify.com` (para `--sync`). |
| `SHOPIFY_ACCESS_TOKEN` *(secret)* | — | Token de Admin API (para `--sync`). |

### Cómo obtener el token de Admin API

1. En Shopify: *Configuración → Aplicaciones y canales de venta → Desarrollar apps*.
2. *Crear una app* → *Configurar Admin API scopes*: marca `write_products`,
   `write_inventory` y `write_publications` (colecciones).
3. *Instalar app* y copia el **Admin API access token**.
4. Guárdalo como secret del repo `SHOPIFY_ACCESS_TOKEN` y el dominio como `SHOPIFY_STORE`.

> **Colecciones en el CSV:** el import nativo de Shopify no asigna colecciones,
> así que cada producto lleva la etiqueta `coleccion:<handle>` y el nombre de la
> oportunidad en *Tags*. Crea **colecciones automáticas por etiqueta** en 2 clics,
> o usa `--sync` (la Admin API sí crea las colecciones).
>
> **Imágenes:** el CSV deja `Image Src` vacío (no hay imagen real de proveedor).
> Añádelas en Shopify o conecta un proveedor (ver próximos pasos).

### Automático (GitHub Actions)

El workflow [`daily-trends.yml`](.github/workflows/daily-trends.yml) ejecuta el
agente 1 y, a continuación, el agente 2: genera los CSV y los commitea. Si defines
los secrets `SHOPIFY_STORE` y `SHOPIFY_ACCESS_TOKEN`, además sincroniza por API.

---

## Próximos pasos sugeridos

- Añadir más regiones y comparativas entre países.
- Cruzar con catálogos de proveedores (AliExpress/CJ) para **imágenes y stock reales**.
- Copys de producto generados con IA (Claude) por colección.
- Enviar el informe por email o publicarlo vía Metricool/n8n.
