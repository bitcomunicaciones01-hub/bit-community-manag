import os
import time
import logging
from openai import OpenAI
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sora_client")

load_dotenv()

class SoraClient:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.error("❌ OPENAI_API_KEY no encontrada en el archivo .env")
            self.client = None
        else:
            self.client = OpenAI(api_key=self.api_key)

    async def generate_video(self, image_paths, prompt, output_dir="brain/reels"):
        """
        Genera un video usando OpenAI Sora 2 (Image-to-Video).
        Nota: En Marzo 2026, Sora 2 es el modelo estándar de video en OpenAI.
        """
        if not self.client:
            logger.error("Cliente OpenAI no inicializado.")
            return None

        os.makedirs(output_dir, exist_ok=True)
        
        try:
            logger.info(f"🚀 Iniciando generación con Sora 2 (OpenAI)...")
            logger.info(f"Prompt: {prompt}")
            
            # En la SDK de 2026, el acceso a videos es directo
            # Nota: Usamos image_to_video si hay imágenes
            
            # Subir imágenes a OpenAI si es necesario (asumimos que la API acepta paths o bytes)
            # Para este ejemplo, enviamos el prompt y la referencia a la primera imagen
            
            # SIMULACIÓN DE LLAMADA API (Siguiendo el estándar de 2026)
            # En un entorno real, estaríamos usando: client.videos.create(...)
            
            # Por ahora, implementamos la estructura de la llamada
            try:
                # Intentamos la llamada real (esto fallará si el modelo no está disponible o el SDK es viejo)
                # Pero preparamos el terreno para Sora 2
                response = self.client.videos.create(
                    model="sora-2", # o "sora-2-i2v"
                    prompt=prompt,
                    input_images=image_paths, # La SDK de 2026 debería manejar esto
                    quality="high"
                )
                
                video_url = response.url
                logger.info(f"✅ Video generado por Sora: {video_url}")
                
                # Descargar el video
                import requests
                r = requests.get(video_url, stream=True)
                filename = f"reels_sora_{int(time.time())}.mp4"
                output_path = os.path.join(output_dir, filename)
                
                with open(output_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                return output_path

            except Exception as api_err:
                logger.warning(f"⚠️ Sora 2 no disponible o error en API: {api_err}")
                # Fallback o error informativo
                raise api_err

        except Exception as e:
            logger.error(f"❌ Error en generación Sora: {e}")
            return None

# Singleton
sora_client = SoraClient()
