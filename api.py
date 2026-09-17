import os

from flask import Flask, request, jsonify

from agent import api_chat


app = Flask(__name__)


@app.get("/")
def home():
    return jsonify({
        "name": "my-agent",
        "status": "online",
        "version": "10.18"
    })


@app.get("/health")
def health():
    return jsonify({
        "status": "healthy"
    })


@app.post("/chat")
def chat():
    data = request.get_json(silent=True) or {}
    message = data.get("message", "").strip()

    if not message:
        return jsonify({
            "status": "error",
            "error": "message is required"
        }), 400

    try:
        result = api_chat(message)

        if result.get("status") == "blocked":
            return jsonify(result), 403

        return jsonify(result)

    except Exception as error:
        return jsonify({
            "status": "failed",
            "error": str(error)
        }), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(
        host="0.0.0.0",
        port=port
    )
