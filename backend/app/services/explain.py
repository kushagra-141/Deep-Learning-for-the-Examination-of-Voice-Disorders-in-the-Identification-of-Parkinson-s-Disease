"""P3.5-01: Explainability Service.

Streams LLM explanations for a given prediction using the OpenAI client.
Connects to Groq by default if GROQ_API_KEY is present, else standard OpenAI.
"""
import asyncio
import json
import logging
from typing import AsyncGenerator

from openai import AsyncOpenAI
import structlog

from app.core.config import get_settings
from app.schemas.explain import ExplainRequest

logger = structlog.get_logger(__name__)

SYSTEM_PROMPT = """You are an expert, compassionate AI research assistant specializing in acoustic voice analysis for Parkinson's disease detection.
Your task is to explain the results of a machine learning ensemble prediction to the user in plain, accessible English.

The user will provide:
1. The 22 acoustic voice features (e.g., Jitter, Shimmer, NHR, HNR, RPDE).
2. The ensemble probability that the voice belongs to a Parkinson's patient.
3. The input method (manual entry or live audio extraction).

Guidelines:
- Start with a clear summary of the probability.
- Explain the top 2 or 3 most significant features from their input that might have contributed to this score (e.g., high Jitter means frequency instability, low HNR means more noise in the voice). Don't list all 22.
- Be concise and structure your explanation with short paragraphs or bullet points.
- CRITICAL: You MUST include a medical disclaimer emphasizing that this is an experimental machine learning tool, NOT a clinical diagnosis, and that they should consult a neurologist or doctor for actual medical advice.
- Use markdown formatting.

Do not use overly dense medical jargon without explaining it simply.
"""

async def generate_explanation_stream(request: ExplainRequest) -> AsyncGenerator[str, None]:
    """Generate a streaming SSE response explaining the prediction."""
    settings = get_settings()
    
    # Determine which client to use based on available keys
    if settings.GROQ_API_KEY:
        client = AsyncOpenAI(
            api_key=settings.GROQ_API_KEY.get_secret_value(),
            base_url="https://api.groq.com/openai/v1",
        )
        model = "llama-3.1-8b-instant"  # Fast, good for text generation
    elif settings.OPENROUTER_API_KEY:
        client = AsyncOpenAI(
            api_key=settings.OPENROUTER_API_KEY.get_secret_value(),
            base_url="https://openrouter.ai/api/v1",
        )
        model = "google/gemini-flash-1.5"
    elif settings.GEMINI_API_KEY:
        # OpenAI SDK now supports Gemini endpoint if we use the right base_url, but it's easier to just use standard openai if they put a key. 
        # Wait, if they have GEMINI_API_KEY, let's just use it as OPENAI_API_KEY if they didn't provide OPENAI_API_KEY, wait no, gemini doesn't have an openai compatible endpoint without proxy.
        # Let's fallback to standard OpenAI.
        client = AsyncOpenAI(api_key=settings.GEMINI_API_KEY.get_secret_value())
        model = "gpt-4o-mini"
    else:
        # Try default OpenAI env var
        try:
            client = AsyncOpenAI()
            model = "gpt-4o-mini"
        except Exception:
            yield "data: " + json.dumps({"text": "Error: No LLM API key configured (GROQ_API_KEY, OPENAI_API_KEY, etc). Please add an API key to the backend .env file.\n"}) + "\n\n"
            return

    # Build the prompt
    user_prompt = f"""
Input Method: {request.input_mode}
Ensemble Probability of Parkinson's: {request.probability * 100:.1f}%

Acoustic Features Provided:
{json.dumps(request.features, indent=2)}

Please explain this result.
"""

    try:
        stream = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            stream=True,
            temperature=0.7,
            max_tokens=800,
        )

        async for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                # SSE Starlette format: yield standard SSE data payload
                # We json-encode the text chunk so newlines don't break SSE framing
                yield "data: " + json.dumps({"text": content}) + "\n\n"
                
    except Exception as e:
        logger.error("llm_stream_error", error=str(e))
        yield "data: " + json.dumps({"text": f"\n\n**Error generating explanation:** {str(e)}"}) + "\n\n"
