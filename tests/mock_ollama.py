"""A tiny fake Ollama server for tests: streams a canned answer with plausible timing fields."""
import json, re, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

def answer(prompt):
    return "Step 1... Step 2...\n42"

class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass
    def do_GET(self):
        body = json.dumps({"models": [{"name": "mock:1b", "size": 2 * 2**30, "size_vram": 2 * 2**30}]}).encode()
        self.send_response(200); self.end_headers(); self.wfile.write(body)
    def do_POST(self):
        req = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        self.send_response(200); self.end_headers()
        text = answer(req.get("prompt", "")); n = max(1, len(text) // 4)
        for i in range(0, len(text), 8):
            self.wfile.write((json.dumps({"response": text[i:i + 8], "done": False}) + "\n").encode()); time.sleep(0.001)
        pc = len(req.get("prompt", "").split())
        self.wfile.write((json.dumps({"response": "", "done": True, "prompt_eval_count": pc, "prompt_eval_duration": pc * 1_000_000,
                                      "eval_count": n, "eval_duration": n * 20_000_000, "load_duration": 0}) + "\n").encode())

def serve(port=11500):
    s = ThreadingHTTPServer(("127.0.0.1", port), H); threading.Thread(target=s.serve_forever, daemon=True).start(); return s
