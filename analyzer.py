"""Orchestrateur principal: recherche web + LLM multi-passes."""
from __future__ import annotations

import logging
import re
from typing import Iterator, Dict

from web_search import search_team_info, search_match_context, format_context_for_llm
from prompts import build_chat_messages
from scout_prompts import build_scout_messages
from llm_client import stream_analysis, generate_full, is_reasoning_model
from config import Config

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


def analyze_match_stream(
    team1: str,
    team2: str,
    date: str,
    competition: str,
) -> Iterator[Dict]:
    """Pipeline complet multi-passes.

    Pass 1 (Scout): extraction rapide des faits clés
    Pass 2 (Expert): analyse probabiliste approfondie

    Événements SSE émis:
      - status: progression
      - context: contexte web récupéré
      - scout_start: début de la passe 1
      - scout_token: tokens du scout
      - scout_done: fiche scout finale
      - expert_start: début de la passe 2
      - token: tokens de l'expert (streamés)
      - done: analyse complète finale
      - error: erreur
    """
    try:
        yield {"event": "status", "data": f"🔎 Recherche d'informations sur {team1}..."}
        info1 = search_team_info(team1)

        yield {"event": "status", "data": f"🔎 Recherche d'informations sur {team2}..."}
        info2 = search_team_info(team2)

        yield {"event": "status", "data": "🔎 Recherche du contexte du match..."}
        match_ctx = search_match_context(team1, team2, date)

        yield {"event": "status", "data": "✅ Contexte collecté."}

        web_context = (
            f"# INFORMATIONS SUR {team1.upper()}\n"
            + format_context_for_llm(info1)
            + f"\n\n# INFORMATIONS SUR {team2.upper()}\n"
            + format_context_for_llm(info2)
            + f"\n\n# CONTEXTE DU MATCH\n"
            + format_context_for_llm(match_ctx)
        )

        # Si le contexte est trop gros, on le tronque pour rester sous la limite TPM
        if len(web_context) > Config.MAX_CONTEXT_CHARS:
            web_context = web_context[: Config.MAX_CONTEXT_CHARS] + "\n\n[... contexte tronqué ...]"

        context_preview = web_context[:1500] + ("..." if len(web_context) > 1500 else "")
        yield {"event": "context", "data": context_preview}

        scout_facts = ""
        if Config.USE_MULTI_PASS:
            # ====== PASS 1: SCOUT (extraction de faits) ======
            yield {
                "event": "status",
                "data": f"🕵️ Pass 1/2: Scout ({Config.LLM_SCOUT_MODEL}) - extraction des faits...",
            }
            yield {"event": "scout_start", "data": "Extraction des faits clés..."}

            scout_messages = build_scout_messages(team1, team2, date, competition, web_context)

            try:
                scout_facts = generate_full(
                    scout_messages,
                    model=Config.LLM_SCOUT_MODEL,
                    temperature=0.3,
                    max_tokens=3000,
                    strip_thinking=False,
                )
                yield {"event": "scout_done", "data": scout_facts}
                yield {
                    "event": "status",
                    "data": "✅ Fiche scout générée. Lancement de l'analyse experte...",
                }
            except Exception as e:
                logger.warning("Échec du scout: %s. Continuation sans fiche.", e)
                yield {"event": "scout_done", "data": f"[SCOUT ÉCHOUÉ: {e}]"}
                scout_facts = ""

        # ====== PASS 2: EXPERT (analyse probabiliste) ======
        expert_model = Config.LLM_MODEL
        model_desc = expert_model
        if is_reasoning_model(expert_model):
            model_desc += " (chain-of-thought)"

        yield {
            "event": "status",
            "data": f"🧠 Pass 2/2: Expert ({model_desc}) - analyse probabiliste...",
        }
        yield {"event": "expert_start", "data": "Analyse experte en cours..."}

        messages = build_chat_messages(team1, team2, date, competition, web_context, scout_facts)

        # Pour les modèles R1, on supprime les blocs <thinking> de la sortie streamée
        strip = is_reasoning_model(expert_model)

        # Limite TPM Groq free tier = 6000. Input typique: ~3500 tokens.
        # Pour les modèles "thinking", on alloue plus de budget car le thinking
        # consomme des tokens qui ne sont pas dans la sortie finale.
        if strip:
            max_tokens_out = 3500
        else:
            max_tokens_out = 2500

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
        yield {"event": "done", "data": final_text}

    except Exception as e:
        logger.exception("Erreur dans analyze_match_stream")
        yield {"event": "error", "data": str(e)}
