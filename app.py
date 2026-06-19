"""Application Flask principale."""
import json
import logging
from flask import Flask, render_template, request, Response, jsonify
from flask_cors import CORS

from config import Config
from analyzer import parse_match_input, analyze_match_stream

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)


@app.route("/")
def index():
    """Page principale avec le formulaire d'analyse."""
    return render_template("index.html", llm_model=Config.LLM_MODEL)


@app.route("/api/health")
def health():
    """Endpoint de santé pour vérifier la configuration."""
    return jsonify(
        {
            "status": "ok",
            "llm_configured": bool(Config.LLM_API_KEY),
            "llm_model": Config.LLM_MODEL,
            "tavily_configured": bool(Config.TAVILY_API_KEY),
        }
    )


@app.route("/api/analyze", methods=["POST"])
def analyze():
    """Endpoint principal: analyse un match avec streaming SSE."""
    data = request.get_json(silent=True) or {}
    raw = (data.get("match") or "").strip()
    if not raw:
        return jsonify({"error": "Le paramètre 'match' est requis"}), 400

    try:
        parsed = parse_match_input(raw)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    if not Config.LLM_API_KEY:
        return (
            jsonify(
                {
                    "error": (
                        "LLM_API_KEY non configurée. Copiez .env.example vers .env "
                        "et ajoutez votre clé API (OpenAI, Mistral, Ollama, etc.)."
                    )
                }
            ),
            500,
        )

    team1 = parsed["team1"]
    team2 = parsed["team2"]
    date = parsed["date"]
    competition = parsed["competition"]

    logger.info("Analyse demandée: %s vs %s (%s)", team1, team2, date)

    def generate():
        for evt in analyze_match_stream(team1, team2, date, competition):
            yield f"event: {evt['event']}\ndata: {json.dumps(evt['data'], ensure_ascii=False)}\n\n"

    return Response(generate(), mimetype="text/event-stream")


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("⚽ Football Analyzer")
    logger.info("=" * 60)
    logger.info("LLM: %s @ %s", Config.LLM_MODEL, Config.LLM_BASE_URL)
    logger.info("LLM_API_KEY configurée: %s", "✅" if Config.LLM_API_KEY else "❌")
    logger.info("Tavily: %s", "✅" if Config.TAVILY_API_KEY else "❌ (DuckDuckGo)")
    logger.info("Serveur: http://%s:%s", Config.FLASK_HOST, Config.FLASK_PORT)
    logger.info("=" * 60)

    app.run(
        host=Config.FLASK_HOST,
        port=Config.FLASK_PORT,
        debug=Config.FLASK_DEBUG,
        threaded=True,
    )
