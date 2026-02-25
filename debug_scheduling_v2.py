"""
Prueba exhaustiva de endpoints de scheduling nativo de Instagram.
Mantiene las medidas de anti-detección (delays, user-agent, etc).
"""
import os
import sys
import json
import time
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

USERNAME = os.getenv("INSTAGRAM_USERNAME")
PASSWORD = os.getenv("INSTAGRAM_PASSWORD")
SESSION_FILE = "./brain/instagram_session.json"

def get_client():
    from instagrapi import Client
    cl = Client()
    cl.delay_range = [2, 5]
    if os.path.exists(SESSION_FILE):
        try:
            cl.load_settings(SESSION_FILE)
            cl.login(USERNAME, PASSWORD)
            return cl
        except Exception:
            pass
    cl.login(USERNAME, PASSWORD)
    cl.dump_settings(SESSION_FILE)
    return cl


def try_endpoint(cl, endpoint, data, label):
    """Intenta un endpoint y muestra la respuesta o error exacto."""
    print(f"\n  --- {label} ---")
    print(f"  POST {endpoint}")
    try:
        result = cl.private_request(endpoint, data)
        print(f"  [OK] EXITO!")
        print(f"  Respuesta: {json.dumps(result, indent=2, default=str)[:800]}")
        return True
    except Exception as e:
        err_str = str(e)
        if "404" in err_str:
            print(f"  [FAIL] 404 Not Found")
        elif "400" in err_str:
            print(f"  [WARN] 400 Bad Request: {err_str[:200]}")
        elif "403" in err_str:
            print(f"  [WARN] 403 Forbidden: {err_str[:200]}")
        elif "login" in err_str.lower():
            print(f"  [WARN] Login requerido")
        else:
            print(f"  [FAIL] Error: {err_str[:300]}")
        return False


def main():
    print("=== PRUEBA EXHAUSTIVA DE ENDPOINTS SCHEDULING ===\n")
    cl = get_client()
    print(f"[OK] Logueado como {USERNAME}")
    
    # Usar imagen local válida
    img_path = None
    for candidate in ["brand_assets/template.png", "brand_assets/bit_robot.png", "debug_output.png"]:
        if os.path.exists(candidate):
            img_path = Path(candidate)
            print(f"[OK] Usando imagen: {candidate}")
            break
    
    if not img_path:
        print("[ERROR] No hay imagen local")
        return
    
    # Subir imagen primero (rupload)
    print("\n[1] Subiendo imagen via rupload...")
    # ANTI-DETECCIÓN: delay antes de subir
    time.sleep(random.uniform(3, 6))
    upload_id, width, height = cl.photo_rupload(img_path, upload_id=None)
    print(f"    Upload ID: {upload_id}, Size: {width}x{height}")
    
    # Timestamp en UTC - 30 minutos desde ahora
    scheduled_dt_utc = datetime.now(timezone.utc) + timedelta(minutes=30)
    scheduled_ts = int(scheduled_dt_utc.timestamp())
    print(f"\n[2] Hora programada: {scheduled_dt_utc.isoformat()} (ts={scheduled_ts})")
    
    # ANTI-DETECCIÓN: delay antes de configurar
    time.sleep(random.uniform(2, 4))
    
    # Base data (igual que una publicación normal)
    base_data = cl.with_default_data({
        "upload_id": upload_id,
        "caption": "TEST scheduling v3 - no publicar",
        "source_type": "library",
        "device": cl.device,
    })
    
    # ============================================================
    # PRUEBA 1: configure_to_scheduled (v1)
    data1 = {**base_data, "scheduled_publish_time": str(scheduled_ts), "is_scheduled_post": "1"}
    try_endpoint(cl, "media/configure_to_scheduled/", data1, "configure_to_scheduled/")
    
    time.sleep(random.uniform(2, 4))
    
    # PRUEBA 2: configure_to_scheduled sin trailing slash
    try_endpoint(cl, "media/configure_to_scheduled", data1, "configure_to_scheduled (sin /)")
    
    time.sleep(random.uniform(2, 4))
    
    # PRUEBA 3: media/schedule (ruta alternativa)
    data3 = {**base_data, "scheduled_publish_time": str(scheduled_ts)}
    try_endpoint(cl, "media/schedule/", data3, "media/schedule/")
    
    time.sleep(random.uniform(2, 4))
    
    # PRUEBA 4: creation/configure_and_create_to_scheduled (variante que usan algunas herramientas)
    try_endpoint(cl, "creation/configure_and_create_to_scheduled/", data1, "creation/configure_and_create_to_scheduled/")
    
    time.sleep(random.uniform(2, 4))
    
    # PRUEBA 5: media/configure con parámetros de scheduled + without client_timestamp
    data5 = cl.with_default_data({
        "upload_id": upload_id,
        "caption": "TEST scheduling v3",
        "source_type": "library",
        "scheduled_publish_time": str(scheduled_ts),
        "is_scheduled_post": "1",
        "is_draft": "0",
    })
    # Quitar client_timestamp si existe (puede forzar publicación inmediata)
    data5.pop("client_timestamp", None)
    try_endpoint(cl, "media/configure/", data5, "media/configure/ (sin client_timestamp + scheduled)")
    
    time.sleep(random.uniform(2, 4))
    
    # PRUEBA 6: Bloks endpoint de scheduling
    bloks_data = {
        "bk_client_context": json.dumps({"bloks_version": cl.bloks_versioning_id}),
        "bloks_versioning_id": cl.bloks_versioning_id if hasattr(cl, 'bloks_versioning_id') else "",
        "params": json.dumps({
            "media_id": upload_id,
            "schedule_time": scheduled_ts,
            "caption": "TEST scheduling bloks",
        })
    }
    try_endpoint(cl, "bloks/apps/com.instagram.creation.schedule_post/", bloks_data, "bloks/apps/creation.schedule_post/")
    
    print("\n\n=== RESULTADO ===")
    print("Revisa arriba qué endpoint respondió con ✅")
    print("Si ninguno funcionó, el scheduling nativo require token OAuth oficial.")


if __name__ == "__main__":
    main()
