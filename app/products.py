PRODUCTS = [
    # Audio
    {"name": "Aurora Wireless Earbuds", "price": 59.99, "category": "Audio",
     "description": "Bluetooth 5.3 earbuds, 24h battery with case, water resistant.", "in_stock": True},
    {"name": "Bassline Over-Ear Headphones", "price": 119.99, "category": "Audio",
     "description": "Active noise cancelling, 40h battery, plush memory-foam cups.", "in_stock": True},
    {"name": "PocketBoom Bluetooth Speaker", "price": 44.99, "category": "Audio",
     "description": "Palm-sized speaker, IPX7 waterproof, 12h playtime.", "in_stock": True},
    {"name": "Echo Clip Mini Speaker", "price": 24.99, "category": "Audio",
     "description": "Ultra-compact clip-on speaker with carabiner, 6h playtime.", "in_stock": False},
    # Wearables
    {"name": "Pulse Smart Watch", "price": 129.99, "category": "Wearables",
     "description": "Heart-rate and sleep tracking, 7-day battery, built-in GPS.", "in_stock": True},
    {"name": "Zenith Fitness Band", "price": 49.99, "category": "Wearables",
     "description": "Slim activity band, step and heart-rate tracking, 10-day battery.", "in_stock": True},
    # Bags
    {"name": "Drifter Canvas Backpack", "price": 45.00, "category": "Bags",
     "description": "18L water-resistant canvas, padded 15\" laptop sleeve.", "in_stock": True},
    {"name": "Metro Messenger Bag", "price": 54.99, "category": "Bags",
     "description": "Slim commuter bag, fits 14\" laptop, magnetic flap closure.", "in_stock": True},
    {"name": "Trailhead 40L Duffel", "price": 69.99, "category": "Bags",
     "description": "Weatherproof travel duffel with stowable backpack straps.", "in_stock": False},
    # Footwear
    {"name": "Stride Running Sneakers", "price": 89.99, "category": "Footwear",
     "description": "Lightweight mesh upper, cushioned sole, sizes 6-12.", "in_stock": False},
    {"name": "CloudStep Walking Shoes", "price": 74.99, "category": "Footwear",
     "description": "Memory-foam insole, slip-resistant outsole, all-day comfort.", "in_stock": True},
    {"name": "Summit Trail Boots", "price": 109.99, "category": "Footwear",
     "description": "Waterproof hiking boots, ankle support, rugged grip.", "in_stock": True},
    # Home
    {"name": "Lumos LED Desk Lamp", "price": 24.99, "category": "Home",
     "description": "3 brightness levels, USB-C powered, adjustable arm.", "in_stock": True},
    {"name": "Terra Ceramic Mug", "price": 12.99, "category": "Home",
     "description": "350ml stoneware, microwave and dishwasher safe.", "in_stock": True},
    {"name": "Nimbus Knit Throw Blanket", "price": 27.99, "category": "Home",
     "description": "Soft knit, 50x60in, machine washable.", "in_stock": True},
    {"name": "Ember Soy Candle", "price": 18.99, "category": "Home",
     "description": "45h burn, cedar and vanilla scent, hand poured.", "in_stock": True},
    # Electronics
    {"name": "Clicky Mechanical Keyboard", "price": 74.99, "category": "Electronics",
     "description": "Hot-swappable switches, RGB backlight, compact 75% layout.", "in_stock": True},
    {"name": "Volt 10K Power Bank", "price": 39.99, "category": "Electronics",
     "description": "10,000mAh, USB-C PD 20W fast charging.", "in_stock": True},
    {"name": "Glide Wireless Mouse", "price": 29.99, "category": "Electronics",
     "description": "Silent clicks, 4000 DPI, USB-C rechargeable.", "in_stock": True},
    {"name": "SnapView 1080p Webcam", "price": 49.99, "category": "Electronics",
     "description": "Full HD webcam, auto light correction, dual mics.", "in_stock": False},
    # Fitness
    {"name": "Grippy Yoga Mat", "price": 29.99, "category": "Fitness",
     "description": "6mm non-slip TPE mat with carry strap.", "in_stock": True},
    {"name": "HydroCore Steel Bottle", "price": 19.99, "category": "Fitness",
     "description": "750ml, double-wall insulated, keeps cold 24h.", "in_stock": True},
    {"name": "IronFlex Resistance Bands", "price": 22.99, "category": "Fitness",
     "description": "Set of 5 latex bands, light to heavy, with door anchor.", "in_stock": True},
    {"name": "PowerGrip Dumbbell Set", "price": 64.99, "category": "Fitness",
     "description": "Adjustable 5-25lb pair, quick-lock plates.", "in_stock": False},
    # Accessories
    {"name": "Solstice Polarized Sunglasses", "price": 34.99, "category": "Accessories",
     "description": "Polarized UV400 lenses, unisex frame.", "in_stock": False},
    {"name": "Nomad Leather Wallet", "price": 39.99, "category": "Accessories",
     "description": "Full-grain leather, RFID blocking, 8 card slots.", "in_stock": True},
    {"name": "Chrono Minimalist Watch", "price": 89.99, "category": "Accessories",
     "description": "Sapphire glass, 40mm case, genuine leather strap.", "in_stock": True},
]


import re

_STOP = {"a", "an", "the", "for", "under", "below", "over", "with", "and", "or",
         "me", "i", "want", "need", "looking", "something", "some", "buy", "get",
         "what", "whats", "is", "are", "do", "you", "have", "any", "in", "stock",
         "cheap", "cheapest", "best", "good", "to", "of", "my", "on", "can"}


def _text(p: dict) -> str:
    return f"{p['name']} {p['category']} {p['description']}".lower()


def _price_cap(query: str) -> float | None:
    m = re.search(r"(?:under|below|less than|<|max)\s*\$?\s*(\d+(?:\.\d+)?)", query.lower())
    return float(m.group(1)) if m else None


def retrieve(query: str, k: int = 4) -> list[dict]:
    """Keyword-overlap retrieval over the catalog. ponytail: no embeddings for 12 rows."""
    cap = _price_cap(query)
    # digits are prices/quantities (handled by cap), not product keywords -> drop them
    terms = [t for t in re.findall(r"[a-z0-9]+", query.lower())
             if t not in _STOP and len(t) > 1 and not t.isdigit()]
    pool = [p for p in PRODUCTS if cap is None or p["price"] <= cap]

    def score(p: dict) -> tuple:
        text = _text(p)
        hits = sum(1 for t in terms if t in text)
        return (hits, p["in_stock"], -p["price"])

    ranked = sorted(pool, key=score, reverse=True)
    hit = [p for p in ranked if any(t in _text(p) for t in terms)]
    # No keyword match but a price cap given -> show cheapest under cap; else top of catalog.
    return (hit or ranked)[:k]


# Commerce/support vocabulary that counts as "on topic" alongside catalog words.
_SUPPORT_TERMS = {
    "order", "orders", "refund", "refunds", "ship", "shipping", "shipment", "deliver",
    "delivery", "return", "returns", "cancel", "cancellation", "payment", "pay", "invoice",
    "account", "price", "prices", "pricing", "cost", "stock", "buy", "purchase", "sell",
    "product", "products", "item", "items", "store", "shop", "cart", "checkout", "gift",
    "recommend", "recommendation", "suggest", "suggestion", "warranty", "track", "tracking",
    "available", "availability", "discount", "sale", "size", "color", "review", "reviews",
}
_VOCAB: set[str] | None = None


def _vocab() -> set[str]:
    v = set(_SUPPORT_TERMS)
    for p in PRODUCTS:
        v |= set(re.findall(r"[a-z0-9]+", f"{p['name']} {p['category']}".lower()))
    return {t for t in v if len(t) > 1}


def is_on_topic(message: str) -> bool:
    """ponytail: bag-of-words gate over catalog + support terms. Cheap and deterministic.
    Ceiling: false-refuses odd phrasings, misses off-topic that shares a word.
    Upgrade to embedding similarity or a tiny classifier if it proves too blunt."""
    global _VOCAB
    if _VOCAB is None:
        _VOCAB = _vocab()
    tokens = {t for t in re.findall(r"[a-z0-9]+", message.lower()) if len(t) > 1 and not t.isdigit()}
    return bool(tokens & _VOCAB)


def catalog_context(products: list[dict] | None = None) -> str:
    products = PRODUCTS if products is None else products
    lines = [
        f"- {p['name']} (${p['price']:.2f}, {p['category']}): {p['description']} "
        f"{'In stock.' if p['in_stock'] else 'Currently out of stock.'}"
        for p in products
    ]
    return "Nova Goods product catalog:\n" + "\n".join(lines)
