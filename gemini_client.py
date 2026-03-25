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

                # --- ESTRATEGIA DE SUBIDA 6.0: PERSISTENCIA TOTAL ---
                logger.info("❤️ LATIDO: Iniciando secuencia de adjunto de fotos...")
                uploaded = False
                
                # 1. Intentamos el selector estructural del bot local
                try:
                    plus_btn = page.locator('rich-textarea').locator('xpath=./../../../..').locator('button').first
                    if await plus_btn.is_visible(timeout=5000):
                        await plus_btn.click(force=True)
                        await page.wait_for_timeout(1500)
                        
                        # Buscamos la opción de subir (probamos varios nombres en español)
                        upload_selectors = [
                            'text="Subir desde la computadora"',
                            'text="Subir archivos"',
                            'text="Subir"',
                            '[aria-label*="computadora"]',
                            'button:has(svg path[d*="M19.35 10.04"])' # Icono de Drive/Nube
                        ]
                        
                        target_opt = None
                        for sel in upload_selectors:
                            opt = page.locator(sel).first
                            if await opt.is_visible():
                                target_opt = opt
                                break
                        
                        if target_opt:
                            async with page.expect_file_chooser(timeout=8000) as fc_info:
                                await target_opt.click(force=True)
                            file_chooser = await fc_info.value
                            await file_chooser.set_files(abs_paths)
                            uploaded = True
                    else:
                        logger.info("Botón '+' estructural no visible, probando SVG...")
                except Exception as e:
                    logger.warning(f"Error en subida estructural: {e}")

                # 2. Fallback: Botón por icono SVG directo
                if not uploaded:
                    try:
                        plus_svg = page.locator('button:has(svg path[d*="M19 13"]), button[aria-label*="Añadir"]').first
                        if await plus_svg.is_visible():
                            async with page.expect_file_chooser(timeout=8000) as fc_info:
                                await plus_svg.click(force=True)
                            file_chooser = await fc_info.value
                            await file_chooser.set_files(abs_paths)
                            uploaded = True
                    except: pass

                # 3. VERIFICACIÓN: ¿Se subieron de verdad?
                if uploaded:
                    logger.info("Esperando confirmación visual de miniaturas...")
                    # Buscamos elementos que representen archivos cargados (suelen tener un botón de cerrar/eliminar)
                    try:
                        await page.wait_for_selector('[aria-label*="Eliminar"], [aria-label*="archivo"], .thumbnail-container', timeout=10000)
                        logger.info("✅ Miniaturas detectadas en el chat.")
                    except:
                        logger.warning("No se detectaron miniaturas, pero Playwright reportó set_files exitoso.")
                    
                    await page.wait_for_timeout(6000) # Pausa estratégica para procesamiento
                else:
                    logger.warning("⚠️ No se pudo adjuntar archivos. El video saldrá genérico.")

                # 4. Ingresar el prompt
                # Simplificación extrema para que Gemini no se confunda
                short_prompt = f"Generar video NANO BANANA para este producto de Bit Comunicaciones. No escribas texto, solo el video."
                
                logger.info(f"⌨️ Escribiendo orden: {short_prompt}")
                input_box = page.locator('div[contenteditable="true"]').first
                if await input_box.is_visible():
                    await input_box.fill(short_prompt)
                    await page.wait_for_timeout(1000)
                    await input_box.press("Enter")
                    logger.info("✅ Enter presionado.")
                else:
                    logger.error("No se encontró área de texto.")
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
