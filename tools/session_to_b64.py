import os
import base64

SESSION_FILE = os.path.join("brain", "gemini_session.json")

def convert_to_b64():
    if not os.path.exists(SESSION_FILE):
        print(f"❌ No se encontró {SESSION_FILE}. Primero corré tools/gemini_login.py")
        return

    with open(SESSION_FILE, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()
        
    print("====================================================")
    print("COPIA ESTE CODIGO PARA RAILWAY")
    print("====================================================")
    print("\n")
    print(encoded)
    print("\n")
    print("====================================================")
    print("1. Anda a tu proyecto en Railway.app.")
    print("2. Anda a 'Variables'.")
    print("3. Agrega una nueva: GEMINI_SESSION_B64")
    print("4. Pega el codigo de arriba en 'Value'.")
    print("====================================================")

if __name__ == "__main__":
    convert_to_b64()
