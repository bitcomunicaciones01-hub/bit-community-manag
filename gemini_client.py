import os
import time
import asyncio
import base64
import json as _json
from playwright.async_api import async_playwright
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeminiClient:
    def __init__(self, session_path="brain/gemini_session.json"):
        self.session_path = session_path
        self.url = "https://gemini.google.com/app"

    async def generate_video(self, image_paths, prompt_text, output_dir="brain/reels"):
        """
        Automates Gemini to generate a video from images using Nano Banana.
        """
        os.makedirs(output_dir, exist_ok=True)
        
        async with async_playwright() as p:
            # Detectamos si estamos en Railway (via variable de entorno)
            is_railway = os.getenv("GEMINI_SESSION_B64") is not None
            
            launch_args = {
                "headless": True if is_railway else False,
            } # type: dict
            
            if not is_railway:
                launch_args["channel"] = "chrome"
                launch_args["args"] = ["--disable-blink-features=AutomationControlled"]
            
            try:
                browser = await p.chromium.launch(**launch_args)
            except:
                # Fallback si chrome no está localizado
                browser = await p.chromium.launch(headless=True)
            
            # Load session
            session_b64 = os.getenv("GEMINI_SESSION_B64")
            if session_b64:
                logger.info("Cargando sesión desde variable de entorno (modo Railway)...")
                try:
                    session_data = _json.loads(base64.b64decode(session_b64).decode())
                    # Escribir temporalmente para que Playwright pueda leerlo
                    import tempfile
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
                        _json.dump(session_data, tmp)
                        tmp_path = tmp.name
                    context = await browser.new_context(storage_state=tmp_path)
                    os.unlink(tmp_path)
                except Exception as e:
                    logger.error(f"Error decodificando GEMINI_SESSION_B64: {e}")
                    return None
            elif os.path.exists(self.session_path):
                context = await browser.new_context(storage_state=self.session_path)
            else:
                logger.error(f"Sesión no encontrada en {self.session_path}. Ejecuta tools/gemini_login.py")
                return None
            page = await context.new_page()
            
            try:
                logger.info(f"Navegando a {self.url}...")
                await page.goto(self.url, wait_until="networkidle")
                
                # 1. Subir material (Imágenes)
                # El input[type=file] suele estar oculto
                file_input = page.locator('input[type="file"]')
                if await file_input.count() > 0:
                    logger.info(f"Subiendo {len(image_paths)} imágenes...")
                    # Convert paths to absolute
                    abs_paths = [os.path.abspath(p) for p in image_paths if os.path.exists(p)]
                    if abs_paths:
                        await file_input.set_input_files(abs_paths)
                        await page.wait_for_timeout(2000) # Wait for upload to process
                else:
                    logger.warning("No se encontró el input de archivos.")

                # 2. Seleccionar Herramienta de Video si está disponible
                # El usuario mostró un botón "Crear un vídeo" o "Herramientas"
                create_video_btn = page.locator('button:has-text("Crear un vídeo")').first
                if await create_video_btn.is_visible():
                    logger.info("Activando herramienta 'Crear un vídeo'...")
                    await create_video_btn.click()
                else:
                    # Intentar via menú herramientas
                    tools_btn = page.locator('button:has-text("Herramientas")').first
                    if await tools_btn.is_visible():
                        await tools_btn.click()
                        await page.wait_for_timeout(1000)
                        video_tool = page.locator('button:has-text("Crear vídeo")').first
                        if await video_tool.is_visible():
                            await video_tool.click()

                # 3. Ingresar la orden
                # El área de texto suele ser un div contenteditable o textarea
                prompt_area = page.locator('div[contenteditable="true"]').first
                if not await prompt_area.is_visible():
                    prompt_area = page.locator('textarea').first
                
                logger.info(f"Enviando orden: {prompt_text}")
                await prompt_area.fill(prompt_text)
                await page.keyboard.press("Enter")

                # 4. Esperar generación y descargar
                # Este paso es tricky porque depende de cómo Gemini entrega el video.
                # Normalmente aparece un mensaje con un video y un botón de descarga.
                logger.info("Esperando que Gemini genere el video (esto puede tardar)...")
                
                # Esperar a que aparezca un elemento de video o un botón de descarga
                # Limitamos la espera a 2 minutos
                start_time = time.time()
                video_element = None
                download_btn = None
                
                while time.time() - start_time < 120:
                    # Buscar selector de video o descarga
                    # Basado en la UI de Gemini, buscamos botones que digan "Descargar" o iconos de descarga
                    download_btn = page.locator('button[aria-label="Descargar"], a[download]').last
                    if await download_btn.is_visible():
                        logger.info("¡Botón de descarga encontrado!")
                        break
                    await page.wait_for_timeout(5000)
                
                if download_btn and await download_btn.is_visible():
                    # Manejar la descarga
                    async with page.expect_download() as download_info:
                        await download_btn.click()
                    download = await download_info.value
                    
                    filename = f"reels_gemini_{int(time.time())}.mp4"
                    output_path = os.path.join(output_dir, filename)
                    await download.save_as(output_path)
                    
                    logger.info(f"Video guardado en: {output_path}")
                    return output_path
                else:
                    logger.error("No se encontró el video generado tras 2 minutos.")
                    # Tomar screenshot para debug
                    await page.screenshot(path="brain/gemini_error.png")
                    return None

            except Exception as e:
                logger.error(f"Error en automatización de Gemini: {e}")
                await page.screenshot(path="brain/gemini_crash.png")
                return None
            finally:
                await browser.close()

# Singleton para uso fácil
client = GeminiClient()

if __name__ == "__main__":
    # Test
    # asyncio.run(client.generate_video(["placeholder.jpg"], "Prueba de video corporativo"))
    pass
