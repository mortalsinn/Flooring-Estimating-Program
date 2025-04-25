#!/usr/bin/env python3
# scraper.py

import os, json, requests

API_URL      = "https://floorforce.myshopify.com/api/2023-07/graphql.json"
ACCESS_TOKEN = "cdef9f8d8cbbcfc6ca01c429d997c76b"   # ← your Storefront token

HEADERS = {
    "Content-Type": "application/json",
    "X-Shopify-Storefront-Access-Token": ACCESS_TOKEN
}

# The five product_type categories we want to pull
CATEGORIES = [
    "Carpet",
    "Laminate",
    "Luxury Vinyl",
    "Engineered Hardwood",
    "Hardwood",
]

# GraphQL query: page through products by type
QUERY = """
query ProductsByType($q: String!, $cursor: String) {
  products(first:100, after:$cursor, query: $q) {
    pageInfo { hasNextPage endCursor }
    edges {
      node {
        id
        handle
        title
        description
        tags
        productType
        vendor
        images(first:10) {
          edges { node { url } }
        }
        variants(first:250) {
          edges {
            node {
              id
              title
              sku
              priceV2 { amount }
              image { url }
              selectedOptions { name value }
            }
          }
        }
      }
    }
  }
}
"""

def fetch_by_type(category):
    """Fetch all products whose productType == category."""
    items = []
    cursor = None
    # Shopify search filter for product_type
    q = f"product_type:'{category}'"

    while True:
        payload = {"query": QUERY, "variables": {"q": q, "cursor": cursor}}
        r = requests.post(API_URL, headers=HEADERS, json=payload)
        r.raise_for_status()
        data = r.json()["data"]["products"]

        for edge in data["edges"]:
            n = edge["node"]
            rec = {
                "id":           n["id"],
                "handle":       n["handle"],
                "title":        n["title"],              # series
                "description":  n.get("description",""),
                "tags":         n.get("tags",[]),
                "productType":  category,                # enforce our category
                "vendor":       n.get("vendor",""),
                "images":       [i["node"]["url"] for i in n["images"]["edges"]],
                "variants":     []
            }
            for ve in n["variants"]["edges"]:
                v = ve["node"]
                img = v.get("image")
                rec["variants"].append({
                    "id":      v["id"],
                    "title":   v["title"],                # color name
                    "sku":     v.get("sku"),
                    "price":   float(v["priceV2"]["amount"]),
                    "image":   img["url"] if img else None,
                    "options": {opt["name"]:opt["value"]
                                for opt in v.get("selectedOptions",[])}
                })
            items.append(rec)

        if not data["pageInfo"]["hasNextPage"]:
            break
        cursor = data["pageInfo"]["endCursor"]

    return items

def main():
    all_products = []
    for cat in CATEGORIES:
        print(f"→ Fetching {cat!r}…")
        prods = fetch_by_type(cat)
        print(f"   • {len(prods):,} products")
        all_products.extend(prods)

    out = os.path.join("data","all_products.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out,"w",encoding="utf-8") as f:
        json.dump({"FlooringSuperstoresCalgary": all_products}, f, indent=2)
    print(f"=> Wrote {len(all_products):,} total products to {out}")

if __name__ == "__main__":
    main()
