from typing import List, Optional
from pydantic import BaseModel

# --- EXISTING INPUT MODELS ---
class PastPost(BaseModel):
    content: str
    platform: str
    tone: str
    hashtags: List[str]
    callToAction: Optional[str] = None

class BrandProfile(BaseModel):
    tone: str
    niche: str
    audience: str
    styleSummary: str
    avgSentenceLength: int
    vocabularyComplexity: str
    commonPhrases: List[str]
    topicPreferences: List[str]
    emotionalTone: str
    storytellingStyle: str

class GeneratePostRequest(BaseModel):
    brandProfile: BrandProfile
    pastPosts: List[PastPost]

# --- OUTPUT MODELS ---

class TextPost(BaseModel):
    caption: str
    hashtags: List[str]

# 1. Create a strict model for the LLM (No imageUrl)
class ImagePostLLM(BaseModel):
    caption: str
    hashtags: List[str]
    imagePrompt: str

class VideoPost(BaseModel):
    hook: str
    caption: str
    script: str
    shootingInstructions: str
    audienceEngagement: str
    hashtags: List[str]

# 2. The Main Schema for LLM Generation (Uses ImagePostLLM)
class GeneratePostResponseLLM(BaseModel):
    text: TextPost
    image: ImagePostLLM
    video: VideoPost

# 3. The Final API Response (Includes imageUrl)
class ImagePost(ImagePostLLM):
    imageUrl: Optional[str] = None

class GeneratePostResponse(BaseModel):
    text: TextPost
    image: ImagePost
    video: VideoPost

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str