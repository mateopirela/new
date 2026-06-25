"""Análisis heurístico de tendencias para detectar oportunidades de dropshipping.

No depende de ninguna IA: clasifica cada tendencia por categoría temática,
estima un "potencial dropshipping" y propone productos vendibles. Es el motor
de respaldo cuando no hay clave de Anthropic, y también enriquece el contexto
que se le pasa al LLM cuando sí la hay.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

from .collect import Trend


# ---------------------------------------------------------------------------
# Diccionario de categorías -> (palabras clave, potencial base, ideas de producto)
#
# El "potencial base" (0-100) refleja cuán fácilmente una tendencia de ese tipo
# se traduce en un producto físico vendible por dropshipping.
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Category:
    key: str
    label: str
    keywords: tuple[str, ...]
    base_score: int
    product_ideas: tuple[str, ...]


CATEGORIES: tuple[Category, ...] = (
    Category("tech", "Tecnología y gadgets",
             ("iphone", "samsung", "xiaomi", "celular", "smartphone", "laptop", "pc",
              "audifonos", "auriculares", "smartwatch", "reloj inteligente", "tablet",
              "drone", "camara", "consola", "playstation", "xbox", "nintendo", "parlante",
              "bluetooth", "cargador", "powerbank", "gadget"),
             85,
             ("Audífonos inalámbricos / TWS", "Smartwatch económico", "Cargadores y power banks",
              "Soportes y accesorios para celular", "Mini proyectores y parlantes bluetooth")),
    Category("beauty", "Belleza y cuidado personal",
             ("maquillaje", "labial", "skincare", "crema", "serum", "perfume", "cabello",
              "shampoo", "uñas", "depilacion", "facial", "cosmetico", "belleza"),
             88,
             ("Rizadores / alisadores de cabello", "Sets de skincare y serums", "Organizadores de maquillaje",
              "Dispositivos de limpieza facial", "Kits de manicura")),
    Category("home", "Hogar y cocina",
             ("cocina", "hogar", "decoracion", "lampara", "organizador", "freidora", "airfryer",
              "licuadora", "sabanas", "almohada", "cortina", "mueble", "limpieza", "jardin"),
             82,
             ("Freidoras de aire y accesorios", "Organizadores de cocina y closet", "Lámparas LED decorativas",
              "Gadgets de limpieza para el hogar", "Textiles: sábanas / cojines")),
    Category("fitness", "Fitness y bienestar",
             ("gym", "gimnasio", "fitness", "ejercicio", "yoga", "proteina", "pesas", "correr",
              "bicicleta", "deporte", "musculacion", "adelgazar", "dieta"),
             80,
             ("Bandas y mini equipos de resistencia", "Botellas y shakers", "Ropa deportiva / leggings",
              "Smart bands para actividad", "Esterillas de yoga")),
    Category("fashion", "Moda y accesorios",
             ("ropa", "zapatos", "tenis", "vestido", "moda", "bolso", "gafas", "joyeria",
              "reloj", "cartera", "chaqueta", "sudadera", "accesorios"),
             78,
             ("Gafas de sol de moda", "Bisutería y accesorios", "Bolsos y riñoneras de tendencia",
              "Relojes de moda económicos", "Prendas virales de temporada")),
    Category("baby_pets", "Bebés y mascotas",
             ("bebe", "pañal", "coche bebe", "mascota", "perro", "gato", "juguete perro",
              "comedero", "correa", "acuario"),
             83,
             ("Juguetes y accesorios para mascotas", "Comederos automáticos", "Productos de aseo para mascotas",
              "Accesorios para bebé", "Organizadores infantiles")),
    Category("seasonal", "Estacional y eventos",
             ("navidad", "halloween", "amor y amistad", "dia de la madre", "dia del padre",
              "san valentin", "black friday", "regalo", "disfraz", "fiesta"),
             75,
             ("Decoración temática de temporada", "Disfraces y accesorios", "Sets de regalo",
              "Luces y adornos LED", "Empaques y detalles personalizados")),
    Category("gaming", "Gaming",
             ("gamer", "gaming", "videojuego", "free fire", "fortnite", "roblox", "minecraft",
              "teclado", "mouse gamer", "stream", "twitch"),
             72,
             ("Periféricos gamer (mouse/teclado)", "Sillas y soportes para setup", "Luces RGB",
              "Controles y accesorios de consola", "Merchandising de juegos populares")),
    # Categorías de bajo potencial directo (noticias, deporte-evento, farándula, política)
    Category("sports_event", "Deporte / evento", (
        "vs", "partido", "champions", "mundial", "liga", "seleccion", "futbol", "gol",
        "nba", "tenis", "f1", "copa", "eliminatorias"), 35,
        ("Camisetas y merch del equipo/jugador", "Banderas y accesorios de hincha",
         "Productos temáticos del evento")),
    Category("entertainment", "Entretenimiento / farándula", (
        "pelicula", "serie", "netflix", "concierto", "cantante", "actor", "actriz",
        "novela", "premios", "tour", "album", "reggaeton"), 40,
        ("Merch del artista/película", "Pósters y coleccionables", "Accesorios temáticos de fans")),
    Category("news", "Noticias / actualidad", (
        "presidente", "gobierno", "elecciones", "paro", "clima", "lluvia", "sismo",
        "dolar", "economia", "muere", "murio", "accidente", "petro"), 10,
        ()),
)

_DEFAULT = Category("other", "Otros", (), 30, ())


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", text).strip()


@dataclass
class Analysis:
    trend: Trend
    category: Category
    score: int                      # potencial dropshipping 0-100
    product_ideas: list[str] = field(default_factory=list)
    rationale: str = ""

    @property
    def is_opportunity(self) -> bool:
        return self.score >= 55 and bool(self.product_ideas)


def _classify(text: str) -> Category:
    """Asigna la categoría cuya palabra clave aparece (la más específica gana)."""
    norm = _normalize(text)
    best: Category | None = None
    best_len = 0
    for cat in CATEGORIES:
        for kw in cat.keywords:
            if re.search(rf"\b{re.escape(kw)}\b", norm) and len(kw) > best_len:
                best, best_len = cat, len(kw)
    return best or _DEFAULT


def analyze_trend(trend: Trend) -> Analysis:
    # El término y los titulares de noticias dan contexto para clasificar mejor.
    haystack = " ".join([trend.term, *trend.news_titles, *trend.related_queries])
    cat = _classify(haystack)

    score = cat.base_score
    # Ajuste por volumen de búsqueda: más tráfico => más demanda potencial.
    if trend.traffic_value >= 200_000:
        score += 10
    elif trend.traffic_value >= 50_000:
        score += 5
    # Señales de intención de compra en noticias / queries relacionadas.
    buy_signals = ("precio", "comprar", "oferta", "descuento", "donde", "barato", "review", "vs")
    norm = _normalize(haystack)
    if any(sig in norm for sig in buy_signals):
        score += 5
    score = max(0, min(100, score))

    ideas = list(cat.product_ideas) if score >= 55 else []
    rationale = _build_rationale(trend, cat, score)
    return Analysis(trend=trend, category=cat, score=score, product_ideas=ideas, rationale=rationale)


def _build_rationale(trend: Trend, cat: Category, score: int) -> str:
    if cat.key == "news":
        return "Tendencia de actualidad/noticias: alto volumen pero baja intención de compra directa."
    if score >= 70:
        return (f"Categoría '{cat.label}' con buena traducción a producto físico y "
                f"demanda visible (tráfico ~{trend.approx_traffic or 'n/d'}).")
    if score >= 55:
        return f"Oportunidad moderada en '{cat.label}'; validar competencia y margen."
    if cat.key in ("sports_event", "entertainment"):
        return ("Evento/farándula: la venta directa es limitada, pero hay nicho de "
                "merch o productos temáticos para fans.")
    return "Bajo encaje con dropshipping; útil más como señal de interés cultural."


def analyze_region(trends: list[Trend]) -> list[Analysis]:
    return [analyze_trend(t) for t in trends]


def top_opportunities(analyses: list[Analysis], limit: int = 8) -> list[Analysis]:
    opps = [a for a in analyses if a.is_opportunity]
    opps.sort(key=lambda a: (a.score, a.trend.traffic_value), reverse=True)
    return opps[:limit]
