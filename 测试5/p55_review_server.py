# -*- coding: utf-8 -*-
"""Phase55 看片服务：冒烟成片专注页（新批次新页，P54 8790 页留档不更新）+
/media 直读项目成片 + FEEDBACK_P55.json 落盘。
用法：python p55_review_server.py [port]  （默认 8791）
"""
import json
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "review"
FEEDBACK = ROOT / "FEEDBACK_P55.json"
PROJECTS = Path(r"C:\Users\曹文淇\Desktop\ai工作流\animation-storyboard\projects")

PAGE = """<!doctype html>
<html lang="zh">
<head>
<meta charset="utf-8">
<title>Phase55 冒烟成片看片页</title>
<style>
  body { font-family: system-ui, "Microsoft YaHei", sans-serif; background:#141419;
         color:#e8e8ee; max-width: 860px; margin: 0 auto; padding: 24px; }
  h1 { font-size: 20px; } .sub { color:#9a9aa8; font-size: 13px; margin-bottom: 16px; }
  video { width: 100%; border-radius: 8px; background:#000; }
  .meta { font-size: 12px; color:#9a9aa8; margin: 8px 0 20px; line-height: 1.7; }
  .row { margin: 10px 0; }
  .btns span { display:inline-block; margin-right:8px; }
  button { background:#2a2a35; color:#e8e8ee; border:1px solid #3a3a48;
           border-radius:6px; padding:6px 14px; cursor:pointer; }
  button.on { background:#4c6fff; border-color:#4c6fff; }
  textarea { width:100%; min-height:60px; background:#1c1c24; color:#e8e8ee;
             border:1px solid #3a3a48; border-radius:6px; padding:8px; }
  #saved { color:#7c7; margin-left:10px; }
  .shots { font-size:13px; color:#b9b9c6; margin-top:16px; line-height:1.8; }
</style>
</head>
<body>
<h1>Phase55 冒烟成片 ——《雨夜递伞》（② Producer 主执行预设）</h1>
<div class="sub">
  Phase55 首次真机接线冒烟：producer_lead 模式经产品 REST 入口全流程自主生产
  （剧本→角色三视图→Look 审批→场景状态图→shot.production.bind→两镜视频→装配）。
  机器阶段完成；本页为用户看片验收。
</div>
<video controls src="/media/P55_SMOKE2B/seq_163beda6/srender_f5abfec2.mp4"></video>
<div class="meta">
  成片：seq_163beda6 / srender_f5abfec2 · 实测 12.20s（计划 12.175s，误差 21ms）· 1280×720 16:9 · H.264/AAC native 音轨<br>
  结构：s01_c02（店内隔门望顾客，5s 反应镜）→ s02_c01（开门递伞/两人同框收尾）· video 额度消耗 +13s<br>
  背景：run_67314129eb 暴露主控租约 TTL 缺陷（已修复+回归）；run_51744a53ce 续跑完成（68min，含 Look/场景视图审批迭代）
</div>
<div class="shots">逐镜候选与选版（引用 run 汇报，细节可在项目工作台核对）：<br>
  · s01 段选 s01_c02（三候选中按三查选定） · s02 段选 s02_c01 · 接续=intentional cut（跨场景硬切）
</div>

<div class="row"><b>画面</b>　<span class="btns" id="pic">
  <button data-v="好">好</button><button data-v="可以">可以</button><button data-v="差">差</button></span></div>
<div class="row"><b>衔接</b>　<span class="btns" id="con">
  <button data-v="好">好</button><button data-v="可以">可以</button><button data-v="差">差</button></span></div>
<div class="row"><b>总评</b>　<span class="btns" id="ovr">
  <button data-v="通过">通过</button><button data-v="不通过">不通过</button></span></div>
<div class="row"><textarea id="note" placeholder="备注（原话即可：哪里好/哪里差/具体镜头）"></textarea></div>
<div class="row"><button id="save">提交看片反馈</button><span id="saved"></span></div>

<script>
const state = {pic:"", con:"", ovr:""};
for (const [id, key] of [["pic","pic"],["con","con"],["ovr","ovr"]]) {
  const box = document.getElementById(id);
  box.querySelectorAll("button").forEach(b => b.onclick = () => {
    box.querySelectorAll("button").forEach(x => x.classList.remove("on"));
    b.classList.add("on"); state[key] = b.dataset.v;
  });
}
document.getElementById("save").onclick = async () => {
  const fb = {...state, note: document.getElementById("note").value,
              film: "P55_SMOKE2B/seq_163beda6/srender_f5abfec2", at: new Date().toISOString()};
  const r = await fetch("/api/feedback", {method:"POST",
    headers:{"Content-Type":"application/json"}, body: JSON.stringify({fb})});
  document.getElementById("saved").textContent = r.ok ? "已保存 ✓" : "保存失败";
};
</script>
</body>
</html>
"""


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
            self.send_response(404)
            self.end_headers()
            return
        if self.path in ("/", "/index.html"):
            b = PAGE.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
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
            FEEDBACK.parent.mkdir(parents=True, exist_ok=True)
            FEEDBACK.write_text(json.dumps(cur, ensure_ascii=False, indent=1), encoding="utf-8")
            b = b'{"ok":true}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(b)))
            self.end_headers()
            self.wfile.write(b)
            return
        self.send_response(404)
        self.end_headers()

    def log_message(self, *a):   # 静默访问日志
        pass


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8791
    srv = ThreadingHTTPServer(("0.0.0.0", port), H)
    print(f"Phase55 review server on http://127.0.0.1:{port}")
    srv.serve_forever()
