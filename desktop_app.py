import sys
import os
import threading
import time
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtCore import QObject, pyqtSlot, QUrl, pyqtSignal
from dotenv import load_dotenv

load_dotenv()

# Import agent
try:
    from graph import app as agent_app
    AGENT_AVAILABLE = True
except:
    AGENT_AVAILABLE = False
    print("⚠️ Agent not available")

class AgentBridge(QObject):
    """Bridge between Python and JavaScript"""
    
    logSignal = pyqtSignal(str, str)  # message, type
    statusSignal = pyqtSignal(str)
    resultSignal = pyqtSignal(str, str)  # image_url, caption
    
    def __init__(self):
        super().__init__()
        self.running = False
    
    @pyqtSlot()
    def runAgent(self):
        if self.running:
            return
        
        self.running = True
        self.statusSignal.emit("PROCESSING...")
        self.logSignal.emit("Initializing Agent Workflow...", "info")
        
        def worker():
            try:
                time.sleep(0.5)
                
                if AGENT_AVAILABLE:
                    self.logSignal.emit("Connecting to Spotify Node...", "info")
                    self.logSignal.emit("Calling AI Agent (GPT-5 mini)...", "info")
                    
                    result = agent_app.invoke({"retry_count": 0})
                    
                    self.logSignal.emit("Workflow Complete. Parsing Data...", "info")
                    
                    self.logSignal.emit(f"DEBUG: Keys extracted: {list(result.keys())}", "info")
                    
                    caption = result.get("draft_caption", "Error generating caption")
                    image_url = result.get("image_url", "")
                    
                    self.logSignal.emit(f"DEBUG: Image URL: {image_url}", "info")

                    self.resultSignal.emit(image_url, caption)
                    self.logSignal.emit("✅ MISSION SUCCESSFUL", "success")
                    self.statusSignal.emit("MISSION COMPLETE")
                else:
                    self.logSignal.emit("⚠️ Agent not available", "error")
                    self.logSignal.emit("Running simulation...", "info")
                    time.sleep(2)
                    self.resultSignal.emit("", "Simulation: AI-generated caption would appear here.")
                    self.logSignal.emit("✅ Simulation complete", "success")
                    self.statusSignal.emit("SIMULATION COMPLETE")
                
            except Exception as e:
                self.logSignal.emit(f"❌ ERROR: {str(e)}", "error")
                self.statusSignal.emit("SYSTEM FAILURE")
            finally:
                self.running = False
        
        threading.Thread(target=worker, daemon=True).start()

class FuturaRadioApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("FUTURA RADIO 2099 - AI MANAGER")
        self.setGeometry(100, 100, 1400, 900)
        
        # Create web view
        self.browser = QWebEngineView()
        
        # Setup bridge
        self.bridge = AgentBridge()
        self.channel = QWebChannel()
        self.channel.registerObject("bridge", self.bridge)
        self.browser.page().setWebChannel(self.channel)
        
        # Load HTML
        html_path = os.path.join(os.path.dirname(__file__), "ui", "desktop.html")
        self.browser.setUrl(QUrl.fromLocalFile(html_path))
        
        self.setCentralWidget(self.browser)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FuturaRadioApp()
    window.show()
    sys.exit(app.exec())
