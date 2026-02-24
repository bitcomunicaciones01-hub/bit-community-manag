import os
import requests
import base64

def create_dummy_image():
    # Create a 1x1 pixel white image (GIF)
    # 1x1 pixel transparent GIF
    data = b'R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7'
    with open("test_upload.gif", "wb") as f:
        f.write(base64.b64decode(data))
    return "test_upload.gif"

def test_upload():
    filename = create_dummy_image()
    
    base_url = os.getenv("WOOCOMMERCE_URL") # https://bitcomunicaciones.com
    ck = os.getenv("WOOCOMMERCE_CONSUMER_KEY")
    cs = os.getenv("WOOCOMMERCE_CONSUMER_SECRET")
    
    # Try WP REST API Media Endpoint
    # Url: /wp-json/wp/v2/media
    url = f"{base_url}/wp-json/wp/v2/media"
    
    print(f"Uploading to {url}...")
    
    with open(filename, "rb") as img:
        headers = {
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Type": "image/gif"
        }
        
        # Method 1: Basic Auth using WC Keys
        # This often works if the server accepts Basic Auth for REST API
        try:
            res = requests.post(url, headers=headers, data=img, auth=(ck, cs), timeout=30)
            print(f"Status: {res.status_code}")
            if res.status_code == 201:
                print("SUCCESS! Image uploaded.")
                print(f"URL: {res.json().get('source_url')}")
            else:
                print("Failed.")
                print(res.text[:500])
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    test_upload()
