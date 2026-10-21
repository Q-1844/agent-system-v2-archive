# -*- coding: utf-8 -*-
"""F 部《雾林快递》动态看片页：每次刷新实时从 project.json 读取已完成的镜。
运行中的片子也能看（完成的镜逐个出现）。FEEDBACK_E_FULL_F.json 落盘。
用法：python e_review_server_F.py [port]（默认 8794）
"""
import json
import sys
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FEEDBACK = ROOT / "FEEDBACK_E_FULL_F.json"
PROJECTS = Path(r"C:\Users\曹文淇\Desktop\ai工作流\animation-storyboard\projects")
PROJ = "P56_E_FULL_F"
RUN_FILE = Path(r"D:\isolated\evidence\e_batch\run_id_P56_E_FULL_F.txt")

STYLE = """  body { font-family: system-ui, "Microsoft YaHei", sans-serif; background:#141419;
         color:#e8e8ee; max-width: 900px; margin: 0 auto; padding: 24px; }
  h1 { font-size: 20px; } h2 { font-size: 16px; margin-top: 30px; color:#cdd6ff; }
  .sub { color:#9a9aa8; font-size: 13px; margin-bottom: 16px; line-height: 1.8; }
  video { width: 100%; border-radius: 8px; background:#000; }
  .card { border:1px solid #2c2c38; border-radius:10px; padding:14px; margin:14px 0; }
  .meta { font-size: 12.5px; color:#9a9aa8; margin: 6px 0 10px; line-height: 1.7; }
  .machine { font-size: 12.5px; color:#d9b96c; margin: 6px 0; line-height: 1.7; }
  .row { margin: 8px 0; }
  button { background:#2a2a35; color:#e8e8ee; border:1px solid #3a3a48;
           border-radius:6px; padding:5px 12px; cursor:pointer; margin-right:6px; }
  button.on { background:#4c6fff; border-color:#4c6fff; }
  textarea { width:100%; min-height:40px; background:#1c1c24; color:#e8e8ee;
             border:1px solid #3a3a48; border-radius:6px; padding:8px; }
  #saved { color:#7c7; margin-left:10px; }"""


def build_page():
    project = json.loads((PROJECTS / PROJ / "output" / "project.json").read_text(encoding="utf-8"))
    run_id = RUN_FILE.read_text(encoding="utf-8").strip() if RUN_FILE.exists() else "?"
    run = {}
    run_file = PROJECTS / PROJ / "output" / "agents" / "collab_runs" / f"{run_id}.json"
    if run_file.exists():
        run = json.loads(run_file.read_text(encoding="utf-8"))
    verdicts = {}
    rvw_id = (run.get("review") or {}).get("batch_id")
    if rvw_id:
        rvw = PROJECTS / PROJ / "output" / "agents" / "review_pipeline" / f"{rvw_id}.json"
        if rvw.exists():
            rv = json.loads(rvw.read_text(encoding="utf-8"))
            for e in rv.get("results", []):
                verdicts[e["shot_id"]] = e.get("overall")

    cards = []
    n_done = 0
    total_secs = 0.0
    for sc in project.get("scenes", []):
        for sh in sc.get("shots", []):
            sid = sh["shot_id"]
            vv = sh.get("video_versions") or []
            if not vv:
                continue
            last = vv[-1]
            fname = Path(last.get("local") or "").name
            if not fname:
                continue
            n_done += 1
            total_secs += (last.get("seconds_returned") or 0)
            v = verdicts.get(sid)
            machine = f"机器审查 {v}" if v else "（终审未出，先看画面）"
            color = {"pass": "#8fd0a0", "hard_error": "#e0a0a0",
                     "incomplete": "#e0a0a0", "uncertain": "#d9b96c",
                     "minor": "#d9b96c"}.get(v, "#9a9aa8")
            dlg = (sh.get("dialogue") or "").strip()
            relay = f"；接力←{sh.get('source_shot_id')}" if sh.get("source_shot_id") else ""
            cards.append(
                '<div class="card"><b>%s</b> <span style="color:%s">%s</span>'
                '<div class="meta">%s%s%s</div>'
                '<video controls src="/media/%s/videos/%s"></video>'
                '<div class="machine">%s</div>'
                '<div class="row"><b>画面</b>　<span class="btns" data-s="%s" data-k="pic">'
                '<button data-v="好">好</button><button data-v="可以">可以</button>'
                '<button data-v="差">差</button></span></div>'
                '<div class="row"><textarea data-s="%s" placeholder="本镜备注（原话即可）"></textarea></div></div>'
                % (sid, color, PROJ, (sh.get("description") or "")[:80], relay,
                   f"；台词: {dlg[:36]}" if dlg else "",
                   PROJ, fname, machine, sid, sid))
    sub = (f"run_{run_id}（combo_recommended v2.1.0 全流程·写实动物）· 已完成 {n_done} 镜 / "
           f"素材 {total_secs:.0f}s · 刷新本页可见新完成的镜 · 机器终审{'已出' if verdicts else '未出（跑完自动显示）'}")
    return (f'<!doctype html><html lang="zh"><head><meta charset="utf-8">'
            f'<title>F 部《雾林快递》动态看片页</title><style>{STYLE}</style></head><body>'
            f'<h1>F 部全流程写实动物片 ——《雾林快递》</h1><div class="sub">{sub}</div>'
            + "\n".join(cards) +
            f'''<div class="row" style="margin-top:26px"><button id="save">提交看片反馈</button><span id="saved"></span></div>
<script>
const state = {{}};
document.addEventListener("click", e => {{
  const b = e.target.closest(".btns button");
  if (!b) return;
  const g = b.parentElement;
  g.querySelectorAll("button").forEach(x => x.classList.remove("on"));
  b.classList.add("on");
  const s = g.dataset.s, k = g.dataset.k;
  state[s] = state[s] || {{}};
  state[s][k] = b.dataset.v;
}});
document.getElementById("save").onclick = async () => {{
  const notes = {{}};
  document.querySelectorAll("textarea").forEach(t => notes[t.dataset.s] = t.value);
  const payload = {{shots: state, notes, film: "{PROJ} run " + "{run_id}", at: new Date().toISOString()}};
  const r = await fetch("/api/feedback", {{method:"POST",
    headers:{{"Content-Type":"application/json"}}, body: JSON.stringify(payload)}});
  document.getElementById("saved").textContent = r.ok ? "已保存 ✓" : "保存失败";
}};
</script></body></html>''')


class H(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(ROOT), **kw)

    def log_message(self, *a):
        pass

    def do_GET(self):
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
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8794
    print(f"F 部动态看片页: http://127.0.0.1:{port}")
    ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()
