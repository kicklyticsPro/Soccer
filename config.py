"""Configuration du projet - charge les variables d'environnement."""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuration centralisée."""

    # LLM (Expert - Pass 2)
    LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    LLM_API_KEY = os.getenv("LLM_API_KEY", "")
    LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")

    # LLM Scout (Pass 1 - extraction rapide)
    LLM_SCOUT_MODEL = os.getenv("LLM_SCOUT_MODEL", "") or LLM_MODEL

    # Multi-passes
    USE_MULTI_PASS = os.getenv("USE_MULTI_PASS", "true").lower() == "true"

    # Recherche web
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")

    # Flask
    FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
    FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
    FLASK_DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"

    # Limites (ajustées pour rester sous les 6000 TPM de Groq free tier)
    MAX_SEARCH_RESULTS = 4
    MAX_CONTEXT_CHARS = 2200  # ~550 tokens - safe pour Groq free
