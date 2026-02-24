import os
from instagram_client import publish_instagram_post
from dotenv import load_dotenv

load_dotenv()

# Buscar una imagen local para probar
test_image = "logo.png"
if not os.path.exists(test_image):
    test_image = "placeholder.jpg"
    if not os.path.exists(test_image):
        with open(test_image, "w") as f: f.write("dummy") # Create dummy

print(f"--- PRUEBA DE PUBLICACIÓN DIRECTA ---")
caption = "Prueba de conexión del sistema BIT Comunicaciones. Ignorar este post. #Test"

res = publish_instagram_post(test_image, caption)

if res:
    print(f"\n✅ ÉXITO TOTAL")
    print(f"URL: {res.get('url')}")
    print(f"ID: {res.get('id')}")
else:
    print(f"\n❌ FALLÓ LA PUBLICACIÓN")
