from PIL import Image, ImageDraw, ImageFont, ImageChops
import requests
import io
import os
from dotenv import load_dotenv
import textwrap

load_dotenv()

# Constants
CANVAS_SIZE = (1080, 1080)
BLUE_DARK = (20, 40, 80)
GREEN_BIT = (0, 160, 0)
WHITE = (255, 255, 255)

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "brand_assets")
ROBOT_PATH = os.path.join(ASSETS_DIR, "bit_robot.png")
FONT_BOLD_PATH = os.path.join(BASE_DIR, "Montserrat-Bold.ttf")
FONT_REG_PATH = os.path.join(BASE_DIR, "Montserrat-Regular.ttf")
ARIAL_BOLD_PATH = os.path.join(BASE_DIR, "arialbd.ttf")

def download_image(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        return Image.open(io.BytesIO(response.content)).convert("RGBA")
    except: return None

def get_font(path_primary, path_fallback, size):
    try:
        if os.path.exists(path_primary): return ImageFont.truetype(path_primary, size)
    except:
        try: return ImageFont.truetype(path_fallback, size)
        except: return ImageFont.load_default()

def trim_whitespace(img):
    try:
        bg = Image.new(img.mode, img.size, img.getpixel((0,0)))
        diff = ImageChops.difference(img, bg)
        diff = ImageChops.add(diff, diff, 2.0, -100)
        bbox = diff.getbbox()
        if bbox: return img.crop(bbox)
    except: pass
    return img

def remove_white_background(img, threshold=240):
    """V37: Balanced threshold 240."""
    img = img.convert("RGBA")
    grayscale = img.convert("L")
    mask = grayscale.point(lambda x: 0 if x > threshold else 255)
    img.putalpha(mask)
    return img

def create_social_post(product, output_path="temp_post.png", override_image_path=None, remove_bg=False, design_settings={}):
    """Layout V37: The Final Stable Pro Layout."""
    title_text = design_settings.get("title_override") or product.get("name", "Producto")
    product_scale = design_settings.get("product_scale", 1.0)
    show_logo = design_settings.get("show_logo", True)
    
    TEMPLATE_PATH = os.path.join(ASSETS_DIR, "template.png")
    using_template = False
    
    if os.path.exists(TEMPLATE_PATH):
        try:
            img = Image.open(TEMPLATE_PATH).convert("RGBA" if show_logo else "RGB")
            img = img.resize(CANVAS_SIZE)
            using_template = True
        except:
            img = Image.new('RGB', CANVAS_SIZE, WHITE)
    else:
        img = Image.new('RGB', CANVAS_SIZE, WHITE)
        
    draw = ImageDraw.Draw(img)
    
    # --- TITLE (72pt, up to 3 lines) ---
    title_y_offset = design_settings.get("title_y_offset", 0)
    title_scale = design_settings.get("title_scale", 1.0)
    current_title_font = get_font(FONT_BOLD_PATH, ARIAL_BOLD_PATH, int(72 * title_scale))
    
    # Start higher to fit 3 lines safely
    SAFE_TOP = 95 + title_y_offset
    TITLE_FILL = BLUE_DARK if using_template else WHITE
    
    if not using_template:
        draw.rectangle([(0,0), (1080, 280)], fill=BLUE_DARK)

    name_upper = title_text.upper()
    lines = textwrap.wrap(name_upper, width=int(22 / title_scale))
    current_y = SAFE_TOP
    for line in lines[:3]: # Support up to 3 lines for long technical names
        bbox = draw.textbbox((0, 0), line, font=current_title_font)
        x = (CANVAS_SIZE[0] - (bbox[2]-bbox[0])) // 2
        draw.text((x, current_y), line, font=current_title_font, fill=TITLE_FILL)
        current_y += int(82 * title_scale)

    # --- MASCOT (No double robot if using template) ---
    if show_logo and not using_template and os.path.exists(ROBOT_PATH):
        try:
            r_img = Image.open(ROBOT_PATH).convert("RGBA")
            ratio = 240 / r_img.height
            r_img = r_img.resize((int(r_img.width * ratio), 240), Image.Resampling.LANCZOS)
            img.paste(r_img, (50, 830), r_img)
        except: pass

    # --- PRODUCT PROCESSING V37 ---
    p_img = None
    if override_image_path and os.path.exists(override_image_path):
        try: p_img = Image.open(override_image_path).convert("RGBA")
        except: pass
    if not p_img:
        imgs = product.get("images", [])
        if imgs: p_img = download_image(imgs[0])

    if p_img:
        # 1. Transparency (Sweet spot 240)
        if remove_bg: p_img = remove_white_background(p_img, threshold=240)
        
        # 2. LOGO REMOVAL (Surgical Corner-Mask BEFORE trimming)
        if not show_logo:
            p_draw = ImageDraw.Draw(p_img)
            pw, ph = p_img.size
            # Corner mask (Bottom-Left) for BIT robot
            mw, mh = int(pw * 0.28), int(ph * 0.22)
            p_draw.rectangle([(0, ph-mh), (mw, ph)], fill=(0,0,0,0) if p_img.mode == "RGBA" else WHITE)
            
        # 3. Trim (Maximizes product size)
        p_img = trim_whitespace(p_img)
        
        # Scale & Position
        max_w, max_h = 980 * product_scale, 650 * product_scale
        ratio = min(max_w / p_img.width, max_h / p_img.height)
        new_size = (int(p_img.width * ratio), int(p_img.height * ratio))
        p_img = p_img.resize(new_size, Image.Resampling.LANCZOS)
        
        pos_x = (CANVAS_SIZE[0] - new_size[0]) // 2 + design_settings.get("product_x_offset", 0)
        # Center in Body (below titles)
        pos_y = 580 - (new_size[1] // 2) + design_settings.get("product_y_offset", 0)
        img.paste(p_img, (pos_x, int(pos_y)), p_img if p_img.mode == "RGBA" else None)

    img.save(output_path, quality=95)
    return output_path
