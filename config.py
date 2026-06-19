"""Configuration du projet - charge les variables d'environnement."""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuration centralisée."""

    # LLM
    LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    LLM_API_KEY = os.getenv("LLM_API_KEY", "")
    LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")

    # Recherche web
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")

    # Flask
    FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
    FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
    FLASK_DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"

    # Limites
    MAX_SEARCH_RESULTS = 8
    MAX_CONTEXT_CHARS = 12000
