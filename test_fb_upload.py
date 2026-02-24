import os
import requests
from dotenv import load_dotenv

load_dotenv()

def create_dummy_image():
    # Create a 100x100 red image
    from PIL import Image
    img = Image.new('RGB', (100, 100), color = 'red')
    img.save('test_fb.jpg')
    return 'test_fb.jpg'

def test_fb_upload():
    # 1. Create dummy image
    try:
        filename = create_dummy_image()
    except ImportError:
        # Fallback if PIL not installed (though it should be)
        with open("test_fb.jpg", "wb") as f:
            f.write(b'\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xFF\xDB\x00C\x00\x08...')
        filename = "test_fb.jpg"

    page_id = os.getenv("FACEBOOK_PAGE_ID")
    access_token = os.getenv("META_ACCESS_TOKEN")
    
    if not page_id or not access_token:
        print("Error: Missing credentials")
        return

    url = f"https://graph.facebook.com/v19.0/{page_id}/photos"
    
    print(f"Uploading to FB Page {page_id}...")
    
    with open(filename, "rb") as img:
        payload = {
            "access_token": access_token,
            "published": "false",
            "message": "Debug Upload - Temporary"
        }
        files = {
            "source": img
        }
        
        res = requests.post(url, data=payload, files=files)
        
        print(f"Status: {res.status_code}")
        try:
            data = res.json()
            if "id" in data:
                photo_id = data["id"]
                print(f"Initial ID: {photo_id}")
                
                # Now fetch the URL
                field_url = f"https://graph.facebook.com/v19.0/{photo_id}?fields=images,source&access_token={access_token}"
                res2 = requests.get(field_url)
                data2 = res2.json()
                print(f"Image Data: {data2.keys()}")
                if "source" in data2:
                    print(f"SUCCESS! Public URL: {data2['source']}")
                elif "images" in data2:
                    print(f"SUCCESS! Public URL: {data2['images'][0]['source']}")
            else:
                print(f"Error: {data}")
        except Exception as e:
            print(f"Parse Error: {e} - {res.text}")

if __name__ == "__main__":
    test_fb_upload()
