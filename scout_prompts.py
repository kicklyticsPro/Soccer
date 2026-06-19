"""Prompts pour la Passe 1 (SCOUT) - extraction de faits clés."""

from datetime import datetime

CURRENT_DATE = datetime.now().strftime("%d %B %Y")


SCOUT_SYSTEM_PROMPT = """Tu es un SCOUT sportif: ton rôle est d'extraire RAPIDEMENT et PRÉCISÉMENT les faits clés d'un match à partir du contexte web et de tes connaissances.

Tu réponds TOUJOURS en français.
Tu ne fais AUCUNE analyse subjective. Tu ne donnes AUCUN avis, AUCUNE recommandation de pari.
Tu te concentres uniquement sur des FAIS VÉRIFIABLES avec des DONNÉES CHIFFRÉES.

FORMAT DE SORTIE: Markdown structuré avec UNIQUEMENT les faits.
"""


def build_scout_prompt(team1: str, team2: str, date: str, competition: str, context: str) -> str:
    """Prompt pour extraire les faits clés (Pass 1)."""

    match_header = f"{team1} vs {team2}"
    if date:
        match_header += f" - {date}"
    if competition:
        match_header += f" ({competition})"

    return f"""# 🎯 MISSION SCOUT

Extrais les faits clés du match suivant, sans aucune analyse subjective.

## Match
{match_header}

## Date d'analyse: {CURRENT_DATE}

## Contexte web
{context}

---

# 📋 FORMAT DE SORTIE EXACT

Produis UNIQUEMENT cette fiche de faits (pas d'analyse, pas d'avis):

```
📋 FICHE SCOUT - {team1.upper()} vs {team2.upper()}

## 1. {team1.upper()} - INFOS FACTUELLES

**Derniers 5 résultats** (DATES PRÉCISES):
| Date | Compétition | Adversaire | Score | Lieu |
| --- | --- | --- | --- | --- |
| [date] | [compét] | [adv] | [score] | [dom/ext] |

**Statistiques 2025-2026**:
- Buts marqués/match: X.X
- Buts encaissés/match: X.X
- Clean sheets: X/20
- xG/match: X.X
- Possession moyenne: XX%

**Blessures / Absents confirmés**:
- [Joueur 1]: type + durée
- [Joueur 2]: type + durée

**Transferts récents**:
- Arrivées notables: [Joueur + club d'origine]
- Départs notables: [Joueur + club de destination]

**Sélectionneur / Coach**:
- Nom: [Nom]
- Bilan: X victoires / X nuls / X défaites

## 2. {team2.upper()} - INFOS FACTUELLES
[Même structure]

## 3. CONFRONTATIONS DIRECTES (5 dernières)
| Date | Compétition | Lieu | Score | Buts {team1} | Buts {team2} |
| --- | --- | --- | --- | --- | --- |

**Bilan global H2H**: X victoires {team1} / X nuls / X victoires {team2} (sur N matchs)

## 4. CONTEXTE DU MATCH
- **Stade**: Nom + capacité
- **Météo prévue**: Conditions + température
- **Enjeu**: Description
- **Date du match**: {date or 'Non précisée'}

## 5. COTES BOOKMAKERS (si disponibles)
| Bookmaker | 1 | X | 2 | Over 2.5 | BTTS Oui |
| --- | --- | --- | --- | --- | --- |
| Bet365 | X.XX | X.XX | X.XX | X.XX | X.XX |
| Pinnacle | X.XX | X.XX | X.XX | X.XX | X.XX |
| Moyenne | X.XX | X.XX | X.XX | X.XX | X.XX |

## 6. COMPOSITIONS PROBABLES (si connues)

**{team1}**: Formation - GK, DEF x4, MID x3, ATT x3

**{team2}**: Formation - GK, DEF x4, MID x3, ATT x3
```

---

# ⚠️ RÈGLES

1. **DATES et CHIFFRES précis**: Pas de "récemment", donne des dates. Pas de "souvent", donne des %.
2. **PAS D'ANALYSE**: Tu ne donnes aucun avis sur "qui va gagner". Tu listes des faits.
3. **PAS D'INVENTION**: Si tu ne sais pas, écris "[À VÉRIFIER]" plutôt que d'inventer.
4. **STRUCTURE RESPECTÉE**: Suis le format exact ci-dessus.
"""


def build_scout_messages(team1: str, team2: str, date: str, competition: str, context: str):
    """Messages pour le scout (Pass 1)."""
    return [
        {"role": "system", "content": SCOUT_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": build_scout_prompt(team1, team2, date, competition, context),
        },
    ]
