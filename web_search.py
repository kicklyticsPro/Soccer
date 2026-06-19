"""Module de recherche web pour récupérer des informations sur les équipes et matchs."""
from __future__ import annotations

import logging
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed

from duckduckgo_search import DDGS

from config import Config

logger = logging.getLogger(__name__)


def _duckduckgo_search(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Effectue une recherche DuckDuckGo et retourne les résultats."""
    results = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results, region="fr-fr"):
                results.append(
                    {
                        "title": r.get("title", ""),
                        "url": r.get("href", r.get("url", "")),
                        "snippet": r.get("body", r.get("snippet", "")),
                    }
                )
    except Exception as e:
        logger.warning("DuckDuckGo a échoué pour '%s': %s", query, e)
    return results


def _tavily_search(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Effectue une recherche via l'API Tavily (si clé configurée)."""
    if not Config.TAVILY_API_KEY:
        return []
    try:
        import requests

        resp = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": Config.TAVILY_API_KEY,
                "query": query,
                "max_results": max_results,
                "search_depth": "advanced",
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        return [
            {
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "snippet": r.get("content", ""),
            }
            for r in data.get("results", [])
        ]
    except Exception as e:
        logger.warning("Tavily a échoué pour '%s': %s", query, e)
        return []


def search(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Recherche principale. Utilise Tavily si dispo, sinon DuckDuckGo."""
    if Config.TAVILY_API_KEY:
        results = _tavily_search(query, max_results)
        if results:
            return results
    return _duckduckgo_search(query, max_results)


def search_team_info(team: str) -> Dict[str, List[Dict[str, str]]]:
    """Récupère toutes les informations pertinentes sur une équipe en parallèle."""
    queries = {
        "effectif": f"{team} effectif joueurs liste 2026",
        "selectionneur": f"{team} sélectionneur coach staff technique 2026",
        "forme": f"{team} résultats derniers matchs forme récente 2026",
        "statistiques": f"{team} statistiques buts marqués encaissés 2026",
        "joueurs_cles": f"{team} joueurs clés capitaine meilleur buteur 2026",
        "actualites": f"{team} actualités blessures news équipe",
    }

    results: Dict[str, List[Dict[str, str]]] = {k: [] for k in queries}

    with ThreadPoolExecutor(max_workers=6) as executor:
        future_to_key = {
            executor.submit(search, q, 3): key for key, q in queries.items()
        }
        for future in as_completed(future_to_key):
            key = future_to_key[future]
            try:
                results[key] = future.result()
            except Exception as e:
                logger.warning("Recherche '%s' a échoué: %s", key, e)

    return results


def search_match_context(team1: str, team2: str, date: str = "") -> Dict[str, List[Dict[str, str]]]:
    """Récupère le contexte spécifique d'un match entre deux équipes."""
    date_str = f" {date}" if date else ""
    match_query = f"{team1} vs {team2}{date_str}"
    queries = {
        "confrontations": f"{team1} {team2} historique confrontations directes head to head",
        "pronostics": f"{match_query} pronostic analyse cotes paris sportif",
        "cotes": f"{match_query} cotes bookmaker betting odds",
        "composition": f"{match_query} composition probable tactique",
        "enjeu": f"{match_query} enjeu contexte compétition",
    }

    results: Dict[str, List[Dict[str, str]]] = {k: [] for k in queries}

    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_key = {
            executor.submit(search, q, 4): key for key, q in queries.items()
        }
        for future in as_completed(future_to_key):
            key = future_to_key[future]
            try:
                results[key] = future.result()
            except Exception as e:
                logger.warning("Recherche '%s' a échoué: %s", key, e)

    return results


def format_context_for_llm(data: Dict[str, List[Dict[str, str]]]) -> str:
    """Formate les données de recherche en contexte textuel pour le LLM."""
    lines = []
    for category, results in data.items():
        if not results:
            continue
        lines.append(f"\n## {category.upper().replace('_', ' ')}")
        for i, r in enumerate(results, 1):
            title = r.get("title", "").strip()
            snippet = r.get("snippet", "").strip()
            url = r.get("url", "").strip()
            if snippet:
                lines.append(f"[Source {i}] {title}")
                lines.append(f"  {snippet}")
                lines.append(f"  URL: {url}")
                lines.append("")
    text = "\n".join(lines)
    # Tronquer si trop long
    if len(text) > Config.MAX_CONTEXT_CHARS:
        text = text[: Config.MAX_CONTEXT_CHARS] + "\n\n[... contexte tronqué ...]"
    return text
