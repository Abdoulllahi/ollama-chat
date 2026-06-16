# Ollama Chat

A small, self-built chat interface for local LLMs running through [Ollama](https://ollama.com).
This is a learning project: a minimal Flask backend talking to Ollama, with a plain
HTML/JS frontend, file upload, and a first simple "tool calling" example.

No cloud APIs, no API keys, no data leaves your machine.

## How it works

```
Browser (frontend/index.html)
        |
        v
Flask backend (backend/app.py)  -- handles file upload, tool calls
        |
        v
Ollama (localhost:11434)        -- runs the actual model
```

## Requirements

- Python 3.9+
- [Ollama](https://ollama.com/download) installed and running
- A model pulled, e.g.:
  ```
  ollama pull llama3.2
  ```

## Setup

### Option A: automated setup script (recommended)

Run this first - it checks whether Ollama is installed, opens the download
page if it isn't, and lets you pick which model to pull:

```
python scripts/setup.py
```

It walks you through the available models and what each one trades off
(speed vs. quality vs. download size), then pulls your choice. If you skip
the choice, it defaults to Llama 3.2 (3B), a good balance for most laptops.

### Option B: manual setup

1. Clone this repo:
   ```
   git clone https://github.com/YOUR_USERNAME/ollama-chat.git
   cd ollama-chat
   ```

2. Create and activate a virtual environment, then install dependencies:

   On Windows:
   ```
   cd backend
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

   On macOS/Linux:
   ```
   cd backend
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. Make sure Ollama is running (it usually starts automatically after install).
   Verify with:
   ```
   ollama list
   ```

4. Start the backend:
   ```
   python app.py
   ```
   This runs on `http://localhost:8000`.

5. Open `frontend/index.html` directly in your browser (just double-click the file,
   or open it via `file://` path). No build step needed.

## Features

- **Chat** - send a message, get a streamed response from your local model
- **File upload** - upload a `.txt`, `.md`, or `.csv` file; its content is added
  as context to your next message
- **Simple tool calling** - type a message containing "calculate ..." and the
  backend will actually compute it and feed the result to the model

## Project structure

```
ollama-chat/
├── backend/
│   ├── app.py             Flask server
│   └── requirements.txt
├── frontend/
│   └── index.html         Single-page chat UI
├── scripts/
│   └── setup.py           Checks for Ollama, installs/pulls a model
├── .gitignore
├── LICENSE
└── README.md
```

## Notes on the tool-calling approach

This is intentionally the simplest possible version of "tool calling" - the
backend looks for a keyword pattern ("calculate ...") rather than having the
model itself decide which tool to call via structured output. That's a
reasonable next step once this basic version works:

- Have the model respond with a structured marker (e.g. a JSON block) when it
  wants to use a tool
- Parse that marker in the backend, run the tool, and send the result back to
  the model for a final answer

## Status

Early prototype, built for learning how local LLMs, basic agent loops, and
simple web interfaces fit together. Not production-ready - no auth, no
persistent storage, minimal error handling.

## License

MIT - see [LICENSE](LICENSE).