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
                # No usamos networkidle porque en Railway puede tardar infinito por analytics/ads
                await page.goto(self.url, wait_until="domcontentloaded", timeout=60000)
                
                # Esperamos extra para que salten los cartelitos ("No te pierdas nada", etc.)
                logger.info("Esperando estabilización de página...")
                await page.wait_for_timeout(5000)

                # Cerrar posibles popups o avisos
                logger.info("Limpiando posibles overlays o popups...")
                overlays = [
                    'button[aria-label="Cerrar"]',
                    'button:has-text("Entendido")',
                    'button:has-text("Aceptar todo")',
                    'button:has-text("Probar")', # Banner de Nano Banana 2
                    'button:has-text("No, gracias")', # Popup de Pizarra/Canvas
                    'button:has-text("No gracias")',
                    'button:has-text("Ahora no")', # Popup de Newsletter/Suscripción
                    'button:has-text("Cerrar")',
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
                    if os.path.exists(ap):
                        abs_paths.append(ap)
                
                if not abs_paths:
                    logger.error(f"¡CRÍTICO! Ninguna imagen encontrada: {image_paths}")
                    return None

                logger.info(f"❤️ LATIDO: Empezando subida de {len(abs_paths)} fotos...")
                
                # INTENTO 1: Buscar CUALQUIER input de tipo file en toda la página
                # A veces hay inputs ocultos que funcionan directamente sin abrir menús
                inputs = await page.locator('input[type="file"]').all()
                uploaded = False
                for idx, inp in enumerate(inputs):
                    try:
                        logger.info(f"Probando input file #{idx}...")
                        await inp.set_input_files(abs_paths)
                        await page.wait_for_timeout(3000)
                        uploaded = True
                        break
                    except: pass

                # INTENTO 2: Click en '+' usando arquitectura SVG (más estable que labels)
                if not uploaded:
                    logger.info("❤️ LATIDO: Buscando botón '+' por patrón SVG...")
                    plus_svg_path = 'button:has(svg path[d*="M19 13"]), button:has(svg path[d*="M11 11V5"]), button[aria-label*="Añadir"]'
                    btn_plus = page.locator(plus_svg_path).first
                    if await btn_plus.is_visible():
                        logger.info("Click en botón + por SVG...")
                        await btn_plus.dispatch_event("click")
                        await page.wait_for_timeout(2000) # Más tiempo para que abra
                        
                        # Opción de subir archivos (Buscamos texto o icono de drive/file)
                        # Agregamos selector de icono de 'Drive/Computer'
                        opt = page.locator('span:has-text("Subir"), [aria-label*="Subir"], .upload-option, button:has(svg path[d*="M19.35 10.04"])').first
                        if await opt.is_visible():
                            async with page.expect_file_chooser() as fc_info:
                                await opt.click(force=True)
                            file_chooser = await fc_info.value
                            await file_chooser.set_files(abs_paths)
                            uploaded = True
                            logger.info("Subida via menú '+' (SVG) completada.")
                            await page.wait_for_timeout(3000)
                        else:
                            await page.keyboard.press("Escape")

                # INTENTO 3: Drag & Drop (Simulación de arrastre)
                if not uploaded:
                    logger.info("❤️ LATIDO: Intentando Drag & Drop de archivos...")
                    try:
                        # Buscamos el área donde se suelen soltar los archivos
                        drop_zone = page.locator('div[contenteditable="true"], .input-area').first
                        if await drop_zone.is_visible():
                            # En Playwright el drag and drop de archivos se suele hacer con set_input_files 
                            # Pero sobre el input oculto que se activa al hacer hover/drag
                            # Probamos de nuevo con un selector más genérico de input
                            hidden_input = page.locator('input[type="file"]').last
                            await hidden_input.set_input_files(abs_paths)
                            uploaded = True
                            logger.info("Subida via hidden input / D&D simulado exitosa.")
                            await page.wait_for_timeout(3000)
                    except: pass

                # 3. Ingresar el prompt
                # Simplificamos el prompt para que NO genere texto de publicidad, solo el video del modelo Nano Banana
                simplified_prompt = f"@Videos Usar las fotos adjuntas para generar un video corto usando el modelo NANO BANANA. El video debe referirse al producto mostrado y a la marca Bit Comunicaciones. No quiero una respuesta con texto publicitario, solo generá el video del modelo."
                
                logger.info(f"❤️ LATIDO: Escribiendo prompt simplificado...")
                prompt_selectors = [
                    'div[contenteditable="true"]',
                    '[aria-label*="Gemini"]',
                    'textarea',
                    '.input-area'
                ]
                
                text_target = None
                for ps in prompt_selectors:
                    el = page.locator(ps).first
                    if await el.is_visible():
                        text_target = el
                        break
                
                if text_target:
                    logger.info(f"Escribiendo prompt forzado en: {await text_target.evaluate('el => el.tagName')}")
                    await text_target.click(force=True)
                    await page.wait_for_timeout(500)
                    # Limpieza agresiva y tipeo
                    await page.keyboard.press("Control+A")
                    await page.keyboard.press("Backspace")
                    await page.wait_for_timeout(3000) # Espera extra antes de escribir
                    await page.keyboard.type(simplified_prompt, delay=65)
                    await page.wait_for_timeout(1000)
                    
                    # 4. Enviar
                    logger.info("❤️ LATIDO: Enviando orden...")
                    await page.keyboard.press("Control+Enter") # Más directo para Gemini
                    await page.wait_for_timeout(1500)
                    
                    # Fallback click
                    send_btn = page.locator('button[aria-label*="Enviar"], .send-button').first
                    if await send_btn.is_enabled():
                        await send_btn.click(force=True)
                else:
                    logger.error("No se encontró área de texto para el prompt.")
                    await page.screenshot(path="brain/gemini_no_text_area.png")

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
