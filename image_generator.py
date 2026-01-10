import os
import base64
import hashlib
import requests
from pathlib import Path
from typing import Optional

# Create directory for storing generated images
IMAGES_DIR = Path("generated_images")
IMAGES_DIR.mkdir(exist_ok=True)

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")


def optimize_image_prompt(caption: str, niche: str) -> str:
    """
    Enhance the image prompt for better generation
    Adds technical details for high-quality output
    """
    base_prompt = f"""Professional photography of {niche}: {caption}

Style: Clean, bright, appetizing, Instagram-worthy
Lighting: Natural daylight, soft shadows
Composition: Rule of thirds, shallow depth of field
Setting: Modern, minimal, organic aesthetic
Quality: High resolution, sharp focus, 4K
Mood: Fresh, healthy, inviting
No text, no watermarks."""
    
    return base_prompt.strip()


def generate_image_with_stability(prompt: str,base_url) -> dict:
    """
    Generate image using Stability AI (SDXL)
    Get free API key: https://platform.stability.ai/account/keys
    """
    api_key = os.getenv("STABILITY_API_KEY")
    
    if not api_key:
        print("⚠️ STABILITY_API_KEY not found in .env")
        return create_placeholder_response()
    
    url = "https://api.stability.ai/v2beta/stable-image/generate/sd3"
    
    headers = {
        "authorization": f"Bearer {api_key}",
        "accept": "image/*"
    }
    
    data = {
        "prompt": prompt,
        "output_format": "png",
        "aspect_ratio": "1:1",
        "model": "sd3-large"
    }
    
    try:
        print(f"🎨 Calling Stability AI API...")
        response = requests.post(
            url, 
            headers=headers, 
            files={"none": ''}, 
            data=data, 
            timeout=60  # Increased timeout for image generation
        )
        
        if response.status_code == 200:
            # Save image
            prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:10]
            filename = f"image_{prompt_hash}.png"
            filepath = IMAGES_DIR / filename
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            # Convert to base64
            image_base64 = base64.b64encode(response.content).decode()
            
            complete_url = f"{base_url}/images/{filename}"
            
            print(f"✅ Image generated and saved: {filepath}")
            
            return {
                "imageUrl": complete_url,
                "imageBase64": image_base64,
                "localPath": str(filepath)
            }
        else:
            error_detail = response.text[:200] if response.text else "Unknown error"
            print(f"❌ Stability AI returned {response.status_code}: {error_detail}")
            
            # Check for specific errors
            if response.status_code == 401:
                print("🔑 Invalid API key. Get one at: https://platform.stability.ai/account/keys")
            elif response.status_code == 402:
                print("💳 Insufficient credits. Add credits at: https://platform.stability.ai/account/billing")
            
            return create_placeholder_response()
            
    except requests.exceptions.Timeout:
        print(f"⏱️ Request timed out after 60s")
        return create_placeholder_response()
    except Exception as e:
        print(f"❌ Image generation error: {type(e).__name__}: {e}")
        return create_placeholder_response()


def create_placeholder_image() -> dict:
    """
    Create an actual placeholder image file using PIL
    """
    from PIL import Image, ImageDraw, ImageFont
    
    # Create 1080x1080 image
    img = Image.new('RGB', (1080, 1080), color='#f0f0f0')
    draw = ImageDraw.Draw(img)
    
    # Add text
    try:
        # Try to use default font
        font = ImageFont.truetype("arial.ttf", 60)
    except:
        font = ImageFont.load_default()
    
    text = "Mushroom Image\nPlaceholder"
    
    # Get text bounding box
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Center text
    position = ((1080 - text_width) // 2, (1080 - text_height) // 2)
    draw.text(position, text, fill='#666666', font=font)
    
    # Save
    filepath = IMAGES_DIR / "placeholder.png"
    img.save(filepath, "PNG")
    
    # Convert to base64
    import io
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    image_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    return {
        "imageUrl": "/images/placeholder.png",
        "imageBase64": image_base64,
        "localPath": str(filepath)
    }


def create_placeholder_response() -> dict:
    """
    Return placeholder - create if doesn't exist
    """
    placeholder_path = IMAGES_DIR / "placeholder.png"
    
    # Create placeholder if it doesn't exist
    if not placeholder_path.exists():
        return create_placeholder_image()
    
    return {
        "imageUrl": "/images/placeholder.png",
        "imageBase64": None,
        "error": "Image generation not configured"
    }


def generate_image_with_imagen(prompt: str, save_locally: bool = True) -> dict:
    """
    Main function: Try multiple providers with fallback
    Priority: Stability AI > Replicate > Placeholder
    
    Note: Google Imagen is not available in the current SDK version
    """
    
    print(f"🎨 Attempting to generate image...")
    
    # Try Stability AI first
    if os.getenv("STABILITY_API_KEY"):
        print("📍 Using Stability AI...")
        result = generate_image_with_stability(prompt,BASE_URL)
        if result.get("imageUrl") and "placeholder" not in result.get("imageUrl", "").lower():
            return result
        print("⚠️ Stability AI failed, trying next provider...")
    
    # Return placeholder if all fail
    print("⚠️ No image API configured. Add STABILITY_API_KEY or REPLICATE_API_TOKEN to .env")
    return create_placeholder_response()