import os
import random
import requests
import urllib.parse
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv

load_dotenv()

# Configure Cloudinary
cloudinary.config( 
  cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME"), 
  api_key = os.getenv("CLOUDINARY_API_KEY"), 
  api_secret = os.getenv("CLOUDINARY_API_SECRET"),
  secure = True
)

def optimize_image_prompt(caption: str, niche: str) -> str:
    """
    Clean and shorten the prompt to prevent URL errors.
    """
    # 1. Strip newlines to prevent URL breaking
    clean_caption = caption.replace("\n", " ").strip()
    
    # 2. Hard limit to 200 chars (Safe for URLs)
    if len(clean_caption) > 200:
        clean_caption = clean_caption[:200]
        
    return f"Professional photo of {niche}, {clean_caption}, 4k, realistic, cinematic lighting"

def generate_image_with_pollinations(prompt: str):
    """
    1. GET request to direct Image API
    2. Download Binary Data
    3. Upload Binary to Cloudinary
    """
    try:
        print("🎨 Generating image via Pollinations API...")
        
        # 1. Prepare Prompt
        seed = random.randint(1, 999999)
        final_prompt = f"{prompt} --seed {seed}"
        
        # 2. Encode URL strictly
        # We use urllib to ensure spaces/symbols become %20, etc.
        encoded_prompt = urllib.parse.quote(final_prompt)
        
        # 3. Call the DIRECT Image Endpoint (Not the /p/ shortcut)
        # This ensures we get Bytes, not HTML
        api_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}"
        
        response = requests.get(
            api_url,
            params={
                "width": 1080,
                "height": 1080,
                "model": "flux",
                "nologo": "true"
            },
            timeout=30
        )
        
        # Check if we actually got an image
        content_type = response.headers.get("Content-Type", "")
        if response.status_code != 200 or "image" not in content_type:
            print(f"❌ Pollinations failed (Status {response.status_code}): {response.text[:100]}")
            raise ValueError("API did not return an image")

        print("☁️  Uploading binary to Cloudinary...")
        
        # 4. Upload Raw Bytes to Cloudinary
        upload_result = cloudinary.uploader.upload(
            response.content,
            folder="ai_generated_posts",
            public_id_prefix="pollinations_img",
            resource_type="image"
        )

        secure_url = upload_result["secure_url"]
        print(f"✅ Permanent Image URL: {secure_url}")

        return {
            "imageUrl": secure_url,
            "localPath": None
        }

    except Exception as e:
        print(f"❌ Image Generation Error: {e}")
        return {
            "imageUrl": "https://placehold.co/1080x1080?text=Image+Generation+Failed",
            "error": str(e)
        }

# Main entry point
def generate_image_with_imagen(prompt: str, save_locally: bool = False) -> dict:
    return generate_image_with_pollinations(prompt)