import os
import sys
import asyncio
from playwright.async_api import async_playwright

# Rutas absolutas
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SESSION_FILE = os.path.join(ROOT_DIR, "brain", "gemini_session.json")
USER_DATA_DIR = os.path.join(ROOT_DIR, "brain", "gemini_profile")

async def capture():
    print(f"Buscando Chrome del sistema...")
    os.makedirs(os.path.dirname(SESSION_FILE), exist_ok=True)
    
    async with async_playwright() as p:
        # Intentar Chrome, luego Edge, luego Chromium
        browser_type = p.chromium
        context = None
        
        for channel in ["chrome", "msedge", None]:
            try:
                print(f"Intentando abrir navegador (canal: {channel})...")
                args = {
                    "user_data_dir": USER_DATA_DIR,
                    "headless": False,
                    "args": ["--disable-blink-features=AutomationControlled"],
                    "no_viewport": True
                }
                if channel:
                    args["channel"] = channel
                
                context = await browser_type.launch_persistent_context(**args)
                print(f"✅ Navegador abierto con éxito ({channel or 'Chromium'})")
                break
            except Exception as e:
                print(f"❌ Falló {channel}: {e}")
        
        if not context:
            print("🛑 No se pudo abrir ningún navegador. ¿Tenés Chrome o Edge instalado?")
            return

        page = context.pages[0] if context.pages else await context.new_page()
        
        print("\n⏳ Abriendo Gemini (https://gemini.google.com/app)...")
        await page.goto("https://gemini.google.com/app")
        
        print("\n" + "="*50)
        print("INSTRUCCIONES FINALIZACIÓN:")
        print("1. Iniciá sesión en la ventana del navegador.")
        print("2. Navegá hasta que veas el chat de Gemini.")
        print("3. CUANDO VEAS EL CHAT, VOLVÉ ACÁ Y APRETÁ ENTER.")
        print("="*50 + "\n")
        
        # Usamos un input simple y directo
        # En Windows, loop.run_in_executor suele ser necesario para no bloquear
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, input, "👉 Presioná ENTER para guardar la sesión y cerrar...")
        
        print("💾 Guardando sesión...")
        await context.storage_state(path=SESSION_FILE)
        print(f"✅ Sesión guardada en {SESSION_FILE}")
        
        await context.close()
        print("🔒 Navegador cerrado.")

if __name__ == "__main__":
    try:
        asyncio.run(capture())
    except KeyboardInterrupt:
        print("\nCancelado por el usuario.")
    except Exception as e:
        print(f"\n🛑 Error fatal: {e}")
        input("\nPresioná ENTER para salir...")
