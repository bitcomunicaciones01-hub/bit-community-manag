"""
Verificación del post publicado por debug_scheduling_v2.py
Verifica si quedó programado o publicado inmediatamente.
"""
import os
import json
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()
USERNAME = os.getenv("INSTAGRAM_USERNAME")
PASSWORD = os.getenv("INSTAGRAM_PASSWORD")
SESSION_FILE = "./brain/instagram_session.json"

from instagrapi import Client

cl = Client()
cl.load_settings(SESSION_FILE)
cl.login(USERNAME, PASSWORD)
print("[OK] Logueado\n")

# El media_id del ultimo post publicado en el test (de la respuesta anterior)
# Buscamos los ultimos medias del usuario
print("=== ULTIMOS 3 POSTS ===")
user_id = cl.user_id_from_username(USERNAME)
medias = cl.user_medias(user_id, 3)

for m in medias:
    # Pedir info raw completa
    raw = cl.private_request(f"media/{m.pk}/info/")
    item = raw.get("items", [{}])[0]
    
    taken_at = item.get("taken_at", "?")
    is_scheduled = item.get("is_scheduled_post", "N/A")
    sched_time = item.get("scheduled_publish_time", "N/A")
    is_draft = item.get("is_draft", "N/A")
    
    # Convertir taken_at a datetime legible
    if isinstance(taken_at, int):
        taken_dt = datetime.fromtimestamp(taken_at, tz=timezone.utc)
    else:
        taken_dt = taken_at
    
    print(f"  ID: {m.pk}")
    print(f"  taken_at: {taken_dt}")
    print(f"  is_scheduled_post: {is_scheduled}")
    print(f"  scheduled_publish_time: {sched_time}")
    print(f"  is_draft: {is_draft}")
    print(f"  URL: https://www.instagram.com/p/{m.code}/")
    print()

# También verificar si hay posts SCHEDULED (no publicados aún)
print("=== VERIFICANDO CONTENIDO PROGRAMADO ===")
try:
    scheduled = cl.private_request("media/scheduled_media/")
    items = scheduled.get("items", [])
    if items:
        print(f"Encontrados {len(items)} posts programados:")
        for item in items:
            print(f"  - ID: {item.get('pk')} | scheduled: {item.get('scheduled_publish_time')}")
    else:
        print("No hay posts programados.")
    print(f"Respuesta completa: {json.dumps(scheduled, indent=2, default=str)[:500]}")
except Exception as e:
    print(f"Error al verificar scheduled: {e}")
