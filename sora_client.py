import os
import time
import logging
import requests as http_requests
from openai import OpenAI
from dotenv import load_dotenv

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
        Genera un video usando OpenAI Sora 2 (text-to-video o image-to-video).
        La API de Sora es asíncrona: primero crea el job y luego hace polling.
        """
        if not self.client:
            raise Exception("Cliente OpenAI no inicializado. Verificá OPENAI_API_KEY en el .env.")

        os.makedirs(output_dir, exist_ok=True)

        try:
            logger.info(f"🚀 Iniciando generación con Sora 2 (OpenAI)...")
            logger.info(f"Prompt: {prompt}")

            # Construir los parámetros base (text-to-video)
            params = {
                "model": "sora-2",
                "prompt": prompt,
                "seconds": 8,
                "size": "720x1280",  # Vertical (9:16 para Reels/TikTok)
            }

            # Si hay imagen disponible, usarla como referencia (image-to-video)
            # El SDK espera un archivo abierto (io.IOBase), no un dict
            if image_paths:
                first_img = image_paths[0]
                if os.path.exists(first_img):
                    logger.info(f"📷 Usando imagen como referencia: {first_img}")
                    # Leer los bytes y pasarlos como tupla (nombre, bytes, mimetype)
                    with open(first_img, "rb") as img_file:
                        img_bytes = img_file.read()
                    params["input_reference"] = (os.path.basename(first_img), img_bytes, "image/jpeg")
                    logger.info(f"✅ Imagen cargada en memoria ({len(img_bytes)} bytes)")

            # Crear el job de video (asíncrono)
            logger.info("📹 Enviando solicitud de video a Sora 2...")
            job = self.client.videos.create(**params)
            job_id = job.id
            logger.info(f"✅ Job creado: {job_id} | Estado: {job.status}")

            # Polling hasta que el video esté listo (max 10 minutos)
            max_wait = 600  # 10 minutos
            interval = 15   # revisar cada 15 segundos
            elapsed = 0

            while elapsed < max_wait:
                time.sleep(interval)
                elapsed += interval

                job = self.client.videos.retrieve(job_id)
                logger.info(f"⏳ [{elapsed}s] Estado del job: {job.status}")

                if job.status == "succeeded":
                    break
                elif job.status in ("failed", "cancelled"):
                    raise Exception(f"Sora job terminó con estado: {job.status}")

            if job.status != "succeeded":
                raise Exception(f"Timeout esperando video de Sora (status: {job.status})")

            # Descargar el video generado
            video_url = job.video.url if hasattr(job, 'video') and job.video else None
            if not video_url:
                # Intentar extraer de otra estructura de respuesta
                for attr in ['url', 'download_url', 'result_url']:
                    video_url = getattr(job, attr, None)
                    if video_url:
                        break

            if not video_url:
                raise Exception("No se encontró la URL del video en la respuesta de Sora.")

            logger.info(f"✅ Video generado por Sora: {video_url[:60]}...")
            r = http_requests.get(video_url, stream=True, timeout=120)
            filename = f"reels_sora_{int(time.time())}.mp4"
            output_path = os.path.join(output_dir, filename)

            with open(output_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

            logger.info(f"✅ Video guardado en: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"❌ Error en generación Sora: {e}")
            raise  # Re-lanzamos para que el dashboard maneje el error correctamente

# Singleton
sora_client = SoraClient()
