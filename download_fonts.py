import requests
import os

fonts = {
    "Montserrat-Bold.ttf": "https://github.com/google/fonts/raw/main/ofl/montserrat/Montserrat-Bold.ttf",
    "Montserrat-Regular.ttf": "https://github.com/google/fonts/raw/main/ofl/montserrat/Montserrat-Regular.ttf"
}

for name, url in fonts.items():
    print(f"Downloading {name}...")
    try:
        r = requests.get(url)
        with open(name, "wb") as f:
            f.write(r.content)
        print("OK")
    except Exception as e:
        print(f"Failed: {e}")
