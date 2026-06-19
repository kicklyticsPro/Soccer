"""Client LLM compatible OpenAI avec retry intelligent et gestion du rate limit."""
from __future__ import annotations

import logging
import time
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


def _stream_with_filter(
    client: OpenAI,
    messages: List[Dict[str, str]],
    model: str,
    temperature: float,
    max_tokens: int,
    strip_thinking: bool,
) -> Iterator[str]:
    """Effectue le streaming et filtre les blocs thinking."""
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
                    # Filtrage streaming des balises <thinking>/</thinking>
                    if "<thinking>" in token:
                        in_thinking = True
                        token = token.split("<thinking>")[0]
                    if "</thinking>" in token:
                        in_thinking = False
                        token = token.split("</thinking>")[-1]
                    if in_thinking and "<thinking>" not in token and "</thinking>" not in token:
                        # En plein thinking, on saute ce token
                        # Mais on ne saute pas si on vient de fermer le thinking
                        continue
                yield token
        except (AttributeError, IndexError, ValueError):
            continue


def stream_analysis(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 4000,
    strip_thinking: bool = False,
) -> Iterator[str]:
    """Stream l'analyse avec retry intelligent et réduction auto du contexte.

    Si on hit le rate limit (413), on:
    1. Attend quelques secondes
    2. Réduit le contexte web de 50%
    3. Réduit max_tokens de 30%
    4. Réessaie jusqu'à 3 fois
    """
    client = get_client()
    model = model or Config.LLM_MODEL

    logger.info("Appel LLM - model=%s, max_tokens=%d, strip_thinking=%s",
                model, max_tokens, strip_thinking)

    max_retries = 3
    current_max_tokens = max_tokens
    current_messages = messages.copy()

    for attempt in range(1, max_retries + 1):
        try:
            for token in _stream_with_filter(
                client, current_messages, model, temperature,
                current_max_tokens, strip_thinking
            ):
                yield token
            return  # Success

        except Exception as e:
            error_str = str(e)
            is_rate_limit = "413" in error_str or "rate_limit" in error_str.lower() or "tokens per minute" in error_str.lower()

            if is_rate_limit and attempt < max_retries:
                # Stratégie: réduire le contexte et max_tokens
                logger.warning(
                    "Rate limit hit (attempt %d/%d). Réduction du contexte...",
                    attempt, max_retries,
                )

                # Réduire max_tokens de 30%
                current_max_tokens = int(current_max_tokens * 0.7)

                # Réduire le contexte web dans le dernier message user
                if current_messages and len(current_messages) > 0:
                    last_user_msg = current_messages[-1]
                    if "content" in last_user_msg:
                        content = last_user_msg["content"]
                        # Couper le bloc de contexte web (chercher "## 📋" ou similaire)
                        for marker in ["## 📋 FICHE SCOUT", "## 🔎 CONTEXTE WEB"]:
                            if marker in content:
                                idx = content.find(marker)
                                # Garder un extrait de 800 chars du contexte
                                context_start = idx + len(marker)
                                truncated = content[context_start:context_start + 800]
                                content = (
                                    content[:idx]
                                    + marker
                                    + "\n" + truncated
                                    + "\n\n[... contexte tronqué pour rate limit ...]"
                                    + content[context_start + 8000:]  # skip le reste
                                )
                                last_user_msg["content"] = content
                                break

                # Attendre avant retry (backoff exponentiel)
                wait_time = 2 ** attempt
                logger.info("Attente de %d secondes avant retry...", wait_time)
                time.sleep(wait_time)

                yield f"\n\n[Rate limit détecté. Réduction auto du contexte et retry...]\n\n"
            else:
                # Erreur non liée au rate limit, ou dernière tentative
                logger.exception("Erreur LLM (tentative finale)")
                yield f"\n\n[ERREUR LLM] {error_str[:300]}\n\n"
                return


def generate_full(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    temperature: float = 0.5,
    max_tokens: int = 4000,
    strip_thinking: bool = False,
) -> str:
    """Génère la réponse complète avec retry intelligent."""
    client = get_client()
    model = model or Config.LLM_MODEL
    logger.info("Appel LLM (full) - model=%s, max_tokens=%d", model, max_tokens)

    max_retries = 3
    current_max_tokens = max_tokens
    current_messages = [dict(m) for m in messages]  # copy

    for attempt in range(1, max_retries + 1):
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=current_messages,
                temperature=temperature,
                max_tokens=current_max_tokens,
            )
            text = resp.choices[0].message.content or ""

            if strip_thinking:
                import re
                # Filtrer les blocs thinking et
                text = re.sub(r'<thinking>.*?</thinking>', '', text, flags=re.DOTALL)
                text = re.sub(r'.*?', '', text, flags=re.DOTALL)
                text = re.sub(r'<\|.*?\|>', '', text)
                text = text.strip()

            return text

        except Exception as e:
            error_str = str(e)
            is_rate_limit = "413" in error_str or "rate_limit" in error_str.lower() or "tokens per minute" in error_str.lower()

            if is_rate_limit and attempt < max_retries:
                logger.warning("Rate limit (full), tentative %d/%d", attempt, max_retries)
                current_max_tokens = int(current_max_tokens * 0.7)

                if current_messages:
                    last = current_messages[-1]
                    if "content" in last:
                        content = last["content"]
                        for marker in ["## 📋 FICHE SCOUT", "## 🔎 CONTEXTE WEB"]:
                            if marker in content:
                                idx = content.find(marker)
                                context_start = idx + len(marker)
                                truncated = content[context_start:context_start + 600]
                                content = (
                                    content[:idx] + marker + "\n" + truncated
                                    + "\n\n[... tronqué ...]" + content[context_start + 6000:]
                                )
                                last["content"] = content
                                break

                time.sleep(2 ** attempt)
            else:
                logger.exception("Erreur LLM (full, dernière tentative)")
                raise


def is_reasoning_model(model: str) -> bool:
    """Détecte si un modèle utilise chain-of-thought."""
    model_lower = model.lower()
    keywords = ["r1", "reasoning", "o1", "qwq", "thinking", "qwen3", "deepseek"]
    return any(k in model_lower for k in keywords)
