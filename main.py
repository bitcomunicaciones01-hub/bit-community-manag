import os
import schedule
import time
import sys

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
from graph import app  # Importing the compiled LangGraph app

load_dotenv()
os.environ["DASHBOARD_MODE"] = "true"

def run_agent_job():
    print("\n--- [System] Iniciando flujo del Agente Community Manager ---")
    try:
        # Trigger the graph. The input is just a kick-off signal.
        result = app.invoke({"messages": [], "status": "start"})
        print("--- [System] Flujo completado ---")
        print(f"Estado final: {result.get('status')}")
    except Exception as e:
        print(f"--- [Error] Error critico en el agente: {e}")

# Scheduler: Run twice a day (e.g., 10:00 AM and 6:00 PM)
# For testing purposes, you can uncomment the direct call below.
schedule.every().day.at("10:00").do(run_agent_job)
schedule.every().day.at("18:00").do(run_agent_job)

# Continuous Publishing: Check every minute for approved drafts
from scheduler_service import job_publish_pending
schedule.every(1).minutes.do(job_publish_pending)

if __name__ == "__main__":
    print("BIT Community Manager (LangGraph) Iniciado.")
    print("📅 Programado para: 10:00 y 18:00 diariamente")
    print("=" * 60)
    
if __name__ == "__main__":
    import threading
    import subprocess
    import sys

    print("BIT Community Manager (LangGraph) Iniciado.")
    print("📅 Procesos activos:")
    print("   1. Generación Automática (10:00 y 18:00)")
    print("   2. Publicador Automático (Chequeo cada minuto)")
    print("   3. Interfase Visual (Dashboard)")
    print("=" * 60)

    # 1. Run Scheduler in Background Thread
    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(1)
    
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    print("✅ Motor de fondo iniciado correctamente.")

    # 2. Launch Interface (Blocking)
    print("🚀 Abriendo Interfase...")
    try:
        # Run Streamlit as a subprocess
        subprocess.run([sys.executable, "-m", "streamlit", "run", "dashboard.py"], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Cerrando sistema...")
