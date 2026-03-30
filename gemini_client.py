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
                # Este paso es crítico: Gemini puede tardar en procesar y el DOM es complejo
                logger.info("⏳ Iniciando escaneo profundo de video (hasta 2 minutos)...")
                await page.wait_for_timeout(10000) # Espera inicial mínima
                
                video_file = None
                for i in range(60): # 60 intentos x 2s = 120s (2 min)
                    logger.info(f"Escaneo de video - Intento {i+1}/60...")
                    
                    # --- MÉTODO A: Búsqueda en el último mensaje del modelo ---
                    try:
                        # Buscamos la respuesta del modelo (varios selectores por si cambia)
                        response_selectors = [
                            'model-response',
                            '.model-response',
                            '[data-message-author-role="assistant"]',
                            'div[role="log"] div[aria-label*="Gemini"]',
                            '.message-content'
                        ]
                        
                        last_response = None
                        for rs in response_selectors:
                            found = page.locator(rs).last
                            if await found.is_visible():
                                last_response = found
                                break

                        if last_response:
                            # 1. Buscar etiqueta <video> real
                            v_els = await last_response.locator('video').all()
                            # Fallback global si no hay en la última respuesta
                            if not v_els:
                                v_els = await page.locator('video').all()

                            for v in v_els:
                                src = await v.get_attribute('src')
                                if src and (src.startswith('http') or src.startswith('blob')):
                                    logger.info(f"✅ Video detectado: {src[:40]}...")
                                    
                                    final_path = os.path.join(output_dir, f"video_{int(time.time())}.mp4")
                                    
                                    if src.startswith('http'):
                                        import requests
                                        r = requests.get(src, timeout=30)
                                        with open(final_path, 'wb') as f:
                                            f.write(r.content)
                                        return final_path
                                    elif src.startswith('blob'):
                                        # Descarga de BLOB via JS
                                        logger.info("⬇️ Descargando video BLOB mediante inyección JS...")
                                        js_code = """
                                        async (src) => {
                                            const resp = await fetch(src);
                                            const blob = await resp.blob();
                                            return new Promise((resolve) => {
                                                const reader = new FileReader();
                                                reader.onloadend = () => resolve(reader.result);
                                                reader.readAsDataURL(blob);
                                            });
                                        }
                                        """
                                        b64_data = await page.evaluate(js_code, src)
                                        if "," in b64_data:
                                            b64_content = b64_data.split(",")[1]
                                            with open(final_path, 'wb') as f:
                                                f.write(base64.b64decode(b64_content))
                                            return final_path
                            
                            # 2. Buscar botones de descarga
                            dl_selectors = [
                                'button:has(svg path[d*="M12 16"])', 
                                'button:has(svg path[d*="M19 9"])',
                                'button[aria-label*="Descargar"]',
                                'button[aria-label*="Download"]',
                                'button[aria-label*="descargar"]',
                                'a[download]', 
                                'button:has-text("Descargar")', 
                                'button:has-text("Download")',
                                '.download-button',
                                '[data-test-id*="download"]'
                            ]
                            
                            for sel in dl_selectors:
                                # Primero en la respuesta, luego global
                                btn = last_response.locator(sel).first
                                if not await btn.is_visible():
                                    btn = page.locator(sel).last
                                
                                if await btn.is_visible():
                                    logger.info(f"✅ Botón de descarga detectado: {sel}")
                                    try:
                                        async with page.expect_download(timeout=30000) as download_info:
                                            await btn.click(force=True)
                                        download = await download_info.value
                                        video_file = os.path.join(output_dir, f"video_{int(time.time())}.mp4")
                                        await download.save_as(video_file)
                                        logger.info(f"✅ Video descargado con éxito: {video_file}")
                                        return video_file
                                    except Exception as de:
                                        logger.warning(f"Fallo al clickear botón de descarga {sel}: {de}")
                    except Exception as e:
                        logger.debug(f"Error escaneando mensaje: {e}")

                    # --- MÉTODO B: Búsqueda Global / Iframes ---
                    try:
                        iframes = await page.query_selector_all('iframe')
                        for frame in iframes:
                            cf = await frame.content_frame()
                            if cf:
                                v = await cf.query_selector('video')
                                if v:
                                    src = await v.get_attribute('src')
                                    if src and (src.startswith('http') or src.startswith('blob')):
                                        logger.info("✅ Video encontrado dentro de un IFRAME.")
                                        final_path = os.path.join(output_dir, f"video_iframe_{int(time.time())}.mp4")
                                        
                                        if src.startswith('http'):
                                            import requests
                                            r = requests.get(src)
                                            with open(final_path, 'wb') as f: f.write(r.content)
                                            return final_path
                                        elif src.startswith('blob'):
                                            # Evaluar en el frame
                                            js_code = "async (s) => { const r = await fetch(s); const b = await r.blob(); return new Promise(res => { const rd = new FileReader(); rd.onloadend = () => res(rd.result); rd.readAsDataURL(b); }); }"
                                            b64_data = await cf.evaluate(js_code, src)
                                            if "," in b64_data:
                                                with open(final_path, 'wb') as f:
                                                    f.write(base64.b64decode(b64_data.split(",")[1]))
                                                return final_path
                    except: pass

                    await page.wait_for_timeout(2000)

                # Si llegamos aquí sin video, error final
                logger.error("No se encontró el video generado tras 2 minutos.")
                try:
                    await page.screenshot(path="brain/gemini_error.png", full_page=True)
                    logger.info("📸 Captura de error guardada en brain/gemini_error.png")
                except: pass
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
