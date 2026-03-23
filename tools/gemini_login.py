import os
import sys
import asyncio
from playwright.async_api import async_playwright

# Configuración de rutas absolutas para evitar problemas con el directorio actual
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SESSION_FILE = os.path.normpath(os.path.join(ROOT_DIR, "brain", "gemini_session.json"))
USER_DATA_DIR = os.path.normpath(os.path.join(ROOT_DIR, "brain", "gemini_profile"))

async def capture_session():
    print("====================================================")
    print("🔐 CAPTURA DE SESIÓN DE GEMINI - BIT MANAGER")
    print("====================================================")
    print(f"Ruta de guardado: {SESSION_FILE}")
    print("----------------------------------------------------")
    print("Se abrirá una ventana del navegador Chrome.")
    print("1. Iniciá sesión en tu cuenta de Google/Gemini.")
    print("2. Una vez que veas el chat de Gemini, el script autodetectará y guardará.")
    print("3. Si no autoguarda, presioná ENTER acá para forzarlo.")
    print("====================================================")

    os.makedirs(os.path.dirname(SESSION_FILE), exist_ok=True)
    os.makedirs(USER_DATA_DIR, exist_ok=True)

    async with async_playwright() as p:
        try:
            print("⏳ Iniciando Chrome del sistema...")
            context = await p.chromium.launch_persistent_context(
                USER_DATA_DIR,
                headless=False,
                channel="chrome",
                args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
                no_viewport=True
            )
        except Exception as e:
            print(f"⚠️ No se pudo usar Chrome nativo ({e}), usando Chromium...")
            context = await p.chromium.launch_persistent_context(
                USER_DATA_DIR,
                headless=False,
                args=["--disable-blink-features=AutomationControlled"],
                no_viewport=True
            )
        
        page = context.pages[0] if context.pages else await context.new_page()
        
        print("\n⏳ Abriendo Gemini...")
        try:
            await page.goto("https://gemini.google.com/app", wait_until="networkidle", timeout=60000)
        except:
            print("⚠️ Timeout al cargar Gemini, intentando continuar...")
        
        print("\n👉 SI GOOGLE TE BLOQUEA:")
        print("1. Cerrá el navegador que se abrió.")
        print("2. Intentá loguearte primero en gmail.com o google.com y luego volvé a Gemini.")
        
        # Lógica de autoguardado
        stop_event = asyncio.Event()
        
        def on_input():
            input("\n👉 Presioná ENTER cuando veas el chat de Gemini para guardar...")
            stop_event.set()

        async def check_for_chat():
            print("📡 Monitoreando ventana para detectar inicio de sesión...")
            while not stop_event.is_set():
                try:
                    # Detectar si estamos en el app y hay un prompt
                    if "gemini.google.com/app" in page.url:
                        if await page.locator('div[contenteditable="true"]').count() > 0:
                            print("\n✨ ¡Detección de chat exitosa!")
                            stop_event.set()
                            break
                except:
                    pass
                await asyncio.sleep(2)

        # Correr detección y espera de ENTER en paralelo
        # Usamos threads para el input porque es bloqueante
        import threading
        t = threading.Thread(target=on_input, daemon=True)
        t.start()
        
        await check_for_chat()
        
        # Guardar el estado
        print("💾 Guardando cookies y estado de sesión...")
        await context.storage_state(path=SESSION_FILE)
        print(f"\n✅ ¡Sesión guardada exitosamente!")
        print(f"📍 Ubicación: {SESSION_FILE}")
        
        await asyncio.sleep(2)
        await context.close()
        print("\nNavegador cerrado. Ya podés usar el dashboard.")

if __name__ == "__main__":
    # Asegurar que el loop de asyncio funcione bien en Windows
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(capture_session())
