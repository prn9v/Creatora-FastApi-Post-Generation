from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from schemas import GeneratePostRequest, GeneratePostResponse, HealthResponse
from prompt_builder import build_prompt, build_system_message
from llm_service import call_llm_with_retry
import logging
import os


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create images directory
IMAGES_DIR = Path("generated_images")
IMAGES_DIR.mkdir(exist_ok=True)

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

# Initialize FastAPI app
app = FastAPI(
    title="AI Social Media Content Generator",
    description="Microservice for generating social media posts with actual images",
    version="2.0.0"
)

# Mount static files directory for serving images
app.mount("/images", StaticFiles(directory=str(IMAGES_DIR)), name="images")

# CORS configuration (adjust origins for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to specific domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint - health check"""
    return HealthResponse(
        status="healthy",
        service="AI Content Generator",
        version="1.0.0"
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for monitoring"""
    return HealthResponse(
        status="healthy",
        service="AI Content Generator",
        version="1.0.0"
    )


@app.post("/generate-post", response_model=GeneratePostResponse)
async def generate_post(payload: GeneratePostRequest):
    """
    Generate 3 social media post variations (text, image with actual image file, video)
    based on brand profile and past posts.
    
    Args:
        payload: Request containing brandProfile and pastPosts
        
    Returns:
        GeneratePostResponse with text, image (with actual imageUrl), and video post options
    """
    
    try:
        logger.info(f"🚀 Generating posts for niche: {payload.brandProfile.niche}")
        
        # Build prompt from brand profile and past posts
        system_message = build_system_message(payload.brandProfile)
        prompt = build_prompt(payload.brandProfile, payload.pastPosts)
        
        # Call LLM with retry logic (now includes image generation)
        response = call_llm_with_retry(
            system_message, 
            prompt, 
            brand_niche=payload.brandProfile.niche
        )
        
        if not response:
            raise ValueError("No response generated from LLM")
        
        logger.info(f"✅ Successfully generated posts")
        logger.info(f"🖼️  Image URL: {response.image.imageUrl if response.image else 'No image'}")
        
        return response
    
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    
    except RuntimeError as e:
        logger.error(f"LLM error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate content. Please try again.")
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/generate-post/debug")
async def generate_post_debug(payload: GeneratePostRequest):
    """
    Debug endpoint that returns the prompt that would be sent to LLM.
    Useful for testing and prompt optimization.
    """
    
    try:
        system_message = build_system_message(payload.brandProfile)
        prompt = build_prompt(payload.brandProfile, payload.pastPosts)
        
        return {
            "system_message": system_message,
            "prompt": prompt
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)