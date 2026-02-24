
import sys
import os
import json
from urllib.parse import unquote

# Fix encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

SESSION_FILE = "./brain/instagram_session.json"
USERNAME = "bitcomunicaciones"

# Decode the latest session ID
raw_session = "57806622843%3AbhNeWDGzcPfs5p%3A12%3AAYgldgy7Oz8uGp_lScFk7QhF4R2EP7BhJt_2WRWdMg"
session_id = unquote(raw_session)

print("====================================================")
print("🔧 CONSTRUCTOR DIRECTO DE SESIÓN")
print("====================================================")
print(f"Session ID decodificado: {session_id[:30]}...")

# Build minimal session structure that instagrapi expects
session_data = {
    "cookies": {
        "sessionid": session_id,
        "ds_user_id": "57806622843",  # Extracted from session ID
        "csrftoken": "",  # Will be populated on first request
    },
    "uuids": {
        "phone_id": "57806622-843b-4e6c-9f5p-12aygldgy7oz",
        "uuid": "57806622-843b-4e6c-9f5p-12aygldgy7oz",
        "client_session_id": "57806622-843b-4e6c-9f5p-12aygldgy7oz",
        "advertising_id": "57806622-843b-4e6c-9f5p-12aygldgy7oz",
        "device_id": "android-57806622843bhne"
    },
    "mid": "",
    "ig_u_rur": "",
    "ig_www_claim": "",
    "authorization_data": {
        "sessionid": session_id
    },
    "user_id": "57806622843",
    "device_settings": {
        "app_version": "275.0.0.27.98",
        "android_version": 29,
        "android_release": "10",
        "dpi": "420dpi",
        "resolution": "1080x2260",
        "manufacturer": "samsung",
        "device": "SM-G975F",
        "model": "beyond2",
        "cpu": "exynos9820",
        "version_code": "458229237"
    },
    "user_agent": "Instagram 275.0.0.27.98 Android (29/10; 420dpi; 1080x2260; samsung; SM-G975F; beyond2; exynos9820; es_AR; 458229237)"
}

# Save to file
os.makedirs(os.path.dirname(SESSION_FILE), exist_ok=True)
with open(SESSION_FILE, 'w') as f:
    json.dump(session_data, f, indent=2)

print(f"✅ Sesión construida y guardada en: {SESSION_FILE}")
print("\n🚀 Ahora ejecuta 'run_force.bat' para probar la publicación.")
print("====================================================")
