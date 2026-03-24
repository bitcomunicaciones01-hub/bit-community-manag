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
                # VERIFICACIÓN DE IMÁGENES
                abs_paths = []
                for p in image_paths:
                    ap = os.path.abspath(p)
                    exists = os.path.exists(ap)
                    logger.info(f"Verificando imagen en Railway: {ap} -> {'EXISTE' if exists else 'NO EXISTE'}")
                    if exists:
                        abs_paths.append(ap)
                
                if not abs_paths:
                    logger.error(f"No hay imágenes válidas para subir. Originales: {image_paths}")
                    return None

                # Intentar subir
                uploaded = False
                
                # Método A: Input directo
                file_input = page.locator('input[type="file"]').first
                if await file_input.count() > 0:
                    try:
                        logger.info("Intentando subida via input[type=file]...")
                        await file_input.set_input_files(abs_paths)
                        await page.wait_for_timeout(4000)
                        uploaded = True
                        logger.info("Subida via input completada.")
                    except Exception as fe:
                        logger.error(f"Fallo método A: {fe}")

                # Método B: Click en "+" y buscar opciones
                if not uploaded:
                    logger.info("Buscando botón '+' o 'Plus' para subir...")
                    plus_selectors = [
                        'button[aria-label*="Subir"]',
                        'button[aria-label*="Más"]',
                        'button[aria-label*="Añadir"]',
                        '.add-button',
                        'button:has(svg)' # Fallback a cualquier botón con icono al lado del prompt
                    ]
                    
                    for sel in plus_selectors:
                        btn = page.locator(sel).first
                        if await btn.is_visible():
                            logger.info(f"Abriendo menú '+' con: {sel}")
                            await btn.click()
                            await page.wait_for_timeout(1500)
                            
                            upload_option = page.locator('span:has-text("Subir"), [aria-label*="Subir"]').first
                            if await upload_option.is_visible():
                                async with page.expect_file_chooser() as fc_info:
                                    await upload_option.click()
                                file_chooser = await fc_info.value
                                await file_chooser.set_files(abs_paths)
                                uploaded = True
                                logger.info("Subida via menú '+' completada.")
                                break
                            await btn.click() # Cerrar menu si no funcionó

                # 2. Seleccionar Herramienta de Video (Opcional)
                logger.info("Buscando herramientas de video (chips)...")
                video_selectors = [
                    'button:has-text("Crear un vídeo")',
                    'div[role="button"]:has-text("vídeo")',
                    '.chip-button'
                ]
                
                for sel in video_selectors:
                    try:
                        btn = page.locator(sel).first
                        if await btn.is_visible():
                            logger.info(f"Clickeando chip: {sel}")
                            await btn.click()
                            await page.wait_for_timeout(2000)
                            break
                    except: pass

                # 3. Ingresar el prompt
                logger.info(f"Ingresando prompt: {prompt_text}")
                # Buscamos el área de texto con selectores más amplios
                prompt_selectors = [
                    'div[contenteditable="true"]',
                    '[aria-label*="Gemini"]',
                    'textarea',
                    '#input-area'
                ]
                
                prompt_found = False
                for ps in prompt_selectors:
                    p_area = page.locator(ps).first
                    if await p_area.is_visible():
                        logger.info(f"Prompt area encontrada: {ps}")
                        await p_area.click()
                        await page.keyboard.type(prompt_text, delay=50) # Tipeo más lento/humano
                        prompt_found = True
                        break
                
                if not prompt_found:
                    logger.warning("No se encontró área de prompt. Listando botones para diagnóstico...")
                    buttons = await page.locator('button').all()
                    for b in buttons:
                        label = await b.get_attribute('aria-label')
                        text = await b.inner_text()
                        logger.info(f"Botón detectado: Label='{label}', Text='{text}'")

                # 4. Enviar
                logger.info("Enviando...")
                await page.keyboard.press("Enter")
                await page.wait_for_timeout(1000)
                
                # Click en el botón de enviar explícito si sigue ahí
                send_btn = page.locator('button[aria-label*="Enviar"], .send-button').first
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
