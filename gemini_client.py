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
    def __init__(self, session_path=None):
        # Configuración de rutas absolutas para robustez
        ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
        self.session_path = session_path or os.path.join(ROOT_DIR, "brain", "gemini_session.json")
        self.url = "https://gemini.google.com/app"

    async def generate_video(self, image_paths, prompt_text, output_dir="brain/reels"):
        """
        Automates Gemini to generate a video from images using Nano Banana.
        """
        os.makedirs(output_dir, exist_ok=True)
        
        async with async_playwright() as p:
            # Detectamos si estamos en Railway (via variable de entorno con contenido)
            session_env = os.getenv("GEMINI_SESSION_B64")
            is_railway = session_env is not None and len(session_env.strip()) > 0
            
            launch_args = {}
            launch_args["headless"] = True if is_railway else False
            
            # Argumentos para evadir detección de bots en Railway
            user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            
            launch_args["args"] = [
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                f"--user-agent={user_agent}"
            ]
            
            try:
                logger.info("Lanzando navegador Chromium...")
                browser = await p.chromium.launch(**launch_args)
            except Exception as le:
                logger.error(f"Fallo al lanzar Chromium: {le}")
                # Fallback extremo
                browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
            
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
            # Fijar un tamaño de ventana estándar
            await page.set_viewport_size({"width": 1280, "height": 800})
            
            try:
                logger.info(f"Navegando a {self.url}...")
                await page.goto(self.url, wait_until="networkidle", timeout=60000)
                
                # Cerrar posibles popups o avisos de cookies/novedades
                logger.info("Limpiando posibles overlays o popups...")
                overlays = [
                    'button[aria-label="Cerrar"]',
                    'button:has-text("Entendido")',
                    'button:has-text("Aceptar todo")',
                    'button:has-text("Probar")', # Banner de Nano Banana 2
                    '.dismiss-button',
                    '[aria-label="Cerrar"]'
                ]
                for ov in overlays:
                    try:
                        btn = page.locator(ov).first
                        if await btn.is_visible():
                            logger.info(f"Cerrando overlay encontrado: {ov}")
                            await btn.click()
                            await page.wait_for_timeout(1000)
                    except: pass

                # 1. Subir material (Imágenes)
                # El input[type=file] suele estar oculto pero presente
                file_input = page.locator('input[type="file"]').first
                
                # VERIFICACIÓN DE IMÁGENES
                abs_paths = []
                for p in image_paths:
                    ap = os.path.abspath(p)
                    exists = os.path.exists(ap)
                    logger.info(f"Verificando imagen: {ap} -> {'EXISTE' if exists else 'NO EXISTE'}")
                    if exists:
                        abs_paths.append(ap)
                
                if abs_paths:
                    if await file_input.count() > 0:
                        try:
                            logger.info(f"Subiendo {len(abs_paths)} imágenes a Gemini...")
                            await file_input.set_input_files(abs_paths)
                            await page.wait_for_timeout(4000) # Más tiempo para carga
                            logger.info("Intento de subida completado.")
                        except Exception as fe:
                            logger.error(f"Error técnico subiendo imágenes: {fe}")
                    else:
                        plus_btn = page.locator('button[aria-label*="Subir"], button[aria-label*="Más"], button[aria-label="Añadir contenido"], .add-button').first
                        if await plus_btn.is_visible():
                            logger.info("Click en el botón '+' para abrir menú...")
                            await plus_btn.click()
                            await page.wait_for_timeout(1500)
                            
                            # Intentar clickear "Subir archivos" en el menú flotante
                            upload_option = page.locator('span:has-text("Subir archivos"), [aria-label*="Subir archivos"]').first
                            if await upload_option.is_visible():
                                logger.info("Click en 'Subir archivos' del menú...")
                                await upload_option.click()
                                await page.wait_for_timeout(1000)
                            
                            # Re-intentar encontrar el input tras el click
                            file_input = page.locator('input[type="file"]').first
                            if await file_input.count() > 0:
                                await file_input.set_input_files(abs_paths)
                                logger.info("Subida forzada tras click en '+' completada.")
                            else:
                                logger.warning("Seguimos sin encontrar input[type=file] tras abrir el menú.")
                else:
                    logger.error(f"No hay imágenes válidas para subir. Originales: {image_paths}")

                # 2. Seleccionar Herramienta de Video (Opcional)
                # En Gemini Plus a veces hay "chips". Si no los vemos, vamos directo al prompt.
                logger.info("Buscando chips de herramientas (video)...")
                video_selectors = [
                    'button:has-text("Crear un vídeo")',
                    'div[role="button"]:has-text("Crear un vídeo")',
                    'button:has-text("vídeo")'
                ]
                
                for sel in video_selectors:
                    btn = page.locator(sel).first
                    if await btn.is_visible():
                        logger.info(f"Clickeando chip: {sel}")
                        await btn.click()
                        await page.wait_for_timeout(2000)
                        break

                # 3. Ingresar la orden (Prompt)
                logger.info(f"Ingresando el prompt: {prompt_text}")
                prompt_selectors = [
                    'div[contenteditable="true"]',
                    '[aria-label="Pregunta a Gemini"]',
                    'textarea'
                ]
                
                prompt_found = False
                for ps in prompt_selectors:
                    p_area = page.locator(ps).first
                    if await p_area.is_visible():
                        logger.info(f"Prompt area encontrada con: {ps}")
                        await p_area.click()
                        await page.keyboard.type(prompt_text)
                        prompt_found = True
                        break
                
                if not prompt_found:
                    logger.warning("No se detectó el prompt area, intentando vía Tab + Type...")
                    await page.keyboard.press("Tab")
                    await page.keyboard.type(prompt_text)

                # 4. Enviar
                logger.info("Enviando orden pulsando Enter...")
                await page.keyboard.press("Enter")
                
                # Intentar click en botón de enviar si Enter no basta
                send_btn = page.locator('button[aria-label="Enviar mensaje"], button:has-text("Enviar")').first
                if await send_btn.is_enabled():
                    await send_btn.click()

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
