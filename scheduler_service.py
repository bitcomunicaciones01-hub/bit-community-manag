import schedule
import time
import os
import json
import glob
import sys
import logging
import pytz
from datetime import datetime
from dotenv import load_dotenv

# Importar módulo de seguridad
from security import (
    validate_draft_json,
    validate_media_path,
    cleanup_orphaned_temp_files,
    is_safe_path,
    ALLOWED_DIRS,
)

# Import publisher logic
from instagram_client import publish_instagram_post, publish_instagram_reel, get_instagram_client
from tiktok_client import publish_tiktok_video

load_dotenv()

# Logger
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(asctime)s %(message)s")
logger = logging.getLogger("scheduler")

# Zona horaria Argentina
AR_TZ = pytz.timezone("America/Argentina/Buenos_Aires")

def get_now_ar():
    return datetime.now(AR_TZ)

# Config
DRAFT_DIR = "./brain/drafts"
ARCHIVE_DIR = "./brain/archive"
ERROR_DIR = "./brain/errors"
os.makedirs(ARCHIVE_DIR, exist_ok=True)
os.makedirs(ERROR_DIR, exist_ok=True)

def job_publish_pending():
    now_ar = get_now_ar()
    print(f"\n[Scheduler] Checking for approved posts at {now_ar.strftime('%Y-%m-%d %H:%M:%S')} (AR)...")
    
    # Find all approved drafts
    if not os.path.exists(DRAFT_DIR):
        print(f"[Scheduler] Draft directory {DRAFT_DIR} not found.")
        return

    files = glob.glob(os.path.join(DRAFT_DIR, "*.json"))
    approved_files = []
    
    # Iterar archivos aprobados y verificar tiempo
    for f in files:
        # ── SEGURIDAD: Verificar que el archivo esté dentro del directorio de drafts ──
        if not is_safe_path(DRAFT_DIR, f):
            logger.error(f"[SECURITY ALERT] Path traversal bloqueado en draft: '{f}'")
            continue

        try:
            with open(f, "r", encoding="utf-8") as json_file:
                data = json.load(json_file)

            # ── SEGURIDAD: Validar schema y rutas del draft ──
            is_valid, validation_errors = validate_draft_json(data, f)
            if not is_valid:
                logger.warning(
                    f"[Scheduler] Draft inválido, se omite: {os.path.basename(f)} — Errores: {validation_errors}"
                )
                continue

            if data.get("approval_status") == "approved":
                # Verificar si es un post futuro
                publish_time_iso = data.get("publish_time_iso")
                if publish_time_iso:
                    try:
                        scheduled_dt = datetime.fromisoformat(publish_time_iso)
                        if scheduled_dt.tzinfo is None:
                            scheduled_dt = AR_TZ.localize(scheduled_dt)
                        
                        if now_ar < scheduled_dt:
                            # SKIP posts futuros
                            logger.info(f"[Scheduler]   WAIT: {os.path.basename(f)} para {scheduled_dt.strftime('%H:%M')} (Faltan: {scheduled_dt - now_ar})")
                            continue
                    except ValueError as ve:
                        logger.warning(f"[Scheduler]   publish_time_iso inválido en '{f}': {ve}")
                        
                approved_files.append((f, data))
                
        except json.JSONDecodeError as je:
            logger.error(f"[Scheduler]   JSON malformado en '{f}': {je}")
        except Exception as e:
            logger.error(f"[Scheduler]   Error leyendo '{f}': {e}")
            
    # Sort candidates: prioritize those with a publish_time_iso (scheduled) 
    # and then by the scheduled time itself.
    def get_sort_key(item):
        path, data = item
        p_time = data.get("publish_time_iso")
        if p_time:
            try:
                return datetime.fromisoformat(p_time).timestamp()
            except ValueError:
                return 9999999999  # Fallback para fechas inválidas
        return os.path.getmtime(path)  # Fallback al mtime del archivo

    approved_files.sort(key=get_sort_key)
    
    if not approved_files:
        return

    # Pick the first one (most urgent/oldest scheduled)
    file_path, draft = approved_files[0]
    print(f"[Scheduler] Found {len(approved_files)} approved drafts. Processing: {os.path.basename(file_path)}")
    print(f"[Scheduler]   Scheduled: {draft.get('publish_time_iso', 'ASAP')}")
    print(f"[Scheduler]   Current AR: {now_ar.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 1. Generate Image (Use Image Composer now)
        product = draft.get("selected_product", {})
        caption = draft.get("draft_caption", "")
        design = draft.get("design_settings", {})
        did = draft.get("id", "unknown")
        
        print("   Composing branded image...")
        image_path = f"temp_publish_{now_ar.strftime('%H%M%S')}.png"
        
        try:
            from image_composer import create_social_post
            
            # Check for custom image override
            custom_img_path = os.path.join(DRAFT_DIR, f"custom_img_{did}.png")
            if not os.path.exists(custom_img_path): custom_img_path = None

            final_image_path = create_social_post(
                product, 
                image_path,
                override_image_path=custom_img_path,
                remove_bg=design.get("remove_bg", False),
                design_settings=design
            )
        except Exception as e:
            print(f"   WARNING: Composition failed: {e}. Fallback to product image.")
            final_image_path = None 
            if product.get("images"):
                final_image_path = product["images"][0]
        
        # 2. Publish to chosen platform
        pref_fmt = draft.get("preferred_format", "image")
        # ── SEGURIDAD: Validar ruta del video reel antes de usarla ──────────────
        reel_path = draft.get("reel_path")  # Ya validado y normalizado por validate_draft_json
        
        # 3. Double check time (Safety)
        if draft.get("publish_time_iso"):
            try:
                s_dt = datetime.fromisoformat(draft["publish_time_iso"])
                if s_dt.tzinfo is None: s_dt = AR_TZ.localize(s_dt)
                if now_ar < s_dt:
                    logger.info(f"   [Safety] Publicación futura: {s_dt}. Cancelando.")
                    return
            except ValueError as ve:
                logger.warning(f"   [Safety] publish_time_iso inválido: {ve}")

        res = None
        if pref_fmt == "tiktok" and reel_path and os.path.exists(reel_path):
            print("   Uploading to TIKTOK as requested...")
            res = publish_tiktok_video(video_path=reel_path, caption=caption)
        elif pref_fmt == "video" and reel_path and os.path.exists(reel_path):
            print("   Uploading to INSTAGRAM REEL as requested...")
            res = publish_instagram_reel(video_path=reel_path, caption=caption)
        else:
            print("   Uploading to INSTAGRAM PHOTO (Default or Fallback)...")
            res = publish_instagram_post(
                image_url=final_image_path if final_image_path else "placeholder.jpg",
                caption=caption
            )
        
        if res:
            publish_url = res.get("url") if isinstance(res, dict) else res
            print(f"   SUCCESS: Published! URL: {publish_url}")
            
            # 3. Archive the draft with a unique name to prevent FileExistsError on Windows
            filename = os.path.basename(file_path)
            name, ext = os.path.splitext(filename)
            unique_filename = f"{name}_{int(time.time())}{ext}"
            
            # Use shutil.move or os.replace for safety, but here we just rename with unique name
            os.rename(file_path, os.path.join(ARCHIVE_DIR, unique_filename))
            print(f"   Draft archived as {unique_filename}.")

            # 4. Cleanup Temp Image
            try:
                if final_image_path and "temp_publish" in final_image_path and os.path.exists(final_image_path):
                    # Verificar que la ruta sea segura antes de eliminar
                    if is_safe_path(os.path.dirname(os.path.abspath(__file__)), final_image_path):
                        os.remove(final_image_path)
                        logger.info("   Temp image limpiada.")
            except Exception as cleanup_err:
                logger.warning(f"   No se pudo limpiar temp image: {cleanup_err}")
        else:
            print("   ERROR: Publishing failed. Moving to errors folder.")
            filename = os.path.basename(file_path)
            name, ext = os.path.splitext(filename)
            unique_filename = f"{name}_{int(time.time())}{ext}"
            os.rename(file_path, os.path.join(ERROR_DIR, unique_filename))
            
    except Exception as e:
        print(f"   ERROR: Critical error publishing: {e}")
        try:
            filename = os.path.basename(file_path)
            name, ext = os.path.splitext(filename)
            unique_filename = f"{name}_error_{int(time.time())}{ext}"
            os.rename(file_path, os.path.join(ERROR_DIR, unique_filename))
        except Exception as inner_e:
            print(f"   CRITICAL: Could not move file to errors folder: {inner_e}")
            # Failsafe: Try to just delete the file so it doesn't loop infinitely
            try:
                os.remove(file_path)
                print(f"   Failsafe: Deleted problematic draft {file_path}")
            except:
                pass

if __name__ == "__main__":
    print("[BIT Scheduler Service Started]")
    print("   Watching 'brain/drafts' for approved posts...")
    print("   Schedule: 10:00 and 18:00 daily + Check every minute")
    
    # Limpieza inicial de archivos tempáneos huérfanos (>2 horas)
    cleanup_orphaned_temp_files()
    
    # Verificar posts pendientes cada minuto
    schedule.every(1).minutes.do(job_publish_pending)
    
    # Limpieza periódica de temp files cada 2 horas
    schedule.every(2).hours.do(cleanup_orphaned_temp_files)
    
    # Verificación inicial
    job_publish_pending()
    
    # Loop de scheduler
    if os.getenv("RUN_ONCE") == "true":
        print("\n[Scheduler] RUN_ONCE detectado. Saliendo.")
    else:
        while True:
            schedule.run_pending()
            time.sleep(60)
