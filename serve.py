#!/usr/bin/env python3
"""
citemap local server with self-healing
=======================================
Serves the app and exposes a /heal endpoint.
When index.html catches an unrecoverable error, it POSTs to /heal.
Claude reads the error + current index.html and writes a fix.

Usage:
    python serve.py          # serves on http://localhost:8000 and opens browser
    python serve.py 8080     # use a different port
"""

import http.server
import json
import os
import socketserver
import sys
import threading
import webbrowser
from pathlib import Path

PORT = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 8000
INDEX = "index.html"

HEAL_PROMPT = """\
You are fixing a bug in index.html — a browser-based citation network fetcher
that calls the OpenAlex API and renders results with vis.js.

Error reported:
{error}

Stack / context:
{context}

Current index.html:
{code}

Return ONLY the fixed, complete index.html. No explanation, no markdown fences.
Change as little as possible — fix the root cause, nothing else.
"""


class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # suppress per-request noise

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_GET(self):
        if self.path == "/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._cors()
            self.end_headers()
            self.wfile.write(json.dumps({"heal": True}).encode())
            return
        super().do_GET()

    def do_POST(self):
        if self.path != "/heal":
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length))
        error = body.get("error", "(no error)")
        context = body.get("context", "")

        print(f"\n[heal] Error: {error}")
        print("[heal] Calling Claude to fix index.html...")

        try:
            from anthropic import Anthropic

            code = Path(INDEX).read_text()
            client = Anthropic()
            resp = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=16000,
                messages=[{
                    "role": "user",
                    "content": HEAL_PROMPT.format(error=error, context=context, code=code),
                }],
            )
            fixed = resp.content[0].text.strip()
            # Strip markdown fences if the model wrapped the response
            if fixed.startswith("```"):
                fixed = fixed.split("\n", 1)[1].rsplit("```", 1)[0].strip()

            Path(INDEX).write_text(fixed)
            print("[heal] index.html updated — browser will reload")

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._cors()
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True}).encode())

        except ImportError:
            msg = "anthropic package not installed — run: pip install anthropic"
            print(f"[heal] {msg}")
            self._respond_error(msg)
        except Exception as e:
            print(f"[heal] Failed: {e}")
            self._respond_error(str(e))

    def _respond_error(self, msg):
        self.send_response(500)
        self.send_header("Content-Type", "application/json")
        self._cors()
        self.end_headers()
        self.wfile.write(json.dumps({"ok": False, "error": msg}).encode())


if __name__ == "__main__":
    os.chdir(Path(__file__).parent)
    url = f"http://localhost:{PORT}"

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    heal_status = "active" if api_key else "disabled (set ANTHROPIC_API_KEY to enable)"

    with socketserver.TCPServer(("", PORT), Handler) as srv:
        print(f"citemap  →  {url}")
        print(f"self-heal   {heal_status}")
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            print("\nStopped.")
