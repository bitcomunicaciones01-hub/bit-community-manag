from fastapi import FastAPI, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import os
from graph import app as agent_app

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global State
current_status = {"status": "idle", "logs": [], "result": None}

class AgentRequest(BaseModel):
    mode: str = "manual"

def run_agent_task():
    global current_status
    current_status["status"] = "running"
    current_status["logs"] = ["🚀 Agent Initialized..."]
    current_status["result"] = None
    
    try:
        current_status["logs"].append("🎵 Fetching Top 5 from Spotify/Web...")
        
        # Invoke Agent
        inputs = {"retry_count": 0}
        result = agent_app.invoke(inputs)
        
        current_status["status"] = "completed"
        current_status["logs"].append("✅ Workflow Finished Successfully.")
        current_status["result"] = {
            "image": result.get("image_url", ""),
            "caption": result.get("draft_caption", ""),
            "research": result.get("research_summary", ""),
            "critique": result.get("critique_feedback", "")
        }
    except Exception as e:
        current_status["status"] = "error"
        current_status["logs"].append(f"❌ Error: {str(e)}")

@app.get("/api/status")
async def get_status():
    return current_status

@app.post("/api/run")
async def run_agent(background_tasks: BackgroundTasks):
    if current_status["status"] == "running":
        return {"message": "Agent is already running."}
    
    background_tasks.add_task(run_agent_task)
    return {"message": "Agent started."}

# Serve Static Files (Frontend)
app.mount("/", StaticFiles(directory="ui", html=True), name="static")

if __name__ == "__main__":
    print("🚀 Starting FUTURA RADIO 2099 Server...")
    print("📡 Opening UI in browser...")
    
    # Auto-open browser
    import webbrowser
    import threading
    import time
    
    def open_browser():
        time.sleep(1.5)
        webbrowser.open("http://localhost:8000")
    
    threading.Thread(target=open_browser, daemon=True).start()
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
