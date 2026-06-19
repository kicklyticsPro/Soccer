"""Orchestrateur principal: recherche web + LLM multi-passes avec cache et retry."""
from __future__ import annotations

import logging
import re
import time
from typing import Iterator, Dict

from web_search import search_team_info, search_match_context, format_context_for_llm
from prompts import build_chat_messages
from scout_prompts import build_scout_messages
from llm_client import stream_analysis, generate_full, is_reasoning_model
from config import Config
from cache import get_cache

logger = logging.getLogger(__name__)


def parse_match_input(text: str) -> Dict[str, str]:
    """Parse l'entrée utilisateur pour extraire équipes, date, compétition."""
    text = text.strip()
    parts = re.split(r"\s+[-\u2014]\s+", text)
    teams_raw = parts[0].strip()
    match = re.split(r"\s+(?:vs\.?|v\.?|contre)\s+", teams_raw, maxsplit=1, flags=re.IGNORECASE)
    if len(match) != 2:
        raise ValueError(
            f"Impossible de détecter les deux équipes dans '{teams_raw}'. "
            "Format attendu: 'ÉquipeA vs ÉquipeB'."
        )
    team1, team2 = match[0].strip(), match[1].strip()

    remaining = " - ".join(parts[1:]).strip() if len(parts) > 1 else ""
    date = ""
    competition = ""
    if remaining:
        months_fr = r"(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)"
        date_pattern_a = re.compile(rf"\d{{1,2}}\s*{months_fr}(?:\s+\d{{4}})?", re.IGNORECASE)
        date_pattern_b = re.compile(r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}")
        m_a = date_pattern_a.search(remaining)
        m_b = date_pattern_b.search(remaining)
        m = m_a or m_b
        if m:
            date = m.group(0).strip()
            competition = remaining.replace(date, "").strip(" -,")
        else:
            competition = remaining
    return {"team1": team1, "team2": team2, "date": date, "competition": competition}


def _clean_thinking_blocks(text: str) -> str:
    """Supprime les blocs thinking (DeepSeek, Qwen) du texte.

    Patterns ciblés:
      - <thinking>...</thinking>  (DeepSeek R1)
      -  (Qwen reasoning)
    """
    if not text:
        return text
    # DeepSeek R1
    text = re.sub(r'<thinking>.*?</thinking>', '', text, flags=re.DOTALL)
    # Qwen reasoning - balises Unicode
    text = re.sub(r'[\U0001f914].*?[\U0001f914]', '', text, flags=re.DOTALL)
    text = re.sub(r'<\|\w+\|>', '', text)
    return text.strip()


def analyze_match_stream(
    team1: str,
    team2: str,
    date: str,
    competition: str,
) -> Iterator[Dict]:
    """Pipeline complet multi-passes avec cache.

    Pass 1 (Scout): extraction rapide des faits clés
    Pass 2 (Expert): analyse probabiliste approfondie

    Émet des événements SSE: status, context, scout_start, scout_done,
    expert_start, token, done, error.
    """
    cache = get_cache()

    # ====== Cache check ======
    cached = cache.get(team1, team2, date, competition)
    if cached:
        yield {"event": "status", "data": "⚡ Analyse trouvée dans le cache (instantané)"}
        yield {"event": "context", "data": cached.get("web_context_preview", "")}
        if cached.get("scout_facts"):
            yield {"event": "scout_done", "data": cached["scout_facts"]}
        yield {"event": "scout_start", "data": "Cached"}
        yield {"event": "expert_start", "data": "Cached"}
        final_text = cached.get("analysis", "")
        # Stream le texte depuis le cache pour l'animation
        chunk_size = 25
        for i in range(0, len(final_text), chunk_size):
            yield {"event": "token", "data": final_text[i:i + chunk_size]}
            time.sleep(0.01)  # petit délai pour effet streaming
        yield {"event": "done", "data": final_text}
        return

    try:
        # ====== Recherche web ======
        yield {"event": "status", "data": f"🔎 Recherche d'informations sur {team1}..."}
        info1 = search_team_info(team1)

        yield {"event": "status", "data": f"🔎 Recherche d'informations sur {team2}..."}
        info2 = search_team_info(team2)

        yield {"event": "status", "data": "🔎 Recherche du contexte du match..."}
        match_ctx = search_match_context(team1, team2, date)

        yield {"event": "status", "data": "✅ Contexte collecté."}

        web_context = (
            f"# {team1.upper()}\n"
            + format_context_for_llm(info1)
            + f"\n\n# {team2.upper()}\n"
            + format_context_for_llm(info2)
            + f"\n\n# MATCH\n"
            + format_context_for_llm(match_ctx)
        )

        if len(web_context) > Config.MAX_CONTEXT_CHARS:
            web_context = web_context[: Config.MAX_CONTEXT_CHARS] + "\n[...truncated...]"

        context_preview = web_context[:1500] + ("..." if len(web_context) > 1500 else "")
        yield {"event": "context", "data": context_preview}

        scout_facts = ""
        if Config.USE_MULTI_PASS:
            # ====== PASS 1: SCOUT ======
            yield {
                "event": "status",
                "data": f"🕵️ Pass 1/2: Scout ({Config.LLM_SCOUT_MODEL})...",
            }
            yield {"event": "scout_start", "data": "Extraction des faits..."}

            try:
                scout_messages = build_scout_messages(team1, team2, date, competition, web_context)
                scout_facts = generate_full(
                    scout_messages,
                    model=Config.LLM_SCOUT_MODEL,
                    temperature=0.3,
                    max_tokens=2000,
                    strip_thinking=False,
                )
                yield {"event": "scout_done", "data": scout_facts}
            except Exception as e:
                logger.warning("Scout échoué: %s", e)
                yield {"event": "scout_done", "data": f"[SCOUT ÉCHOUÉ]"}
                scout_facts = ""

        # ====== PASS 2: EXPERT ======
        expert_model = Config.LLM_MODEL
        yield {
            "event": "status",
            "data": f"🧠 Pass 2/2: Expert ({expert_model}) - analyse probabiliste...",
        }
        yield {"event": "expert_start", "data": "Analyse experte..."}

        messages = build_chat_messages(team1, team2, date, competition, web_context, scout_facts)
        strip = is_reasoning_model(expert_model)
        max_tokens_out = 3500 if strip else 2500

        full = []
        for token in stream_analysis(
            messages,
            model=expert_model,
            temperature=0.7,
            max_tokens=max_tokens_out,
            strip_thinking=strip,
        ):
            full.append(token)
            yield {"event": "token", "data": token}

        final_text = "".join(full)
        # Post-cleanup des blocs thinking
        final_text = _clean_thinking_blocks(final_text)
        yield {"event": "done", "data": final_text}

        # ====== Mise en cache ======
        cache.set(team1, team2, date, competition, {
            "web_context_preview": context_preview,
            "scout_facts": scout_facts,
            "analysis": final_text,
        })

    except Exception as e:
        logger.exception("Erreur dans analyze_match_stream")
        yield {"event": "error", "data": str(e)}
