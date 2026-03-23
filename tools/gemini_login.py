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

    os.makedirs("brain", exist_ok=True)

    async with async_playwright() as p:
        # Usamos msedge o chromium si msedge no está
        browser = await p.chromium.launch(headless=False)
        
        # Intentar cargar sesión existente si existe para no empezar de cero
        context_args = {}
        if os.path.exists(SESSION_FILE):
             context_args["storage_state"] = SESSION_FILE
        
        context = await browser.new_context(**context_args)
        page = await context.new_page()
        
        await page.goto("https://gemini.google.com/app", wait_until="networkidle")
        
        input("\n👉 Presioná ENTER después de haber iniciado sesión y ver el chat de Gemini...")
        
        # Guardar el estado (cookies y local storage)
        await context.storage_state(path=SESSION_FILE)
        print(f"\n✅ ¡Sesión guardada exitosamente en {SESSION_FILE}!")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(capture_session())
