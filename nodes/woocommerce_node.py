from woocommerce_client import get_recent_products, search_products
import random
import json
import os
from datetime import datetime, timedelta

def woocommerce_intake(state):
    """
    Fetch products and determine POST STRATEGY based on day of week.
    """
    print("--- [Node] WooCommerce / Content Strategy Strategy ---")
    try:
        # 1. Determine Date & Strategy
        now = datetime.now()
        if now.hour < 12:
            target_date = now
        else:
            target_date = now + timedelta(days=1)
            
        weekday = target_date.weekday() # 0=Mon, 6=Sun
        
        # Strategy Map
        # Sales Days: Tuesday (1), Friday (4), Wednesday (2 - Upgrade/Product)
        # Content Days: Monday (0), Thursday (3), Saturday (5), Sunday (6)
        
        SALES_DAYS = [1, 2, 4] 
        CONTENT_DAYS = [0, 3, 5, 6]
        
        if weekday in SALES_DAYS:
            post_type = "sales"
        else:
            post_type = "content"
            
        # Overrides for specific themes
        # 3 = Jueves (Humor) -> content
        # 0 = Lunes (Edu) -> content
        
        print(f"Target Date: {target_date.strftime('%A')} | Type: {post_type}")

        # --- THEME LOADING ---
        settings_path = os.path.join("brain", "settings.json")
        weekly_theme = ""
        if os.path.exists(settings_path):
            try:
                with open(settings_path, "r") as f:
                    settings = json.load(f)
                    weekly_theme = settings.get("weekly_theme", "").lower().strip()
            except:
                pass

        # 2. PROMPT-DRIVEN PRODUCT SELECTION
        available_products = []
        
        if weekly_theme:
            # V39.2 SNIPER SEARCH (Handle plurals & marketing fluff)
            STOP_WORDS = ["semana", "de", "especial", "promo", "ofertas", "del", "dia", "mes", "gran", "super"]
            theme_parts = [w.strip() for w in weekly_theme.lower().split() if w.strip() and w.strip() not in STOP_WORDS]
            
            # Normalization (Plurals)
            search_variations = []
            if theme_parts:
                search_variations.append(" ".join(theme_parts)) # Original clean
                # Try simple singularization (remove 's' at end)
                singular_parts = [w[:-1] if w.endswith('s') and len(w) > 3 else w for w in theme_parts]
                if singular_parts != theme_parts:
                    search_variations.append(" ".join(singular_parts))
            
            all_searched = []
            for query in search_variations:
                print(f"Sniper Attempt: '{query}'")
                res = search_products(query, limit=30)
                if res: all_searched.extend(res)
            
            # Remove duplicates by ID
            seen_ids = set()
            searched_products = []
            for p in all_searched:
                if p['id'] not in seen_ids:
                    searched_products.append(p)
                    seen_ids.add(p['id'])

            # V39 Safety Filter
            searched_products = [p for p in searched_products if p.get("stock_status") == "instock"]
            
            def get_match_score(product_name, product_cats, theme_parts):
                text = (product_name + " " + " ".join(product_cats)).lower()
                score = 0
                matches_found = 0
                for k in theme_parts:
                    k_singular = k[:-1] if k.endswith('s') and len(k) > 3 else k
                    # High weight for technical/short terms
                    if k in text or k_singular in text:
                        matches_found += 1
                        weight = 3.0 if len(k) <= 3 else 1.5
                        if f" {k} " in f" {text} " or f" {k_singular} " in f" {text} ":
                            weight *= 2.0
                        score += weight
                
                # V39.2 STRICTURE: For multi-word themes, must match at least 50% of the words
                if len(theme_parts) >= 2 and matches_found < (len(theme_parts) / 2):
                    return 0
                return score

            scored_products = []
            for p in searched_products:
                score = get_match_score(p.get("name", ""), p.get("categories", []), theme_parts)
                if score > 0:
                    scored_products.append((score, p))
            
            scored_products.sort(key=lambda x: x[0], reverse=True)
            
            if scored_products:
                max_score = scored_products[0][0]
                # High cutoff to ensure NO fallback to rubbish
                available_products = [p for s, p in scored_products if s >= (max_score * 0.8)]
                print(f"Sniper found {len(available_products)} precise matches for '{weekly_theme}'.")
            else:
                print(f"No precise matches found for theme '{weekly_theme}'.")

        # 3. FALLBACK TO RECENT PRODUCTS (if no theme or no themed results)
        if not available_products:
            print("📦 Fetching recent products for pool...")
            available_products = get_recent_products(days=180, limit=50)
            available_products = [p for p in available_products if p.get("stock_status") == "instock"]
            
        if not available_products:
            print("⚠️ Still no products. Trying year-long timeframe...")
            available_products = get_recent_products(days=365, limit=50)
            available_products = [p for p in available_products if p.get("stock_status") == "instock"]

        if not available_products:
            return {"status": "error", "selected_product": None}
            
        # --- FILTER PUBLISHED PRODUCTS ---
        published_ids = set()
        archive_dir = os.path.join("brain", "archive")
        if os.path.exists(archive_dir):
            import glob
            for arch_file in glob.glob(os.path.join(archive_dir, "*.json")):
                try:
                    with open(arch_file, "r", encoding="utf-8") as f:
                        arch_data = json.load(f)
                        p_id = arch_data.get("selected_product", {}).get("id")
                        if p_id: published_ids.add(str(p_id))
                except: continue
        
        # Also check current drafts
        draft_dir = os.path.join("brain", "drafts")
        if os.path.exists(draft_dir):
            for draft_file in glob.glob(os.path.join(draft_dir, "*.json")):
                try:
                    with open(draft_file, "r", encoding="utf-8") as f:
                        d_data = json.load(f)
                        p_id = d_data.get("selected_product", {}).get("id")
                        if p_id: published_ids.add(str(p_id))
                except: continue

        final_pool = [p for p in available_products if str(p['id']) not in published_ids]
        
        if not final_pool:
            print("⚠️ All available products already published. Resetting filter.")
            final_pool = available_products

        # 4. Final Selection
        selected_product = random.choice(final_pool)
        
        # Inject Post Type into product dict so Copywriter knows
        selected_product["post_type"] = post_type
        selected_product["target_weekday"] = weekday
        
        print(f"Final Selected product: {selected_product['name']} (Type: {post_type})")
        
        return {
            "recent_products": available_products,
            "selected_product": selected_product,
            "status": "researching"
        }
        
    except Exception as e:
        print(f"WooCommerce Node Error: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "error"}
