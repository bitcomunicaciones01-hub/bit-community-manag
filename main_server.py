"""
main_server.py — Entry point para Railway / Servidor en la nube
Corre el scheduler y el dashboard de Streamlit en modo servidor.
No depende del display visual de Windows.
"""
import os
import sys
import time
import schedule
import threading
import subprocess
import pytz
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Configurar Zona Horaria (Argentina) para todo el proceso
os.environ["TZ"] = "America/Argentina/Buenos_Aires"
try:
    time.tzset() # Solo funciona en Linux (Railway)
except:
    pass

def get_now_ar():
    return datetime.now(pytz.timezone("America/Argentina/Buenos_Aires"))

# Inicializar carpetas necesarias (evita Errno 2 en el servidor)
for directory in ["brain/drafts", "brain/previews", "brain/reels", "brain/archive", "brand_assets"]:
    os.makedirs(directory, exist_ok=True)
    print(f"[OK] Directorio verificado: {directory}")

# Forzar encoding UTF-8 en el servidor
os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["DASHBOARD_MODE"] = "true"

def run_agent_job():
    """Genera nuevos posts automaticamente (10:00 y 18:00)."""
    print("\n--- [Agente] Iniciando generacion automatica ---")
    try:
        from graph import app
        result = app.invoke({"messages": [], "status": "start"})
        print(f"--- [Agente] Completado. Estado: {result.get('status')} ---")
    except Exception as e:
        print(f"--- [Agente] Error critico: {e} ---")

def run_scheduler_loop():
    """Corre el loop de scheduler en background thread con Heartbeat."""
    last_heartbeat = 0
    while True:
        try:
            schedule.run_pending()
            
            # Heartbeat cada 10 minutos para no saturar logs pero confirmar vida
            now_ts = time.time()
            if now_ts - last_heartbeat > 600: 
                print(f"[HEARTBEAT] {get_now_ar().strftime('%Y-%m-%d %H:%M:%S')} - El motor sigue activo.")
                last_heartbeat = now_ts
                
            time.sleep(30)
        except Exception as e:
            print(f"[CRITICAL ERROR] Fallo en el loop del scheduler: {e}")
            time.sleep(60) # Esperar un poco antes de reintentar

if __name__ == "__main__":
    print("=" * 60)
    print("BIT Community Manager - Modo Servidor (Railway)")
    print(f"Hora actual (AR): {get_now_ar().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Importar la funcion de publicacion
    from scheduler_service import job_publish_pending

    # Horarios (Usa la hora local del sistema que seteamos arriba con TZ)
    schedule.every().day.at("10:00").do(run_agent_job)
    schedule.every().day.at("18:00").do(run_agent_job)
    schedule.every(1).minutes.do(job_publish_pending)

    print("[OK] Scheduler configurado: 10:00 y 18:00 generacion + publicacion cada minuto")

    # Verificacion inmediata al arrancar
    print("[OK] Verificando posts pendientes al inicio...")
    job_publish_pending()

    # Correr scheduler en thread background
    t = threading.Thread(target=run_scheduler_loop, daemon=True)
    t.start()
    print("[OK] Motor de publicacion corriendo en background")

    # Dashboard en el proceso principal
    port = int(os.getenv("PORT", 8501))
    print(f"[OK] Abriendo Dashboard en puerto {port}...")
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", "dashboard.py",
        "--server.port", str(port),
        "--server.address", "0.0.0.0",
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false",
    ])
