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
.github/workflows/daily-trends.yml   cron diario
reports/        informes generados (AAAA-MM-DD.md + latest.md)
tests/          pruebas offline + fixtures
```

---

## 🏪 Agente 2 — Constructor de tiendas (Astro)

Un segundo agente lee el informe estructurado (`reports/latest.json`) y genera,
**con una plantilla de framework (Astro)**, una **tienda e-commerce por cada
oportunidad** de dropshipping, con **pedido por WhatsApp**.

```
reports/latest.json  ──►  storefront/ (Astro)  ──►  dist/
                                                     ├─ index.html              (directorio de tiendas)
                                                     ├─ audifonos-inalambricos/ (tienda autocontenida)
                                                     │    ├─ index.html
                                                     │    └─ <producto>/index.html
                                                     ├─ serum-facial-vitamina-c/...
                                                     └─ freidora-de-aire/...
```

Cada oportunidad se convierte en una mini-tienda de nicho:
- **Marca y estética por categoría** (color, emoji, tagline).
- **Productos** derivados de las ideas del informe, con **precio en COP**
  (determinista), precio tachado y % de descuento.
- **Imágenes** SVG autocontenidas (sin peticiones externas).
- **Botón "Pedir por WhatsApp"** con mensaje prellenado (producto + precio).
- **Bloque geográfico** con dónde se busca más cada término.

Cada carpeta `dist/<slug>/` es un **sub-sitio independiente**: puedes desplegar
todo `dist/` junto o copiar una sola tienda a su propio dominio.

### Construir las tiendas (local)

```bash
cd storefront
npm install
STORE_WHATSAPP=573001112233 STORE_BRAND_SUFFIX="Store" npm run build
npm run preview          # vista previa local
```

### Configuración (entorno)

| Variable | Por defecto | Descripción |
|----------|-------------|-------------|
| `STORE_WHATSAPP` | `573000000000` | Número de WhatsApp (formato internacional, solo dígitos). |
| `STORE_BRAND_SUFFIX` | `Store` | Sufijo del nombre de cada tienda. |
| `STORE_MAX` | `10` | Nº máximo de tiendas a generar. |
| `STORE_REGION` | (1ª del informe) | Código de región del informe a usar. |
| `SITE_BASE` / `SITE_URL` | `/` | Base/URL para el despliegue (las pone GitHub Pages). |

### Despliegue automático (GitHub Pages)

[`.github/workflows/build-stores.yml`](.github/workflows/build-stores.yml) se
dispara cuando el agente 1 actualiza `reports/`, construye las tiendas y las
publica en **GitHub Pages**. Para activarlo:

1. *Settings → Pages → Source: GitHub Actions*.
2. *Settings → Variables → Actions*: define `STORE_WHATSAPP`, `STORE_BRAND_SUFFIX`, etc.

> Conexión con **Shopify**: la arquitectura deja la puerta abierta. Se puede
> añadir un exportador CSV (importable en *Shopify → Productos → Importar*) o un
> sincronizador vía Shopify Admin API como paso adicional del agente 2.

---

## Próximos pasos sugeridos

- Añadir más regiones y comparativas entre países.
- Cruzar con catálogos de proveedores (AliExpress/CJ) para validar disponibilidad.
- **Conector Shopify** (CSV o Admin API) para el agente 2.
- Copys de producto generados con IA (Claude) por tienda.
- Enviar el informe por email o publicarlo vía Metricool/n8n.
