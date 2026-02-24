import os
import subprocess
import json
import textwrap
import math
import random
import requests
import io
from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageFilter
from dotenv import load_dotenv

load_dotenv()

REEL_SIZE = (1080, 1920)
BLUE_DARK = (20, 40, 80)
GREEN_BIT = (0, 160, 0)
WHITE = (255, 255, 255)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "brand_assets")
FONT_BOLD_PATH = os.path.join(BASE_DIR, "Montserrat-Bold.ttf")
ARIAL_BOLD_PATH = os.path.join(BASE_DIR, "arialbd.ttf")

def download_image(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=15)
        return Image.open(io.BytesIO(response.content)).convert("RGBA")
    except: return None

def get_font_master(path_primary, path_fallback, size):
    try:
        if os.path.exists(path_primary) and os.path.getsize(path_primary) > 10000: # Check it's a real font
            return ImageFont.truetype(path_primary, size)
    except: pass
    try:
        if os.path.exists(path_fallback): return ImageFont.truetype(path_fallback, size)
    except: pass
    return ImageFont.load_default()

def trim_whitespace(img):
    try:
        bbox = img.getbbox()
        if bbox: return img.crop(bbox)
    except: pass
    return img

def remove_white_background_v37(img, threshold=240):
    img = img.convert("RGBA")
    gray = img.convert("L")
    mask = gray.point(lambda p: 0 if p > threshold else 255)
    img.putalpha(mask)
    return img

def get_base_bg():
    TEMPLATE_PATH = os.path.join(ASSETS_DIR, "template.png")
    bg = Image.new("RGB", REEL_SIZE, WHITE)
    if os.path.exists(TEMPLATE_PATH):
        try:
            temp = Image.open(TEMPLATE_PATH).convert("RGB")
            tw, th = temp.size
            ratio = 1080 / tw
            new_h = int(th * ratio)
            temp = temp.resize((1080, new_h), Image.Resampling.LANCZOS)
            bg.paste(temp, (0, REEL_SIZE[1] - new_h))
        except: pass
    return bg

def create_reel_video(product, output_path, override_image_path=None, design_settings={}):
    """Elite Pro V37: Final Sincronized Stability."""
    temp_dir = os.path.join("brain", "temp_frames")
    os.makedirs(temp_dir, exist_ok=True)
    
    p_img = None
    if override_image_path and os.path.exists(override_image_path):
        try: p_img = Image.open(override_image_path).convert("RGBA")
        except: pass
    if not p_img:
        imgs = product.get("images", [])
        if imgs: p_img = download_image(imgs[0])

    if not p_img: return None

    # Pipeline V37 Sync
    if design_settings.get("remove_bg", True):
        p_img = remove_white_background_v37(p_img, threshold=240)
    
    if not design_settings.get("show_logo", True):
        p_draw = ImageDraw.Draw(p_img)
        pw, ph = p_img.size
        # Corner mask (Bottom-Left)
        mw, mh = int(pw * 0.28), int(ph * 0.22)
        p_draw.rectangle([(0, ph-mh), (mw, ph)], fill=(0,0,0,0))
    
    p_img = trim_whitespace(p_img)
    
    name = (design_settings.get("title_override") or product.get("name", "Producto")).upper()
    price_txt = f"${product.get('price', '0')}"
    # V40.6: Scaled Pro Sizing (Reels 9:16) - Match static post feel
    title_font = get_font_master(FONT_BOLD_PATH, ARIAL_BOLD_PATH, 50) 
    price_font = get_font_master(FONT_BOLD_PATH, ARIAL_BOLD_PATH, 45)
    
    total_frames = 150
    bg_full = get_base_bg()
    
    for i in range(total_frames):
        progress = i / total_frames
        frame = bg_full.copy()
        draw = ImageDraw.Draw(frame)
        
        zoom = 1.0 + (0.12 * progress)
        lev = int(22 * math.sin(progress * 3 * math.pi))
        
        target_w = int(920 * zoom * design_settings.get("product_scale", 1.0))
        ratio = target_w / p_img.width
        p_res = p_img.resize((target_w, int(p_img.height * ratio)), Image.Resampling.LANCZOS)
        
        cw, ch = p_res.size
        pos_y = 580 + ((750 - ch) // 2) + lev
        frame.paste(p_res, ((1080-cw)//2, pos_y), p_res)
        
        if progress > 0.1:
            # Wrap for perfect scale look
            lines = textwrap.wrap(name, width=int(22 / design_settings.get("title_scale", 1.0)))
            y_t = 150 # Balanced top margin
            for line in lines[:3]:
                bbox = draw.textbbox((0,0), line, font=title_font)
                draw.text(((1080-(bbox[2]-bbox[0]))//2, y_t), line, font=title_font, fill=BLUE_DARK)
                y_t += 55 # Tight proportional line spacing
        
        if progress > 0.4:
            bbox = draw.textbbox((0,0), price_txt, font=price_font)
            pw = bbox[2]-bbox[0]
            # V40.6: Centered for smaller text
            draw.rounded_rectangle([(540-pw//2-30, 1420), (540+pw//2+30, 1550)], radius=65, fill=GREEN_BIT)
            draw.text((540-pw//2, 1455), price_txt, font=price_font, fill=WHITE)

        frame.save(os.path.join(temp_dir, f"frame_{i:04d}.jpg"), "JPEG")

    try:
        subprocess.run(['ffmpeg', '-y', '-framerate', '30', '-i', os.path.join(temp_dir, 'frame_%04d.jpg'), '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', output_path], check=True)
        for f in os.listdir(temp_dir): os.remove(os.path.join(temp_dir, f))
        os.rmdir(temp_dir)
        return output_path
    except: return None
