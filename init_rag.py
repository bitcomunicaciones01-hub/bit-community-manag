"""
Script de inicialización del sistema RAG.
Ejecutar una sola vez para cargar la base de conocimientos técnicos.
"""
# -*- coding: utf-8 -*-
import sys
import os

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

from rag_system import initialize_rag_system, load_knowledge_base

if __name__ == "__main__":
    print("=" * 80)
    print("INICIALIZACION DEL SISTEMA RAG")
    print("BIT Comunicaciones - Base de Conocimientos Tecnicos")
    print("=" * 80)
    
    print("\n[1] Inicializando ChromaDB con OpenAI embeddings...")
    collection = initialize_rag_system()
    
    if not collection:
        print("\n[ERROR] No se pudo inicializar el sistema RAG")
        print("Verifica que OPENAI_API_KEY este configurada en .env")
        exit(1)
    
    print("\n[2] Cargando archivos de conocimiento...")
    success = load_knowledge_base(collection)
    
    if not success:
        print("\n[ERROR] No se pudo cargar la base de conocimientos")
        print("Verifica que existan archivos .txt en ./brain/knowledge_base/")
        exit(1)
    
    print("\n[3] Verificando sistema con queries de prueba...")
    from rag_system import query_rag
    
    test_queries = [
        "baterias de notebook",
        "SSD NVMe",
        "memoria RAM DDR4"
    ]
    
    for query in test_queries:
        print(f"\n[TEST] '{query}'")
        results = query_rag(query, k=1, collection=collection)
        if results:
            print(f"   [OK] Encontrado: {results[0]['source']} - {results[0]['section']}")
        else:
            print(f"   [WARNING] Sin resultados")
    
    print("\n" + "=" * 80)
    print("[SUCCESS] SISTEMA RAG INICIALIZADO CORRECTAMENTE")
    print("=" * 80)
    print("\nEl sistema esta listo para usar.")
    print("Los nodos del agente ahora pueden consultar la base de conocimientos.")
    print("\nPara probar el sistema completo, ejecuta: python main.py")
