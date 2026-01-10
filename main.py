from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from schemas import GeneratePostRequest, GeneratePostResponse, HealthResponse
from prompt_builder import build_prompt, build_system_message
from llm_service import call_llm_with_retry
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# NOTE: Local IMAGES_DIR creation is removed for Vercel compatibility.
# Vercel has a read-only file system. We now rely on Cloudinary.

# Initialize FastAPI app
app = FastAPI(
    title="AI Social Media Content Generator",
    description="Microservice for generating social media posts with Cloudinary integration",
    version="2.1.0"
)

# NOTE: StaticFiles mount is removed.
# Images are served directly via public Cloudinary URLs returned in the JSON response.

# CORS configuration
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
        version="2.1.0"
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for monitoring"""
    return HealthResponse(
        status="healthy",
        service="AI Content Generator",
        version="2.1.0"
    )

@app.post("/generate-post", response_model=GeneratePostResponse)
async def generate_post(payload: GeneratePostRequest):
    try:
        logger.info(f"🚀 Generating posts for niche: {payload.brandProfile.niche}")
        
        system_message = build_system_message(payload.brandProfile)
        prompt = build_prompt(payload.brandProfile, payload.pastPosts)
        
        response = call_llm_with_retry(
            system_message, 
            prompt, 
            brand_niche=payload.brandProfile.niche
        )
        
        logger.info(f"✅ Successfully generated posts")
        img_url = response.image.imageUrl if response.image and response.image.imageUrl else 'No image'
        logger.info(f"🖼️  Image URL: {img_url}")
        
        return response
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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