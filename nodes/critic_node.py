import chromadb
from chromadb.utils import embedding_functions

import os

# Initialize ChromaDB (Local) with OpenAI Embeddings
collection = None

try:
    embedding_model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=os.getenv("OPENAI_API_KEY"),
        model_name=embedding_model
    )
    chroma_client = chromadb.PersistentClient(path="./brain/memory_openai")
    collection = chroma_client.get_or_create_collection(name="post_history", embedding_function=openai_ef)
except Exception as e:
    print(f"⚠️ Critic Memory Disabled: {e}")
    collection = None

def quality_control(state):
    print("--- [Node] Critic (Quality Control) ---")
    draft = state.get("draft_caption")
    product = state.get("selected_product")
    
    # 1. Check for Similarity (Duplication Check)
    print("🧠 Memory: Checking for duplicates...")
    # if collection:
    #     try:
    #         results = collection.query(
    #             query_texts=[draft],
    #             n_results=1
    #         )
    #         if results['documents'] and results['documents'][0]:
    #             # If distance is very low, it means it's too similar (optional logic)
    #             pass
    #     except Exception as e:
    #         print(f"⚠️ Similarity check failed: {e}")
    # else:
    print("ℹ️ Skipping similarity check (Memory disabled temporarily)")

    # 2. Heuristic Checks for BIT branding
    feedback = []
    if "#BITComunicaciones" not in draft and "#bitcomunicaciones" not in draft.lower():
        feedback.append("Missing mandatory hashtag #BITComunicaciones.")
    if len(draft) > 2200:
        feedback.append("Caption is too long for Instagram.")
    
    # Check for inappropriate futuristic/cyberpunk language
    cyberpunk_keywords = ["cyberpunk", "2099", "neon", "futuristic", "hologram"]
    if any(keyword in draft.lower() for keyword in cyberpunk_keywords):
        feedback.append("Tone is too futuristic/cyberpunk. Use educational and approachable tone instead.")
    
    # Decision
    if feedback:
        return {
            "critique_feedback": " ".join(feedback),
            "flow_status": "revision_needed"
        }
        
    # If approved, save to memory with product metadata
    # if collection and product:
    #     try:
    #         collection.add(
    #             documents=[draft],
    #             ids=[str(hash(draft))],
    #             metadatas=[{
    #                 "product_id": product.get("id"),
    #                 "product_name": product.get("name"),
    #                 "timestamp": str(hash(draft))  # Simple timestamp placeholder
    #             }]
    #         )
    #         print("✅ Caption saved to memory")
    #     except Exception as e:
    #         print(f"⚠️ Memory save failed: {e}")
    
    print("✅ Critic Approved. Moving to Manual Approval...")
    return {
        "critique_feedback": "APPROVED",
        "flow_status": "approved"
    }
