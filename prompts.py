"""Prompts LLM pour générer une analyse de match style parieur professionnel."""


SYSTEM_PROMPT = """Tu es un analyste sportif professionnel spécialisé dans les paris sportifs sur le football.
Tu combines rigueur statistique, connaissance du jeu et sens du risque pour produire des analyses complètes.

RÈGLES DE STYLE ET DE FORMATAGE:
- Tu réponds TOUJOURS en français
- Tu utilises le format Markdown avec emojis pour les titres de sections
- Tu utilises des tableaux Markdown pour présenter les données chiffrées
- Tu fais des analyses PRÉCISES basées UNIQUEMENT sur les sources fournies dans le contexte
- Si une information n'est pas disponible dans le contexte, tu écris "Non disponible" plutôt que d'inventer
- Tu es prudent: tu ne recommandes jamais de mises trop risquées
- Tu justifies TOUJOURS chaque recommandation avec des données chiffrées

RÈGLES SUR LES PARIS:
- Tu présentes toujours entre 8 et 12 paris différents
- Tu classes les paris en 3 catégories: HAUTE CONFIANCE (⭐⭐⭐⭐⭐), CONFIANCE (⭐⭐⭐⭐), VALEUR (⭐⭐⭐), SPÉCULATIF (⭐⭐⭐)
- Pour chaque pari tu donnes: le type de pari, une cote approximative, un niveau de confiance, une justification, et une mise recommandée sur 10
- Tu recommandes TOUJOURS un ACCUMULATEUR (combiné) en fin d'analyse
- Tu termines TOUJOURS par un SCORE PRÉDIT final avec justification

LONGUEUR: Sois exhaustif et détaillé comme un vrai parieur pro (entre 1500 et 2500 mots).
"""


def build_user_prompt(
    team1: str,
    team2: str,
    date: str,
    competition: str,
    context: str,
) -> str:
    """Construit le prompt utilisateur avec le contexte de recherche."""

    match_header = f"{team1} vs {team2}"
    if date:
        match_header += f" - {date}"
    if competition:
        match_header += f" ({competition})"

    return f"""# ANALYSE DE MATCH DEMANDÉE

**Match**: {match_header}
**Équipe 1**: {team1}
**Équipe 2**: {team2}
**Date**: {date or "Non précisée"}
**Compétition**: {competition or "Non précisée"}

---

# CONTEXTE RÉCUPÉRÉ SUR LE WEB

Voici les informations les plus récentes que j'ai collectées sur les deux équipes et le match.
Tu dois utiliser UNIQUEMENT ces informations (et tes connaissances générales du football)
pour produire l'analyse. Si une donnée manque, écris "Non disponible".

{context}

---

# CONSIGNE

Produis maintenant l'analyse complète et professionnelle de ce match, dans le style d'un parieur expert,
en suivant EXACTEMENT cette structure Markdown:

```
⚽ ANALYSE COMPLÈTE {team1.upper()} vs {team2.upper()} - {competition or "Match"}

📊 RÉSUMÉ DU MATCH
[Tableau Markdown avec: Date, Heure, Stade, Compétition, Groupe/Phase, Classement FIFA, Forme récente, Effectif]

🏆 ANALYSE DÉTAILLÉE DES ÉQUIPES

🇫🇷/[Drapeau] ÉQUIPE {team1.upper()}
**Sélectionneur**: [Nom]
**Effectif clé**: [Liste des joueurs par poste avec statistiques clés]
**Forme récente (5 derniers matchs)**: [Tableau Markdown date/adversaire/score]
[2-3 phrases de synthèse de la forme]

**Points forts**:
- [3 à 5 points avec emojis]

**Points faibles**:
- [3 à 5 points avec emojis]

🇸🇳/[Drapeau] ÉQUIPE {team2.upper()}
[Même structure]

📈 CONFRONTATIONS DIRECTES
[Tableau des confrontations historiques + paragraphe d'analyse]

💰 ANALYSE DES COTES DE PARIS
[Tableau des cotes par marché avec probabilité implicite]

🎯 MEILLEURS PARIS - ANALYSE PROFESSIONNELLE

🥇 PARIS HAUTE CONFIANCE (3-4 paris)
[Numérotés, chacun avec: titre, cote, confiance ⭐, analyse détaillée, mise recommandée /10]

🥈 PARIS CONFIANCE (2-3 paris)
[Même structure]

🥉 PARIS VALEUR (2-3 paris)
[Même structure]

⚡ PARIS SPÉCULATIFS (1-2 paris)
[Même structure]

📊 TABLEAU RÉCAPITULATIF DES PARIS
[Tableau Markdown avec Rang, Type, Cote, Confiance, Mise]

📈 STRATÉGIE DE MISE RECOMMANDÉE
[2 profils: parieur prudent + parieur agressif avec répartition]

🎯 PRÉDICTION FINALE
**Score prédit**: [Score]
[Paragraphe d'analyse avec facteurs clés]

🔥 ACCUMULATEUR RECOMMANDÉ
[Une combinaison de 2-3 paris avec cote totale]
```

N'oublie aucun emoji, aucun tableau. Sois exhaustif.
"""


def build_chat_messages(team1: str, team2: str, date: str, competition: str, context: str):
    """Construit la liste de messages pour l'API chat."""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": build_user_prompt(team1, team2, date, competition, context),
        },
    ]
