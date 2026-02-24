
import sys
import os
import json
from instagrapi import Client

from urllib.parse import unquote

# Fix encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

SESSION_FILE = "./brain/instagram_session.json"

def import_session():
    print("====================================================")
    print("🍪 IMPORTADOR DE SESIÓN DE INSTAGRAM")
    print("====================================================")
    print("Si Instagram no envía el código SMS, usaremos tu sesión del navegador.")
    print("\nINSTRUCCIONES:")
    print("1. Abre Instagram.com en tu navegador (Chrome/Edge) y asegúrate de estar logueado.")
    print("2. Presiona F12 -> Ve la pestaña 'Application' (o Aplicación).")
    print("3. En el menú izquierdo: Cookies -> https://www.instagram.com")
    print("4. Busca la cookie llamada 'sessionid'.")
    print("5. Copia su 'Value' (es una cadena larga de letras y números).")
    print("====================================================")
    
    raw_session_id = input("\n👉 PEGA AQUÍ EL VALOR DE 'sessionid': ").strip()
    
    if not raw_session_id:
        print("❌ No ingresaste nada.")
        return

    # Clean and decode
    session_id = unquote(raw_session_id).strip()
    if session_id != raw_session_id:
        print(f"🔓 Detectamos formato codificado (con %), lo estamos corrigiendo...")
        print(f"   Decodificado: {session_id[:20]}...")

    print("\n⏳ Verificando sesión...")
    
    cl = Client()
    try:
        # Login using ONLY the sessionid
        cl.login_by_sessionid(session_id)
        
        # Verify it works
        info = cl.account_info()
        print(f"✅ ¡ÉXITO! Logueado como: {info.username}")
        
        # Save to the file the bot uses
        # Create directory if missing
        os.makedirs(os.path.dirname(SESSION_FILE), exist_ok=True)
        
        cl.dump_settings(SESSION_FILE)
        print(f"💾 Sesión guardada en: {SESSION_FILE}")
        print("\n¡Ahora sí! Cierra esto y vuelve a ejecutar 'run_force.bat' o 'run_bot.bat'.")
        
    except Exception as e:
        print(f"❌ Error: La sesión no parece válida. {e}")
        print("Asegúrate de haber copiado todo el código correctamente.")

    input("\nPresiona Enter para salir...")

if __name__ == "__main__":
    import_session()
