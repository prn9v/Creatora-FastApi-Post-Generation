import os
import json
import time
import google.generativeai as genai
from dotenv import load_dotenv
from schemas import GeneratePostResponse, GeneratePostResponseLLM, ImagePost
from json_fixer import validate_and_fix_json
# IMPORT THE NEW IMAGE GENERATOR
from image_generator import generate_image_with_imagen, optimize_image_prompt

load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def call_gemini(system_message: str, prompt: str) -> GeneratePostResponse:
    """Primary: Google Gemini 2.5 Flash"""
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash", 
        system_instruction=(
                f"{system_message} "
                "IMPORTANT: You must generate content for ALL three keys: "
                "'text', 'image', and 'video'. Do not skip any section."
            ),
        generation_config={
            "temperature": 0.7,
            "top_p": 0.95,
            "max_output_tokens": 8192,
            "response_mime_type": "application/json",
            "response_schema": GeneratePostResponseLLM
        }
    )
    
    response = model.generate_content(prompt)
    validated_json = validate_and_fix_json(response.text)
    llm_output = GeneratePostResponseLLM(**validated_json)
    
    # Return partial response first (image will be filled later)
    return GeneratePostResponse(
            text=llm_output.text,
            video=llm_output.video,
            image=ImagePost(
                caption=llm_output.image.caption,
                hashtags=llm_output.image.hashtags,
                imagePrompt=llm_output.image.imagePrompt,
                imageUrl=None 
            )
        )

def generate_post_with_image(system_message: str, prompt: str, brand_niche: str) -> GeneratePostResponse:
    """
    Generate posts AND actual image
    """
    try:
        # 1. Generate text content
        print("📝 Generating text content with Gemini...")
        response_data = call_gemini(system_message, prompt)
        
        # 2. Optimize prompt
        image_prompt = response_data.image.imagePrompt
        enhanced_prompt = optimize_image_prompt(image_prompt, brand_niche)
        
        # 3. Generate actual image (Pollinations + Cloudinary)
        print(f"🎨 Generating image with AI...")
        image_result = generate_image_with_imagen(enhanced_prompt)
        
        # 4. Attach URL to response
        response_data.image.imageUrl = image_result.get("imageUrl")
        
        return response_data
        
    except Exception as e:
        print(f"❌ Error in generate_post_with_image: {e}")
        raise

def call_llm_with_retry(system_message: str, prompt: str, brand_niche: str = "general", max_retries: int = 2) -> GeneratePostResponse:
    """Retry logic"""
    last_error = None
    
    for attempt in range(max_retries):
        try:
            return generate_post_with_image(system_message, prompt, brand_niche)
            
        except Exception as e:
            last_error = e
            print(f"❌ Attempt {attempt + 1}/{max_retries} failed: {e}")
            
            if attempt < max_retries - 1:
                time.sleep(2)
    
    raise RuntimeError(f"All retry attempts failed. Last error: {last_error}")