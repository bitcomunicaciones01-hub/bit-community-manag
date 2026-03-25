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
                # Aplicamos Stealth de forma ultra-segura para no crashear
                try:
                    import playwright_stealth
                    if hasattr(playwright_stealth, 'stealth'):
                        await playwright_stealth.stealth(page)
                    elif hasattr(playwright_stealth, 'stealth_async'):
                        await playwright_stealth.stealth_async(page)
                    logger.info("✅ Modo Stealth aplicado con éxito.")
                except Exception as se:
                    logger.warning(f"⚠️ No se pudo aplicar Stealth (esto podría ser normal en Cloud): {se}")
                
                logger.info(f"Navegando a {self.url}...")
                # No usamos networkidle porque en Railway puede tardar infinito por analytics/ads
                await page.goto(self.url, wait_until="domcontentloaded", timeout=60000)
                
                # Esperamos extra para que salten los cartelitos ("No te pierdas nada", etc.)
                logger.info("Esperando estabilización de página...")
                await page.wait_for_timeout(5000)

                # 1. ACTIVACIÓN DE GEMA "NANO BANANA" (Lógica del bot del usuario)
                logger.info("🍌 [Gemini Web] Buscando herramienta especializada 'nano banana'...")
                try:
                    # Buscamos en el sidebar o menú por texto
                    banana_btn = page.locator('span, div, a, p, span[title]').filter(has_text="nano banana").last
                    if await banana_btn.is_visible(timeout=8000):
                        logger.info("🍌 [Gemini Web] ¡Activando Nano Banana!")
                        await banana_btn.click(force=True)
                        await page.wait_for_timeout(4000)
                except Exception as be:
                    logger.warning(f"No se encontró 'nano banana' en el menú, se usará el modelo base: {be}")

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

                logger.info(f"❤️ LATIDO: Iniciando subida de {len(abs_paths)} fotos...")
                
                # DIAGNÓSTICO DE ARCHIVOS (Para ver si Railway los ve)
                for ap in abs_paths:
                    exists = os.path.exists(ap)
                    size = os.path.getsize(ap) if exists else 0
                    logger.info(f"Archivo: {os.path.basename(ap)} | Existe: {exists} | Tamaño: {size} bytes")

                # --- ESTRATEGIA DE SUBIDA 5.0: SELECTOR ESTRUCTURAL (Lógica del bot del usuario) ---
                logger.info("❤️ LATIDO: Buscando botón '+' mediante selector estructural profundo...")
                uploaded = False
                
                try:
                    # Buscamos el componente rich-textarea y navegamos hacia su hermano o padre que contiene los botones
                    # La lógica exacta del bot local es: rich-textarea -> parent/sibling -> button
                    # Intentamos el XPATH directo del bot: rich-textarea/../../../..//button
                    plus_btn = page.locator('rich-textarea').locator('xpath=./../../../..').locator('button').first
                    if await plus_btn.is_visible(timeout=5000):
                        logger.info("✅ Encontrado botón '+' estructural. Ejecutando click...")
                        await plus_btn.click(force=True)
                        await page.wait_for_timeout(2000)
                        
                        # Opción de subir archivos (Buscamos texto "Subir" como en el bot local)
                        with page.expect_file_chooser(timeout=8000) as fc_info:
                            upload_option = page.locator('text="Subir archivos", text="Subir", [aria-label*="Subir"]').first
                            if await upload_option.is_visible():
                                await upload_option.click(force=True)
                            else:
                                # Fallback si el menú no abrió bien o el texto es distinto
                                await page.keyboard.press("Escape")
                                raise Exception("Menú de subida no visible")
                        
                        file_chooser = await fc_info.value
                        await file_chooser.set_files(abs_paths)
                        uploaded = True
                        logger.info("✅ Foto cargada con éxito mediante selector estructural.")
                except Exception as se:
                    logger.warning(f"Fallo selector estructural: {se}. Probando inyección ciega...")

                # Fallback: Inyección en inputs si el selector estructural falló
                if not uploaded:
                    try:
                        inputs = await page.query_selector_all('input[type="file"]')
                        for inp in inputs:
                            try:
                                await inp.set_input_files(abs_paths)
                                uploaded = True
                            except: pass
                    except: pass

                if uploaded:
                    logger.info("✅ [Gemini Web] ¡FOTO CARGADA! Esperando 8s para sincronización visual...")
                    await page.wait_for_timeout(8000) # Pausa vital del bot local
                else:
                    logger.warning("⚠️ No se pudo confirmar la subida, procediendo con el prompt...")

                # 4. Ingresar el prompt
                # Simplificamos el prompt para que NO genere texto de publicidad, solo el video del modelo Nano Banana
                simplified_prompt = f"@Videos Usar las fotos adjuntas para generar un video corto usando el modelo NANO BANANA. El video debe referirse al producto mostrado y a la marca Bit Comunicaciones. No quiero una respuesta con texto publicitario, solo generá el video del modelo."
                
                logger.info(f"❤️ LATIDO: Escribiendo orden corporativa al cerebro...")
                
                input_box = page.locator('div[contenteditable="true"]').first
                if await input_box.is_visible():
                    # Usamos .fill() y .press("Enter") como el bot local
                    await input_box.fill(simplified_prompt)
                    await page.wait_for_timeout(1000)
                    await input_box.press("Enter")
                    logger.info("✅ Orden enviada.")
                else:
                    logger.error("No se encontró área de texto para el prompt.")
                    return None

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
