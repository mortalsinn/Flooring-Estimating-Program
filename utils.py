import json, os

DEFAULT_PRODUCTS_FILE  = "products.json"
USER_PRODUCTS_FILE     = "user_products.json"
SAVED_ESTIMATES_FILE   = "saved_estimates.json"

def load_default_products():
    if os.path.exists(DEFAULT_PRODUCTS_FILE):
        with open(DEFAULT_PRODUCTS_FILE) as f: prods=json.load(f)
    else: prods=[]
    for p in prods: p.setdefault("margin",0)
    return prods

def load_user_products():
    if not os.path.exists(USER_PRODUCTS_FILE):
        with open(USER_PRODUCTS_FILE,"w") as f: json.dump([],f)
    with open(USER_PRODUCTS_FILE) as f: ups=json.load(f)
    for p in ups: p.setdefault("margin",0)
    return ups

def save_user_products(ups):
    with open(USER_PRODUCTS_FILE,"w") as f: json.dump(ups,f,indent=2)

def save_estimate(items):
    recs=[]
    for it in items:
        recs.append({
          "category":it["category"],"supplier":it["supplier"],
          "series":it["series"],"color":it["color"],"quantity":it["qty"]
        })
    with open(SAVED_ESTIMATES_FILE,"w") as f:
        json.dump({"items":recs},f,indent=2)

def load_estimate():
    if not os.path.exists(SAVED_ESTIMATES_FILE): return []
    with open(SAVED_ESTIMATES_FILE) as f: data=json.load(f)
    return data.get("items",[])

def merge_products(defaults, users):
    # flatten override: user items replace defaults by 4-tuple key
    user_keys={(u['category'],u['supplier'],u['series'],u['color']) for u in users}
    out=[p for p in defaults if (p['category'],p['supplier'],p['series'],p['color']) not in user_keys]
    out.extend(users)
    return out
