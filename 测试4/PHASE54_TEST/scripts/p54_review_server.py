# -*- coding: utf-8 -*-
"""Phase 54 看片服务：六部候选对比页 + /media 直读项目成片 + FEEDBACK_P54.json 落盘。
用法：python p54_review_server.py [port]  （默认 8790）
"""
import json, sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "review"
FEEDBACK = ROOT / "FEEDBACK_P54.json"
PROJECTS = Path(r"C:\Users\曹文淇\Desktop\ai工作流\animation-storyboard\projects")


class H(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(ROOT), **kw)

    def do_GET(self):
        if self.path.startswith("/media/"):
            parts = self.path[len("/media/"):].split("/")
            if len(parts) == 3 and all(p.strip() for p in parts):
                fp = PROJECTS / parts[0] / "output" / "sequences" / parts[1] / parts[2]
                if fp.exists():
                    self.send_response(200)
                    self.send_header("Content-Type", "video/mp4")
                    self.send_header("Content-Length", str(fp.stat().st_size))
                    self.end_headers()
                    with open(fp, "rb") as f:
                        while True:
                            chunk = f.read(1 << 20)
                            if not chunk:
                                break
                            self.wfile.write(chunk)
                    return
            self.send_response(404); self.end_headers(); return
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
