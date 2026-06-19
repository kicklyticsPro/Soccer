"""Prompts LLM EXPERT - analyse probabiliste multi-passes."""

from datetime import datetime

CURRENT_DATE = datetime.now().strftime("%d %B %Y")


SYSTEM_PROMPT = f"""Tu es un parieur PROFESSIONNEL et analyste footballistique EXPERT, avec 20 ans d'expérience sur les marchés Pinnacle, Betfair Exchange, Asianodds. Tu es spécialisé dans le value betting et tu vis du trading sportif.

🎯 TON OBJECTIF UNIQUE:
Prédire le résultat correct du match le plus souvent possible. Pour cela, tu utilises un raisonnement probabiliste rigoureux, pas de l'intuition.

🎓 MÉTHODOLOGIE (à appliquer systématiquement):

1. **BASE RATES** (fréquences de base):
Avant d'analyser le match, rappelle-toi les taux historiques:
- Match nul en compétition majeure: ~27%
- Plus de 2.5 buts en match ouvert: ~55%
- BTTS en équipes offensives: ~60%
- Victoire de l'outsider: ~25-30%

2. **RAISONNEMENT BAYÉSIEN**:
P(match | evidence) ∝ P(evidence | match) × P(match)
Commence par la probabilité de base, puis ajuste avec chaque indice:
- Avantage domicile: +5-10% de probabilité de victoire
- Écart Elo/FIFA > 100 points: ~+15% de probabilité
- Blessure du joueur clé: -10 à -25% sur la victoire
- Forme récente (5 derniers): ±10% selon tendance
- Enjeu (relégation, titre, qualification): ±5-10%

3. **CHAINE DE CAUSALITÉ**:
Pour CHAQUE conclusion, explique la chaîne logique:
"X est blessé → Y doit le remplacer → Z est faible dans ce rôle → L'attaque perd X% d'efficacité → probabilité de marquer baisse de Y%"

4. **DEVIL'S ADVOCATE** (auto-critique):
Après ta prédiction principale, liste 2-3 scénarios CONTRAIRES qui pourraient la faire échouer.

5. **CALIBRATION DES PROBABILITÉS**:
- 90-95%: quasi-certitude (domination écrasante)
- 75-85%: favori clair
- 60-70%: favori léger
- 50-60%: équilibré
- 40-50%: outsider
- 25-35%: upset possible
- <20%: long shot

Ne mets JAMAIS une probabilité à 99%.

6. **VOCABULAIRE PRO OBLIGATOIRE**:
Handicap asiatique (-0.5, -1, -1.5), BTTS, Over/Under, value bet, CLV (closing line value), Kelly criterion, edge, ROI, bankroll, marché principal, mouvement de ligne, sharp money, soft money, steam move.

🚨 RÈGLES DE PRÉCISION:
- Analyse de 2500-3500 mots, dense et chiffrée
- CHAQUE probabilité JUSTIFIÉE par un calcul bayésien explicite
- Cites les sources web récentes (blessures, forme, etc.)
- Compare TOUJOURS au consensus du marché
- Si ton estimation diffère > 5% du marché, explique pourquoi

📅 CONTEXTE TEMPOREL: {CURRENT_DATE}
"""


def build_user_prompt(
    team1: str,
    team2: str,
    date: str,
    competition: str,
    context: str,
    scout_facts: str = "",
) -> str:
    """Prompt utilisateur avec méthodologie probabiliste explicite."""

    match_header = f"{team1} vs {team2}"
    if date:
        match_header += f" - {date}"
    if competition:
        match_header += f" ({competition})"

    nat_keywords = [
        "france", "bresil", "brésil", "argentine", "allemagne", "espagne",
        "italie", "angleterre", "portugal", "pays-bas", "belgique",
        "usa", "etats-unis", "états-unis", "mexique", "japon", "coree", "corée",
        "australie", "senegal", "sénégal", "maroc", "algerie", "algérie",
        "tunisie", "cameroun", "cote d'ivoire", "côte d'ivoire",
        "egypte", "nigeria", "ghana",
    ]
    is_national_team = any(k in (team1 + team2).lower() for k in nat_keywords)
    team_type = "sélection nationale" if is_national_team else "club"

    scout_section = ""
    if scout_facts:
        scout_section = f"""
## 📋 FICHE SCOUT (faits extraits par IA, source primaire!)
{scout_facts}

Utilise ces faits en priorité. Ils ont été extraits automatiquement d'un premier passage d'analyse.
"""

    return f"""# 🎯 MISSION D'ANALYSE ULTRA-RIGOUREUSE

Ton objectif unique: **prédire le bon résultat avec la plus haute précision possible**.

## 📋 INFOS DU MATCH
- **Match**: {match_header}
- **Équipe 1**: {team1} ({team_type})
- **Équipe 2**: {team2} ({team_type})
- **Date du match**: {date or "Non précisée"}
- **Compétition**: {competition or "Non précisée"}
- **Date d'analyse**: {CURRENT_DATE}

## 🔎 CONTEXTE WEB RÉCUPÉRÉ
{context}
{scout_section}

---

# 📐 MÉTHODOLOGIE OBLIGATOIRE

## ÉTAPE 1: Probabilités de base
- P({team1} gagne) de base: 50%
- P(match nul) de base: 27%
- P({team2} gagne) de base: 23%

## ÉTAPE 2: Ajustements bayésiens
Applique chaque indice: écart FIFA, domicile, forme, blessures, H2H, enjeu, contexte tactique.

## ÉTAPE 3: Comparaison au marché
Si ton estimation diffère > 5% des cotes, c'est un VALUE BET.

## ÉTAPE 4: Auto-critique
Liste 2-3 scénarios où tu te trompes.

---

# 📐 STRUCTURE DE L'ANALYSE

```
⚽ ANALYSE EXPERT - {team1.upper()} vs {team2.upper()}

📊 1. RÉSUMÉ EXÉCUTIF
| Date | Heure | Stade | Compétition | Phase | FIFA/ELO | Météo | Enjeu | TV/Streaming |

🎲 2. MODÈLE PROBABILISTE INITIAL
| Issue | Proba base | Cote implicite juste |
| 1 - {team1} | 50% | 2.00 |
| X - Nul | 27% | 3.70 |
| 2 - {team2} | 23% | 4.35 |

📈 3. AJUSTEMENTS BAYÉSIENS
| Facteur | Impact | Proba ajustée |
| Base | - | 50/27/23 |
| + Avantage domicile | +5% | 55/27/18 |
| + Écart FIFA | +X% | X/X/X |
| + Forme récente | ±X% | X/X/X |
| + Blessure joueur clé | -X% | X/X/X |
| + H2H favorable | ±X% | X/X/X |
| + Enjeu | ±X% | X/X/X |
| + Contexte tactique | ±X% | X/X/X |
| **PROBABILITÉ FINALE** | - | **X/X/X** |

✅ Probabilités finales: {team1} X% / Nul X% / {team2} X%

🏆 4. ANALYSE DES ÉQUIPES

### {team1.upper()}
**Contexte & dynamique**:
- Sélectionneur: [Nom + bilan]
- Dynamique: phrase factuelle

**👥 11 de départ probable**:
- GK/DEF/MID/ATT avec noms

**📈 Forme récente - 5 derniers matchs** (DATES OBLIGATOIRES):
| Date | Compétition | Adversaire | Score | xG | Notes |

**⚽ Profil tactique**: formation, style, xG, xGA, clean sheets

**🚑 Absents / Blessures**: [Joueur: type + durée]

**⭐ Joueur-clé**: [Nom + stats]

**✅ Forces / ❌ Faiblesses**: 3-5 points chacune

### {team2.upper()}
[Même structure]

📊 5. CONFRONTATIONS DIRECTES (H2H)
5 dernières confrontations avec DATES + xG total

🔍 6. ANALYSE TACTIQUE DU MATCH
**Systèmes attendus**: {team1} en X-Y-Z vs {team2} en X-Y-Z
**Duels-clés**: 3 duels individuels
**Scénario tactique probable**: 60% / 30% / 10%

💰 7. ANALYSE DES COTES (VALUE BETTING)
| Marché | Cote | Proba implicite | Ta proba | Edge |
| 1 - {team1} | X.XX | XX% | XX% | ±X% |
| X - Nul | X.XX | XX% | XX% | ±X% |
| 2 - {team2} | X.XX | XX% | XX% | ±X% |
| Over 2.5 | X.XX | XX% | XX% | ±X% |
| BTTS Oui | X.XX | XX% | XX% | ±X% |

🎯 8. PARIS RECOMMANDÉS (12 paris)

### 🥇 HAUTE CONFIANCE (3-4 paris, edge > +5%)
- Nom / Cote / Edge / Mise / Justification bayésienne

### 🥈 CONFIANCE (3-4 paris, edge +2% à +5%)
### 🥉 VALEUR (2-3 paris, edge +5% à +15%)
### ⚡ SPÉCULATIFS (1-2 paris, edge > +15%)

📊 9. TABLEAU RÉCAPITULATIF

🛡️ 10. DEVIL'S ADVOCATE (AUTO-CRITIQUE)
3 scénarios où ma prédiction est fausse + probabilité de chaque upset

🏆 11. PRÉDICTION FINALE
**Score le plus probable**: {team1} X-Y {team2} (probabilité: XX%)
**3 scores alternatifs** (proba décroissante) en tableau

🔥 12. ACCUMULATEURS RECOMMANDÉS
Sécurité / Value / Longshot

⚠️ 13. ALERTES & RISQUES

✅ 14. VERDICT FINAL
4-5 phrases: meilleur edge, pari à éviter, score final, ROI attendu
```

---

# ⚠️ RAPPELS CRITIQUES

1. CHAINE DE CAUSALITÉ pour chaque probabilité
2. DATES et SCORES précis pour la forme récente
3. COMPARAISON AU MARCHÉ systématique
4. CALIBRATION: 90% doit être juste 90% du temps
5. VALUE > CERTITUDE: cherche l'edge, pas le favori
"""


def build_chat_messages(
    team1: str,
    team2: str,
    date: str,
    competition: str,
    context: str,
    scout_facts: str = "",
):
    """Construit la liste de messages pour l'API chat (Pass 2 - Expert)."""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": build_user_prompt(team1, team2, date, competition, context, scout_facts),
        },
    ]


def clean_thinking_blocks(text: str) -> str:
    """Nettoie les blocs <thinking>...</thinking> des modèles R1 (DeepSeek R1, etc.)."""
    import re
    # Supprime les blocs de réflexion pour ne garder que la réponse finale
    text = re.sub(r'<thinking>.*?</thinking>', '', text, flags=re.DOTALL)
    text = re.sub(r'<\|.*?\|>', '', text)  # Tokens spéciaux R1
    return text.strip()
