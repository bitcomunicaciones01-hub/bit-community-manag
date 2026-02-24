from image_composer import create_social_post
import json
import os

# Mock data based on the failing draft
product = {
    "name": "Placa Madre Notebook Cx Cx23800w Intel N4020 Lista Para Usar",
    "images": ["https://bitcomunicaciones.com/wp-content/uploads/2025/07/Cx2800w-7-500x500-1.png"]
}

design_settings = {
    "title_override": "Placa Madre Notebook Cx Cx23800w Intel N4020 Lista Para Usar",
    "product_scale": 1.0,
    "title_scale": 1.0,
    "show_logo": True,
    "show_footer": True,
    "remove_bg": True,  # THIS IS KEY
    "title_y_offset": 0,
    "product_y_offset": 90,
    "product_x_offset": 0
}

output = "debug_output.png"

print("--- Starting Debug Composer ---")
try:
    final_path = create_social_post(
        product, 
        output,
        override_image_path=None, 
        remove_bg=True,  # Passing explicit True as scheduler does
        design_settings=design_settings
    )
    print(f"Success! Image saved to {final_path}")
except Exception as e:
    print(f"CRITICAL ERROR: {e}")
