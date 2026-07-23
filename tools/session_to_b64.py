"""
session_to_b64.py
=================
Convierte archivos de sesión locales a cadenas Base64 para usar como
variables de entorno en Railway.app (u otros servidores en la nube).
"""

import os
import sys
import base64

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SESSIONS = {
    "INSTAGRAM_PLAYWRIGHT_SESSION_B64": os.path.join("brain", "instagram_playwright_session.json"),
    "INSTAGRAM_SESSION_B64": os.path.join("brain", "instagram_session.json"),
    "GEMINI_SESSION_B64": os.path.join("brain", "gemini_session.json"),
}

def convert_to_b64():
    print("=" * 60)
    print("  CONVERTIDOR DE SESIONES A BASE64 PARA RAILWAY / NUBE")
    print("=" * 60)
    print()

    found = 0
    for env_var, file_path in SESSIONS.items():
        if os.path.exists(file_path):
            found += 1
            with open(file_path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode("utf-8")
            
            print(f"[SESION DETECTADA] {env_var} ({file_path}):")
            print("-" * 60)
            print(encoded)
            print("-" * 60)
            print()
        else:
            print(f"[NO ENCONTRADO] {env_var}: Archivo no existe ({file_path})")
            print()

    if found == 0:
        print("[!] No se encontraron archivos de sesión en la carpeta 'brain/'.")
    else:
        print("INSTRUCCIONES PARA RAILWAY:")
        print("1. Ve a tu proyecto en Railway.app")
        print("2. Abre la pestaña 'Variables'")
        print("3. Añade la variable correspondiente (ej: INSTAGRAM_PLAYWRIGHT_SESSION_B64)")
        print("4. Pega el código Base64 como valor")
        print("=" * 60)

if __name__ == "__main__":
    convert_to_b64()
