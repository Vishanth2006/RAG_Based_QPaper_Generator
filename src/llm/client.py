"""
LLM Client — Stage 4
Supports Groq (primary) via OpenAI-compatible API.
Groq base URL: https://api.groq.com/openai/v1
Falls back to OpenAI if GROQ_API_KEY is not set.
"""
import os
import time
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
DEFAULT_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")


def _is_valid_key(key: str) -> bool:
    """A key is valid if it's non-empty and not a placeholder."""
    return bool(key) and not key.startswith("your_") and len(key) > 10


def _get_client():
    """Return (OpenAI client, model_name) using Groq or OpenAI."""
    from openai import OpenAI

    groq_key = os.getenv("GROQ_API_KEY", "")
    if _is_valid_key(groq_key):
        return OpenAI(api_key=groq_key, base_url=GROQ_BASE_URL), DEFAULT_MODEL

    openai_key = os.getenv("OPENAI_API_KEY", "")
    if _is_valid_key(openai_key) and not openai_key.startswith("sk-your"):
        return OpenAI(api_key=openai_key), "gpt-4o-mini"

    raise RuntimeError(
        "No valid API key found.\n"
        "• Groq (free): set GROQ_API_KEY in .env  →  console.groq.com\n"
        "• OpenAI: set OPENAI_API_KEY in .env"
    )


def chat_completion(
    messages: list[dict],
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2000,
    retries: int = 3,
) -> str:
    """
    Send a chat completion request to Groq (or OpenAI).
    Returns the assistant message text.
    Raises RuntimeError on failure after retries.
    """
    from openai import RateLimitError, APIError

    client, default_model = _get_client()
    use_model = model or default_model

    for attempt in range(1, retries + 1):
        try:
            response = client.chat.completions.create(
                model=use_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content.strip()

        except RateLimitError:
            if attempt < retries:
                time.sleep(2 ** attempt)
                continue
            raise RuntimeError("Rate limit exceeded. Please wait and retry.")

        except APIError as e:
            if attempt < retries:
                time.sleep(1)
                continue
            raise RuntimeError(f"API error: {e}")

        except Exception as e:
            raise RuntimeError(f"LLM call failed: {e}")


def count_tokens(text: str, model: str = "openai/gpt-oss-120b") -> int:
    """Approximate token count using tiktoken cl100k_base, else 4-char heuristic."""
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except Exception:
        return len(text) // 4


def active_provider() -> str:
    """Human-readable name of the active LLM provider."""
    groq_key = os.getenv("GROQ_API_KEY", "")
    if _is_valid_key(groq_key):
        return f"Groq ({DEFAULT_MODEL})"
    openai_key = os.getenv("OPENAI_API_KEY", "")
    if _is_valid_key(openai_key) and not openai_key.startswith("sk-your"):
        return "OpenAI (gpt-4o-mini)"
    return "⚠️ No valid API key"


def has_valid_key() -> bool:
    """True if at least one usable API key is configured."""
    groq_key = os.getenv("GROQ_API_KEY", "")
    openai_key = os.getenv("OPENAI_API_KEY", "")
    return (
        _is_valid_key(groq_key) or
        (_is_valid_key(openai_key) and not openai_key.startswith("sk-your"))
    )
