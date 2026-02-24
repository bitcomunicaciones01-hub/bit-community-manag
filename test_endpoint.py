import os
from instagrapi import Client
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

USERNAME = os.getenv("INSTAGRAM_USERNAME")
PASSWORD = os.getenv("INSTAGRAM_PASSWORD")

def test_scheduled_endpoint():
    cl = Client()
    print(f"Logging in as {USERNAME}...")
    cl.login(USERNAME, PASSWORD)
    
    # Fake device data or use client's
    upload_id = "1234567890123" # Dummy
    future_time = int((datetime.now() + timedelta(hours=2)).timestamp())
    
    data = {
        "scheduled_publish_time": str(future_time),
        "timezone_offset": str(cl.timezone_offset),
        "source_type": "4",
        "caption": "Test scheduled endpoint",
        "upload_id": upload_id,
        "device": cl.device
    }
    
    print(f"Trying media/configure_to_scheduled/ with timestamp {future_time}...")
    try:
        # We expect a 400 because the upload_id is fake, 
        # but the error message will confirm if the endpoint exists.
        res = cl.private.post("media/configure_to_scheduled/", data=cl.with_default_data(data))
        print("Response status:", res.status_code)
        print("Response text:", res.text)
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    test_scheduled_endpoint()
