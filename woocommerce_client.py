from woocommerce import API
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

# Initialize WooCommerce API
wcapi = API(
    url=os.getenv("WOOCOMMERCE_URL"),
    consumer_key=os.getenv("WOOCOMMERCE_CONSUMER_KEY"),
    consumer_secret=os.getenv("WOOCOMMERCE_CONSUMER_SECRET"),
    version="wc/v3",
    timeout=30
)

def get_recent_products(days=7, limit=10):
    """
    Fetch recently added products from WooCommerce.
    
    Args:
        days: Number of days to look back for new products
        limit: Maximum number of products to return
    
    Returns:
        List of product dictionaries with relevant information
    """
    try:
        # Calculate date threshold
        date_threshold = (datetime.now() - timedelta(days=days)).isoformat()
        
        # Fetch products
        response = wcapi.get("products", params={
            "after": date_threshold,
            "per_page": limit,
            "orderby": "date",
            "order": "desc",
            "status": "publish",
            "stock_status": "instock"
        })
        
        if response.status_code != 200:
            print(f"WooCommerce API Error: {response.status_code}")
            print(f"Response: {response.text}")
            return []
        
        products = response.json()
        
        # Extract relevant information
        product_list = []
        for product in products:
            product_data = {
                "id": product.get("id"),
                "name": product.get("name"),
                "price": product.get("price"),
                "regular_price": product.get("regular_price"),
                "sale_price": product.get("sale_price"),
                "description": product.get("description", ""),
                "short_description": product.get("short_description", ""),
                "categories": [cat["name"] for cat in product.get("categories", [])],
                "images": [img["src"] for img in product.get("images", [])],
                "permalink": product.get("permalink"),
                "stock_status": product.get("stock_status"),
                "date_created": product.get("date_created")
            }
            product_list.append(product_data)
        
        print(f"[OK] Fetched {len(product_list)} products from WooCommerce")
        return product_list
        
    except Exception as e:
        print(f"Error fetching WooCommerce products: {e}")
        return []

def search_products(query, limit=20):
    """
    Search products by string in WooCommerce.
    """
    try:
        response = wcapi.get("products", params={
            "search": query,
            "per_page": limit,
            "status": "publish",
            "stock_status": "instock"
        })
        
        if response.status_code != 200:
            print(f"WooCommerce API Error: {response.status_code}")
            return []
        
        products = response.json()
        product_list = []
        for product in products:
            product_data = {
                "id": product.get("id"),
                "name": product.get("name"),
                "price": product.get("price"),
                "description": product.get("description", ""),
                "short_description": product.get("short_description", ""),
                "categories": [cat["name"] for cat in product.get("categories", [])],
                "images": [img["src"] for img in product.get("images", [])],
                "permalink": product.get("permalink"),
                "stock_status": product.get("stock_status")
            }
            product_list.append(product_data)
        
        print(f"[OK] Search found {len(product_list)} products for '{query}'")
        return product_list
    except Exception as e:
        print(f"Error searching WooCommerce products: {e}")
        return []

def get_product_by_id(product_id):
    """
    Fetch a specific product by ID.
    
    Args:
        product_id: WooCommerce product ID
    
    Returns:
        Product dictionary or None
    """
    try:
        response = wcapi.get(f"products/{product_id}")
        
        if response.status_code != 200:
            print(f"WooCommerce API Error: {response.status_code}")
            return None
        
        product = response.json()
        
        return {
            "id": product.get("id"),
            "name": product.get("name"),
            "price": product.get("price"),
            "regular_price": product.get("regular_price"),
            "sale_price": product.get("sale_price"),
            "description": product.get("description", ""),
            "short_description": product.get("short_description", ""),
            "categories": [cat["name"] for cat in product.get("categories", [])],
            "images": [img["src"] for img in product.get("images", [])],
            "permalink": product.get("permalink"),
            "stock_status": product.get("stock_status")
        }
        
    except Exception as e:
        print(f"Error fetching product {product_id}: {e}")
        return None

if __name__ == "__main__":
    # Test the WooCommerce connection
    print("Testing WooCommerce API connection...")
    products = get_recent_products(days=30, limit=5)
    
    if products:
        print(f"\n[OK] Successfully connected to WooCommerce!")
        print(f"Found {len(products)} recent products:\n")
        for p in products:
            print(f"- {p['name']} (${p['price']}) - Categories: {', '.join(p['categories'])}")
    else:
        print("\n[ERROR] No products found or connection failed.")
