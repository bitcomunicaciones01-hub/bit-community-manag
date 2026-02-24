import os
import requests
from openai import OpenAI
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont
import io

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_product_image(product, custom_prompt=None):
    """
    Generate product image using DALL-E 3 with BIT branding.
    
    Args:
        product: Product dictionary with name, categories, etc.
        custom_prompt: Optional custom prompt override
    
    Returns:
        URL of generated image or None if failed
    """
    try:
        product_name = product.get("name", "Repuesto de notebook")
        categories = product.get("categories", [])
        
        # Build prompt with BIT brand identity
        if custom_prompt:
            prompt = custom_prompt
        else:
            # Extract component type
            component_type = "repuesto de notebook"
            if categories:
                component_type = categories[0].lower()
            
            prompt = f"""Professional product photography for {product_name}.
            
Style: Clean, modern, tech-focused e-commerce product shot.
Background: White or light gray gradient, professional studio lighting.
Colors: Incorporate green (#00AA00) and navy blue (#1E3A8A) accent elements.
Composition: Product centered, well-lit, high detail, sharp focus.
Mood: Professional, trustworthy, high-quality.
Format: Square 1024x1024, Instagram-ready.

DO NOT include: Futuristic elements, neon lights, cyberpunk aesthetics, text overlays.
DO include: Clean professional look, subtle green/blue color accents in background or lighting."""

        print(f"🎨 Generating image with DALL-E 3...")
        print(f"   Prompt: {prompt[:100]}...")
        
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        
        image_url = response.data[0].url
        print(f"✅ Image generated: {image_url}")
        
        return image_url
        
    except Exception as e:
        print(f"❌ Error generating image: {e}")
        return None

def add_brand_overlay(image_url, output_path="./temp_branded_image.jpg"):
    """
    Download image and add BIT branding overlay (logo, colors).
    
    Args:
        image_url: URL of the image to brand
        output_path: Where to save the branded image
    
    Returns:
        Path to branded image or None if failed
    """
    try:
        # Download image
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        
        img = Image.open(io.BytesIO(response.content))
        
        # Convert to RGB if necessary
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Create drawing context
        draw = ImageDraw.Draw(img)
        
        # Add subtle brand color border (green)
        border_width = 10
        brand_green = (0, 170, 0)  # #00AA00
        
        # Draw border
        width, height = img.size
        draw.rectangle(
            [(0, 0), (width, border_width)],  # Top
            fill=brand_green
        )
        draw.rectangle(
            [(0, height - border_width), (width, height)],  # Bottom
            fill=brand_green
        )
        
        # Save
        img.save(output_path, 'JPEG', quality=95)
        print(f"✅ Branded image saved: {output_path}")
        
        return output_path
        
    except Exception as e:
        print(f"❌ Error adding brand overlay: {e}")
        return None

def generate_branded_product_image(product, custom_prompt=None, add_overlay=False):
    """
    Generate and optionally brand a product image.
    
    Args:
        product: Product dictionary
        custom_prompt: Optional custom prompt
        add_overlay: Whether to add brand overlay
    
    Returns:
        Image URL or local path if overlay was added
    """
    # Generate base image
    image_url = generate_product_image(product, custom_prompt)
    
    if not image_url:
        return None
    
    # Optionally add branding
    if add_overlay:
        return add_brand_overlay(image_url)
    else:
        return image_url

if __name__ == "__main__":
    # Test image generation
    print("=" * 80)
    print("IMAGE GENERATION TEST - BIT Comunicaciones")
    print("=" * 80)
    
    test_product = {
        "name": "Batería Original HP Pavilion 15",
        "categories": ["Baterías", "HP", "Repuestos de Notebook"],
        "price": "25000"
    }
    
    print(f"\n📦 Test Product: {test_product['name']}")
    print(f"   Categories: {', '.join(test_product['categories'])}")
    
    # Generate image
    image_url = generate_branded_product_image(
        product=test_product,
        add_overlay=False  # Set to True to add green border
    )
    
    if image_url:
        print(f"\n✅ SUCCESS!")
        print(f"   Image URL: {image_url}")
        print(f"\n💡 You can now use this image in Instagram posts")
    else:
        print(f"\n❌ FAILED to generate image")
    
    print("\n" + "=" * 80)
