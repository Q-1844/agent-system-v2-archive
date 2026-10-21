# -*- coding: utf-8 -*-
"""E 批看片服务：R1.1 真实验证组专注页（新批次新页）。
三分区：完整素材（6+1 镜逐镜）→ 保留区间建议（机器审查依据）→ 排除说明（失败任务）。
FEEDBACK_E_R11.json 落盘（逐镜 画面/衔接/总评/备注）。
用法：python e_review_server.py [port]  （默认 8792）
"""
import json
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from http.server import BaseHTTPRequestHandler
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FEEDBACK = ROOT / "FEEDBACK_E_R11.json"
PROJECTS = Path(r"C:\Users\曹文淇\Desktop\ai工作流\animation-storyboard\projects")

SHOTS = [
    {"shot": "s01_c01", "proj": "P56_E_R11_A", "file": "s01_c01_vv_3d40291d9cf1.mp4",
     "desc": "夜山道要塞外，两名队员掩体观察（链首，独立开场）",
     "machine": "机器审查 incomplete：景别错配（中景 vs 全景）+构图未还原「岩石掩体后方」——按审查政策 v2 属降次维，不构成硬错；请以肉眼为准",
     "suggest": "8s；若景别满意可整段保留，不满足则整镜重生成（决策单未涉本镜）"},
    {"shot": "s01_c02", "proj": "P56_E_R11_A", "file": "s01_c02_vv_ff222382d710.mp4",
     "desc": "要塞外墙接近入口（接力 s01_c01 末帧）",
     "machine": "机器审查硬错 missing_character（预期人数缺员）→ 有界修复重试同错 → 决策单待答复（不抽卡）",
     "suggest": "8s；机器判缺员——请确认是否真缺人；若画面可接受可人工豁免，否则答策略决策后重生成"},
    {"shot": "s01_c03", "proj": "P56_E_R11_A", "file": "s01_c03_vv_12483bd6bc4f.mp4",
     "desc": "要塞大门侧闸（接力 s01_c02 末帧，链尾）",
     "machine": "机器审查 pass ✓（两棒接续链整体一致）",
     "suggest": "8s；建议整段保留"},
    {"shot": "s01_c04", "proj": "P56_E_R11_A", "file": "s01_c04_vv_f251876ceae6.mp4",
     "desc": "控制室机器警卫巡逻（独立镜；BOUND 重锚后生成）",
     "machine": "机器审查 pass ✓（首帧经 R1.1 fail-closed → BOUND 重锚 3 张后合格）",
     "suggest": "8s；建议整段保留"},
    {"shot": "s01_c05", "proj": "P56_E_R11_A", "file": "s01_c05_vv_acaee528eb9a.mp4",
     "desc": "队员半离掩体回望要塞（独立镜）",
     "machine": "机器审查硬错 missing_character → 决策单待答复（同 c02）",
     "suggest": "8s；请确认人数；机器与人工不一致时以人工为准并记录"},
    {"shot": "s02_c01", "proj": "P56_E_R11_A", "file": "s02_c01_vv_459793346579.mp4",
     "desc": "内部通道信号中继装置（独立镜，含台词）",
     "machine": "机器审查 pass ✓；native 对白控制生效（Mandarin Chinese，speaker 精确匹配）",
     "suggest": "8s；建议整段保留，重点听台词口型与声线"},
    {"shot": "smoke s01_c01", "proj": "P56_E_SMOKE", "file": "s01_c01_vv_730e74328751.mp4",
     "desc": "冒烟镜（独立项目 P56_E_SMOKE，独立计费不入组统计）",
     "machine": "技术链全绿：版本回执/intent/manifest/末帧托管/配额 8s",
     "suggest": "8s；与组内 c01 同底（对照看两次生成的稳定性）"},
    {"shot": "B s01_c01", "proj": "P56_E_R11_B", "file": "s01_c01_vv_3a9526d04c67.mp4",
     "desc": "【anime 组·断电前的证词】调查员开场（批准首帧，含台词）",
     "machine": "机器审查 pass ✓（部分帧构图/景别降次维记录，政策 v2 未算硬错）",
     "suggest": "8s；风格与写实组对照看"},
    {"shot": "B s01_c02", "proj": "P56_E_R11_B", "file": "s01_c02_vv_10f7e76fbbbd.mp4",
     "desc": "【anime 组】工程师（台词镜）",
     "machine": "机器审查 pass ✓",
     "suggest": "8s；注意对白口型与声线"},
    {"shot": "B s01_c03", "proj": "P56_E_R11_B", "file": "s01_c03_vv_efb8318a0145.mp4",
     "desc": "【anime 组】（显式无对白镜）",
     "machine": "机器审查 pass ✓",
     "suggest": "8s"},
    {"shot": "B s01_c04", "proj": "P56_E_R11_B", "file": "s01_c04_vv_f1e168f024f6.mp4",
     "desc": "【anime 组】（冻结源首帧无凭据→BOUND 重锚后生成）",
     "machine": "机器审查 incomplete：missing_character/unexpected_people 打在中帧（降次维，未构成硬错）；请肉眼复核人数",
     "suggest": "8s；人数以你裁决为准"},
    {"shot": "B s01_c05", "proj": "P56_E_R11_B", "file": "s01_c05_vv_ae2c32c5a107.mp4",
     "desc": "【anime 组】安保负责人（台词镜，首帧为运行中补选）",
     "machine": "机器审查 pass ✓",
     "suggest": "8s"},
]

PAGE_TMPL = """<!doctype html>
<html lang="zh">
<head>
<meta charset="utf-8">
<title>E 批 R1.1 真实验证组 看片页</title>
<style>
  body { font-family: system-ui, "Microsoft YaHei", sans-serif; background:#141419;
         color:#e8e8ee; max-width: 900px; margin: 0 auto; padding: 24px; }
  h1 { font-size: 20px; } h2 { font-size: 16px; margin-top: 34px; color:#cdd6ff; }
  .sub { color:#9a9aa8; font-size: 13px; margin-bottom: 16px; line-height: 1.7; }
  video { width: 100%%; border-radius: 8px; background:#000; }
  .card { border:1px solid #2c2c38; border-radius:10px; padding:14px; margin:14px 0; }
  .meta { font-size: 12.5px; color:#9a9aa8; margin: 6px 0 10px; line-height: 1.7; }
  .machine { font-size: 12.5px; color:#d9b96c; margin: 6px 0; line-height: 1.7; }
  .suggest { font-size: 12.5px; color:#8fd0a0; margin: 6px 0 12px; line-height: 1.7; }
  .row { margin: 8px 0; }
  button { background:#2a2a35; color:#e8e8ee; border:1px solid #3a3a48;
           border-radius:6px; padding:5px 12px; cursor:pointer; margin-right:6px; }
  button.on { background:#4c6fff; border-color:#4c6fff; }
  textarea { width:100%%; min-height:44px; background:#1c1c24; color:#e8e8ee;
             border:1px solid #3a3a48; border-radius:6px; padding:8px; }
  #saved { color:#7c7; margin-left:10px; }
  .excl { font-size: 13px; color:#e08c8c; line-height: 1.9; }
</style>
</head>
<body>
<h1>E 批 R1.1 真实验证组 ——《铁门后的信号》冻结包 6 镜 + 冒烟 1 镜</h1>
<div class="sub">
  run_22e43019c8（combo_recommended v2.1.0 + approved_package，真实 Producer，并发=模式默认 1）<br>
  视频消耗 56s/74s 上限 · 生图 3 张（c04 BOUND 重锚）· 文本 100 次 · 3 次失败任务全部 fail-closed 零浪费<br>
  机器终审 rvw_9390d943：3 pass / 2 硬错（missing_character，决策单待答复）/ 1 incomplete（景别降次维）<br>
  裁切与取舍由你定版：本页只供素材与依据（保留区间建议非定版）。
</div>

<h2>〇、整片成片（先看这个）</h2>
<div class="card"><b>A《铁门后的信号》整片 32.0s</b>
<div class="meta">正式装配 seq_150c9faa / srender_8eb72992 · 当前选版直拼（2 张决策单裁决后可重装配）</div>
<video controls src="/media4/P56_E_R11_A/sequences/seq_150c9faa/srender_8eb72992.mp4"></video></div>
<div class="card"><b>B《断电前的证词》草稿整片 40.0s（非正式直拼）</b>
<div class="meta">ffmpeg 直拼当前选版（正式装配待做）</div>
<video controls src="/media/P56_E_R11_B/sequences/_draft_full_film.mp4"></video></div>

<h2>一、完整素材（逐镜，每镜 1 条成片）</h2>
{cards}

<h2>二、保留区间建议（依据，非定版）</h2>
<div class="suggest">
  · 建议 c03 / c04 / s02_c01 / 冒烟镜 整段保留（机器 pass）；<br>
  · c01 景别问题请你裁决：机器按政策 v2 未算硬错；<br>
  · c02 / c05 人数问题请你裁决：若与机器判断不一致，以你为准，我将把决策单按你的答复闭环
   （豁免=人工接受当前版本；重生成=需换输入策略，动用补测预算 ≤6s/1 次）。
</div>

<h2>三、排除说明（未产出素材的任务）</h2>
<div class="excl">
  · s01_c04 视频任务 ×2（boundary_frame_stale：冻结源首帧批次缺 BOUND 凭据——fail-closed 拒发，0 视频配额；<br>
  　随后 Producer 经 BOUND 重锚生成合格首帧 ff_27946388 → 第 3 次任务成功）；<br>
  · s01_c02 视频任务 ×1（reference_media_unresolvable：接力视频参考缺公网 URL——fail-closed，0 消耗；<br>
  　正式 rehost 登记后重试成功）；<br>
  · 冒烟项目首次任务 ×1（speaker_not_in_characters：冻结源台词前缀「队员甲」与角色全名不符——
  　17.md §8 reject 语义拒发，0 消耗；修正前缀后重发成功）。<br>
  以上 4 次失败均为系统按契约拒发，未产生任何 provider 计费。
</div>

<div class="row" style="margin-top:26px"><button id="save">提交看片反馈</button><span id="saved"></span></div>

<script>
const state = {};
const SHOTS = {shots_json};
function btnGroup(shot, key, label) {
  return `<div class="row"><b>${label}</b>　<span class="btns" data-s="${shot}" data-k="${key}">
    <button data-v="好">好</button><button data-v="可以">可以</button><button data-v="差">差</button></span></div>`;
}
document.addEventListener("click", e => {
  const b = e.target.closest(".btns button");
  if (!b) return;
  const g = b.parentElement;
  g.querySelectorAll("button").forEach(x => x.classList.remove("on"));
  b.classList.add("on");
  const s = g.dataset.s, k = g.dataset.k;
  state[s] = state[s] || {{}};
  state[s][k] = b.dataset.v;
});
document.getElementById("save").onclick = async () => {{
  const notes = {{}};
  document.querySelectorAll("textarea").forEach(t => notes[t.dataset.s] = t.value);
  const payload = {{shots: state, notes, film: "P56_E_R11_A run_22e43019c8",
                    at: new Date().toISOString()}};
  const r = await fetch("/api/feedback", {{method:"POST",
    headers:{{"Content-Type":"application/json"}}, body: JSON.stringify(payload)}});
  document.getElementById("saved").textContent = r.ok ? "已保存 ✓" : "保存失败";
}};
</script>
</body>
</html>
"""


def build_page():
    def btnGroup(shot, key, label):
        return ('<div class="row"><b>%s</b>　<span class="btns" data-s="%s" data-k="%s">'
                '<button data-v="好">好</button><button data-v="可以">可以</button>'
                '<button data-v="差">差</button></span></div>' % (label, shot, key))

    cards = []
    for s in SHOTS:
        notes = ('<div class="row"><textarea data-s="%s" placeholder="本镜备注（原话即可）"></textarea></div>'
                 % s["shot"])
        cards.append(
            '<div class="card"><b>%s</b>（%s）<div class="meta">%s</div>'
            '<video controls src="/media/%s/videos/%s"></video>'
            '<div class="machine">机器审查：%s</div>'
            '<div class="suggest">建议：%s</div>%s%s%s</div>'
            % (s["shot"], s["proj"], s["desc"], s["proj"], s["file"],
               s["machine"], s["suggest"],
               btnGroup(s["shot"], "pic", "画面"),
               btnGroup(s["shot"], "con", "衔接"),
               notes))
    return PAGE_TMPL.replace("{cards}", "\n".join(cards)).replace(
        "{shots_json}", json.dumps([s["shot"] for s in SHOTS], ensure_ascii=False)
    ).replace("{{", "{").replace("}}", "}")


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
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8792
    print(f"E 批看片页: http://127.0.0.1:{port}  (FEEDBACK -> {FEEDBACK.name})")
    ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()
