import os
import json
from dotenv import load_dotenv
from nodes.copywriter_node import draft_content

load_dotenv()

# Simulate state
state = {
    "selected_product": {
        "name": "Receptor WiFi Original Samsung UN32J4300",
        "price": "15000",
        "categories": ["Repuestos TV", "WiFi"],
        "short_description": "Modulo wifi original para tv samsung compatible con serie J4300.",
        "post_type": "sales" # or "value"
    },
    "research_summary": "Chipset: WIDT30Q. Protocolo: 802.11n. Frecuencia: 2.4GHz. Conector: 8-pin flat cable. Compatible con modelos UN32J4300, UN32J4300AF. Repuesto original testeado.",
    "retry_count": 0
}

# Run copywriter
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

print("\n--- TESTING SALES POST ---")
result_sales = draft_content(state)
print("\nCAPTION GENERATED:\n")
print(result_sales["draft_caption"])

print("\n--- TESTING VALUE POST ---")
state["selected_product"]["post_type"] = "value"
result_value = draft_content(state)
print("\nCAPTION GENERATED:\n")
print(result_value["draft_caption"])
