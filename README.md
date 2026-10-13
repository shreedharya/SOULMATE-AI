# SOULMATE

SOULMATE is a browser chat frontend served by a small Python backend. The
backend uses the existing keyword-based chatbot when no LLM key is configured.
The backend proxies NVIDIA's OpenAI-compatible Chat Completions API without
exposing the secret key to the browser.

## Run locally

From this folder, start the backend with Python 3.9 or newer:

```powershell
python server.py
```

Open <http://127.0.0.1:8000> in your browser. Do not open `index.html` directly:
the page needs the backend API at the same origin.

## Enable an LLM

1. Copy `.env.example` to `.env`.
2. Replace `SOULMATE_API_KEY` with your NVIDIA API key.
3. The API URL and model are preconfigured for NVIDIA. Change them only if you
   want to use a different compatible provider or a model available to your
   NVIDIA account.
4. Restart `python server.py`. The header reports whether SOULMATE is using
   local replies or the configured LLM.

`.env` is ignored by Git. Never place an API key in `index.html`, `script.js`,
or any other browser-delivered file. The backend accepts JSON chat messages at
`POST /api/chat` and reports its configuration at `GET /api/health`.

## Run backend checks

```powershell
python -m unittest -v test_server
```
