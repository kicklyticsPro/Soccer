"""Module de recherche web pour récupérer des informations sur les équipes et matchs."""
from __future__ import annotations

import logging
import time
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed

from duckduckgo_search import DDGS

from config import Config

logger = logging.getLogger(__name__)


def _duckduckgo_search(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Effectue une recherche DuckDuckGo avec retries."""
    results = []
    last_err = None
    for attempt in range(3):
        try:
            with DDGS() as ddgs:
                # Essai avec région française d'abord
                try:
                    for r in ddgs.text(query, max_results=max_results, region="fr-fr"):
                        results.append(
                            {
                                "title": r.get("title", ""),
                                "url": r.get("href", r.get("url", "")),
                                "snippet": r.get("body", r.get("snippet", "")),
                            }
                        )
                except Exception:
                    # Fallback mondial
                    for r in ddgs.text(query, max_results=max_results):
                        results.append(
                            {
                                "title": r.get("title", ""),
                                "url": r.get("href", r.get("url", "")),
                                "snippet": r.get("body", r.get("snippet", "")),
                            }
                        )
            if results:
                return results
        except Exception as e:
            last_err = e
            logger.warning(
                "DuckDuckGo tentative %d/3 échouée pour '%s': %s",
                attempt + 1,
                query,
                e,
            )
            time.sleep(0.5 * (attempt + 1))  # backoff
    if last_err:
        logger.warning("DuckDuckGo a totalement échoué pour '%s': %s", query, last_err)
    return results


def _tavily_search(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Recherche Tavily (optionnelle, meilleure qualité)."""
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
    """Recherche principale. Tavily si configuré, sinon DuckDuckGo."""
    if Config.TAVILY_API_KEY:
        results = _tavily_search(query, max_results)
        if results:
            return results
    return _duckduckgo_search(query, max_results)


def search_team_info(team: str) -> Dict[str, List[Dict[str, str]]]:
    """Récupère des infos complètes et RÉCENTES sur une équipe."""
    current_year = time.strftime("%Y")
    queries = {
        # Infos générales
        "effectif": f"{team} effectif joueurs 2026",
        "selectionneur": f"{team} sélectionneur coach 2026",
        # Données récentes (critique pour la précision)
        "forme_recente": f"{team} résultats derniers matchs {current_year} forme",
        "stats": f"{team} statistiques buts xG possession {current_year}",
        "joueurs_cles": f"{team} meilleur buteur passeur {current_year}",
        "blessures": f"{team} blessés absents suspensions dernière minute {current_year}",
        "composition": f"{team} composition probable XI départ {current_year}",
        "transferts": f"{team} transferts recrues départs mercato {current_year}",
    }

    results: Dict[str, List[Dict[str, str]]] = {k: [] for k in queries}

    with ThreadPoolExecutor(max_workers=8) as executor:
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
    """Récupère le contexte complet d'un match spécifique."""
    current_year = time.strftime("%Y")
    date_str = f" {date}" if date else ""
    match_query = f"{team1} vs {team2}{date_str}"

    queries = {
        # Confrontations et historique
        "h2h": f"{team1} {team2} historique confrontations head to head",
        "h2h_recents": f"{team1} {team2} derniers face à face résultats",
        # Prédictions et cotes
        "pronostics": f"{match_query} pronostic analyse",
        "cotes": f"{match_query} cotes bookmaker betting odds",
        "cotes_mouvement": f"{match_query} cotes évolution mouvement ligne sharp money",
        # Contexte tactique
        "composition": f"{match_query} composition probable tactique schéma",
        "duels_cles": f"{match_query} duels clés confrontations joueurs",
        # Contexte général
        "enjeu": f"{match_query} enjeu contexte qualification titre",
        "stade_meteo": f"{match_query} stade météo conditions",
        "actualites": f"{match_query} actualités news dernière minute",
    }

    results: Dict[str, List[Dict[str, str]]] = {k: [] for k in queries}

    with ThreadPoolExecutor(max_workers=10) as executor:
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
                # Tronquer le snippet à 200 chars max pour économiser les tokens
                if len(snippet) > 250:
                    snippet = snippet[:250] + "..."
                lines.append(f"[{i}] {title}: {snippet}")
    text = "\n".join(lines)
    return text
