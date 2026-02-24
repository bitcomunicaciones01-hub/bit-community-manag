import requests
import os
from datetime import datetime
from instagram_client import publish_instagram_post
from generate_image import generate_branded_product_image
from image_composer import create_social_post

def publish_to_instagram(state):
    """
    Genera imagen del producto con composición de marca (o DALL-E) y publica en Instagram.
    """
    print("--- [Node] Publisher (Branding + Instagram) ---")
    
    prompt = state.get("image_prompt")
    caption = state.get("draft_caption")
    product = state.get("selected_product", {})
    
    # 1. Generar/Obtener imagen del producto
    print(f"🎨 Preparando imagen del producto...")
    
    # Opción A: Usar imagen del producto de WooCommerce y COMPONERLA
    product_images = product.get("images", [])
    use_product_image = product_images and len(product_images) > 0
    
    image_url = None
    temp_image_path = None
    
    if use_product_image:
        print(f"[OK] Usando imagen de WooCommerce para composición...")
        try:
            # Create a temporary path for the composed image
            # We use absolute path to be safe
            temp_image_path = os.path.abspath(f"temp_force_{datetime.now().strftime('%H%M%S')}.png")
            
            # Apply branding (Background removal, logo, template)
            image_url = create_social_post(
                product=product,
                output_path=temp_image_path,
                remove_bg=True, # Default to True for a cleaner look
                design_settings={"show_logo": True}
            )
            print(f"[OK] Imagen compuesta exitosamente: {image_url}")
        except Exception as e:
            print(f"[WARNING] Error en composición: {e}. Usando imagen cruda como fallback.")
            image_url = product_images[0]
    else:
        # Opción B: Generar imagen con DALL-E 3
        print("[INFO] No hay imagen del producto, generando con DALL-E 3...")
        
        try:
            image_url = generate_branded_product_image(
                product=product,
                custom_prompt=prompt,
                add_overlay=False  # Set to True to add green border
            )
            
            if image_url:
                print(f"[OK] Imagen generada con DALL-E: {image_url}")
            else:
                print("[ERROR] Fallo la generación de imagen con DALL-E")
                image_url = f"https://picsum.photos/seed/{hash(prompt)}/1080/1080"
        
        except Exception as e:
            print(f"[ERROR] Error generando imagen: {e}")
            image_url = f"https://picsum.photos/seed/{hash(prompt)}/1080/1080"
    
    # 2. Publicar en Instagram
    print(f"📱 Publicando en Instagram...")
    
    # NUEVO: Lógica de Programación Native (Private API)
    publish_time_iso = state.get("publish_time_iso")
    scheduled_dt = None
    if publish_time_iso:
        try:
            scheduled_dt = datetime.fromisoformat(publish_time_iso)
            # Solo programamos si es en el futuro (la API suele pedir > 20 min)
            if scheduled_dt > datetime.now():
                print(f"⏰ Programando nativamente para: {scheduled_dt}")
            else:
                print(f"⏩ Fecha programada ya pasada. Publicando ahora...")
                scheduled_dt = None
        except Exception as e:
            print(f"⚠️ Error procesando fecha: {e}")
            scheduled_dt = None

    result = publish_instagram_post(image_url, caption, schedule_time=scheduled_dt)
    
    # 3. Cleanup local temp image if created
    if temp_image_path and os.path.exists(temp_image_path):
        try:
            os.remove(temp_image_path)
            print(f"🗑️ Limpieza de imagen temporal: {temp_image_path}")
        except:
            pass
            
    if result:
        print(f"[OK] Publicado exitosamente: {result['url']}")
        return {
            "status": "published",
            "image_url": image_url,
            "post_url": result['url']
        }
    else:
        print("[ERROR] Fallo la publicación")
        return {
            "status": "failed",
            "image_url": image_url
        }
