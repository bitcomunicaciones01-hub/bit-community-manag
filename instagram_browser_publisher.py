"""
instagram_browser_publisher.py
================================
Publicación automatizada en Instagram para servidores (Railway / Cloud) y desarrollo local.
Funciona 100% Headless sin necesidad de interfaz gráfica, CMD interactivo ni navegadores visibles.

Carga la sesión desde:
- Variable de entorno `INSTAGRAM_PLAYWRIGHT_SESSION_B64` (Railway / Cloud)
- O desde el archivo local `brain/instagram_playwright_session.json`
"""

import os
import sys
import asyncio
import logging
import base64
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(asctime)s - %(message)s")
logger = logging.getLogger("ig_browser")

PLAYWRIGHT_SESSION = "./brain/instagram_playwright_session.json"

USERNAME = None
PASSWORD = None


def _load_credentials():
    global USERNAME, PASSWORD
    from dotenv import load_dotenv
    load_dotenv()
    USERNAME = os.getenv("INSTAGRAM_USERNAME")
    PASSWORD = os.getenv("INSTAGRAM_PASSWORD")


def _ensure_session_file():
    """
    Restaura la sesión desde INSTAGRAM_PLAYWRIGHT_SESSION_B64 siempre que la variable esté configurada.
    Asegura que Railway utilice la última sesión inyectada sin importar archivos locales.
    """
    dst_path = os.path.abspath(PLAYWRIGHT_SESSION)
    session_b64 = os.getenv("INSTAGRAM_PLAYWRIGHT_SESSION_B64")
    
    if session_b64:
        try:
            os.makedirs(os.path.dirname(dst_path), exist_ok=True)
            with open(dst_path, "wb") as f:
                f.write(base64.b64decode(session_b64))
            logger.info("[OK] Sesión de Playwright cargada desde la variable INSTAGRAM_PLAYWRIGHT_SESSION_B64")
        except Exception as e:
            logger.error(f"[ERROR] Error decodificando INSTAGRAM_PLAYWRIGHT_SESSION_B64: {e}")


async def _dismiss_dialogs(page):
    """Cierra diálogos de notificaciones y guardado de sesión que tapan la pantalla."""
    logger.info("Buscando diálogos de descarte...")
    for txt in ["Not Now", "Ahora no", "Cancel", "Cancelar", "Cerrar", "Close"]:
        try:
            btns = await page.query_selector_all(f'button:has-text("{txt}"), div[role="button"]:has-text("{txt}")')
            for btn in btns:
                if await btn.is_visible():
                    logger.info(f"Cerrando diálogo detectado: {txt}")
                    await btn.click(force=True)
                    await asyncio.sleep(1)
        except Exception as e:
            logger.debug(f"Error al intentar cerrar diálogo {txt}: {e}")


async def publish_photo_browser(image_path: str, caption: str) -> dict | None:
    """
    Publica una foto en Instagram de forma 100% autónoma y Headless.
    Apto para Railway / servidores en la nube.
    """
    _load_credentials()
    _ensure_session_file()

    if not os.path.exists(image_path):
        logger.error(f"[ERROR] Imagen no encontrada: {image_path}")
        return None

    image_path = os.path.abspath(image_path)
    playwright_session = os.path.abspath(PLAYWRIGHT_SESSION)

    if not os.path.exists(playwright_session):
        logger.error(
            "[ERROR] No hay archivo de sesión de Playwright en: "
            f"{playwright_session} ni variable INSTAGRAM_PLAYWRIGHT_SESSION_B64."
        )
        return None

    # Headless=True por defecto para servidores (Railway / Cloud)
    is_headless = os.getenv("HEADLESS", "true").lower() != "false"

    async with async_playwright() as p:
        logger.info(f"Lanzando Chromium en servidor (Headless={is_headless})...")
        try:
            browser = await p.chromium.launch(
                headless=is_headless,
                args=["--disable-blink-features=AutomationControlled", "--no-sandbox", "--disable-setuid-sandbox"],
            )
        except Exception as e:
            logger.error(f"Error lanzando Chromium: {e}")
            return None

        context = await browser.new_context(
            storage_state=playwright_session,
            viewport={"width": 1280, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0.0.0 Safari/537.36"
            ),
        )
        page = await context.new_page()

        try:
            # ── PASO 1: VERIFICAR SESIÓN ──────────────────────────────────
            logger.info("Navegando a Instagram en modo autónomo...")
            await page.goto("https://www.instagram.com/", wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(4)

            if "accounts/login" in page.url:
                logger.error("[ERROR] Sesión expirada. Actualizar variable INSTAGRAM_PLAYWRIGHT_SESSION_B64 en Railway.")
                await browser.close()
                return None

            logger.info(f"[OK] Sesión activa confirmada en Instagram: {page.url}")
            await _dismiss_dialogs(page)

            # ── PASO 2: ABRIR CREADOR DE POST ─────────────────────────────
            logger.info("Buscando botón 'Crear / Create'...")
            new_post_clicked = False
            for sel in [
                'a:has-text("Create")', 'a:has-text("Crear")',
                '[aria-label="New post"]', '[aria-label="Nuevo post"]',
                '[aria-label="Create"]', '[aria-label="Crear"]',
            ]:
                try:
                    el = await page.query_selector(sel)
                    if el and await el.is_visible():
                        await el.click(force=True)
                        new_post_clicked = True
                        logger.info(f"[OK] Botón Crear clickeado: {sel}")
                        break
                except:
                    continue

            if not new_post_clicked:
                logger.warning("[WARN] No se encontró el botón Crear. Intentando navegación directa...")
                await page.goto("https://www.instagram.com/create/style/", wait_until="domcontentloaded", timeout=30000)

            await asyncio.sleep(2)

            # Hacer clic en la opción exacta del submenú ('Post' / 'Publicación')
            logger.info("Seleccionando opción 'Post / Publicación' en el submenú...")
            post_item = None
            for loc in [
                page.get_by_text("Post", exact=True),
                page.get_by_text("Publicación", exact=True),
                page.locator('span:has-text("Post")').first,
                page.locator('span:has-text("Publicación")').first,
            ]:
                try:
                    if await loc.count() > 0 and await loc.first.is_visible():
                        post_item = loc.first
                        break
                except:
                    continue

            if post_item:
                box = await post_item.bounding_box()
                if box:
                    await page.mouse.click(box["x"] + box["width"]/2, box["y"] + box["height"]/2)
                    logger.info(f"[OK] Submenú 'Post' clickeado por coordenadas en el centro del elemento.")
                else:
                    await post_item.click(force=True)
                    logger.info(f"[OK] Submenú 'Post' clickeado (force=True).")

            await asyncio.sleep(2)

            # ── PASO 3: SUBIR IMAGEN ──────────────────────────────────────
            logger.info("Esperando selector de archivos (state=attached)...")
            file_input = None
            try:
                # state="attached" permite detectar el <input type="file"> aunque tenga display:none en el DOM de React
                file_input = await page.wait_for_selector('input[type="file"]', state="attached", timeout=15000)
            except Exception as e:
                logger.warning(f"wait_for_selector falló: {e}")

            if file_input:
                logger.info("Cargando archivo de imagen...")
                await file_input.set_input_files(image_path)
                logger.info("[OK] Imagen adjuntada exitosamente al modal.")
            else:
                logger.error("[ERROR] No se pudo encontrar el input de archivos.")
                await page.screenshot(path="brain/ig_debug_no_input.png")
                await browser.close()
                return None

            await asyncio.sleep(4)

            # ── PASO 4: Crop → Filtros → Caption ─────────────────────────
            for step in ["Recorte", "Filtros", "Caption"]:
                next_btn = None
                for sel in [
                    'div[role="button"]:has-text("Next")', 'div[role="button"]:has-text("Siguiente")',
                    'button:has-text("Next")', 'button:has-text("Siguiente")',
                    '*:has-text("Next")', '*:has-text("Siguiente")',
                ]:
                    try:
                        el = await page.query_selector(sel)
                        if el and await el.is_visible():
                            next_btn = el
                            break
                    except:
                        continue

                if next_btn:
                    await next_btn.click(force=True)
                    logger.info(f"[OK] Paso completado: {step}")
                    await asyncio.sleep(2)

            await asyncio.sleep(2)

            # ── PASO 5: ESCRIBIR CAPTION ──────────────────────────────────
            logger.info("Escribiendo pie de foto (caption)...")
            for sel in [
                'div[aria-label="Write a caption..."]',
                'div[aria-label="Escribe un pie de foto..."]',
                'div[aria-label*="caption"]', 'div[aria-label*="pie de foto"]',
                'textarea[aria-label*="caption"]', 'div[contenteditable="true"]',
            ]:
                try:
                    el = await page.query_selector(sel)
                    if el and await el.is_visible():
                        await el.click(force=True)
                        await asyncio.sleep(0.5)
                        await page.keyboard.type(caption[:2200], delay=5)
                        logger.info("[OK] Pie de foto escrito.")
                        break
                except:
                    continue

            await asyncio.sleep(2)

            # ── PASO 6: COMPARTIR / PUBLICAR ─────────────────────────────
            logger.info("Presionando botón 'Share / Compartir'...")
            share_btn = None
            for sel in [
                'div[role="button"]:has-text("Share")', 'div[role="button"]:has-text("Compartir")',
                'button:has-text("Share")', 'button:has-text("Compartir")',
            ]:
                try:
                    el = await page.query_selector(sel)
                    if el and await el.is_visible():
                        share_btn = el
                        break
                except:
                    continue

            if not share_btn:
                logger.error("[ERROR] Botón 'Share / Compartir' no encontrado.")
                await page.screenshot(path="brain/ig_debug_no_share.png")
                await browser.close()
                return None

            await share_btn.click(force=True)
            logger.info("[OK] Botón 'Share' presionado. Procesando publicación...")
            await asyncio.sleep(15)

            # ── PASO 7: CONFIRMACIÓN ──────────────────────────────────────
            published = False
            for sel in [
                'span:has-text("Your post has been shared")',
                'span:has-text("Tu publicación se compartió")',
                '[aria-label="Post shared"]',
            ]:
                try:
                    if await page.query_selector(sel):
                        published = True
                        logger.info("[OK] Confirmación de publicación detectada.")
                        break
                except:
                    continue

            if not published and "create" not in page.url:
                published = True

            try:
                await context.storage_state(path=playwright_session)
            except Exception:
                pass

            if published:
                logger.info("[SUCCESS] ¡Post publicado exitosamente!")
                target_user = USERNAME if USERNAME else "bitcomunicaciones"
                await browser.close()
                return {"url": f"https://www.instagram.com/{target_user}/", "media_type": "image"}
            else:
                await page.screenshot(path="brain/ig_debug_result.png")
                logger.warning("[WARN] Publicación final no confirmada.")
                await browser.close()
                return {"url": f"https://www.instagram.com/{USERNAME}/", "media_type": "image", "status": "unconfirmed"}

        except Exception as e:
            logger.error(f"[ERROR] Excepción en Playwright: {e}")
            try:
                await page.screenshot(path="brain/ig_debug_error.png")
            except:
                pass
            await browser.close()
            return None


def publish_instagram_post_browser(image_path: str, caption: str) -> dict | None:
    """
    Wrapper síncrono para ser llamado desde scheduler_service.py.
    """
    temp_downloaded = False
    local_path = image_path

    if image_path.startswith("http://") or image_path.startswith("https://"):
        logger.info("Descargando imagen desde URL...")
        try:
            from instagram_client import download_image_to_temp
            downloaded_path = download_image_to_temp(image_path)
            if downloaded_path and os.path.exists(downloaded_path):
                local_path = downloaded_path
                temp_downloaded = True
            else:
                logger.error("[ERROR] No se pudo descargar la imagen desde URL.")
                return None
        except Exception as e:
            logger.error(f"[ERROR] Falló la descarga de la imagen: {e}")
            return None

    try:
        return asyncio.run(publish_photo_browser(local_path, caption))
    finally:
        if temp_downloaded and os.path.exists(local_path):
            try:
                os.remove(local_path)
            except:
                pass


if __name__ == "__main__":
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")

    from dotenv import load_dotenv
    load_dotenv()

    print("=== Test de publicación síncrona / Servidor ===")
    test_image = "test_fb.jpg"
    if not os.path.exists(test_image):
        from PIL import Image
        img = Image.new("RGB", (1080, 1080), color="blue")
        img.save(test_image)

    caption = "Test automático de publicación BIT Comunicaciones"
    result = publish_instagram_post_browser(test_image, caption)
    if result:
        print(f"ÉXITO! URL: {result.get('url')}")
    else:
        print("FALLÓ la publicación.")
