from schemas import BrandProfile, PastPost
from typing import List
# REMOVED: from json_fixer import sanitize_text_for_json

def clean_str(text: str) -> str:
    """
    Simple local helper to clean text for the prompt.
    Replaces newlines and double quotes to keep the prompt tidy.
    """
    if not text:
        return ""
    return str(text).replace("\n", " ").replace('"', "'").strip()

def build_prompt(brand: BrandProfile, past_posts: List[PastPost]) -> str:
    """
    Constructs the prompt using the local clean_str helper.
    """
    
    # Use clean_str locally
    niche = clean_str(brand.niche)
    audience = clean_str(brand.audience)
    tone = clean_str(brand.tone)
    style_summary = clean_str(brand.styleSummary)
    
    past_examples = ""
    for i, post in enumerate(past_posts[:5], 1):
        content = clean_str(post.content[:150])
        post_tone = clean_str(post.tone)
        cta = clean_str(post.callToAction) if post.callToAction else 'None'
        past_examples += f"{i}. Tone: {post_tone} | CTA: {cta}\n   Content: {content}...\n\n"

    # Simplified Prompt for Schema Mode
    prompt = f"""You are a professional social media copywriter specializing in {niche}.

BRAND PROFILE:
- Niche: {niche}
- Target Audience: {audience}
- Brand Tone: {tone}
- Style: {style_summary}
- Emotional Tone: {clean_str(brand.emotionalTone)}
- Common Phrases: {", ".join([clean_str(p) for p in brand.commonPhrases[:5]])}

SUCCESSFUL PAST POSTS:
{past_examples}

TASK:
Create 3 distinct Instagram content pieces. You must generate content for ALL three types:

1. TEXT-ONLY POST: Engaging caption and hashtags.
2. IMAGE POST: Visual-optimized caption and a detailed image generation prompt.
3. VIDEO POST: A full Reel script including hook, shooting instructions, and engagement strategy.

REQUIREMENTS:
- Match the brand's tone ({tone})
- Be educational yet promotional
- Use single quotes (') instead of double quotes (") for emphasis.
- Do NOT include markdown formatting.
"""
    
    return prompt.strip()

def build_system_message(brand: BrandProfile) -> str:
    return f"You are an expert social media creator. You strictly output JSON data matching the provided schema."