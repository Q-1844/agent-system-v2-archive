# -*- coding: utf-8 -*-
"""Phase 53 A1 看片服务：静态托管 review/ + FEEDBACK_P53_I.json 落盘。
用法：python p53_review_server.py [port]  （默认 8790）
"""
import json, sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "review"
FEEDBACK = ROOT / "FEEDBACK_P53_I.json"


class H(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(ROOT), **kw)

    def do_GET(self):
        if self.path == "/api/feedback":
            data = json.loads(FEEDBACK.read_text(encoding="utf-8")) if FEEDBACK.exists() else {}
            b = json.dumps(data, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(b)))
            self.end_headers()
            self.wfile.write(b)
            return
        super().do_GET()

    def do_POST(self):
        if self.path == "/api/feedback":
            n = int(self.headers.get("Content-Length") or 0)
            body = json.loads(self.rfile.read(n).decode("utf-8"))
            cur = json.loads(FEEDBACK.read_text(encoding="utf-8")) if FEEDBACK.exists() else {}
            cur.setdefault("entries", []).append(body.get("fb") or {})
            FEEDBACK.write_text(json.dumps(cur, ensure_ascii=False, indent=1), encoding="utf-8")
            b = b'{"ok":true}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(b)))
            self.end_headers()
            self.wfile.write(b)
            return
        self.send_response(404); self.end_headers()

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8790
    ThreadingHTTPServer(("0.0.0.0", port), H).serve_forever()
