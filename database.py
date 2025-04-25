# database.py — v1.2
import os, json
from collections import defaultdict

# Path to your scraped JSON
DATA_FILE = os.path.join(os.path.dirname(__file__), 'data', 'all_products.json')

def _load_products():
    if not os.path.isfile(DATA_FILE):
        raise FileNotFoundError(f"Missing data file: {DATA_FILE}")
    with open(DATA_FILE, encoding='utf-8') as f:
        all_data = json.load(f)

    raw = all_data.get('FlooringSuperstoresCalgary', [])
    flat = []
    for p in raw:
        # Category
        cat = p.get('productType') or 'Other'
        # Specs from tags
        specs = {}
        for tag in p.get('tags', []):
            if '::' in tag:
                k, v = tag.split('::', 1)
                specs[k.strip()] = v.strip()
        # Variants (colors)
        variants = []
        for v in p.get('variants', []):
            variants.append({
                'title': v.get('title'),
                'price': float(v.get('price') or 0),
                'sku':   v.get('sku'),
            })
        # Build flat entry
        flat.append({
            'category': cat,
            'brand':    p.get('vendor'),
            'name':     p.get('title'),        # <— use "title" from JSON
            'price':    float(p.get('priceMin') or 0),
            'images':   p.get('images', []),
            'specs':    specs,
            'variants': variants,
        })
    return flat

PRODUCTS = _load_products()
