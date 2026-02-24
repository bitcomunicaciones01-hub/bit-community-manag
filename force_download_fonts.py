import requests
import os

FONTS = {
    "Montserrat-Bold.ttf": [
        "https://raw.githubusercontent.com/google/fonts/main/ofl/montserrat/static/Montserrat-Bold.ttf",
        "https://cdn.jsdelivr.net/npm/@fontsource/montserrat/files/montserrat-latin-700-normal.woff", 
        "https://github.com/google/fonts/raw/main/ofl/montserrat/Montserrat-Bold.ttf"
    ],
    "Montserrat-Regular.ttf": [
        "https://raw.githubusercontent.com/google/fonts/main/ofl/montserrat/static/Montserrat-Regular.ttf",
        "https://cdn.jsdelivr.net/npm/@fontsource/montserrat/files/montserrat-latin-400-normal.woff"
    ]
}

def download_file(filename, urls):
    for url in urls:
        try:
            print(f"Trying {url}...")
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                with open(filename, "wb") as f:
                    f.write(r.content)
                print(f"SUCCESS: Downloaded {filename} from {url} ({len(r.content)} bytes)")
                return True
            else:
                print(f"Failed {url}: Status {r.status_code}")
        except Exception as e:
            print(f"Error {url}: {e}")
    return False

print("Starting Font Recovery...")
for font, urls in FONTS.items():
    if download_file(font, urls):
        print(f"Validating {font}...")
        try:
            from PIL import ImageFont
            ImageFont.truetype(font, 20)
            print("Font Validated OK.")
        except Exception as e:
            print(f"Font Corrupt: {e}")
            os.remove(font)
    else:
        print(f"FAILED to download {font}")
