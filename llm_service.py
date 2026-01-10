import os
import json
from typing import Optional, Callable
import google.generativeai as genai
from dotenv import load_dotenv
from schemas import GeneratePostResponse,GeneratePostResponseLLM,ImagePost
from json_fixer import validate_and_fix_json

load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


def call_gemini(system_message: str, prompt: str) -> GeneratePostResponse:
    """Primary: Google Gemini 1.5 Flash"""
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
    
    full_prompt = f"""{system_message}

{prompt}

Return ONLY valid JSON, no markdown."""
    
    response = model.generate_content(full_prompt)
    validated_json = validate_and_fix_json(response.text)
    llm_output = GeneratePostResponseLLM(**validated_json)
    
    return GeneratePostResponse(
            text=llm_output.text,
            video=llm_output.video,
            image=ImagePost(
                caption=llm_output.image.caption,
                hashtags=llm_output.image.hashtags,
                imagePrompt=llm_output.image.imagePrompt,
                imageUrl=None # Explicitly set to None or let default handle it
            )
        )



def call_llm(system_message: str, prompt: str) -> GeneratePostResponse:
    """
    Try Gemini first, fallback to OpenAI if needed
    """
    try:
        return call_gemini(system_message, prompt)
    except Exception as gemini_error:
        print(f"Gemini failed: {gemini_error}")
        


def generate_post_with_image(system_message: str, prompt: str, brand_niche: str) -> GeneratePostResponse:
    """
    Generate posts AND actual image
    """
    from image_generator import generate_image_with_imagen, optimize_image_prompt
    
    try:
        # First, generate text content (without imageUrl)
        print("📝 Generating text content with Gemini...")
        response_data = call_llm(system_message, prompt)
        
        if not response_data or not hasattr(response_data, 'image'):
            raise ValueError("Invalid response structure from LLM")
        
        # Extract image prompt from response
        image_prompt = response_data.image.imagePrompt
        
        # Optimize prompt for better image generation
        enhanced_prompt = optimize_image_prompt(image_prompt, brand_niche)
        
        # Generate actual image
        print(f"🎨 Generating image with AI...")
        image_result = generate_image_with_imagen(enhanced_prompt)
        
        # Update response with actual image URL
        response_data.image.imageUrl = image_result.get("imageUrl", "https://placehold.co/1080x1080/png?text=Image")
        
        print(f"✅ Image URL: {response_data.image.imageUrl}")
        
        return response_data
        
    except Exception as e:
        print(f"❌ Error in generate_post_with_image: {e}")
        raise


def call_llm_with_retry(system_message: str, prompt: str, brand_niche: str = "general", max_retries: int = 2) -> GeneratePostResponse:
    """Retry logic with exponential backoff"""
    import time
    
    last_error = None
    
    for attempt in range(max_retries):
        try:
            return generate_post_with_image(system_message, prompt, brand_niche)
            
        except Exception as e:
            last_error = e
            error_msg = str(e).lower()
            
            print(f"❌ Attempt {attempt + 1}/{max_retries} failed: {e}")
            
            # Rate limit handling
            if "429" in error_msg or "quota" in error_msg or "rate limit" in error_msg:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"⏳ Rate limit. Waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue
            
            # For other errors, shorter wait
            if attempt < max_retries - 1:
                print(f"⏳ Retrying in 2s...")
                time.sleep(2)
    
    # If all retries failed, raise the last error
    raise RuntimeError(f"All retry attempts failed. Last error: {last_error}")