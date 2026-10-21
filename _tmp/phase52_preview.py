# -*- coding: utf-8 -*-
"""生成 Phase52 视频复测预览页（分类分层，含全部视频与三帧对比）。"""
import json, pathlib, datetime

OUT = pathlib.Path(r"C:\Users\曹文淇\Desktop\ai工作流\PHASE52_VIDEO_OUTPUT")

# case -> (镜头, 时长, 判定, 说明)
D = {
 "T1a1":("s01_c01 空旷",10,"major","漂为热带船舱两男人，保持到结尾"),
 "T1a2":("s01_c01 空旷",10,"major","凭空插入竹栅栏+救生圈前景"),
 "T2":  ("s03_c02 触须拍船(接力端点输入)",10,"稳定","动作因果完整，无凭空元素"),
 "A1":("s01_c01 空旷",5,"稳定",""), "A2":("s01_c01 空旷",5,"稳定",""),
 "A3":("s01_c01 空旷",5,"机位漂移","平视→高空俯拍远景"),
 "A4":("s01_c01 空旷",10,"major","漂为船舱内端杯老妇人"),
 "B1":("s01_c02 船长+大副双人",10,"稳定","双人同框/服装/动作与分镜一致"),
 "B2":("s02_c01 全速逃逸(接力镜)",10,"稳定","黑烟/尾迹/衔接上游；minor:船名文字系模型添加"),
 "B3":("s03_c04 船长特写",10,"稳定","对抗倾斜/咬牙/服装帽兜吻合"),
 "B4":("s05_c02 收束",10,"major","首帧钉住后漂为舱内两男人+血迹"),
 "T3":("s03_c03(接力链: T2真实末帧输入)",10,"稳定","倾斜延续/T2碎壳连续/光线一致——闭环成立"),
 "C10a":("s01_c01 空旷",10,"稳定",""), "C10b":("s01_c01 空旷",10,"稳定",""),
 "C5a":("s01_c01 空旷",5,"机位漂移","俯拍"), "C5b":("s01_c01 空旷",5,"稳定",""),
 "C8a":("s01_c01 空旷",8,"机位漂移","俯拍"), "C8b":("s01_c01 空旷",8,"机位漂移","俯拍"),
 "P5a":("s01_c02 双人",5,"稳定","质量佳"), "P5b":("s01_c02 双人",5,"稳定",""),
 "D10a":("s01_c01 空旷",10,"稳定",""), "D10b":("s01_c01 空旷",10,"机位漂移","俯拍远景"),
 "D10c":("s01_c01 空旷",10,"major","漂为欧式宫廷贵族男女"),
 "D10d":("s01_c01 空旷",10,"major","画面横置+爬窗男人"),
 "D8a":("s01_c01 空旷",8,"机位漂移","俯拍"), "D8b":("s01_c01 空旷",8,"稳定",""),
 "D8c":("s01_c01 空旷",8,"机位漂移","俯拍"),
 "D10p1":("s05_c02 收束",10,"稳定","船长甲板/港口背景保持"),
 "D10p2":("s05_c02 收束",10,"major","凭空甲板尸体+血迹"),
 "E10a":("s01_c01 空旷",10,"机位漂移","俯拍+画面旋转"),
 "E10b":("s01_c01 空旷",10,"major","漂为热带棕榈林水道（恢复收货样本）"),
 "E10c":("s01_c01 空旷",10,"机位漂移","俯拍远景"),
 "E10d":("s01_c01 空旷",10,"稳定",""),
 "E10e":("s01_c01 空旷",10,"机位漂移","俯拍（中断恢复收货）"),
 "E10p1":("s05_c02 收束",10,"major","凭空救援人员3-4人+燃烧弹孔"),
 "E10p2":("s05_c02 收束",10,"major","凭空多人+船体弹孔血迹（恢复收货）"),
 "E10p3":("s05_c02 收束",10,"major","凭空舱壁弹孔血迹"),
 "E5b":("s01_c01 空旷",5,"稳定",""), "E5c":("s01_c01 空旷",5,"机位漂移","俯拍旋转"),
 "E5d":("s01_c01 空旷",5,"机位漂移","俯拍"),
 "E8a":("s01_c01 空旷",8,"稳定",""), "E8b":("s01_c01 空旷",8,"机位漂移","俯拍"),
 "E8c":("s01_c01 空旷",8,"稳定",""),
}
VID = {"T1a1":"T1_s01_c01_attempt1.mp4","T1a2":"T1_s01_c01.mp4","T2":"T2_s03_c02.mp4",
       "T3":"T3.mp4","E10b":"E10b.mp4","E10e":"E10e.mp4","E10p2":"E10p2.mp4"}
def vid(c): return VID.get(c, f"{c}.mp4")
def img(c, tag): return f"{c}_{tag}.png"
def thumb(c): return f"{c}_mid.png"
BADGE = {"major":("#b91c1c","#fecaca"),"机位漂移":("#92400e","#fde68a"),"稳定":("#166534","#bbf7d0")}

def card(c, big=False):
    shot, sec, verdict, note = D[c]
    bg, fg = BADGE[verdict]
    note_h = f'<div class="note">{note}</div>' if note else ""
    if big:
        media = (f'<video controls preload="metadata" src="{vid(c)}"></video>'
                 f'<div class="tri"><figure><img src="{img(c,"first")}"><figcaption>首帧(输入)</figcaption></figure>'
                 f'<figure><img src="{img(c,"mid")}"><figcaption>中段</figcaption></figure>'
                 f'<figure><img src="{img(c,"end")}"><figcaption>尾帧</figcaption></figure></div>')
    else:
        media = (f'<a href="{vid(c)}" target="_blank"><img class="th" src="{thumb(c)}" loading="lazy"></a>'
                 f'<div class="vlink"><a href="{vid(c)}" target="_blank">▶ 播放 {vid(c)}</a></div>')
    return (f'<div class="card {"big" if big else ""}">'
            f'<div class="head"><span class="cid">{c}</span><span class="meta">{shot} · {sec}s</span>'
            f'<span class="badge" style="background:{bg};color:{fg}">{verdict}</span></div>'
            f'{media}{note_h}</div>')

def grid(cases, big=()):
    return '<div class="grid">' + "".join(card(c, big=c in big) for c in cases) + "</div>"

major = [c for c in D if D[c][2]=="major"]
drift = [c for c in D if D[c][2]=="机位漂移"]
ok    = [c for c in D if D[c][2]=="稳定"]

now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
html = f"""<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8">
<title>PHASE52 视频复测预览（33 条真实样本）</title><style>
:root{{--bg:#0f172a;--card:#1e293b;--line:#334155;--tx:#e2e8f0;--dim:#94a3b8}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--tx);font:15px/1.6 "Segoe UI",system-ui,sans-serif}}
.wrap{{max-width:1280px;margin:0 auto;padding:24px 20px 80px}}
h1{{font-size:26px;margin:8px 0 4px}} h2{{font-size:20px;margin:42px 0 12px;border-left:4px solid #38bdf8;padding-left:10px}}
h3{{font-size:16px;margin:24px 0 8px;color:#7dd3fc}}
.sub{{color:var(--dim);font-size:13px}}
table{{border-collapse:collapse;width:100%;margin:12px 0}} td,th{{border:1px solid var(--line);padding:7px 12px;text-align:left;font-size:14px}}
th{{background:#26334b}} .num{{font-variant-numeric:tabular-nums}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:14px}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px}}
.card.big{{grid-column:1/-1;max-width:900px}}
.head{{display:flex;align-items:center;gap:10px;margin-bottom:8px;flex-wrap:wrap}}
.cid{{font-weight:700;color:#7dd3fc}} .meta{{color:var(--dim);font-size:12.5px}}
.badge{{padding:2px 10px;border-radius:99px;font-size:12px;font-weight:600}}
img{{width:100%;border-radius:6px;display:block}} .th{{aspect-ratio:16/9;object-fit:cover}}
video{{width:100%;border-radius:6px;background:#000}}
.note{{font-size:13px;color:#fca5a5;margin-top:8px}} .vlink{{font-size:12px;margin-top:6px}}
.vlink a{{color:#7dd3fc;text-decoration:none}}
.tri{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-top:10px}}
.tri figcaption{{font-size:11.5px;color:var(--dim);text-align:center;margin-top:3px}}
.kpi{{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:12px;margin:18px 0}}
.kpi .card{{text-align:center}} .kpi .v{{font-size:30px;font-weight:800}} .kpi .l{{color:var(--dim);font-size:12.5px}}
.concl{{background:#132743;border:1px solid #1e4976;border-radius:10px;padding:16px 20px;margin:16px 0}}
.concl li{{margin:7px 0}} .warn{{color:#fca5a5}} .good{{color:#86efac}}
a{{color:#7dd3fc}}
</style></head><body><div class="wrap">
<h1>PHASE52 视频复测预览</h1>
<div class="sub">33 条真实视频（agnes-video-2.5-flash / keyframe i2v / 已批准首帧）· 配额 369/500s · 生成 {now} · 判定=视觉模型实看 mid/end 帧</div>

<div class="concl"><b>结论摘要</b><ul>
<li class="warn"><b>major 场景替换（凭空人物/场景/物体）只发生在 10s 直出：11/25（44%）vs 5s+8s 0/18（0%），p&lt;0.001</b>——时长是最强预测因子</li>
<li class="warn"><b>首帧语义污染放大幻觉</b>：带伤痕脸的 s05_c02 收束镜 10s 直出 5/6 major（凭空救援人员/弹孔/尸体/多人）；干净首帧的人物/动作镜 5/5 稳定</li>
<li>机位/构图漂移是独立模式（场景保持、视角失控）：5s 4/8、8s 5/8、10s 4/14，「镜头固定」约束对该模型整体偏弱</li>
<li class="good">接力链闭环成立（T2 末帧→T3 下游，状态/碎片/光线连续）；5s×2+末帧接力 = 0/10 major，生产策略定稿依据</li>
<li class="good">系统侧 33/33 全链路零缺陷；本轮另修复图床 &gt;1MB 二次托管 bug（commit d734144）</li>
</ul></div>

<h2>一、核心对照：同输入同时长（s01_c01 空旷镜）</h2>
<table><tr><th>时长</th><th>n</th><th>major 场景替换</th><th>机位/构图漂移</th><th>稳定</th></tr>
<tr><td>5s</td><td class="num">8</td><td class="num"><b>0</b></td><td class="num">4</td><td class="num">4</td></tr>
<tr><td>8s</td><td class="num">8</td><td class="num"><b>0</b></td><td class="num">5</td><td class="num">3</td></tr>
<tr><td><b>10s</b></td><td class="num">14</td><td class="num"><b style="color:#f87171">6</b></td><td class="num">4</td><td class="num">4</td></tr></table>
<h3>10s 稳定代表（同输入也可能成功）</h3>{grid(["C10a","C10b","D10a","E10d"])}
<h3>10s 机位漂移代表（场景保持、视角失控）</h3>{grid(["D10b","E10a","E10c","E10e"])}
<h3>5s / 8s 机位漂移代表（无 major）</h3>{grid(["A3","C8a","E5c","E8b"])}

<h2>二、major 场景替换画廊（11 条——幻觉形态全景）</h2>
<div class="sub">同输入 prompt 含「没有其他船只、镜头固定」，全部被无视；keyframe 仅钉第 0 帧；漂移不自愈。</div>
{grid(sorted(major), big=set(major))}

<h2>三、人物 / 动作 / 接力镜（10s 直出）</h2>
<h3>s05_c02 收束镜——首帧语义污染专题（5/6 major：伤痕脸 → 战斗叙事脑补）</h3>
{grid(["D10p1","B4","D10p2","E10p1","E10p2","E10p3"])}
<h3>干净首帧人物 / 动作 / 接力镜（5/5 稳定）</h3>
{grid(["B1","B3","B2","P5a","P5b"])}

<h2>四、接力链闭环（T2 → T3）与高难动作镜</h2>
{grid(["T2","T3"], big={"T2","T3"})}
<div class="sub">T2 末帧（真实解码帧）→ 托管 → T3 下游生成：船体倾斜延续、碎壳残片连续、光线一致——E16 裁切端点依赖完整实证。</div>

<h2>五、全部稳定样本（19 条缩略）</h2>
{grid(ok)}

<h2>六、视频文件索引（点击播放）</h2>
<div class="grid">{"".join(f'<div class="card"><div class="head"><span class="cid">{c}</span></div><video controls preload="none" src="{vid(c)}"></video></div>' for c in D)}</div>

<div class="sub" style="margin-top:30px">E5a 在途（video_id 保留续查）；漂移样本全部归档留证。数据：PHASE52_VIDEO_LEDGER.jsonl + timing_ledger(phase52_retest)。</div>
</div></body></html>"""

(OUT / "index.html").write_text(html, encoding="utf-8")
print("index.html generated:", (OUT/"index.html").stat().st_size, "bytes")
print("cases:", len(D), "| major:", len(major), "| drift:", len(drift), "| ok:", len(ok))
