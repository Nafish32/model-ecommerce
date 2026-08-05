PRODUCTS = [
    {"name": "Wireless Earbuds", "price": 59.99, "category": "Audio",
     "description": "Bluetooth 5.3 earbuds, 24h battery with case, water resistant.", "in_stock": True},
    {"name": "Smart Watch", "price": 129.99, "category": "Wearables",
     "description": "Heart-rate and sleep tracking, 7-day battery, GPS.", "in_stock": True},
    {"name": "Canvas Backpack", "price": 45.00, "category": "Bags",
     "description": "18L water-resistant canvas, padded 15\" laptop sleeve.", "in_stock": True},
    {"name": "Running Sneakers", "price": 89.99, "category": "Footwear",
     "description": "Lightweight mesh upper, cushioned sole, sizes 6-12.", "in_stock": False},
    {"name": "Desk Lamp", "price": 24.99, "category": "Home",
     "description": "LED, 3 brightness levels, USB-C powered.", "in_stock": True},
    {"name": "Ceramic Mug", "price": 12.99, "category": "Home",
     "description": "350ml, microwave and dishwasher safe.", "in_stock": True},
    {"name": "Mechanical Keyboard", "price": 74.99, "category": "Electronics",
     "description": "Hot-swappable switches, RGB backlight, compact 75% layout.", "in_stock": True},
    {"name": "Yoga Mat", "price": 29.99, "category": "Fitness",
     "description": "6mm non-slip TPE mat with carry strap.", "in_stock": True},
    {"name": "Stainless Water Bottle", "price": 19.99, "category": "Fitness",
     "description": "750ml, double-wall insulated, keeps cold 24h.", "in_stock": True},
    {"name": "Sunglasses", "price": 34.99, "category": "Accessories",
     "description": "Polarized UV400 lenses, unisex frame.", "in_stock": False},
    {"name": "Portable Charger", "price": 39.99, "category": "Electronics",
     "description": "10,000mAh, USB-C PD 20W fast charging.", "in_stock": True},
    {"name": "Throw Blanket", "price": 27.99, "category": "Home",
     "description": "Soft knit, 50x60in, machine washable.", "in_stock": True},
]


def catalog_context() -> str:
    lines = [
        f"- {p['name']} (${p['price']:.2f}, {p['category']}): {p['description']} "
        f"{'In stock.' if p['in_stock'] else 'Currently out of stock.'}"
        for p in PRODUCTS
    ]
    return "Nova Goods product catalog:\n" + "\n".join(lines)
