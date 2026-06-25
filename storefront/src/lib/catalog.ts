// Metadatos por categoría: estética y rangos de precio (COP) para los productos
// que se derivan de cada oportunidad del informe.
export interface CategoryMeta {
  color: string;       // color de marca de la tienda
  accent: string;      // color de acento
  emoji: string;
  tagline: string;
  priceMin: number;
  priceMax: number;
  benefits: string[];
}

export const CATEGORY_META: Record<string, CategoryMeta> = {
  tech: {
    color: '#0f172a', accent: '#38bdf8', emoji: '🎧',
    tagline: 'Tecnología que se vende sola',
    priceMin: 49900, priceMax: 259900,
    benefits: ['Envío a todo el país', 'Garantía de 30 días', 'Pago contra entrega'],
  },
  beauty: {
    color: '#831843', accent: '#f472b6', emoji: '✨',
    tagline: 'Belleza que está en tendencia',
    priceMin: 24900, priceMax: 129900,
    benefits: ['Productos virales', 'Envío discreto', 'Pago contra entrega'],
  },
  home: {
    color: '#1c1917', accent: '#f59e0b', emoji: '🏠',
    tagline: 'Tu hogar, más práctico',
    priceMin: 39900, priceMax: 299900,
    benefits: ['Envío a todo el país', 'Devolución fácil', 'Pago contra entrega'],
  },
  fitness: {
    color: '#064e3b', accent: '#34d399', emoji: '💪',
    tagline: 'Entrena donde quieras',
    priceMin: 29900, priceMax: 159900,
    benefits: ['Resultados visibles', 'Envío rápido', 'Pago contra entrega'],
  },
  fashion: {
    color: '#1e1b4b', accent: '#a78bfa', emoji: '👜',
    tagline: 'La moda del momento',
    priceMin: 29900, priceMax: 149900,
    benefits: ['Tendencias virales', 'Cambios fáciles', 'Pago contra entrega'],
  },
  baby_pets: {
    color: '#7c2d12', accent: '#fb923c', emoji: '🐾',
    tagline: 'Lo mejor para los que más quieres',
    priceMin: 24900, priceMax: 119900,
    benefits: ['Calidad garantizada', 'Envío rápido', 'Pago contra entrega'],
  },
  seasonal: {
    color: '#7f1d1d', accent: '#f87171', emoji: '🎁',
    tagline: 'Por tiempo limitado',
    priceMin: 19900, priceMax: 99900,
    benefits: ['Edición de temporada', 'Stock limitado', 'Pago contra entrega'],
  },
  gaming: {
    color: '#111827', accent: '#22d3ee', emoji: '🎮',
    tagline: 'Sube de nivel tu setup',
    priceMin: 49900, priceMax: 349900,
    benefits: ['Para gamers', 'Envío rápido', 'Pago contra entrega'],
  },
  default: {
    color: '#0f172a', accent: '#6366f1', emoji: '🛍️',
    tagline: 'Lo que todos están buscando',
    priceMin: 29900, priceMax: 149900,
    benefits: ['Envío a todo el país', 'Garantía', 'Pago contra entrega'],
  },
};

export function categoryMeta(key: string): CategoryMeta {
  return CATEGORY_META[key] ?? CATEGORY_META.default;
}
