# ⚽ Football Analyzer

Une application web Python qui analyse un match de football comme un parieur professionnel,
en combinant **recherche web en temps réel** + **LLM** pour générer automatiquement une analyse
structurée (forme, confrontations, cotes, paris recommandés, score prédit).

Interface en streaming : l'analyse s'écrit en temps réel pendant que le LLM répond.

---

## ✨ Fonctionnalités

- 🔎 **Recherche web automatique** sur les deux équipes et le contexte du match
  (DuckDuckGo par défaut, Tavily en option)
- 🤖 **Génération LLM** via une API compatible OpenAI (OpenAI, Mistral, DeepSeek,
  Groq, Ollama local, LM Studio, etc.)
- 📊 **Analyse structurée** : résumé, forme récente, confrontations, cotes, paris recommandés
  (HAUTE CONFIANCE / CONFIANCE / VALEUR / SPÉCULATIF), accumulateur, score prédit
- ⚡ **Streaming en temps réel** (Server-Sent Events) avec rendu Markdown progressif
- 🎨 **Interface moderne** dark mode, responsive, copier / télécharger / imprimer
- 🇫🇷 **Entièrement en français**

---

## 🚀 Installation rapide

### 1. Installer les dépendances

```bash
cd football-analyzer
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configurer la clé API

Copiez le fichier d'exemple et éditez-le :

```bash
cp .env.example .env
```

Renseignez au minimum `LLM_API_KEY`. Les configurations les plus courantes :

| Fournisseur | `LLM_BASE_URL` | `LLM_MODEL` |
|---|---|---|
| **OpenAI** | `https://api.openai.com/v1` | `gpt-4o-mini` ou `gpt-4o` |
| **Mistral** | `https://api.mistral.ai/v1` | `mistral-large-latest` |
| **DeepSeek** | `https://api.deepseek.com/v1` | `deepseek-chat` |
| **Groq** | `https://api.groq.com/openai/v1` | `llama-3.1-70b-versatile` |
| **Ollama (local)** | `http://localhost:11434/v1` | `llama3.1`, `mistral`, `qwen2.5` |
| **LM Studio (local)** | `http://localhost:1234/v1` | modèle chargé |

> 💡 Pour Arena.ai : si vous avez un endpoint compatible OpenAI fourni par Arena.ai,
> pointez `LLM_BASE_URL` vers cet endpoint et utilisez la clé fournie.

### 3. Lancer le serveur

```bash
python app.py
```

Ouvrez http://localhost:5000 dans votre navigateur.

---

## 🧪 Utilisation

Dans l'interface, entrez simplement le match à analyser. Formats acceptés :

```
France vs Sénégal
France vs Sénégal - 16 Juin 2026
France vs Sénégal - 16 Juin 2026 - Coupe du Monde
Real Madrid vs Barcelone - 26/10/2025
```

L'application va :
1. 🔎 Rechercher les infos sur les 2 équipes (effectif, forme, joueurs clés, blessures)
2. 🔎 Rechercher le contexte du match (confrontations directes, cotes bookmakers, compositions)
3. 🤖 Envoyer tout ce contexte au LLM avec un prompt structuré
4. 📝 Générer l'analyse en streaming

---

## 🔍 Recherche web

| Source | Coût | Qualité | Clé requise |
|---|---|---|---|
| **DuckDuckGo** (défaut) | Gratuit | ⭐⭐⭐ | ❌ |
| **Tavily** (option) | Gratuit jusqu'à 1000 req/mois | ⭐⭐⭐⭐⭐ | ✅ `TAVILY_API_KEY` |

Pour activer Tavily, obtenez une clé sur https://tavily.com et ajoutez-la dans `.env`.

---

## 📂 Structure du projet

```
football-analyzer/
├── app.py                  # Serveur Flask + endpoints
├── analyzer.py             # Orchestrateur (parse match → search → LLM)
├── web_search.py           # Recherche DuckDuckGo + Tavily
├── llm_client.py           # Client OpenAI-compatible avec streaming
├── prompts.py              # Prompts système + utilisateur
├── config.py               # Configuration via .env
├── requirements.txt
├── .env.example
├── templates/
│   └── index.html          # Interface principale
└── static/
    ├── css/style.css       # Thème dark moderne
    └── js/script.js        # Frontend streaming + rendu Markdown
```

---

## 🎯 Personnaliser le prompt

Le prompt qui structure l'analyse est dans **`prompts.py`** :

- `SYSTEM_PROMPT` : la personnalité et les règles de formatage du LLM
- `build_user_prompt()` : la structure exacte (sections, tableaux, emojis) que le LLM doit produire

Vous pouvez modifier ces prompts pour ajuster le style (plus court, plus agressif, focus sur un championnat, etc.).

---

## 🔌 API

### `POST /api/analyze`

Lance une analyse. Réponse en streaming SSE.

**Body** :
```json
{ "match": "France vs Sénégal - 16 Juin 2026" }
```

**Événements SSE** :
- `event: status` — texte de statut intermédiaire
- `event: context` — extrait du contexte web utilisé
- `event: token` — token du LLM (à concaténer)
- `event: done` — analyse complète
- `event: error` — message d'erreur

### `GET /api/health`

Vérifie la configuration :
```json
{ "status": "ok", "llm_configured": true, "llm_model": "gpt-4o-mini", "tavily_configured": false }
```

---

## ⚠️ Avertissement

Cette application est conçue à des fins éducatives et d'analyse. Les analyses générées
ne constituent pas un conseil en paris sportif. Les paris comportent des risques
financiers. Vérifiez toujours les cotes réelles sur les sites de bookmakers avant
toute mise.
