"""Client LLM compatible OpenAI pour générer les analyses."""
from __future__ import annotations

import logging
from typing import Iterator, List, Dict

from openai import OpenAI

from config import Config

logger = logging.getLogger(__name__)


def get_client() -> OpenAI:
    """Retourne un client OpenAI configuré."""
    if not Config.LLM_API_KEY:
        raise RuntimeError(
            "LLM_API_KEY non configurée. "
            "Définissez-la dans le fichier .env (voir .env.example)."
        )
    return OpenAI(base_url=Config.LLM_BASE_URL, api_key=Config.LLM_API_KEY)


def stream_analysis(
    messages: List[Dict[str, str]],
    model: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 4000,
) -> Iterator[str]:
    """Stream l'analyse depuis le LLM, token par token."""
    client = get_client()
    model = model or Config.LLM_MODEL

    logger.info("Appel LLM - model=%s", model)

    try:
        stream = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        for chunk in stream:
            try:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
            except (AttributeError, IndexError):
                continue
    except Exception as e:
        logger.exception("Erreur LLM")
        yield f"\n\n[ERREUR LLM] {e}\n\n"


def generate_full_analysis(
    messages: List[Dict[str, str]],
    model: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 4000,
) -> str:
    """Génère l'analyse complète en un seul appel (non streaming)."""
    client = get_client()
    model = model or Config.LLM_MODEL

    logger.info("Appel LLM (non-stream) - model=%s", model)

    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content or ""
