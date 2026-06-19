"""Orchestrateur principal: recherche web + LLM pour produire l'analyse."""
from __future__ import annotations

import logging
import re
from typing import Iterator, Dict

from web_search import search_team_info, search_match_context, format_context_for_llm
from prompts import build_chat_messages
from llm_client import stream_analysis

logger = logging.getLogger(__name__)


def parse_match_input(text: str) -> Dict[str, str]:
    """Parse l'entrée utilisateur pour extraire équipes, date, compétition.

    Formats acceptés:
      - "France vs Sénégal"
      - "France vs Sénégal - 16 Juin 2026"
      - "France vs Sénégal 16/06/2026"
      - "France vs Sénégal - Coupe du Monde 2026"
      - "France vs Sénégal - 16 Juin 2026 - Coupe du Monde"
    """
    text = text.strip()

    # Séparer par " - " ou " — "
    parts = re.split(r"\s+[-\u2014]\s+", text)

    # Premier élément = les deux équipes
    teams_raw = parts[0].strip()

    # Séparer les deux équipes par " vs ", " v ", " contre "
    match = re.split(r"\s+(?:vs\.?|v\.?|contre)\s+", teams_raw, maxsplit=1, flags=re.IGNORECASE)
    if len(match) != 2:
        raise ValueError(
            f"Impossible de détecter les deux équipes dans '{teams_raw}'. "
            "Format attendu: 'ÉquipeA vs ÉquipeB'."
        )
    team1, team2 = match[0].strip(), match[1].strip()

    # Le reste = date + compétition
    remaining = " - ".join(parts[1:]).strip() if len(parts) > 1 else ""

    date = ""
    competition = ""
    if remaining:
        # Heuristique: matche une date type "16 Juin 2026" ou "16/06/2026"
        months_fr = r"(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)"
        # 1) "16 Juin 2026" ou "16 Juin" (jour + mois + année optionnelle)
        date_pattern_a = re.compile(
            rf"\d{{1,2}}\s*{months_fr}(?:\s+\d{{4}})?", re.IGNORECASE
        )
        # 2) "16/06/2026" ou "16-06-2026"
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
    """Pipeline complet: produit des événements au format SSE.

    Événements émis:
      - {"event": "status", "data": "..."}  - statut intermédiaire
      - {"event": "context", "data": "..."} - extrait du contexte utilisé
      - {"event": "token", "data": "..."}   - token du LLM (texte)
      - {"event": "done", "data": "..."}    - fin
      - {"event": "error", "data": "..."}   - erreur
    """
    try:
        yield {
            "event": "status",
            "data": f"🔎 Recherche d'informations sur {team1}...",
        }
        info1 = search_team_info(team1)

        yield {
            "event": "status",
            "data": f"🔎 Recherche d'informations sur {team2}...",
        }
        info2 = search_team_info(team2)

        yield {
            "event": "status",
            "data": "🔎 Recherche du contexte du match (confrontations, cotes, compositions)...",
        }
        match_ctx = search_match_context(team1, team2, date)

        yield {
            "event": "status",
            "data": "✅ Contexte collecté. Préparation de l'analyse...",
        }

        context = (
            f"# INFORMATIONS SUR {team1.upper()}\n"
            + format_context_for_llm(info1)
            + f"\n\n# INFORMATIONS SUR {team2.upper()}\n"
            + format_context_for_llm(info2)
            + f"\n\n# CONTEXTE DU MATCH\n"
            + format_context_for_llm(match_ctx)
        )

        # Petit extrait du contexte pour l'afficher dans l'UI
        context_preview = context[:1500] + ("..." if len(context) > 1500 else "")
        yield {"event": "context", "data": context_preview}

        yield {
            "event": "status",
            "data": "🤖 Génération de l'analyse par l'IA...",
        }

        messages = build_chat_messages(team1, team2, date, competition, context)

        full = []
        for token in stream_analysis(messages):
            full.append(token)
            yield {"event": "token", "data": token}

        yield {"event": "done", "data": "".join(full)}

    except Exception as e:
        logger.exception("Erreur dans analyze_match_stream")
        yield {"event": "error", "data": str(e)}
