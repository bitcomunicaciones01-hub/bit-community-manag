
import os
import json
import sys
from datetime import datetime, timedelta
from scheduler_service import job_publish_pending
import shutil

# Config
DRAFT_DIR = "./brain/drafts"
TEST_DRAFT = os.path.join(DRAFT_DIR, "test_schedule_fix.json")

if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

def create_test_draft():
    # Schedule for 25 minutes from now
    future_time = (datetime.now() + timedelta(minutes=25)).isoformat()
    
    draft_data = {
        "id": "test_schedule_fix",
        "approval_status": "approved",
        "publish_time_iso": future_time,
        "selected_product": {
            "id": 99999,
            "name": "Test Product Fix",
            "images": ["https://picsum.photos/500/500"]
        },
        "draft_caption": "Test caption for native scheduling fix #BITComunicaciones",
        "preferred_format": "image",
        "design_settings": {
            "show_logo": False,
            "remove_bg": False
        }
    }
    
    os.makedirs(DRAFT_DIR, exist_ok=True)
    with open(TEST_DRAFT, "w", encoding="utf-8") as f:
        json.dump(draft_data, f, indent=2)
    
    print(f"Created test draft scheduled for: {future_time}")
    return TEST_DRAFT

def run_test():
    draft_path = create_test_draft()
    print("Running scheduler job...")
    
    # We set RUN_ONCE=true to prevent the loop
    os.environ["RUN_ONCE"] = "true"
    
    try:
        job_publish_pending()
        print("\n[VERIFICATION] Check the terminal logs above.")
        print("Expected behavior: '[Scheduler] FUTURE DETECTED' and 'Programando Reel nativo para timestamp: {timestamp}'")
    except Exception as e:
        print(f"Error during test: {e}")
    finally:
        # Cleanup is optional but good
        # if os.path.exists(draft_path):
        #     os.remove(draft_path)
        pass

if __name__ == "__main__":
    run_test()
