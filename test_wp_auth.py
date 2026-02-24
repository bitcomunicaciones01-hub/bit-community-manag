from woocommerce_client import wcapi
import os
import requests

def test_upload():
    # Create a dummy image if not exists
    if not os.path.exists("test_upload.jpg"):
        # Download a placeholder
        img_data = requests.get("https://via.placeholder.com/150").content
        with open("test_upload.jpg", "wb") as f:
            f.write(img_data)
        print("Created dummy image test_upload.jpg")

    # The Endpoint for media in WP REST API is /wp-json/wp/v2/media
    # But wcapi is initialized with /wc/v3. 
    # We might need to use a raw request or valid wcapi endpoint?
    # Actually, wcapi object (Python wrapper) usually allows calling other endpoints?
    # Let's try passing the full path if the wrapper supports it, or use requests with the same auth.
    
    # The woocommerce python lib signs requests for WC. 
    # For WP media, we typically need Basic Auth or JWT. 
    # WC keys might NOT work for WP core endpoints unless permissions are set broadly.
    # Let's try using the wcapi wrapper to hit a WC endpoint or see if we can hack it.
    
    # Official WC API doesn't have "Upload Media" (it's a WP core feature).
    # However, creating a product allows passing an image URL, not file.
    
    # Let's try to verify if we can use the credentials to post to /wp-json/wp/v2/media
    
    url = os.getenv("WOOCOMMERCE_URL") + "/wp-json/wp/v2/media"
    consumer_key = os.getenv("WOOCOMMERCE_CONSUMER_KEY")
    consumer_secret = os.getenv("WOOCOMMERCE_CONSUMER_SECRET")
    
    # WC Consumer Keys usually work for WP REST API if authentication method is set to "Query String" or headers.
    # But often Basic Auth (Application Passwords) is required for WP.
    
    print(f"Attempting upload to {url}...")
    
    with open("test_upload.jpg", "rb") as img:
        headers = {
            "Content-Disposition": "attachment; filename=test_upload.jpg",
            "Content-Type": "image/jpeg"
        }
        # Try Basic Auth with CK/CS? Usually not. 
        # But let's try the wcapi's internal session if possible.
        pass

    # Alternative: Use Requests with Basic Auth if the user has it? 
    # They only provided WC keys in .env.
    
    # If we can't upload to WP, we can't use Graph API easily from local.
    # Let's try a simple GET to WP API to check auth.
    
    test_url = os.getenv("WOOCOMMERCE_URL") + "/wp-json/wp/v2/users/me"
    print(f"Checking auth against {test_url}")
    
    # Try using WC auth
    res = requests.get(test_url, auth=(consumer_key, consumer_secret))
    print(f"Status: {res.status_code}")
    print(res.text[:200])

if __name__ == "__main__":
    test_upload()
