import requests
import os

url = "https://raw.githubusercontent.com/google/fonts/main/ofl/montserrat/Montserrat-Bold.ttf"
dest = "Montserrat-Bold.ttf"

print(f"Downloading {url}...")
try:
    r = requests.get(url)
    r.raise_for_status()
    with open(dest, "wb") as f:
        f.write(r.content)
    print(f"Downloaded {len(r.content)} bytes to {dest}")
except Exception as e:
    print(f"Error: {e}")
