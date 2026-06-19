"""Client LLM compatible OpenAI pour générer les analyses (multi-passes)."""
from __future__ import annotations

import logging
from typing import Iterator, List, Dict, Optional

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
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 4000,
    strip_thinking: bool = False,
) -> Iterator[str]:
    """Stream l'analyse depuis le LLM, token par token.

    Args:
        messages: Liste des messages
        model: Nom du modèle (défaut = Config.LLM_MODEL)
        temperature: Température (0.0 déterministe, 1.0 créatif)
        max_tokens: Limite de tokens
        strip_thinking: Si True, supprime les blocs <thinking>/<think>...</thinking>/think>
                        (utile pour DeepSeek R1, Qwen reasoning, etc.)
    """
    client = get_client()
    model = model or Config.LLM_MODEL

    logger.info("Appel LLM - model=%s, strip_thinking=%s", model, strip_thinking)

    try:
        stream = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        in_thinking = False
        for chunk in stream:
            try:
                if chunk.choices and chunk.choices[0].delta.content:
                    token = chunk.choices[0].delta.content
                    if strip_thinking:
                        # Filtrer les blocs <thinking> ET  (Qwen utilise)
                        if "<thinking>" in token or "<think>" in token:
                            in_thinking = True
                            token = token.split("<thinking>")[0].split("<think>")[0]
                        if "</thinking>" in token or "</think>" in token:
                            in_thinking = False
                            token = token.split("</thinking>")[-1].split("</think>")[-1]
                            yield token
                            continue
                        if in_thinking:
                            continue
                    yield token
            except (AttributeError, IndexError):
                continue
    except Exception as e:
        logger.exception("Erreur LLM")
        yield f"\n\n[ERREUR LLM] {e}\n\n"


def generate_full(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    temperature: float = 0.5,
    max_tokens: int = 4000,
    strip_thinking: bool = False,
) -> str:
    """Génère la réponse complète en un seul appel (non streaming)."""
    client = get_client()
    model = model or Config.LLM_MODEL

    logger.info("Appel LLM (full) - model=%s", model)

    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    text = resp.choices[0].message.content or ""

    if strip_thinking:
        import re
        text = re.sub(r'<thinking>.*?</thinking>', '', text, flags=re.DOTALL)
        text = re.sub(r'<\|.*?\|>', '', text)
        text = text.strip()

    return text


def is_reasoning_model(model: str) -> bool:
    """Détecte si un modèle utilise chain-of-thought (DeepSeek R1, Qwen reasoning, etc.)."""
    model_lower = model.lower()
    keywords = ["r1", "reasoning", "o1", "qwq", "thinking", "qwen3", "deepseek"]
    return any(k in model_lower for k in keywords)
