// @ts-check
import { defineConfig } from 'astro/config';

// `site` y `base` se pueden sobreescribir por entorno para desplegar en
// GitHub Pages (subcarpeta) o en un dominio propio.
export default defineConfig({
  site: process.env.SITE_URL || 'https://example.com',
  base: process.env.SITE_BASE || '/',
  output: 'static',
  build: {
    // Cada tienda y cada producto queda en su propia carpeta /<slug>/index.html,
    // de modo que una tienda es un sub-sitio autocontenido y desplegable aparte.
    format: 'directory',
  },
});
