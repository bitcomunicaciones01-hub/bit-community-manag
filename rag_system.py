import os
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv
import glob

load_dotenv()

# Initialize ChromaDB with embeddings (local by default)
def initialize_rag_system():
    """
    Initialize RAG system with ChromaDB.
    Uses local sentence-transformers embeddings (free, no API needed).
    """
    try:
        # Use local embeddings (free, no API needed)
        try:
            from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
            local_ef = SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"  # Small, fast, multilingual model
            )
        except ImportError:
            print("⚠️ sentence-transformers not installed. RAG initialization disabled.")
            return None
        
        chroma_client = chromadb.PersistentClient(path="./brain/rag_knowledge")
        collection = chroma_client.get_or_create_collection(
            name="technical_knowledge",
            embedding_function=local_ef,
            metadata={"description": "Technical knowledge about notebook parts and repairs"}
        )
        
        print("✅ RAG system initialized with local embeddings (sentence-transformers)")
        return collection
        
    except Exception as e:
        print(f"❌ Error initializing RAG system: {e}")
        return None

def load_knowledge_base(collection, knowledge_dir="./brain/knowledge_base"):
    """
    Load all text files from knowledge_base directory into ChromaDB.
    
    Args:
        collection: ChromaDB collection
        knowledge_dir: Directory containing knowledge files
    """
    if not collection:
        print("❌ Collection not initialized")
        return False
    
    try:
        # Find all .txt files in knowledge_base directory
        txt_files = glob.glob(os.path.join(knowledge_dir, "*.txt"))
        
        if not txt_files:
            print(f"⚠️ No .txt files found in {knowledge_dir}")
            return False
        
        print(f"\n📚 Loading {len(txt_files)} knowledge files...")
        
        for file_path in txt_files:
            filename = os.path.basename(file_path)
            print(f"  Loading: {filename}...")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Split content into chunks (by sections marked with ##)
            sections = content.split('\n## ')
            
            documents = []
            metadatas = []
            ids = []
            
            for i, section in enumerate(sections):
                if section.strip():
                    # Add back the ## if it's not the first section
                    if i > 0:
                        section = '## ' + section
                    
                    # Extract section title (first line)
                    lines = section.split('\n', 1)
                    title = lines[0].replace('#', '').strip()
                    
                    documents.append(section)
                    metadatas.append({
                        "source": filename,
                        "section": title,
                        "chunk_index": i
                    })
                    ids.append(f"{filename}_{i}")
            
            # Add to collection
            if documents:
                collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
                print(f"    ✅ Added {len(documents)} sections from {filename}")
        
        print(f"\n✅ Knowledge base loaded successfully!")
        print(f"   Total documents in collection: {collection.count()}")
        return True
        
    except Exception as e:
        print(f"❌ Error loading knowledge base: {e}")
        import traceback
        traceback.print_exc()
        return False

def query_rag(query, k=3, collection=None):
    """
    Query the RAG system for relevant information.
    Uses local embeddings by default.
    
    Args:
        query: Search query
        k: Number of results to return
        collection: ChromaDB collection (optional, will initialize if None)
    
    Returns:
        List of relevant text chunks with metadata
    """
    try:
        if collection is None:
            # Initialize with local embeddings
            try:
                from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
                local_ef = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
                chroma_client = chromadb.PersistentClient(path="./brain/rag_knowledge")
                collection = chroma_client.get_collection(
                    name="technical_knowledge",
                    embedding_function=local_ef
                )
            except ImportError:
                print("⚠️ sentence-transformers not installed. Cannot query RAG.")
                return []
        
        results = collection.query(
            query_texts=[query],
            n_results=k
        )
        
        if not results['documents'] or not results['documents'][0]:
            return []
        
        # Format results
        formatted_results = []
        for i, doc in enumerate(results['documents'][0]):
            metadata = results['metadatas'][0][i] if results['metadatas'] else {}
            formatted_results.append({
                "content": doc,
                "source": metadata.get("source", "unknown"),
                "section": metadata.get("section", "unknown"),
                "distance": results['distances'][0][i] if results.get('distances') else None
            })
        
        return formatted_results
        
    except Exception as e:
        print(f"⚠️ RAG query failed: {e}")
        return []

def get_rag_context(query, k=3):
    """
    Get RAG context as a formatted string for use in prompts.
    
    Args:
        query: Search query
        k: Number of results to return
    
    Returns:
        Formatted string with relevant knowledge
    """
    results = query_rag(query, k=k)
    
    if not results:
        return "No relevant technical information found in knowledge base."
    
    context_parts = []
    for i, result in enumerate(results, 1):
        context_parts.append(
            f"[Fuente: {result['source']} - {result['section']}]\n{result['content'][:500]}..."
        )
    
    return "\n\n".join(context_parts)

if __name__ == "__main__":
    print("=" * 80)
    print("RAG SYSTEM - Technical Knowledge Base")
    print("=" * 80)
    
    # Initialize
    collection = initialize_rag_system()
    
    if collection:
        # Load knowledge base
        success = load_knowledge_base(collection)
        
        if success:
            # Test queries
            print("\n" + "=" * 80)
            print("TESTING RAG QUERIES")
            print("=" * 80)
            
            test_queries = [
                "baterías de notebook",
                "SSD NVMe compatibilidad",
                "memoria RAM DDR4"
            ]
            
            for query in test_queries:
                print(f"\n🔍 Query: '{query}'")
                print("-" * 80)
                results = query_rag(query, k=2, collection=collection)
                
                if results:
                    for i, result in enumerate(results, 1):
                        print(f"\n[{i}] {result['source']} - {result['section']}")
                        print(f"    {result['content'][:200]}...")
                else:
                    print("  No results found")
            
            print("\n" + "=" * 80)
            print("✅ RAG System Test Complete!")
            print("=" * 80)
