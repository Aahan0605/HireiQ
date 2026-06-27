import os
import re
import json
import logging
import asyncio
from typing import Any, Dict, Optional, Type
from pydantic import BaseModel
import google.generativeai as genai
from hiring_agent.retry import retry_with_backoff

logger = logging.getLogger(__name__)

# Constants
DEFAULT_MODEL = os.getenv("HIRING_AGENT_MODEL", "gemini-2.5-flash")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Initialize the Gemini API client
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    logger.warning("⚠️ GEMINI_API_KEY not found in environment. Gemini API calls will fail.")

def extract_json_from_response(response_text: str) -> str:
    """
    Extract JSON content from markdown code blocks.
    """
    response_text = response_text.strip()
    if "<think>" in response_text:
        think_start = response_text.find("<think>")
        think_end = response_text.find("</think>")
        if think_start != -1 and think_end != -1:
            response_text = response_text[:think_start] + response_text[think_end + 8 :]

    # Remove leading ```json if present
    if response_text.startswith("```json"):
        response_text = response_text[7:]
    elif response_text.startswith("```"):
        response_text = response_text[3:]
        
    # Remove trailing ``` if present
    if response_text.endswith("```"):
        response_text = response_text[:-3]
        
    return response_text.strip()

async def call_llm(
    system_prompt: str,
    user_prompt: str,
    response_model: Optional[Type[BaseModel]] = None,
    model_name: str = DEFAULT_MODEL,
    temperature: float = 0.1,
    top_p: float = 0.9,
) -> str:
    """
    High-level async function to call Gemini LLM with system and user prompts,
    optional structured output schema (response_model), and built-in retry logic.
    """
    if not GEMINI_API_KEY:
        # Fallback check
        api_key = os.getenv("GEMINI_API_KEY", "")
        if api_key:
            genai.configure(api_key=api_key)
        else:
            raise ValueError("GEMINI_API_KEY is not configured. Cannot make LLM calls.")

    async def _execute_call():
        generation_config = {
            "temperature": temperature,
            "top_p": top_p,
        }
        
        if response_model:
            generation_config["response_mime_type"] = "application/json"
            # Do not pass response_schema directly to avoid 'ValueError: Unknown field for Schema: default'
            # and unsupported nested $ref/$defs in google-generativeai package.
            # Gemini-2.0-flash is highly capable and will follow the schema from the prompt instructions.

        # Using thread pool executor since genai calls are blocking synchronous network calls
        loop = asyncio.get_running_loop()
        
        def _sync_call():
            # Initialize model with system instruction
            model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=system_prompt,
                generation_config=generation_config
            )
            # Generate content
            response = model.generate_content(user_prompt)
            return response.text

        return await loop.run_in_executor(None, _sync_call)

    # Call with retry wrapper (handles rate limits, ResourceExhausted, etc.)
    max_retries = int(os.getenv("HIRING_AGENT_MAX_RETRIES", "3"))
    response_text = await retry_with_backoff(_execute_call, max_retries=max_retries)
    return response_text
