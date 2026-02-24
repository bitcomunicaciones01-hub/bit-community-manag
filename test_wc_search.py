from woocommerce_client import search_products, get_recent_products
import os
from dotenv import load_dotenv

load_dotenv()

def test_search(query):
    print(f"\n--- Testing Search for: '{query}' ---")
    results = search_products(query, limit=10)
    print(f"Found {len(results)} results with stock filter.")
    for p in results:
        print(f"- {p['name']} (ID: {p['id']}, Stock: {p.get('stock_status')})")

if __name__ == "__main__":
    test_search("placas")
