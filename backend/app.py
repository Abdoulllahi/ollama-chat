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
conversations = {}

TOOL_SYSTEM_PROMPT = """You have access to these tools:

calculator(expression) - evaluate basic arithmetic
current_time() - get the current date and time

If you need a tool, respond with ONLY this exact format, nothing else:
TOOL_CALL: tool_name(argument)

If you don't need a tool, just answer normally.
"""


def run_calculator(expression: str) -> str:
    if not re.fullmatch(r"[0-9+\-*/().\s]+", expression):
        return "Error: invalid characters in expression."
    try:
        return str(eval(expression))
    except Exception as exc:
        return f"Error: {exc}"


def run_current_time(_unused: str = "") -> str:
    import datetime
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


TOOL_FUNCTIONS = {
    "calculator": run_calculator,
    "current_time": run_current_time,
}


def call_ollama(prompt: str) -> str:
    response = requests.post(
        OLLAMA_URL,
        json={"model": MODEL_NAME, "prompt": prompt, "stream": False},
        timeout=120,
    )
    return response.json().get("response", "")


def try_parse_tool_call(text: str):
    match = re.search(r"TOOL_CALL:\s*(\w+)\((.*?)\)", text)
    if not match:
        return None
    tool_name, argument = match.group(1), match.group(2)
    return tool_name, argument


def build_history_text(session_id: str) -> str:
    history = conversations.get(session_id, [])
    lines = []
    for turn in history:
        lines.append(f"User: {turn['user']}")
        lines.append(f"Assistant: {turn['assistant']}")
    return "\n".join(lines)


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

    file_text = uploaded_files.get(session_id)
    history_text = build_history_text(session_id)

    prompt_parts = [TOOL_SYSTEM_PROMPT]
    if file_text:
        prompt_parts.append(f"Uploaded file content:\n---\n{file_text}\n---")
    if history_text:
        prompt_parts.append(f"Conversation so far:\n{history_text}")
    prompt_parts.append(f"User: {user_message}\nAssistant:")

    first_prompt = "\n\n".join(prompt_parts)
    first_response = call_ollama(first_prompt)

    tool_call = try_parse_tool_call(first_response)
    final_response = first_response

    if tool_call:
        tool_name, argument = tool_call
        tool_fn = TOOL_FUNCTIONS.get(tool_name)
        if tool_fn:
            tool_result = tool_fn(argument)
            follow_up_prompt = (
                f"{first_prompt}\n"
                f"{first_response}\n\n"
                f"Tool result: {tool_result}\n\n"
                f"Now give the user a final natural-language answer using this result."
            )
            final_response = call_ollama(follow_up_prompt)
        else:
            final_response = f"(Requested unknown tool: {tool_name})"

    conversations.setdefault(session_id, []).append(
        {"user": user_message, "assistant": final_response}
    )

    def generate():
        yield final_response

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
