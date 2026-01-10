import json
import logging
from json_repair import repair_json 

logger = logging.getLogger(__name__)

def validate_and_fix_json(raw_json: str, max_attempts: int = 1) -> dict:
    """
    Uses json_repair to fix common LLM errors like unescaped quotes 
    inside strings (e.g., "caption": "The "fresh" look").
    """
    try:
        # standard parse first (fastest)
        return json.loads(raw_json)
    except Exception:
        pass

    try:
        logger.info("🔧 JSON broken. Attempting repair with json_repair...")
        # repair_json automatically fixes unescaped quotes and missing brackets
        parsed = repair_json(raw_json, return_objects=True)
        
        if parsed:
            return parsed
        else:
            raise ValueError("json_repair returned empty object")
            
    except Exception as e:
        logger.error(f"❌ JSON Repair failed: {e}")
        # Log the raw output so you can debug what specifically broke it
        logger.error(f"Raw broken JSON snippet: {raw_json[:200]}...")
        raise ValueError(f"Could not parse JSON even after repair: {e}")