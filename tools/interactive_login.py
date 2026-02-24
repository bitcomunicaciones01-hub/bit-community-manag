
import sys
import os
import json
from dotenv import load_dotenv
import logging

# Fix encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Add parent dir
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from instagram_client import get_instagram_client, SESSION_FILE
from instagrapi.exceptions import ChallengeRequired, TwoFactorRequired

# Load env
load_dotenv()
USERNAME = os.getenv("INSTAGRAM_USERNAME")
PASSWORD = os.getenv("INSTAGRAM_PASSWORD")

def interactive_login():
    print("====================================================")
    print("🔐 DEBLOQUEO DE INSTAGRAM - BIT MANAGER")
    print("====================================================")
    print(f"Cuenta: {USERNAME}")
    print("Intentando iniciar sesión...")

    cl = get_instagram_client()

    # Eliminar sesión vieja si existe para empezar limpio
    if os.path.exists(SESSION_FILE):
        try:
            os.remove(SESSION_FILE)
            print("🗑️ Sesión anterior eliminada.")
        except:
            pass

    try:
        cl.login(USERNAME, PASSWORD)
        print("✅ ¡Login exitoso a la primera!")
    
    except TwoFactorRequired:
        print("\n⚠️ SE REQUIERE CODIGO 2FA (Autenticación de dos pasos)")
        code = input("👉 Ingresa el código de tu app de autenticación o SMS: ")
        cl.two_factor_login(code)
        print("✅ ¡Verificado!")

    except ChallengeRequired:
        print("\n⚠️ INSTAGRAM PIDE VERIFICACIÓN (Challenge)")
        print("Es posible que te hayan enviado un SMS o Email.")
        
        # A veces el challenge ya envió el código, a veces hay que elegir método.
        # Instagrapi intenta resolverlo auto.
        api_resp = cl.last_json
        print(f"DEBUG: {api_resp}")
        
        method = "sms" # Default
        
        # Si el challenge path está disponible, intentamos resolver
        try:
            # Preguntar al usuario si recibió código
            code = input("👉 Revisa tu SMS/Email. Ingresa el código numérico (o presiona Enter si no llegó nada): ")
            
            if code:
                cl.challenge_resolve(cl.last_json, code)
                print("✅ ¡Challenge resuelto!")
            else:
                print("❌ No se ingresó código. Intenta entrar desde el navegador primero.")
                return

        except Exception as e:
            print(f"❌ Error intentando resolver challenge: {e}")
            return

    except Exception as e:
        print(f"❌ Error general en login: {e}")
        return

    # Si llegamos acá, estamos logueados. Guardar sesión.
    print("💾 Guardando nueva sesión segura...")
    cl.dump_settings(SESSION_FILE)
    print(f"✅ Sesión guardada en: {SESSION_FILE}")
    print("====================================================")
    print("¡Listo! Ahora puedes cerrar esto y volver a correr el bot.")
    print("====================================================")
    input("Presiona Enter para salir...")

if __name__ == "__main__":
    interactive_login()
