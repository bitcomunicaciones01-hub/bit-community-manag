from duckduckgo_search import DDGS
# RAG temporarily disabled due to embedding issues
# from rag_system import query_rag, get_rag_context

def research_product(state):
    """
    Research tech topics related to the product.
    Uses web search (DuckDuckGo) for product information.
    """
    print("--- [Node] Product/Tech Researcher ---")
    
    product = state.get("selected_product")
    if not product:
        return {"research_summary": "No product information available."}
    
    product_name = product.get("name", "")
    categories = product.get("categories", [])
    
    # Build search queries based on product type
    search_queries = []
    
    # Extract component type from product name or categories
    component_keywords = ["batería", "battery", "disco", "ssd", "ram", "memoria", 
                         "pantalla", "screen", "teclado", "keyboard", "placa", 
                         "motherboard", "cargador", "charger", "fuente", "power"]
    
    component_type = None
    for keyword in component_keywords:
        if keyword.lower() in product_name.lower():
            component_type = keyword
            break
    
    if not component_type and categories:
        component_type = categories[0]
    
    # === WEB SEARCH ===
    # Create relevant search queries
    # Create relevant search queries
    if component_type:
        search_queries.append(f"{component_type} notebook info")
        search_queries.append(f"how to choose {component_type}")
    elif "notebook" in product_name.lower() or "laptop" in product_name.lower():
         search_queries.append(f"{product_name} specs")
         search_queries.append(f"notebook repair tips")
    else:
        # Generic product or non-notebook item (e.g. Galaxy Fit, Monitors, etc.)
        search_queries.append(f"{product_name} review")
        search_queries.append(f"{product_name} características español")
    
    print(f"🌍 Searching web for: {search_queries}")
    
    research_data = []
    try:
        from duckduckgo_search import DDGS
        ddgs = DDGS()
        
        for query in search_queries[:2]:
            try:
                # Use updated syntax for DuckDuckGo search (max_results instead of max_results param which changed)
                results = list(ddgs.text(query, max_results=2))
                if results:
                    for r in results:
                        research_data.append(f"- {r['title']}: {r['body'][:200]}")
                        print(f"   found: {r['title'][:50]}...")
                else:
                    print(f"   no results for: {query}")
            except Exception as e:
                print(f"⚠️ Search error for '{query}': {e}")
                
    except Exception as e:
        print(f"❌ General search error: {e} - Try 'pip install -U duckduckgo_search'")
    
    # Compile research summary (Web only)
    if research_data:
        research_summary = "\n".join(research_data[:4])  # Limit to 4 results
    else:
        research_summary = f"Información general sobre {component_type or 'repuestos de notebook'}. Importante verificar compatibilidad con tu modelo específico."
    
    print(f"✅ Research completed for: {product_name}")
    print(f"   Web results: {len(research_data)}")
    
    return {
        "research_summary": research_summary,
        "status": "drafting"
    }
