import reportData from '../../../reports/latest.json';
import { config } from './config';
import { categoryMeta, type CategoryMeta } from './catalog';
import { hash32, slugify, formatPrice } from './format';

// ---- Tipos del informe que produce el agente analista (reports/latest.json) ----
interface ReportOpportunity {
  term: string;
  category_key: string;
  category_label: string;
  score: number;
  approx_traffic: string;
  rationale: string;
  product_ideas: string[];
  related_queries: string[];
  geo_breakdown: Record<string, number>;
}
interface ReportRegion {
  code: string;
  name: string;
  opportunities: ReportOpportunity[];
}
interface Report {
  date: string;
  regions: ReportRegion[];
}

// ---- Modelo de tienda/producto que consume la plantilla ----
export interface Product {
  name: string;
  slug: string;
  price: number;
  priceLabel: string;
  compareAt: number;
  compareAtLabel: string;
  discountPct: number;
  description: string;
  image: string; // data-URI SVG autocontenido
}
export interface Store {
  slug: string;
  name: string;
  term: string;
  categoryKey: string;
  categoryLabel: string;
  meta: CategoryMeta;
  score: number;
  approxTraffic: string;
  rationale: string;
  geo: Record<string, number>;
  relatedQueries: string[];
  products: Product[];
}

const report = reportData as unknown as Report;

function priceFor(meta: CategoryMeta, seedKey: string): number {
  const span = meta.priceMax - meta.priceMin;
  const raw = meta.priceMin + (hash32(seedKey) % span);
  // Redondea a terminación .900 (precio psicológico típico en CO).
  return Math.max(meta.priceMin, Math.round(raw / 1000) * 1000 - 100);
}

function describe(productName: string, term: string, label: string): string {
  return (
    `${productName} en tendencia: una de las búsquedas que más está creciendo ` +
    `en la categoría de ${label.toLowerCase()}. Aprovecha el interés por "${term}" ` +
    `con un producto de alta demanda, listo para envío a todo el país.`
  );
}

// Genera una imagen SVG autocontenida (sin peticiones externas) con el nombre.
function placeholderImage(name: string, meta: CategoryMeta): string {
  const initials = name
    .split(/\s+/)
    .slice(0, 2)
    .map((w) => w[0]?.toUpperCase() ?? '')
    .join('');
  const svg =
    `<svg xmlns="http://www.w3.org/2000/svg" width="600" height="600" viewBox="0 0 600 600">` +
    `<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">` +
    `<stop offset="0" stop-color="${meta.color}"/>` +
    `<stop offset="1" stop-color="${meta.accent}"/></linearGradient></defs>` +
    `<rect width="600" height="600" fill="url(#g)"/>` +
    `<text x="300" y="300" font-family="Arial, sans-serif" font-size="160" ` +
    `font-weight="bold" fill="#ffffff" fill-opacity="0.92" text-anchor="middle" ` +
    `dominant-baseline="central">${meta.emoji}</text>` +
    `<text x="300" y="470" font-family="Arial, sans-serif" font-size="42" ` +
    `fill="#ffffff" fill-opacity="0.85" text-anchor="middle">${initials}</text></svg>`;
  return `data:image/svg+xml,${encodeURIComponent(svg)}`;
}

function buildProducts(opp: ReportOpportunity, meta: CategoryMeta): Product[] {
  const ideas = opp.product_ideas.length ? opp.product_ideas : [opp.term];
  return ideas.map((name) => {
    const price = priceFor(meta, name + opp.term);
    const compareAt = Math.round((price * 1.6) / 1000) * 1000 - 100;
    const discountPct = Math.round((1 - price / compareAt) * 100);
    return {
      name,
      slug: slugify(name),
      price,
      priceLabel: formatPrice(price),
      compareAt,
      compareAtLabel: formatPrice(compareAt),
      discountPct,
      description: describe(name, opp.term, opp.category_label),
      image: placeholderImage(name, meta),
    };
  });
}

function buildStore(opp: ReportOpportunity): Store {
  const meta = categoryMeta(opp.category_key);
  const term = opp.term.trim();
  const name = `${term.charAt(0).toUpperCase()}${term.slice(1)} ${config.brandSuffix}`;
  return {
    slug: slugify(term),
    name,
    term,
    categoryKey: opp.category_key,
    categoryLabel: opp.category_label,
    meta,
    score: opp.score,
    approxTraffic: opp.approx_traffic,
    rationale: opp.rationale,
    geo: opp.geo_breakdown ?? {},
    relatedQueries: opp.related_queries ?? [],
    products: buildProducts(opp, meta),
  };
}

function pickRegion(): ReportRegion | undefined {
  const wanted = process.env.STORE_REGION;
  if (wanted) {
    const found = report.regions.find((r) => r.code === wanted);
    if (found) return found;
  }
  return report.regions[0];
}

// Lista de tiendas a generar (deduplicadas por slug, top por potencial).
export function getStores(): Store[] {
  const region = pickRegion();
  if (!region) return [];
  const seen = new Set<string>();
  const stores: Store[] = [];
  for (const opp of region.opportunities) {
    const store = buildStore(opp);
    if (seen.has(store.slug)) continue;
    seen.add(store.slug);
    stores.push(store);
    if (stores.length >= config.maxStores) break;
  }
  return stores;
}

export function getReportDate(): string {
  return report.date;
}
export function getRegionName(): string {
  return pickRegion()?.name ?? '';
}
