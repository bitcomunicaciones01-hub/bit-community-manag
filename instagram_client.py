import os
import requests
import tempfile
import time
import random
from dotenv import load_dotenv
from instagrapi import Client
from instagrapi.exceptions import LoginRequired, ChallengeRequired
from datetime import datetime
import logging

load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Credenciales desde .env
USERNAME = os.getenv("INSTAGRAM_USERNAME")
PASSWORD = os.getenv("INSTAGRAM_PASSWORD")
PROXY = os.getenv("INSTAGRAM_PROXY")  # New Proxy Support

# Configuración anti-detección
SESSION_FILE = "./brain/instagram_session.json"

def get_instagram_client():
    """
    Crea y configura un cliente de Instagram con medidas anti-detección.
    """
    client = Client()
    
    # 1. Configurar delays aleatorios (simular comportamiento humano)
    client.delay_range = [2, 5]  # Delay entre 2-5 segundos entre acciones
    
    # 2. Configurar User Agent realista (simular dispositivo móvil)
    # Rotar entre diferentes dispositivos Android comunes
    user_agents = [
        "Instagram 282.0.0.22.119 Android (31/12; 480dpi; 1080x2400; Google; Pixel 6; oriole; qcom; en_US; 475829103)",
        "Instagram 281.0.0.20.105 Android (30/11; 420dpi; 1080x2260; samsung; SM-G973F; beyond1; exynos9820; es_AR; 469210345)",
        "Instagram 280.0.0.15.115 Android (29/10; 440dpi; 1080x2160; Xiaomi; Mi A3; laurel_sprout; qcom; pt_BR; 455209341)",
    ]
    client.set_user_agent(random.choice(user_agents))
    
    # 3. Configurar settings para simular dispositivo real (Nuevo perfil)
    client.set_device({
        "app_version": "282.0.0.22.119",
        "android_version": 31,
        "android_release": "12",
        "dpi": "480dpi",
        "resolution": "1080x2400",
        "manufacturer": "Google",
        "device": "Pixel 6",
        "model": "oriole",
        "cpu": "qcom",
        "version_code": "475829103"
    })
    
    # 4. Proxy Support
    if PROXY:
        try:
            client.set_proxy(PROXY)
            logger.info(f"Proxy configurado: {PROXY[:15]}...")
        except Exception as e:
            logger.error(f"Error configurando proxy: {e}")

    return client

def login_with_session():
    """
    Intenta login usando sesión guardada, o crea nueva sesión.
    Esto evita logins repetidos que pueden ser detectados.
    """
    client = get_instagram_client()
    
    try:
        # Intentar cargar sesión existente
        if os.path.exists(SESSION_FILE):
            logger.info("Cargando sesión guardada...")
            client.load_settings(SESSION_FILE)
            client.login(USERNAME, PASSWORD)
            
            # Verificar que la sesión sigue válida
            try:
                client.get_timeline_feed()
                logger.info("[OK] Sesión válida reutilizada")
                return client
            except LoginRequired:
                logger.warning("Sesión expirada, creando nueva...")
                os.remove(SESSION_FILE)
        
        # Login nuevo
        logger.info("Creando nueva sesión...")
        client.login(USERNAME, PASSWORD)
        
        # Guardar sesión para próximos usos
        client.dump_settings(SESSION_FILE)
        logger.info("[OK] Nueva sesión creada y guardada")
        
        return client
        
    except ChallengeRequired as e:
        logger.error(f"[ERROR] Instagram requiere verificación (Challenge). Por favor, inicia sesión manualmente en Instagram desde tu navegador.")
        logger.error(f"Detalles: {e}")
        return None
    except Exception as e:
        logger.error(f"[ERROR] Error en login: {e}")
        return None

def download_image_to_temp(image_url):
    """Descarga la imagen de la URL a un archivo temporal."""
    try:
        from PIL import Image
        import io
        
        logger.info(f"Descargando desde: {image_url}")
        response = requests.get(image_url, stream=True, timeout=30)
        response.raise_for_status()
        
        # Leer contenido completo
        image_data = response.content
        
        # Verificar que sea una imagen válida
        try:
            img = Image.open(io.BytesIO(image_data))
            
            # Convertir a RGB si es necesario (elimina canal alpha)
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Guardar como JPEG
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
            img.save(temp_file.name, 'JPEG', quality=95)
            temp_file.close()
            
            logger.info(f"[OK] Imagen guardada: {temp_file.name}")
            return temp_file.name
            
        except Exception as img_error:
            logger.error(f"[ERROR] No se pudo procesar la imagen: {img_error}")
            return None
            
    except Exception as e:
        logger.error(f"[ERROR] Error descargando imagen: {e}")
        return None


def publish_instagram_post(image_url, caption):
    """
    Publica un post en Instagram usando Instagrapi con medidas anti-detección.
    """
    logger.info(f"Iniciando publicación en Instagram para: {USERNAME}")
    
    client = login_with_session()
    if not client:
        return None
    
    try:
        # LOGICA DE ENGAÑOS: Delay aleatorio antes de publicar
        delay = random.uniform(3, 7)
        logger.info(f"Esperando {delay:.1f}s antes de subir (anti-detección)...")
        time.sleep(delay)
        
        image_path = None
        if os.path.exists(str(image_url)):
             image_path = str(image_url)
        else:
             image_path = download_image_to_temp(image_url)
        
        if not image_path:
            return None
        
        from pathlib import Path
        media = client.photo_upload(Path(image_path), caption=caption)
        
        logger.info(f"[OK] Publicado exitosamente! URL: https://www.instagram.com/p/{media.code}/")
        return {
            "id": media.pk,
            "url": f"https://www.instagram.com/p/{media.code}/",
            "media_type": "image"
        }
            
    except Exception as e:
        logger.error(f"[ERROR] Error publicando en Instagram: {e}")
        return None

def publish_instagram_reel(video_path, caption):
    """
    Publica un Reel en Instagram.
    """
    logger.info(f"Publicando REEL en Instagram para: {USERNAME}")
    
    if not os.path.exists(video_path):
        logger.error(f"[ERROR] Archivo de video no encontrado: {video_path}")
        return None
        
    client = login_with_session()
    if not client:
        return None
        
    try:
        # LOGICA DE ENGAÑOS: Delay anti-detección
        time.sleep(random.uniform(7, 15))
        
        from pathlib import Path
        media = client.clip_upload(path=video_path, caption=caption)
        logger.info(f"[OK] Reel publicado exitosamente! URL: https://www.instagram.com/reels/{media.code}/")
        return {
            "id": media.pk,
            "url": f"https://www.instagram.com/reels/{media.code}/",
            "media_type": "video"
        }
    except Exception as e:
        logger.error(f"[ERROR] Error publicando Reel: {e}")
        return None

def simulate_human_activity(client):
    """
    Simula actividad humana en Instagram para evitar detección.
    Llama esto ocasionalmente entre publicaciones.
    """
    try:
        logger.info("Simulando actividad humana...")
        
        # Ver timeline
        time.sleep(random.uniform(2, 5))
        client.get_timeline_feed()
        
        # Ver perfil propio
        time.sleep(random.uniform(3, 7))
        client.user_info_by_username(USERNAME)
        
        logger.info("[OK] Actividad humana simulada")
        
    except Exception as e:
        logger.warning(f"Error simulando actividad: {e}")

if __name__ == "__main__":
    # Test block intact
    pass
