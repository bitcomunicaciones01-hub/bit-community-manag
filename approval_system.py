"""
Sistema de aprobación manual para posts de Instagram.
Permite revisar y aprobar/modificar contenido antes de publicar.
"""

def show_content_preview(state):
    """
    Muestra el contenido generado en la consola para revisión.
    """
    print("\n" + "=" * 80)
    print("📋 REVISIÓN DE CONTENIDO - BIT COMUNICACIONES")
    print("=" * 80)
    
    # Producto seleccionado
    product = state.get("selected_product", {})
    print(f"\n🛒 PRODUCTO:")
    print(f"   Nombre: {product.get('name', 'N/A')}")
    print(f"   Precio: ${product.get('price', 'N/A')}")
    print(f"   Categorías: {', '.join(product.get('categories', []))}")
    
    # Investigación
    research = state.get("research_summary", "")
    print(f"\n🔍 INVESTIGACIÓN:")
    print(f"   {research[:200]}..." if len(research) > 200 else f"   {research}")
    
    # Caption generado
    caption = state.get("draft_caption", "")
    print(f"\n✍️ CAPTION GENERADO:")
    print("-" * 80)
    print(caption)
    print("-" * 80)
    
    # Prompt de imagen
    image_prompt = state.get("image_prompt", "")
    print(f"\n🎨 PROMPT DE IMAGEN:")
    print(f"   {image_prompt}")
    
    # Imagen del producto (si existe)
    product_images = product.get("images", [])
    if product_images:
        print(f"\n📸 IMAGEN DEL PRODUCTO:")
        print(f"   {product_images[0]}")
    
    print("\n" + "=" * 80)
    return True

def get_user_approval():
    """
    Solicita aprobación del usuario.
    Retorna: 'approve', 'modify', 'reject'
    """
    print("\n¿Qué deseas hacer?")
    print("  [1] ✅ Aprobar y publicar")
    print("  [2] ✏️  Modificar caption")
    print("  [3] ❌ Rechazar y generar nuevo contenido")
    print("  [4] 🚫 Cancelar (no publicar)")
    
    import sys
    sys.stdout.flush()
    
    while True:
        try:
            choice = input("\n👉 Elige una opción (1-4): ").strip()
        except EOFError:
            return "cancel"
            
        if choice == "1":
            return "approve"
        elif choice == "2":
            return "modify"
        elif choice == "3":
            return "reject"
        elif choice == "4":
            return "cancel"
        else:
            print("❌ Opción inválida. Por favor elige 1, 2, 3 o 4.")

def modify_caption(current_caption):
    """
    Permite al usuario modificar el caption.
    """
    print("\n" + "=" * 80)
    print("✏️  MODIFICAR CAPTION")
    print("=" * 80)
    print("\nCaption actual:")
    print("-" * 80)
    print(current_caption)
    print("-" * 80)
    
    print("\nEscribe el nuevo caption (o presiona Enter para mantener el actual):")
    print("(Tip: Puedes copiar el texto de arriba y modificarlo)")
    print("\nNuevo caption:")
    
    lines = []
    print("(Escribe línea por línea. Escribe 'FIN' en una línea vacía para terminar)")
    
    import sys
    sys.stdout.flush()
    
    while True:
        line = input()
        if line.strip().upper() == "FIN":
            break
        lines.append(line)
    
    new_caption = "\n".join(lines).strip()
    
    if not new_caption:
        print("\n[INFO] Manteniendo caption original")
        return current_caption
    
    print("\n✅ Caption actualizado")
    return new_caption

def approval_workflow(state):
    """
    Workflow completo de aprobación.
    Retorna el estado actualizado con la decisión del usuario.
    """
    # Mostrar preview
    show_content_preview(state)
    
    # Obtener decisión
    decision = get_user_approval()
    
    if decision == "approve":
        print("\n✅ Contenido aprobado. Procediendo a publicar...")
        state["approval_status"] = "approved"
        return state
    
    elif decision == "modify":
        current_caption = state.get("draft_caption", "")
        new_caption = modify_caption(current_caption)
        state["draft_caption"] = new_caption
        
        # Mostrar preview actualizado
        print("\n" + "=" * 80)
        print("📋 PREVIEW ACTUALIZADO")
        print("=" * 80)
        print(new_caption)
        print("=" * 80)
        
        # Confirmar publicación
        confirm = input("\n¿Publicar con este caption? (s/n): ").strip().lower()
        if confirm == "s" or confirm == "si" or confirm == "sí":
            print("\n✅ Contenido aprobado. Procediendo a publicar...")
            state["approval_status"] = "approved"
        else:
            print("\n❌ Publicación cancelada")
            state["approval_status"] = "cancelled"
        
        return state
    
    elif decision == "reject":
        print("\n🔄 Regenerando contenido...")
        state["approval_status"] = "rejected"
        state["retry_count"] = state.get("retry_count", 0) + 1
        return state
    
    else:  # cancel
        print("\n🚫 Publicación cancelada por el usuario")
        state["approval_status"] = "cancelled"
        return state

if __name__ == "__main__":
    # Test del sistema de aprobación
    test_state = {
        "selected_product": {
            "name": "Batería Notebook HP Pavilion 15",
            "price": "25000",
            "categories": ["Baterías", "HP", "Repuestos de Notebook"]
        },
        "research_summary": "Las baterías originales HP tienen mayor durabilidad y compatibilidad garantizada...",
        "draft_caption": "🔋 Batería Original HP Pavilion 15\n\n✅ 100% Original\n✅ Garantía 6 meses\n✅ Instalación incluida\n\n💰 $25.000\n\n📍 Santa Fe Capital\n📞 (342) 5482454\n\n#BITComunicaciones #HP #BateríaNotebook #SantaFe",
        "image_prompt": "Professional photo of HP laptop battery, green and blue colors, clean background"
    }
    
    result = approval_workflow(test_state)
    print(f"\nEstado final: {result.get('approval_status')}")
