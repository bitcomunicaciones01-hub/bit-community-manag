
import sys
import os
import json
from urllib.parse import unquote
from instagrapi import Client

# Fix encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

SESSION_FILE = "./brain/instagram_session.json"
USER_SESSION_ID = "57806622843%3ALNbhLcLqcUmIN2%3A12%3AAYga48_FCwZR86S3eshkAX1Ut-6A_r4r-bLqczzbvGwi"

def fix_session():
    print("====================================================")
    print("🔧 REPARADOR DE SESIÓN MANUAL")
    print("====================================================")
    
    # 1. Decode the session ID
    decoded_session_id = unquote(USER_SESSION_ID)
    print(f"📥 Original: {USER_SESSION_ID}")
    print(f"🔓 Decodificado: {decoded_session_id}")
    
    # 2. Verify with Instagrapi
    print("\n⏳ Verificando sesión decodificada...")
    
    cl = Client()
    try:
        cl.login_by_sessionid(decoded_session_id)
        
        info = cl.account_info()
        print(f"✅ ¡ÉXITO! Logueado como: {info.username}")
        
        # 3. Save
        os.makedirs(os.path.dirname(SESSION_FILE), exist_ok=True)
        cl.dump_settings(SESSION_FILE)
        print(f"💾 Sesión guardada en: {SESSION_FILE}")
        
    except Exception as e:
        print(f"❌ Error: La sesión sigue sin funcionar. {e}")

if __name__ == "__main__":
    fix_session()
