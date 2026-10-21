# -*- coding: utf-8 -*-
"""E 部 3 分钟全流程片《雾港行动》看片专注页（新批次新页）。
数据源：film_E_shots.json（程序化从 project.json + rvw_210f31ea 生成）。
FEEDBACK_E_FULL.json 落盘。用法：python e_review_server_E.py [port]（默认 8793）。
"""
import json
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FEEDBACK = ROOT / "FEEDBACK_E_FULL.json"
PROJECTS = Path(r"C:\Users\曹文淇\Desktop\ai工作流\animation-storyboard\projects")
SHOTS = json.loads((ROOT / "film_E_shots.json").read_text(encoding="utf-8"))

PAGE_HEAD = """<!doctype html>
<html lang="zh">
<head>
<meta charset="utf-8">
<title>E 部全流程 3 分钟片《雾港行动》看片页</title>
<style>
  body { font-family: system-ui, "Microsoft YaHei", sans-serif; background:#141419;
         color:#e8e8ee; max-width: 900px; margin: 0 auto; padding: 24px; }
  h1 { font-size: 20px; } h2 { font-size: 16px; margin-top: 30px; color:#cdd6ff; }
  .sub { color:#9a9aa8; font-size: 13px; margin-bottom: 16px; line-height: 1.8; }
  video { width: 100%%; border-radius: 8px; background:#000; }
  .card { border:1px solid #2c2c38; border-radius:10px; padding:14px; margin:14px 0; }
  .meta { font-size: 12.5px; color:#9a9aa8; margin: 6px 0 10px; line-height: 1.7; }
  .machine { font-size: 12.5px; color:#d9b96c; margin: 6px 0; line-height: 1.7; }
  .suggest { font-size: 12.5px; color:#8fd0a0; margin: 6px 0 12px; line-height: 1.7; }
  .row { margin: 8px 0; }
  button { background:#2a2a35; color:#e8e8ee; border:1px solid #3a3a48;
           border-radius:6px; padding:5px 12px; cursor:pointer; margin-right:6px; }
  button.on { background:#4c6fff; border-color:#4c6fff; }
  textarea { width:100%%; min-height:40px; background:#1c1c24; color:#e8e8ee;
             border:1px solid #3a3a48; border-radius:6px; padding:8px; }
  #saved { color:#7c7; margin-left:10px; }
  .legend span { display:inline-block; margin-right:14px; font-size:12.5px; }
</style>
</head>
<body>
<h1>E 部全流程 3 分钟片 ——《雾港行动》（写实悬疑动作，23 镜）</h1>
<div class="sub">
  run_e214e08766（combo_recommended v2.1.0 全流程：剧本→Look→场景→分镜→视频→装配）<br>
  全流程净墙钟 <b>4h15min</b>（其中视频段 ~1.6h）· 成片素材 ~191s（23 镜 × 8-10s）· 视频 23/23 零失败<br>
  消耗：视频 191s / 图 76 / 文本 ~480 · 机器终审 rvw_210f31ea：
  <span class="legend"><span style="color:#8fd0a0">pass 15</span><span style="color:#d9b96c">决策单 6</span><span style="color:#e0a0a0">incomplete 1</span><span style="color:#9a9aa8">minor 1</span></span><br>
  看片建议顺序：先整页快速过一遍挑出明显问题镜，再对决策单镜逐个裁决（豁免=接受当前版本；重生成=换输入策略动用补测预算）。
</div>
"""


def build_page():
    cards = ['<div class="card" style="border-color:#4c6fff"><b>《雾港行动》整片 191.8s（3.2 分钟）——先看这个</b>'
             '<div class="meta">装配 seq_983fb32e / srender_8120bfc0 · 当前选版直拼（决策单裁决后可重装配）</div>'
             '<video controls src="/media4/P56_E_FULL_E/sequences/seq_983fb32e/srender_8120bfc0.mp4"></video></div>']

    def btnGroup(shot, key, label):
        return ('<div class="row"><b>%s</b>　<span class="btns" data-s="%s" data-k="%s">'
                '<button data-v="好">好</button><button data-v="可以">可以</button>'
                '<button data-v="差">差</button></span></div>' % (label, shot, key))

    for s in SHOTS:
        notes = ('<div class="row"><textarea data-s="%s" placeholder="本镜备注（原话即可）"></textarea></div>'
                 % s["shot"])
        color = "#8fd0a0" if "pass ✓" in s["machine"] else (
            "#e0a0a0" if "incomplete" in s["machine"] else "#d9b96c")
        cards.append(
            '<div class="card"><b>%s</b> <span style="color:%s">%s</span>'
            '<div class="meta">%s</div>'
            '<video controls src="/media/%s/videos/%s"></video>'
            '<div class="machine">%s</div>'
            '<div class="suggest">%s</div>%s%s</div>'
            % (s["shot"], color, s["proj"], s["desc"], s["proj"], s["file"],
               s["machine"], s["suggest"],
               btnGroup(s["shot"], "pic", "画面"),
               notes))
    ids = json.dumps([s["shot"] for s in SHOTS], ensure_ascii=False)
    return (PAGE_HEAD + "\n".join(cards) + """
<div class="row" style="margin-top:26px"><button id="save">提交看片反馈</button><span id="saved"></span></div>
<script>
const state = {};
document.addEventListener("click", e => {
  const b = e.target.closest(".btns button");
  if (!b) return;
  const g = b.parentElement;
  g.querySelectorAll("button").forEach(x => x.classList.remove("on"));
  b.classList.add("on");
  const s = g.dataset.s, k = g.dataset.k;
  state[s] = state[s] || {};
  state[s][k] = b.dataset.v;
});
document.getElementById("save").onclick = async () => {
  const notes = {};
  document.querySelectorAll("textarea").forEach(t => notes[t.dataset.s] = t.value);
  const payload = {shots: state, notes, film: "P56_E_FULL_E run_e214e08766",
                   at: new Date().toISOString()};
  const r = await fetch("/api/feedback", {method:"POST",
    headers:{"Content-Type":"application/json"}, body: JSON.stringify(payload)});
  document.getElementById("saved").textContent = r.ok ? "已保存 ✓" : "保存失败";
};
</script>
</body>
</html>
""")


class H(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(ROOT), **kw)

    def log_message(self, *a):
        pass

    def do_GET(self):
        if self.path.startswith("/media4/"):
            parts = self.path[len("/media4/"):].split("/")
            if len(parts) == 4 and all(p.strip() for p in parts):
                fp = PROJECTS / parts[0] / "output" / parts[1] / parts[2] / parts[3]
                if fp.exists():
                    self.send_response(200)
                    self.send_header("Content-Type", "video/mp4")
                    self.send_header("Content-Length", str(fp.stat().st_size))
                    self.send_header("Accept-Ranges", "bytes")
                    self.end_headers()
                    with open(fp, "rb") as f:
                        while True:
                            chunk = f.read(1 << 20)
                            if not chunk:
                                break
                            self.wfile.write(chunk)
                    return
            self.send_response(404)
            self.end_headers()
            return
        if self.path.startswith("/media/"):
            parts = self.path[len("/media/"):].split("/")
            if len(parts) == 3 and all(p.strip() for p in parts):
                fp = PROJECTS / parts[0] / "output" / parts[1] / parts[2]
                if fp.exists():
                    self.send_response(200)
                    self.send_header("Content-Type", "video/mp4")
                    self.send_header("Content-Length", str(fp.stat().st_size))
                    self.send_header("Accept-Ranges", "bytes")
                    self.end_headers()
                    with open(fp, "rb") as f:
                        while True:
                            chunk = f.read(1 << 20)
                            if not chunk:
                                break
                            self.wfile.write(chunk)
                    return
            self.send_response(404)
            self.end_headers()
            return
        if self.path in ("/", "/index.html"):
            b = build_page().encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(b)))
            self.end_headers()
            self.wfile.write(b)
            return
        super().do_GET()

    def do_POST(self):
        if self.path == "/api/feedback":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            try:
                data = json.loads(body.decode("utf-8"))
                FEEDBACK.write_text(json.dumps(data, ensure_ascii=False, indent=1),
                                    encoding="utf-8")
                self.send_response(200)
            except Exception:
                self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"ok": true}')
            return
        self.send_response(404)
        self.end_headers()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8793
    print(f"E 部看片页: http://127.0.0.1:{port}  (FEEDBACK -> {FEEDBACK.name})")
    ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()
