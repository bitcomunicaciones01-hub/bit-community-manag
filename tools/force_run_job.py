
import sys
import os
import time
from datetime import datetime
from dotenv import load_dotenv

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Load environment variables
load_dotenv()

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from graph import app

def force_run_job():
    print(f"[Force Run] Starting immediate job execution at {datetime.now()}")
    print(f"[Force Run] AUTO_APPROVE is set to: {os.getenv('AUTO_APPROVE')}")
    
    inputs = {
        "status": "start",
        "recent_products": [],
        "selected_product": {},
        "research_summary": "",
        "draft_caption": "",
        "image_prompt": "",
        "image_url": "",
        "publish_time_iso": "",
        "critique_feedback": "",
        "retry_count": 0,
        "approval_status": "pending"
    }
    
    print("[Force Run] Invoking graph...")
    try:
        # Stream events from the graph
        for event in app.stream(inputs):
            for key, value in event.items():
                print(f"[Node] Node finished: {key}")
                # Optional: Print approval status if available
                if "approval_status" in value:
                     print(f"   Status: {value['approval_status']}")
                     
        print("[Force Run] Job completed successfully.")
        
    except Exception as e:
        print(f"[Error] Job failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    force_run_job()
