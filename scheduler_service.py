import schedule
import time
import os
import json
import glob
import sys
from datetime import datetime
from dotenv import load_dotenv

# Import publisher logic
# We need to reuse the publisher node logic, but isolated
from instagram_client import publish_instagram_post, publish_instagram_reel, get_instagram_client
from tiktok_client import publish_tiktok_video
from generate_image import generate_product_image

load_dotenv()

# Config
DRAFT_DIR = "./brain/drafts"
ARCHIVE_DIR = "./brain/archive"
ERROR_DIR = "./brain/errors"
os.makedirs(ARCHIVE_DIR, exist_ok=True)
os.makedirs(ERROR_DIR, exist_ok=True)

def job_publish_pending():
    print(f"\n[Scheduler] Checking for approved posts at {datetime.now()}...")
    
    # Find all approved drafts
    files = glob.glob(os.path.join(DRAFT_DIR, "*.json"))
    approved_files = []
    
    # Iterate through all approved files and check time
    for f in files:
        try:
            with open(f, "r", encoding="utf-8") as json_file:
                data = json.load(json_file)
                if data.get("approval_status") == "approved":
                    # Check if it's a future post
                    publish_time_iso = data.get("publish_time_iso")
                    if publish_time_iso:
                        try:
                            scheduled_dt = datetime.fromisoformat(publish_time_iso)
                            if datetime.now() < scheduled_dt:
                                # SKIP future posts, wait for their time to come
                                print(f"[Scheduler] FUTURE: {os.path.basename(f)} scheduled for {scheduled_dt}. Waiting.")
                                continue
                        except ValueError:
                            pass
                            
                    approved_files.append((f, data))
                    
        except Exception as e:
            print(f"Error reading {f}: {e}")
            
    # Sort candidates: prioritize those with a publish_time_iso (scheduled) 
    # and then by the scheduled time itself.
    def get_sort_key(item):
        path, data = item
        p_time = data.get("publish_time_iso")
        if p_time:
            try:
                return datetime.fromisoformat(p_time).timestamp()
            except:
                return 9999999999 # Fallback for invalid dates
        return os.path.getmtime(path) # Fallback to file mtime

    approved_files.sort(key=get_sort_key)
    
    if not approved_files:
        return

    # Pick the first one (most urgent/oldest scheduled)
    file_path, draft = approved_files[0]
    print(f"[Scheduler] Found {len(approved_files)} approved drafts. Processing most urgent: {os.path.basename(file_path)}")
    print(f"[Scheduler]   Scheduled Time: {draft.get('publish_time_iso', 'ASAP')}")
    print(f"[Scheduler]   Current Time:   {datetime.now().isoformat()}")
    
    try:
        # 1. Generate Image (Use Image Composer now)
        product = draft.get("selected_product", {})
        caption = draft.get("draft_caption", "")
        # FIX: Retrieve design settings
        design = draft.get("design_settings", {})
        did = draft.get("id", "unknown")
        
        print("   Composing branded image...")
        image_path = f"temp_publish_{datetime.now().strftime('%H%M%S')}.png"
        
        try:
            from image_composer import create_social_post
            
            # Check for custom image override (same logic as dashboard)
            custom_img_path = os.path.join(DRAFT_DIR, f"custom_img_{did}.png")
            if not os.path.exists(custom_img_path): custom_img_path = None

            final_image_path = create_social_post(
                product, 
                image_path,
                override_image_path=custom_img_path,
                remove_bg=design.get("remove_bg", False),
                design_settings=design
            )
        except Exception as e:
            print(f"   WARNING: Composition failed: {e}. Using product image fallback.")
            final_image_path = None 
            if product.get("images"):
                final_image_path = product["images"][0]
        
        # 2. Publish to chosen platform
        pref_fmt = draft.get("preferred_format", "image")
        reel_path = draft.get("reel_path")
        
        # NUEVO: Extraer fecha para programación nativa
        publish_time_iso = draft.get("publish_time_iso")
        scheduled_dt = None
        if publish_time_iso:
            try:
                scheduled_dt = datetime.fromisoformat(publish_time_iso)
                if scheduled_dt > datetime.now():
                    print(f"   FUTURE: Scheduled for {scheduled_dt}. Skipping for now...")
                    return
                scheduled_dt = None # Es hora de publicar
            except:
                pass

        res = None
        if pref_fmt == "tiktok" and reel_path and os.path.exists(reel_path):
            print("   Uploading to TIKTOK as requested...")
            res = publish_tiktok_video(video_path=reel_path, caption=caption)
        elif pref_fmt == "video" and reel_path and os.path.exists(reel_path):
            print("   Uploading to INSTAGRAM REEL as requested...")
            res = publish_instagram_reel(video_path=reel_path, caption=caption)
        else:
            print("   Uploading to INSTAGRAM PHOTO (Default or Fallback)...")
            res = publish_instagram_post(
                image_url=final_image_path if final_image_path else "placeholder.jpg",
                caption=caption
            )
        
        if res:
            publish_url = res.get("url") if isinstance(res, dict) else res
            print(f"   SUCCESS: Published! URL: {publish_url}")
            
            # 3. Archive the draft
            filename = os.path.basename(file_path)
            os.rename(file_path, os.path.join(ARCHIVE_DIR, filename))
            print("   Draft archived.")

            # 4. Cleanup Temp Image
            try:
                if final_image_path and "temp_publish" in final_image_path and os.path.exists(final_image_path):
                    os.remove(final_image_path)
                    print("   Temp image cleaned up.")
            except:
                pass
        else:
            print("   ERROR: Publishing failed. Moving to errors folder.")
            filename = os.path.basename(file_path)
            os.rename(file_path, os.path.join(ERROR_DIR, filename))
            
    except Exception as e:
        print(f"   ERROR: Critical error publishing: {e}")
        try:
            filename = os.path.basename(file_path)
            os.rename(file_path, os.path.join(ERROR_DIR, filename))
        except:
            pass

if __name__ == "__main__":
    print("[BIT Scheduler Service Started]")
    print("   Watching 'brain/drafts' for approved posts...")
    print("   Schedule: 10:00 and 18:00 daily + Check every minute (debugging)")
    
    # For production:
    # We check every minute to catch custom scheduled times accurately
    schedule.every(1).minutes.do(job_publish_pending)
    
    # Initial check
    job_publish_pending()
    
    # Loop de scheduler
    if os.getenv("RUN_ONCE") == "true":
        print("\n[Scheduler] RUN_ONCE detectado. Saliendo.")
    else:
        while True:
            schedule.run_pending()
            time.sleep(60)
