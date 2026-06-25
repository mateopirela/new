import { config } from './config';

// Slug URL-safe a partir de un texto en español (quita acentos y símbolos).
export function slugify(text: string): string {
  return text
    .normalize('NFKD')
    .replace(/[̀-ͯ]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/(^-|-$)/g, '');
}

// Hash determinista (FNV-1a de 32 bits) para precios reproducibles por nombre.
export function hash32(str: string): number {
  let h = 0x811c9dc5;
  for (let i = 0; i < str.length; i++) {
    h ^= str.charCodeAt(i);
    h = Math.imul(h, 0x01000193);
  }
  return h >>> 0;
}

// Formatea un precio entero (COP) -> "$ 79.900".
export function formatPrice(value: number): string {
  const s = Math.round(value)
    .toString()
    .replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  return `${config.currencySymbol} ${s}`;
}

// Construye el enlace de pedido por WhatsApp con mensaje prellenado.
export function whatsappLink(storeName: string, productName: string, price: string): string {
  const msg =
    `¡Hola ${storeName}! 👋 Quiero pedir este producto:\n\n` +
    `• ${productName}\n• Precio: ${price}\n\n¿Me ayudas con el envío?`;
  return `https://wa.me/${config.whatsappNumber}?text=${encodeURIComponent(msg)}`;
}
