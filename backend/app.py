import json
import re

import requests
from flask import Flask, request, jsonify, Response
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2"

uploaded_files = {}


def calculator_tool(expression: str) -> str:
    if not re.fullmatch(r"[0-9+\-*/().\s]+", expression):
        return "Error: invalid characters in expression."
    try:
        return str(eval(expression))
    except Exception as exc:
        return f"Error: {exc}"


def build_prompt(user_message: str, session_id: str) -> str:
    file_text = uploaded_files.get(session_id)
    if not file_text:
        return user_message
    return (
        f"File content:\n\n---\n{file_text}\n---\n\n"
        f"Question: {user_message}"
    )


@app.route("/api/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]
    session_id = request.form.get("session_id", "default")

    try:
        text = file.read().decode("utf-8", errors="ignore")
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400

    uploaded_files[session_id] = text
    return jsonify({"message": f"Uploaded '{file.filename}'", "length": len(text)})


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_message = data.get("message", "")
    session_id = data.get("session_id", "default")

    if not user_message.strip():
        return jsonify({"error": "Message cannot be empty"}), 400

    calc_match = re.search(r"calculate\s+(.+)", user_message, re.IGNORECASE)
    tool_result = calculator_tool(calc_match.group(1)) if calc_match else None

    prompt = build_prompt(user_message, session_id)
    if tool_result is not None:
        prompt += f"\n\n(Calculator result: {tool_result})"

    def generate():
        with requests.post(
            OLLAMA_URL,
            json={"model": MODEL_NAME, "prompt": prompt, "stream": True},
            stream=True,
            timeout=120,
        ) as r:
            for line in r.iter_lines():
                if not line:
                    continue
                token = json.loads(line).get("response", "")
                if token:
                    yield token

    return Response(generate(), mimetype="text/plain")


@app.route("/api/health", methods=["GET"])
def health():
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=5)
        ollama_ok = r.status_code == 200
    except requests.exceptions.RequestException:
        ollama_ok = False
    return jsonify({"backend": "ok", "ollama_reachable": ollama_ok})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)