import os
import sys
import asyncio
from playwright.async_api import async_playwright

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SESSION_FILE = os.path.join("brain", "gemini_session.json")

async def capture_session():
    print("====================================================")
    print("🔐 CAPTURA DE SESIÓN DE GEMINI - BIT MANAGER")
    print("====================================================")
    print("Se abrirá una ventana del navegador.")
    print("1. Iniciá sesión en tu cuenta de Google/Gemini.")
    print("2. Una vez que veas el chat de Gemini, volvé acá.")
    print("3. Presioná ENTER en esta consola para guardar la sesión.")
    print("====================================================")

    user_data_dir = os.path.join("brain", "gemini_profile")
    os.makedirs(user_data_dir, exist_ok=True)

    async with async_playwright() as p:
        # Usamos el Chrome del sistema si está disponible para mayor confianza de Google
        # Y un perfil persistente para que no parezca una "ventana de incógnito" nueva
        try:
            context = await p.chromium.launch_persistent_context(
                user_data_dir,
                headless=False,
                channel="chrome", # Intenta usar Google Chrome instalado
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox"
                ],
                no_viewport=True
            )
        except Exception:
            # Fallback a chromium normal si chrome no está
            print("⚠️ No se encontró Chrome nativo, usando Chromium...")
            context = await p.chromium.launch_persistent_context(
                user_data_dir,
                headless=False,
                args=["--disable-blink-features=AutomationControlled"],
                no_viewport=True
            )
        
        page = context.pages[0] if context.pages else await context.new_page()
        
        print("\n⏳ Abriendo Gemini...")
        await page.goto("https://gemini.google.com/app", wait_until="networkidle")
        
        print("\n👉 SI GOOGLE TE BLOQUEA:")
        print("1. Cerrá el navegador que se abrió.")
        print("2. Intentá loguearte primero en google.com y luego ir a gemini.google.com")
        
        input("\n👉 Presioná ENTER después de haber iniciado sesión y ver el chat de Gemini...")
        
        # Guardar el estado (cookies y local storage)
        await context.storage_state(path=SESSION_FILE)
        print(f"\n✅ ¡Sesión guardada exitosamente en {SESSION_FILE}!")
        
        await context.close()

if __name__ == "__main__":
    asyncio.run(capture_session())
