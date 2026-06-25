// Configuración de la tienda, parametrizable por variables de entorno en build.
export const config = {
  brandSuffix: process.env.STORE_BRAND_SUFFIX ?? 'Store',
  whatsappNumber: process.env.STORE_WHATSAPP ?? '573000000000',
  currencySymbol: process.env.STORE_CURRENCY_SYMBOL ?? '$',
  currencyCode: process.env.STORE_CURRENCY ?? 'COP',
  // Nº máximo de tiendas a generar (las de mayor potencial).
  maxStores: Number(process.env.STORE_MAX ?? '10'),
  base: process.env.SITE_BASE ?? '/',
};

// Une la base del sitio con una ruta relativa, evitando dobles barras.
export function withBase(path: string): string {
  const b = config.base.endsWith('/') ? config.base.slice(0, -1) : config.base;
  const p = path.startsWith('/') ? path : `/${path}`;
  return `${b}${p}`;
}
