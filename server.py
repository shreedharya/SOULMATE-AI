import json
import os
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urlsplit
from urllib.request import Request, urlopen

from chatbot import RESPONSES, detect_emotion


HOST = "127.0.0.1"
PORT = 8000
MAX_BODY_BYTES = 64 * 1024
MAX_MESSAGES = 30
MAX_MESSAGE_LENGTH = 2000


def load_env_file():
    env_path = Path(__file__).resolve().parent / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        os.environ.setdefault(name.strip(), value)


load_env_file()
API_URL = os.environ.get(
    "SOULMATE_API_URL", "https://api.openai.com/v1/chat/completions"
)
MODEL = os.environ.get("SOULMATE_MODEL", "gpt-4o-mini")
API_KEY = os.environ.get("SOULMATE_API_KEY")
SYSTEM_PROMPT = (
    "You are SOULMATE, a warm, empathetic conversational companion. "
    "Listen carefully, respond naturally and concisely, and avoid diagnosing "
    "mental health conditions. You are not a substitute for professional care. "
    "If someone may be in immediate danger, encourage them to contact local "
    "emergency services or a trusted person."
)


class SoulmateHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(Path(__file__).resolve().parent), **kwargs)

    def do_GET(self):
        path = unquote(urlsplit(self.path).path)
        if any(part.startswith(".env") for part in path.split("/")):
            self.send_error(404)
            return
        if self.path == "/api/health":
            self._send_json(
                200,
                {
                    "ok": True,
                    "mode": "llm" if API_KEY else "local",
                    "model": MODEL if API_KEY else None,
                },
            )
            return
        super().do_GET()

    def do_POST(self):
        if self.path != "/api/chat":
            self._send_json(404, {"error": "Endpoint not found."})
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._send_json(400, {"error": "Invalid content length."})
            return

        if content_length <= 0 or content_length > MAX_BODY_BYTES:
            self._send_json(413, {"error": "Request body is empty or too large."})
            return

        try:
            payload = json.loads(self.rfile.read(content_length))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._send_json(400, {"error": "Request body must be valid JSON."})
            return

        messages = payload.get("messages") if isinstance(payload, dict) else None
        if not self._valid_messages(messages):
            self._send_json(
                400,
                {
                    "error": (
                        "Provide 1–30 messages with role 'user' or 'assistant'; "
                        "the latest message must be from the user."
                    )
                },
            )
            return

        message = messages[-1]["content"]
        emotion = detect_emotion(message)
        if API_KEY:
            try:
                reply = self._request_llm(messages)
            except (HTTPError, URLError, TimeoutError, OSError, ValueError) as error:
                if isinstance(error, HTTPError):
                    self.log_error("LLM provider returned HTTP %s", error.code)
                else:
                    self.log_error("LLM provider request failed: %s", error)
                self._send_json(
                    502,
                    {
                        "error": (
                            "The LLM provider request failed. Check server logs "
                            "and API configuration."
                        )
                    },
                )
                return
        else:
            reply = RESPONSES[emotion]

        self._send_json(200, {"reply": reply, "emotion": emotion})

    @staticmethod
    def _valid_messages(messages):
        if not isinstance(messages, list) or not 1 <= len(messages) <= MAX_MESSAGES:
            return False
        for message in messages:
            if not isinstance(message, dict):
                return False
            if message.get("role") not in {"user", "assistant"}:
                return False
            content = message.get("content")
            if (
                not isinstance(content, str)
                or not content.strip()
                or len(content) > MAX_MESSAGE_LENGTH
            ):
                return False
        return messages[-1]["role"] == "user"

    def _request_llm(self, messages):
        request_body = json.dumps(
            {
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    *messages,
                ],
            }
        ).encode("utf-8")
        request = Request(
            API_URL,
            data=request_body,
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urlopen(request, timeout=45) as response:
            provider_data = json.loads(response.read().decode("utf-8"))
        reply = provider_data["choices"][0]["message"]["content"]
        if not isinstance(reply, str) or not reply.strip():
            raise ValueError("LLM provider response did not contain a reply.")
        return reply.strip()

    def _send_json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)


def main():
    server = ThreadingHTTPServer((HOST, PORT), partial(SoulmateHandler))
    print(f"SOULMATE server running at http://{HOST}:{PORT}")
    print(f"Chat mode: {'LLM' if API_KEY else 'local keyword responses'}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping SOULMATE server.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
