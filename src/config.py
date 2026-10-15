"""
Central configuration for the RAG Question Paper Generator.
All settings are loaded from environment variables via .env file.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()

# ── Project Root ──────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent

# ── API Configuration ─────────────────────────────────────────────────────────
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL: str = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
XAI_API_KEY: str = os.getenv("XAI_API_KEY", "")
XAI_MODEL: str = os.getenv("XAI_MODEL", "grok-beta")

# ── Application Meta ──────────────────────────────────────────────────────────
APP_TITLE: str = os.getenv("APP_TITLE", "RAG Question Paper Generator")
APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")

# ── Storage Paths ─────────────────────────────────────────────────────────────
CHROMADB_PATH: Path = PROJECT_ROOT / os.getenv("CHROMADB_PATH", "data/chromadb")
UPLOAD_DIR: Path = PROJECT_ROOT / os.getenv("UPLOAD_DIR", "data/uploads")
EXPORT_DIR: Path = PROJECT_ROOT / os.getenv("EXPORT_DIR", "data/exports")

# Ensure directories exist at import time
CHROMADB_PATH.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

# ── Chunking ──────────────────────────────────────────────────────────────────
CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "700"))
CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "70"))

# ── Retrieval ─────────────────────────────────────────────────────────────────
TOP_K_RESULTS: int = int(os.getenv("TOP_K_RESULTS", "8"))
MIN_SIMILARITY_THRESHOLD: float = float(os.getenv("MIN_SIMILARITY_THRESHOLD", "0.3"))

# ── Generation ────────────────────────────────────────────────────────────────
MAX_REPAIR_ATTEMPTS: int = int(os.getenv("MAX_REPAIR_ATTEMPTS", "3"))
MAX_API_CALLS_PER_SESSION: int = int(os.getenv("MAX_API_CALLS_PER_SESSION", "50"))
GENERATION_TIMEOUT_SECONDS: int = int(os.getenv("GENERATION_TIMEOUT_SECONDS", "120"))


def is_api_configured() -> bool:
    """Return True if the configured Groq API key is usable."""
    return bool(GROQ_API_KEY and not GROQ_API_KEY.startswith("your_"))


def get_config_summary() -> dict:
    """Return a safe summary of config (no secret values)."""
    return {
        "app_title": APP_TITLE,
        "app_version": APP_VERSION,
        "model": GROQ_MODEL,
        "api_configured": is_api_configured(),
        "chromadb_path": str(CHROMADB_PATH),
        "upload_dir": str(UPLOAD_DIR),
        "export_dir": str(EXPORT_DIR),
        "chunk_size": CHUNK_SIZE,
        "chunk_overlap": CHUNK_OVERLAP,
        "top_k": TOP_K_RESULTS,
        "max_repair_attempts": MAX_REPAIR_ATTEMPTS,
    }
