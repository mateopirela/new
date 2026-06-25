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

## Próximos pasos sugeridos

- Añadir más regiones y comparativas entre países.
- Cruzar con catálogos de proveedores (AliExpress/CJ) para validar disponibilidad.
- Enviar el informe por email o publicarlo vía Metricool/n8n.
