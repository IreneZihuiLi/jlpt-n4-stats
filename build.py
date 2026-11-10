"""Build the mobile page from data.json.  Usage: python3 -I build.py
Outputs: <lv>_page.html (Artifact body, no skeleton), <LV>高频词汇与考点统计.html and index.html (standalone)."""
import json, os, math, re
data = json.load(open("data.json", encoding="utf-8"))
lv = data.get("_level", "N4")

def rows(name): return data[name]["rows"] if name in data else []
def thirds(m):
    c = sorted(set([max(2, math.ceil(m/3)), max(2, math.ceil(2*m/3)), m]))
    return c

# session counts: 笔试 = rows in 统计范围; 听力 = sessions with listening material; 旧题 = max frequency in that sheet
scope = rows("统计范围")
def maxfreq(name): return max([int(r["考试频次"]) for r in rows(name)] or [1])
def included(r, key): return "不纳入" not in str(r.get(key, "")) and "未找到" not in str(r.get(key, ""))
bishi_n = max(sum(1 for r in scope if included(r, "笔试材料")), maxfreq("笔试高频词汇"))
choukai_n = max(sum(1 for r in scope if included(r, "听力文字原文")), maxfreq("听力高频词汇"))
kyuu_n = maxfreq("旧题词汇参考")

TABS = [
  {"id":"bishi-goi",      "sheet":"笔试高频词汇", "label":"笔试词汇", "kind":"vocab",   "max":bishi_n,   "freqChips":thirds(bishi_n)},
  {"id":"bishi-bunpo",    "sheet":"笔试语法考点", "label":"笔试语法", "kind":"grammar", "max":bishi_n,   "freqChips":[2,3,4]},
  {"id":"bunpo-mondai",   "sheet":"语法逐题明细", "label":"语法逐题", "kind":"gq"},
  {"id":"choukai-goi",    "sheet":"听力高频词汇", "label":"听力词汇", "kind":"vocab",   "max":choukai_n, "freqChips":thirds(choukai_n)},
  {"id":"choukai-kouten", "sheet":"听力考点统计", "label":"听力考点", "kind":"lpoint",  "max":choukai_n, "freqChips":thirds(choukai_n)},
  {"id":"choukai-mondai", "sheet":"听力逐题明细", "label":"听力逐题", "kind":"lq"},
  {"id":"choukai-hyougen","sheet":"听力语法表达", "label":"听力表达", "kind":"lexpr",   "max":choukai_n, "freqChips":thirds(choukai_n)},
  {"id":"kyuu-goi",       "sheet":"旧题词汇参考", "label":"旧题词汇", "kind":"vocab",   "max":kyuu_n,    "freqChips":thirds(kyuu_n)},
  {"id":"setsumei",       "label":"说明", "kind":"info"},
]
TABS = [t for t in TABS if t["kind"] == "info" or t.get("sheet") in data]

# ---------- optional practice module: quiz_src.txt (hand-curated 文法問題1 bank) ----------
CATS = [
  {"id":"juju",  "label":"授受动词",          "re":r"てくれ|てもら|てあげ|てやる",
   "tip":"「〜てくれる」主语是别人（别人为我做）；「〜てもらう」主语是我（我请别人做）；「〜てあげる／やる」是我为别人做。先看括号前的动作是谁做的。"},
  {"id":"joshi", "label":"助词 から・で",     "re":r"^(から|で)（|^から＋",
   "tip":"来源、看不出原样的原料用「から」；原因、看得出的材料、完成所需的时间用「で」。"},
  {"id":"ukemi", "label":"被动・使役",        "re":r"被动|使役",
   "tip":"被动句先找「谁被怎么了」（が／は）；做动作的人用「に／によって」，来源用「から」，原因用「で」。使役句里被要求的人用「を／に」。"},
  {"id":"koto",  "label":"こと句型",          "re":r"ことにする|ことになる|ことができる|ことがある",
   "tip":"「ことにする」自己决定；「ことになる」被决定、事情定下来；「ことになっている」规定如此；「ことができる」能够；「たことがある」经历。"},
  {"id":"suiryo","label":"推量・打算",        "re":r"つもり|でしょう|かもしれない|そうだ|意志形＋と思う|はず",
   "tip":"「はず」是有依据的推断；「つもり」是本人的打算；「でしょう／かもしれない」是推测；「そうだ」（样态）是看起来要……。"},
  {"id":"joken", "label":"条件 たら・なら・ても","re":r"〜たら|〜なら|〜ても（",
   "tip":"「たら」完成后或假定；「なら」承接对方的话题；「ても」即使……也。ば形从辞书形变：う段→え段＋ば。"},
  {"id":"gyaku", "label":"逆接 のに・けれど",  "re":r"のに（逆接）|けれど|だけど",
   "tip":"「のに」明明……却（带不满、意外）；「けれど／だけど」是一般的转折，名词、な形容词后要加「だ」。"},
  {"id":"ndesu", "label":"〜んです",          "re":r"んです",
   "tip":"「のです／んです」前接普通形，名词、な形容词现在肯定加「な」；用来说明情况或追问原因。「〜たいんですが」用来委婉地引出请求。"},
  {"id":"sugiru","label":"〜すぎる",          "re":r"すぎる",
   "tip":"动词去ます、い形容词去い，再接「すぎる」，表示过度。"},
]
def load_quiz():
    if not os.path.exists("quiz_src.txt"):
        return None
    detail = {}
    for r in rows("语法逐题明细"):
        m = re.search(r"第(\d+)题", str(r.get("题号", "")))
        if m:
            detail[(str(r["考试年月"]), int(m.group(1)))] = r
    items, skipped = [], []
    for line in open("quiz_src.txt", encoding="utf-8"):
        line = line.rstrip("\n")
        if not line.strip() or line.startswith("#"):
            continue
        ym, n, a, fl, stem, *opts = line.split("|")
        n, a = int(n), int(a)
        if fl.startswith("skip:"):
            skipped.append({"ym": ym, "n": n, "why": fl[5:]})
            continue
        assert len(opts) == 4 and all(opts) and 1 <= a <= 4 and "（　）" in stem, line
        d = detail.get((ym, n), {})
        pt = d.get("日语考点", "")
        items.append({"id": f"{ym}-{n}", "ym": ym, "n": n, "s": stem.replace("⏎", "\n"), "o": opts, "a": a,
                      "pt": pt, "ex": d.get("中文解释", ""), "src": d.get("来源", ""),
                      "fl": 1 if fl == "ocr" else 0, "c": [c["id"] for c in CATS if re.search(c["re"], pt)]})
    cats = []
    for c in CATS:
        k = sum(1 for it in items if c["id"] in it["c"])
        if k:
            cats.append({"id": c["id"], "label": c["label"], "tip": c["tip"], "n": k})
    exams = sorted(set(it["ym"] for it in items))
    nocr = sum(it["fl"] for it in items)
    total = len(items) + len(skipped)
    fmt = lambda ym: f"{ym[:4]}/{ym[4:]}"
    notes = [
        f"题库收录 {len(items)} / {total} 道文法問題1 单选题，来自 {len(exams)} 场新版 {lv} 真题，题干和选项按识别文本人工整理。",
        "答案是根据题干和选项判断的，并与现有参考答案中能辨认的部分核对一致；不是官方公布的答案。",
        f"其中 {nocr} 道标有「OCR 修复」：识别文本有错字或缺字，按上下文修正过，个别人名、机构名用〇〇代替，可能与原卷略有出入。",
    ]
    if skipped:
        notes.append("未收录 " + str(len(skipped)) + " 道：" + "；".join(f"{fmt(x['ym'])} 第{x['n']}题（{x['why']}）" for x in skipped) + "。")
    notes.append("考点和解析取自「语法逐题」表；弱项分类按考点名称自动归类。")
    print(f"quiz: {len(items)} items, {len(skipped)} skipped, {nocr} ocr-fixed; cats:", [(c['label'], c['n']) for c in cats])
    return {"intro": f"从 {len(exams)} 场新版 {lv} 真题的文法問題1（单选）里随机抽题，共 {len(items)} 道。答完马上看正确答案、考点和解析。",
            "items": items, "cats": cats, "notes": notes}
quiz = load_quiz()
if quiz:
    data["_quiz"] = quiz
    TABS.insert(0, {"id": "renshuu", "label": "小练习", "kind": "quiz"})
print(f"{lv}: 笔试 {bishi_n} 场, 听力 {choukai_n} 场, 旧题 {kyuu_n} 场")

payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
tabs_json = json.dumps(TABS, ensure_ascii=False)
sub = f"{bishi_n}场新版{lv}真题统计 · 点卡片看例句"

TEMPLATE = r'''<title>__LEVEL__ 高频词汇与考点</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Shippori+Mincho:wght@600&family=BIZ+UDPGothic:wght@400;700&display=swap">
<style>
/* Layout: sticky header (title + search + scrolling category tabs) → filter chips → one-column card list, max 760px centered; cards expand in place. */
:root{
  --bg:#f3f5f8; --surface:#ffffff; --fg:#1a2130; --muted:#66718a;
  --line:#dce2eb; --accent:#2f4f80; --accent-soft:#e6ecf6; --on-accent:#ffffff;
  --seg:#cfd7e4; --mark:#fff0a3; --quote:#f3f5f8;
  --ok:#1c7548; --ok-soft:#e3f3ea; --bad:#b0352d; --bad-soft:#fbe9e7;
  --font-ui:"BIZ UDPGothic","Hiragino Sans","PingFang SC","Noto Sans JP","Noto Sans CJK JP",system-ui,sans-serif;
  --font-jp:"Shippori Mincho","Hiragino Mincho ProN","Yu Mincho","Noto Serif JP","Noto Serif CJK JP","Songti SC",serif;
  --font-zh:"PingFang SC","Hiragino Sans GB","Noto Sans SC","Noto Sans CJK SC","Microsoft YaHei",var(--font-ui);
}
@media (prefers-color-scheme: dark){ :root:not([data-theme="light"]){
  --bg:#11151d; --surface:#1a2029; --fg:#e7eaf0; --muted:#98a3b8; --line:#2c3545;
  --accent:#8fb0e6; --accent-soft:#22304a; --on-accent:#0f1420; --seg:#334057; --mark:#6b5a12; --quote:#131822;
  --ok:#74d19c; --ok-soft:#15301f; --bad:#f18c82; --bad-soft:#3a1c19; color-scheme:dark } }
:root[data-theme="dark"]{
  --bg:#11151d; --surface:#1a2029; --fg:#e7eaf0; --muted:#98a3b8; --line:#2c3545;
  --accent:#8fb0e6; --accent-soft:#22304a; --on-accent:#0f1420; --seg:#334057; --mark:#6b5a12; --quote:#131822;
  --ok:#74d19c; --ok-soft:#15301f; --bad:#f18c82; --bad-soft:#3a1c19; color-scheme:dark }

*,*::before,*::after{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--fg);font-family:var(--font-ui);font-size:15px;line-height:1.5}
body::before{content:"";position:fixed;inset:0 0 auto;height:env(safe-area-inset-top,0px);z-index:10;background:var(--surface)}
button{-webkit-tap-highlight-color:transparent;touch-action:manipulation}
.top{position:sticky;top:env(safe-area-inset-top,0px);z-index:9;background:var(--surface);border-bottom:1px solid var(--line)}
.wrap{max-width:760px;margin:0 auto;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}
.top .wrap{padding-block:10px 0}
.brand{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap}
.brand h1{margin:0;font-size:17px;font-weight:700;letter-spacing:.02em}
.brand .sub{color:var(--muted);font-size:12px}
.search{position:relative;margin-top:8px}
.search input{width:100%;height:38px;border:1px solid var(--line);border-radius:10px;background:var(--bg);color:var(--fg);padding:0 36px 0 12px;font:inherit;font-size:15px;-webkit-appearance:none;appearance:none}
.search input:focus{outline:2px solid var(--accent);outline-offset:-1px}
.search input::-webkit-search-cancel-button,.search input::-webkit-search-decoration{-webkit-appearance:none;display:none}
.search .clr{position:absolute;right:4px;top:4px;height:30px;width:30px;border:0;background:transparent;color:var(--muted);font-size:20px;line-height:1;border-radius:8px;cursor:pointer}
.tabs{display:flex;gap:2px;overflow-x:auto;scrollbar-width:none;margin-top:6px}
.tabs::-webkit-scrollbar{display:none}
.tab{flex:0 0 auto;border:0;background:transparent;color:var(--muted);font:inherit;font-size:14px;padding:8px 10px 9px;border-bottom:2px solid transparent;white-space:nowrap;display:flex;gap:5px;align-items:baseline;cursor:pointer}
.tab .c{font-size:11px;font-variant-numeric:tabular-nums}
.tab[aria-selected="true"]{color:var(--accent);border-bottom-color:var(--accent);font-weight:700}
.main{padding-block:10px 90px}
.filters{display:flex;flex-direction:column;gap:6px}
.chips{display:flex;gap:6px;overflow-x:auto;scrollbar-width:none;padding-block:2px;align-items:center}
.chips::-webkit-scrollbar{display:none}
.chips .lab{flex:0 0 auto;font-size:12px;color:var(--muted);padding-right:2px}
.chip{flex:0 0 auto;border:1px solid var(--line);background:var(--surface);color:var(--fg);border-radius:999px;padding:4px 11px;font:inherit;font-size:13px;line-height:1.3;white-space:nowrap;cursor:pointer}
.chip[aria-pressed="true"]{background:var(--accent);border-color:var(--accent);color:var(--on-accent)}
.chip .c{opacity:.7;font-size:11px;margin-left:3px;font-variant-numeric:tabular-nums}
.note{color:var(--muted);font-size:12px;line-height:1.5;margin-top:6px;text-wrap:pretty}
.note span+span::before{content:"｜";opacity:.5}
.bar{display:flex;justify-content:space-between;align-items:center;margin-block:10px 8px;font-size:13px;color:var(--muted);font-variant-numeric:tabular-nums}
.bar button{border:0;background:transparent;color:var(--accent);font:inherit;font-size:13px;padding:4px 6px;cursor:pointer}
.list{display:flex;flex-direction:column;gap:8px}
.card{background:var(--surface);border:1px solid var(--line);border-radius:12px;overflow:hidden}
.card-head{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:5px 12px;width:100%;text-align:left;border:0;background:transparent;color:inherit;font:inherit;padding:12px 14px;cursor:pointer}
.card-head:focus-visible{outline:2px solid var(--accent);outline-offset:-2px}
.hw{min-width:0;display:flex;flex-direction:column}
.yomi{font-size:12px;color:var(--muted);letter-spacing:.04em}
.jp{font-family:var(--font-jp);font-size:22px;line-height:1.25;font-weight:600;overflow-wrap:anywhere}
.meta{grid-column:1/-1;display:flex;flex-wrap:wrap;gap:4px 10px;align-items:center;min-width:0}
.zh{font-family:var(--font-zh)}
.tag{font-size:11px;color:var(--accent);background:var(--accent-soft);border-radius:4px;padding:1px 6px;white-space:nowrap}
.freq{display:flex;flex-direction:column;align-items:flex-end;gap:4px;align-self:start}
.segs{display:flex;gap:2px}
.segs i{display:block;width:5px;height:10px;border-radius:1px;background:var(--seg)}
.segs i.on{background:var(--accent)}
.track{display:block;width:88px;height:8px;border-radius:4px;background:var(--seg);overflow:hidden}
.track i{display:block;height:100%;background:var(--accent);border-radius:4px}
.freq .n{font-size:13px;font-variant-numeric:tabular-nums;white-space:nowrap}
.freq .n small{color:var(--muted);font-size:11px}
.card-body{border-top:1px dashed var(--line);padding:10px 14px 12px;display:flex;flex-direction:column;gap:9px;font-size:14px}
.row{display:flex;flex-direction:column;gap:4px;min-width:0}
.row .k{font-size:11px;color:var(--muted);letter-spacing:.06em}
.dates{display:flex;flex-wrap:wrap;gap:4px}
.dates span{font-size:12px;border:1px solid var(--line);border-radius:4px;padding:0 5px;font-variant-numeric:tabular-nums;color:var(--muted)}
blockquote{margin:0;padding:8px 10px;background:var(--quote);border-left:3px solid var(--accent);border-radius:0 6px 6px 0;font-family:var(--font-jp);font-size:15px;line-height:1.65;overflow-wrap:anywhere;white-space:pre-wrap}
.src{font-size:12px;color:var(--muted);overflow-wrap:anywhere}
.eyebrow{font-size:12px;color:var(--muted);font-variant-numeric:tabular-nums}
.ttl{font-size:17px;font-weight:700;line-height:1.35;overflow-wrap:anywhere}
.desc{font-size:14px;opacity:.85;grid-column:1/-1;overflow-wrap:anywhere}
.desc.jp-text{font-family:var(--font-jp);font-size:15px;opacity:1}
mark{background:var(--mark);color:inherit;border-radius:2px;padding:0 1px}
.group-h{font-size:13px;color:var(--muted);margin-top:10px;display:flex;gap:8px;align-items:baseline}
.group-h b{color:var(--fg);font-size:15px}
.group-h:first-child{margin-top:0}
.more{border:1px solid var(--line);background:var(--surface);color:var(--accent);font:inherit;font-size:14px;border-radius:10px;padding:11px;cursor:pointer}
.empty{text-align:center;color:var(--muted);padding:48px 0;font-size:14px}
.empty .link{border:0;background:var(--accent-soft);color:var(--accent);font:inherit;font-size:13px;border-radius:999px;padding:4px 10px;margin:4px 3px 0;cursor:pointer}
.info h2{font-size:16px;margin:18px 0 8px}
.info h2:first-child{margin-top:4px}
.info p.lead{margin:0 0 8px;color:var(--muted);font-size:13px}
.tbl{overflow-x:auto;background:var(--surface);border:1px solid var(--line);border-radius:12px}
table{border-collapse:collapse;width:100%;font-size:13px;min-width:540px;font-variant-numeric:tabular-nums}
th,td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--line);vertical-align:top}
th{font-weight:700;color:var(--muted);font-size:12px;white-space:nowrap}
tr:last-child td{border-bottom:0}
.kv{display:flex;flex-direction:column;gap:8px}
.kv .it{background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:10px 12px}
.kv .it b{display:block;font-size:13px;margin-bottom:2px}
.kv .it span{font-size:14px;opacity:.85}
.srcs{display:flex;flex-direction:column;gap:6px}
.srcs .it{background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:9px 12px;display:grid;grid-template-columns:auto minmax(0,1fr);gap:2px 10px;font-size:13px}
.srcs .it .ym{font-variant-numeric:tabular-nums;font-weight:700}
.srcs .it .u{color:var(--accent);font-size:12px}
.srcs .it .f{grid-column:1/-1;overflow-wrap:anywhere}
.srcs .it .d{grid-column:1/-1;color:var(--muted);font-size:12px}
.qz{display:flex;flex-direction:column;gap:10px}
.qz-card{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:16px;display:flex;flex-direction:column;gap:12px}
.qz-card h2{margin:0;font-size:18px}
.qz-card .lead{margin:0;color:var(--muted);font-size:13px}
.qz-card .note{margin:0}
.qz .chips{flex-wrap:wrap;overflow:visible}
.chip:disabled{opacity:.45;cursor:default}
.qz-go{border:0;background:var(--accent);color:var(--on-accent);font:inherit;font-size:16px;font-weight:700;border-radius:12px;padding:13px;cursor:pointer}
.qz-go.ghost{background:transparent;color:var(--accent);border:1px solid var(--line);font-weight:400;font-size:15px}
.qz-go:focus-visible,.qz-opt:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.qz-top{display:flex;justify-content:space-between;align-items:center;font-size:13px;color:var(--muted);font-variant-numeric:tabular-nums}
.qz-top button{border:0;background:transparent;color:var(--accent);font:inherit;font-size:13px;padding:4px 0;cursor:pointer}
.qz-prog{width:100%;height:6px}
.qz-stem{font-family:var(--font-jp);font-size:19px;line-height:1.75;font-weight:600;overflow-wrap:anywhere}
.qz-stem.small{font-size:16px}
.blank{color:var(--accent);white-space:nowrap}
.blank.filled{border-bottom:2px solid var(--accent);padding:0 4px;white-space:normal}
.qz-opts{display:flex;flex-direction:column;gap:8px}
.qz-opt{display:flex;gap:12px;align-items:baseline;text-align:left;width:100%;border:1px solid var(--line);background:var(--surface);color:var(--fg);font:inherit;border-radius:12px;padding:12px 14px;cursor:pointer}
.qz-opt b{font-size:13px;color:var(--muted);font-variant-numeric:tabular-nums;flex:0 0 auto}
.qz-opt span{font-family:var(--font-jp);font-size:18px;font-weight:600;min-width:0;overflow-wrap:anywhere}
.qz-opts.done .qz-opt{cursor:default}
.qz-opt.is-ok{border-color:var(--ok);background:var(--ok-soft)}
.qz-opt.is-ok b{color:var(--ok)}
.qz-opt.is-bad{border-color:var(--bad);background:var(--bad-soft)}
.qz-opt.is-bad b{color:var(--bad)}
.qz-exp{border:1px solid var(--ok);background:var(--ok-soft);border-radius:12px;padding:12px 14px;display:flex;flex-direction:column;gap:8px;font-size:14px}
.qz-exp.bad{border-color:var(--bad);background:var(--bad-soft)}
.qz-exp .verdict{font-weight:700;color:var(--ok);font-size:15px}
.qz-exp.bad .verdict{color:var(--bad)}
.qz-score{display:flex;align-items:baseline;gap:8px}
.qz-score b{font-size:40px;line-height:1;font-variant-numeric:tabular-nums}
.qz-score span{color:var(--muted)}
.qz-actions{display:flex;flex-direction:column;gap:8px}
.fab{position:fixed;right:max(14px,env(safe-area-inset-right,0px));bottom:calc(14px + env(safe-area-inset-bottom,0px));width:42px;height:42px;border-radius:50%;border:1px solid var(--line);background:var(--surface);color:var(--accent);box-shadow:0 2px 10px rgba(0,0,0,.14);font-size:18px;cursor:pointer;z-index:8}
@media (prefers-reduced-motion:no-preference){.card-body{animation:fade .16s ease}@keyframes fade{from{opacity:0}to{opacity:1}}}
</style>

<header class="top">
  <div class="wrap">
    <div class="brand">
      <h1>__LEVEL__ 高频词汇与考点</h1>
      <span class="sub">__SUB__</span>
    </div>
    <div class="search">
      <input id="q" type="search" placeholder="搜索日语 / 读音 / 中文 / 考点…" autocomplete="off" autocorrect="off" autocapitalize="off" spellcheck="false" aria-label="搜索">
      <button class="clr" id="clr" type="button" aria-label="清除搜索" hidden>×</button>
    </div>
    <nav class="tabs" id="tabs" role="tablist" aria-label="分类"></nav>
  </div>
</header>

<main class="wrap main">
  <div class="filters" id="filters"></div>
  <div class="bar" id="bar"></div>
  <div class="list" id="list"></div>
</main>
<button class="fab" id="fab" type="button" aria-label="回到顶部" hidden>↑</button>

<script type="application/json" id="n4-data">__DATA__</script>
<script>
(function(){
'use strict';
var DATA = JSON.parse(document.getElementById('n4-data').textContent);
var TABS = __TABS__;
var LEVEL = '__LEVEL__';
var POS_ORDER = ['名词','动词','形容词','形容动词','副词','时间','疑问词','表达','词汇'];
var CHUNK = 400;

var state = { tab: (TABS.filter(function(t){ return t.kind!=='quiz'; })[0] || TABS[0]).id, q: '', f: {} };
TABS.forEach(function(t){ state.f[t.id] = {pos:'全部', min:0, sort:'freq', year:'全部', point:'全部'}; });

var $ = function(id){ return document.getElementById(id); };
var elTabs = $('tabs'), elFilters = $('filters'), elBar = $('bar'), elList = $('list'), elQ = $('q'), elClr = $('clr'), elFab = $('fab');

function esc(s){ return String(s==null?'':s).replace(/[&<>"']/g, function(c){ return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]; }); }
function hl(s){
  var t = esc(s); var q = state.q.trim();
  if(!q) return t;
  var re = new RegExp(q.replace(/[.*+?^${}()|[\]\\]/g,'\\$&'), 'gi');
  return t.replace(re, function(m){ return '<mark>'+m+'</mark>'; });
}
function pick(r){ for(var i=1;i<arguments.length;i++){ if(r[arguments[i]]!=null) return r[arguments[i]]; } return ''; }
function fmtYM(s){ s=String(s).trim(); return /^\d{6}$/.test(s) ? s.slice(0,4)+'/'+s.slice(4) : s; }
function splitDates(s){ return String(s||'').split(/[、，,\s]+/).filter(Boolean); }
function datesHtml(s){ return '<div class="dates">'+splitDates(s).map(function(d){ return '<span>'+esc(fmtYM(d))+'</span>'; }).join('')+'</div>'; }
function segs(n, max){
  if(max<=16){ var h='<span class="segs" aria-hidden="true">'; for(var i=0;i<max;i++){ h+='<i'+(i<n?' class="on"':'')+'></i>'; } return h+'</span>'; }
  var pct = Math.max(0, Math.min(100, n/max*100));
  return '<span class="track" aria-hidden="true"><i style="width:'+pct.toFixed(1)+'%"></i></span>';
}
function freqBox(n, max, extra){ return '<div class="freq" title="出现过的考试场次">'+segs(+n,max)+'<span class="n">'+esc(n)+'<small>/'+max+'场'+(extra?' · '+esc(extra):'')+'</small></span></div>'; }
function row(k, inner){ return inner ? '<div class="row"><span class="k">'+k+'</span>'+inner+'</div>' : ''; }
function tabById(id){ for(var i=0;i<TABS.length;i++) if(TABS[i].id===id) return TABS[i]; return null; }
function rowsOf(t){ return t.sheet ? DATA[t.sheet].rows : []; }

function matchesQ(r, q){
  if(!q) return true;
  for(var k in r){ if(String(r[k]).toLowerCase().indexOf(q)>=0) return true; }
  return false;
}
function filtered(t){
  var st = state.f[t.id], q = state.q.trim().toLowerCase();
  var rows = rowsOf(t).map(function(r,i){ return {r:r,i:i}; });
  if(t.kind==='vocab'){
    if(st.pos!=='全部') rows = rows.filter(function(x){ return x.r['词性／类别']===st.pos; });
  }
  if(st.min>0 && (t.kind==='vocab'||t.kind==='grammar'||t.kind==='lpoint'||t.kind==='lexpr')){
    rows = rows.filter(function(x){ return +x.r['考试频次']>=st.min; });
  }
  if(t.kind==='gq'||t.kind==='lq'){
    if(st.year!=='全部') rows = rows.filter(function(x){ return String(x.r['考试年月'])===st.year; });
    if(st.point!=='全部') rows = rows.filter(function(x){ return (x.r['考点']||x.r['日语考点'])===st.point; });
  }
  if(q) rows = rows.filter(function(x){ return matchesQ(x.r, q); });
  if(t.kind==='vocab' && st.sort==='kana'){
    rows.sort(function(a,b){ return String(a.r['读音']).localeCompare(String(b.r['读音']),'ja'); });
  }
  return rows;
}
function countQ(t){
  var q = state.q.trim().toLowerCase(); var rows = rowsOf(t);
  if(!q) return rows.length;
  var n=0; for(var i=0;i<rows.length;i++) if(matchesQ(rows[i],q)) n++; return n;
}

/* ---------- tabs ---------- */
function renderTabs(){
  elTabs.innerHTML = TABS.map(function(t){
    var c = (t.kind==='info' || t.kind==='quiz') ? '' : '<span class="c">'+countQ(t)+'</span>';
    return '<button class="tab" role="tab" type="button" data-tab="'+t.id+'" aria-selected="'+(t.id===state.tab)+'">'+esc(t.label)+c+'</button>';
  }).join('');
  var sel = elTabs.querySelector('[aria-selected="true"]');
  if(sel && sel.scrollIntoView) { try{ sel.scrollIntoView({block:'nearest', inline:'center'}); }catch(e){} }
}

/* ---------- filters ---------- */
function chip(label, pressed, data, count){
  return '<button class="chip" type="button" aria-pressed="'+pressed+'" '+data+'>'+esc(label)+(count!=null?'<span class="c">'+count+'</span>':'')+'</button>';
}
function chipsRow(lab, inner){ return '<div class="chips">'+(lab?'<span class="lab">'+lab+'</span>':'')+inner+'</div>'; }
function noteHtml(t){
  if(!t.sheet) return '';
  var sub = DATA[t.sheet].subtitle || '';
  return '<div class="note">'+sub.split('｜').map(function(s){ return '<span>'+esc(s)+'</span>'; }).join('')+'</div>';
}
function freqChipsRow(t, st){
  return chipsRow('频次', chip('全部', st.min===0, 'data-min="0"') + t.freqChips.map(function(n){ return chip('≥'+n+'场', st.min===n, 'data-min="'+n+'"'); }).join(''));
}
function renderFilters(t){
  var st = state.f[t.id], h = '';
  if(t.kind==='vocab'){
    var cnt = {}; rowsOf(t).forEach(function(r){ var p=r['词性／类别']; cnt[p]=(cnt[p]||0)+1; });
    var poss = POS_ORDER.filter(function(p){ return cnt[p]; }).concat(Object.keys(cnt).filter(function(p){ return POS_ORDER.indexOf(p)<0; }));
    h += chipsRow('词性', chip('全部', st.pos==='全部', 'data-pos="全部"', rowsOf(t).length) + poss.map(function(p){ return chip(p, st.pos===p, 'data-pos="'+esc(p)+'"', cnt[p]); }).join(''));
    h += freqChipsRow(t, st);
    h += chipsRow('排序', chip('按频次', st.sort==='freq', 'data-sort="freq"') + chip('按词性分组', st.sort==='pos', 'data-sort="pos"') + chip('五十音', st.sort==='kana', 'data-sort="kana"'));
  } else if(t.kind==='grammar'||t.kind==='lpoint'||t.kind==='lexpr'){
    h += freqChipsRow(t, st);
  } else if(t.kind==='gq'||t.kind==='lq'){
    var ys = []; var yc = {}; rowsOf(t).forEach(function(r){ var y=String(r['考试年月']); if(!yc[y]){ yc[y]=0; ys.push(y);} yc[y]++; });
    h += chipsRow('考试', chip('全部', st.year==='全部', 'data-year="全部"') + ys.map(function(y){ return chip(fmtYM(y), st.year===y, 'data-year="'+y+'"', yc[y]); }).join(''));
    if(t.kind==='lq'){
      var pc = {}, ps = []; rowsOf(t).forEach(function(r){ var p=r['考点']; if(!pc[p]){ pc[p]=0; ps.push(p);} pc[p]++; });
      ps.sort(function(a,b){ return pc[b]-pc[a]; });
      h += chipsRow('考点', chip('全部', st.point==='全部', 'data-point="全部"') + ps.map(function(p){ return chip(p, st.point===p, 'data-point="'+esc(p)+'"', pc[p]); }).join(''));
    }
  }
  h += noteHtml(t);
  elFilters.innerHTML = h;
}

/* ---------- cards ---------- */
function cardOpen(inner, body){
  return '<article class="card"><button class="card-head" type="button" aria-expanded="false">'+inner+'</button><div class="card-body" hidden>'+body+'</div></article>';
}
function vocabCard(r, t){
  var jp = r['日语'], yomi = r['读音'];
  var head = '<div class="hw">'+(yomi && yomi!==jp ? '<span class="yomi">'+hl(yomi)+'</span>' : '')+'<span class="jp" lang="ja">'+hl(jp)+'</span></div>'
    + freqBox(r['考试频次'], t.max)
    + '<div class="meta"><span class="zh">'+hl(r['中文翻译'])+'</span><span class="tag">'+esc(r['词性／类别'])+'</span></div>';
  var body = row('出现考试', datesHtml(r['出现考试年月']))
    + row('原文摘录', '<blockquote lang="ja">'+hl(r['原文摘录（含选项）'])+'</blockquote>')
    + row('来源', '<span class="src">'+esc(r['摘录来源'])+'</span>');
  return cardOpen(head, body);
}
function grammarCard(r, t){
  var cnt = pick(r, '题目数', '已归类条目数');
  var head = '<div class="hw"><span class="ttl" lang="ja">'+hl(r['日语考点'])+'</span></div>'
    + freqBox(r['考试频次'], t.max, cnt!=='' ? cnt+'题' : '')
    + '<div class="desc zh">'+hl(r['中文说明／考查用法'])+'</div>';
  var body = row('出现考试', datesHtml(r['出现考试年月']))
    + row('示例题号', '<span class="src">'+esc(pick(r,'示例题号','示例编号'))+'</span>')
    + row('题目摘录', '<blockquote lang="ja">'+hl(r['题目摘录'])+'</blockquote>');
  return cardOpen(head, body);
}
function gqCard(r){
  var head = '<div class="hw"><span class="eyebrow">'+esc(fmtYM(r['考试年月']))+' · '+esc(pick(r,'题号','编号'))+'</span><span class="ttl" lang="ja">'+hl(r['日语考点'])+'</span></div><div></div>'
    + '<div class="desc zh">'+hl(r['中文解释'])+'</div>';
  var body = row('题目摘录', '<blockquote lang="ja">'+hl(r['题目摘录'])+'</blockquote>')
    + row('识别依据', '<span class="src">'+esc(r['识别依据／状态'])+'</span>')
    + row('来源', '<span class="src">'+esc(r['来源'])+'</span>');
  return cardOpen(head, body);
}
function lqCard(r){
  var head = '<div class="hw"><span class="eyebrow">'+esc(fmtYM(r['考试年月']))+' · '+esc(pick(r,'题号','编号'))+'</span><span class="ttl">'+hl(r['考点'])+'</span></div><div></div>'
    + '<div class="desc jp-text" lang="ja">'+hl(r['提问摘录'])+'</div>';
  var body = row('解题关注点', '<span class="zh">'+hl(r['解题关注点'])+'</span>')
    + row('对话摘录', '<blockquote lang="ja">'+hl(r['对话摘录'])+'</blockquote>')
    + row('来源', '<span class="src">'+esc(r['来源'])+'</span>')
    + row('识别依据', '<span class="src">'+esc(r['识别依据／状态'])+'</span>');
  return cardOpen(head, body);
}
function lpointCard(r, t){
  var cnt = pick(r, '题目数', '材料段／提问数');
  var head = '<div class="hw"><span class="ttl">'+hl(r['考点'])+'</span></div>'
    + freqBox(r['考试频次'], t.max, cnt!=='' ? cnt+'条' : '')
    + '<div class="desc zh">'+hl(r['解题关注点'])+'</div>';
  var body = row('出现考试', datesHtml(r['出现考试年月']))
    + row('示例题号', '<span class="src">'+esc(pick(r,'示例题号','示例编号'))+'</span>');
  return cardOpen(head, body);
}
function lexprCard(r, t){
  var head = '<div class="hw"><span class="ttl" lang="ja">'+hl(r['日语表达'])+'</span></div>'
    + freqBox(r['考试频次'], t.max)
    + '<div class="desc zh">'+hl(r['中文解释'])+'</div>';
  var body = row('出现考试', datesHtml(r['出现考试年月']))
    + row('原文摘录', '<blockquote lang="ja">'+hl(r['原文摘录'])+'</blockquote>')
    + row('来源', '<span class="src">'+esc(r['来源'])+'</span>');
  return cardOpen(head, body);
}
var CARD = {vocab:vocabCard, grammar:grammarCard, gq:gqCard, lq:lqCard, lpoint:lpointCard, lexpr:lexprCard};

var pendingItems = [];
function moreBtn(){ return pendingItems.length ? '<button class="more" type="button" data-more>显示更多（还有 '+pendingItems.length+' 条）</button>' : ''; }
function appendChunk(){
  var btn = elList.querySelector('[data-more]');
  var part = pendingItems.splice(0, CHUNK).join('');
  if(btn){ btn.insertAdjacentHTML('beforebegin', part); btn.remove(); if(pendingItems.length) elList.insertAdjacentHTML('beforeend', moreBtn()); }
  else { elList.innerHTML = part + moreBtn(); }
}
function renderList(t){
  if(t.kind==='info'){ renderInfo(); return; }
  var rows = filtered(t), total = rowsOf(t).length, st = state.f[t.id];
  elBar.innerHTML = '<span>'+(rows.length===total ? '共 '+total+' 条' : '显示 '+rows.length+' / '+total+' 条')+'</span>'
    + (rows.length ? '<span><button type="button" data-expand="1">全部展开</button><button type="button" data-expand="0">收起</button></span>' : '');
  pendingItems = [];
  if(!rows.length){
    var others = state.q.trim() ? TABS.filter(function(o){ return o.kind!=='info' && o.kind!=='quiz' && o.id!==t.id && countQ(o)>0; }) : [];
    elList.innerHTML = '<div class="empty">没有匹配的条目。试试换个关键词或放宽筛选。'
      + (others.length ? '<div style="margin-top:12px">其他分类中有匹配：<br>'+others.map(function(o){ return '<button class="link" type="button" data-goto="'+o.id+'">'+esc(o.label)+' '+countQ(o)+'</button>'; }).join('')+'</div>' : '')
      + '</div>';
    return;
  }
  if(t.kind==='vocab' && st.sort==='pos'){
    var groups = {}; rows.forEach(function(x){ var p=x.r['词性／类别']; (groups[p]=groups[p]||[]).push(x); });
    POS_ORDER.concat(Object.keys(groups).filter(function(p){ return POS_ORDER.indexOf(p)<0; })).forEach(function(p){
      if(!groups[p]) return;
      pendingItems.push('<div class="group-h"><b>'+esc(p)+'</b><span>'+groups[p].length+' 个</span></div>');
      groups[p].forEach(function(x){ pendingItems.push(vocabCard(x.r, t)); });
    });
  } else {
    var fn = CARD[t.kind];
    rows.forEach(function(x){ pendingItems.push(fn(x.r, t)); });
  }
  elList.innerHTML = '';
  appendChunk();
}

function renderInfo(){
  var sc = DATA['统计范围'], kj = DATA['统计口径'], ly = DATA['材料来源'];
  elBar.innerHTML = '';
  var h = '<div class="info">';
  if(kj) h += '<h2>统计口径</h2><p class="lead">'+esc(kj.subtitle)+'</p><div class="kv">'
    + kj.rows.map(function(r){ return '<div class="it"><b>'+esc(r['项目'])+'</b><span class="zh">'+esc(r['说明'])+'</span></div>'; }).join('') + '</div>';
  if(sc) h += '<h2>统计范围</h2><p class="lead">'+esc(sc.subtitle)+'</p><div class="tbl"><table><thead><tr>'
    + sc.headers.map(function(x){ return '<th>'+esc(x)+'</th>'; }).join('') + '</tr></thead><tbody>'
    + sc.rows.map(function(r){ return '<tr>'+sc.headers.map(function(k,i){ return '<td>'+esc(i===0?fmtYM(r[k]):r[k])+'</td>'; }).join('')+'</tr>'; }).join('')
    + '</tbody></table></div>';
  if(QUIZ) h += '<h2>小练习题库</h2><div class="kv">' + QUIZ.notes.map(function(x){ return '<div class="it"><span class="zh">'+esc(x)+'</span></div>'; }).join('') + '</div>';
  if(ly) h += '<h2>材料来源</h2><p class="lead">'+esc(ly.subtitle)+'</p><div class="srcs">'
    + ly.rows.map(function(r){ return '<div class="it"><span class="ym">'+esc(fmtYM(r['考试年月']))+'</span><span class="u">'+esc(r['用途'])+'</span><span class="f">'+esc(r['文件名'])+(r['页码范围']!=null?' · 第 '+esc(r['页码范围'])+' 页':'')+'</span><span class="d zh">'+esc(r['计数说明'])+'</span></div>'; }).join('')
    + '</div>';
  h += '</div>';
  elList.innerHTML = h;
}

/* ---------- quiz (小练习) ---------- */
var QUIZ = DATA._quiz || null;
var KEY_WRONG = 'jlpt-'+LEVEL+'-quiz-wrong', KEY_STAT = 'jlpt-'+LEVEL+'-quiz-stat';
var qz = { scope:'all', n:10, run:null };
function lsGet(k, d){ try{ var v = localStorage.getItem(k); return v ? JSON.parse(v) : d; }catch(e){ return d; } }
function lsSet(k, v){ try{ localStorage.setItem(k, JSON.stringify(v)); }catch(e){} }
function catById(id){ for(var i=0;i<QUIZ.cats.length;i++) if(QUIZ.cats[i].id===id) return QUIZ.cats[i]; return null; }
function qPool(scope){
  var items = QUIZ.items;
  if(scope==='all') return items;
  if(scope==='weak') return items.filter(function(x){ return x.c.length; });
  if(scope==='wrong'){ var w = lsGet(KEY_WRONG, {}); return items.filter(function(x){ return w[x.id]; }); }
  return items.filter(function(x){ return x.c.indexOf(scope)>=0; });
}
function shuffle(a){ for(var i=a.length-1;i>0;i--){ var j=Math.floor(Math.random()*(i+1)); var t=a[i]; a[i]=a[j]; a[j]=t; } return a; }
function qStart(list){
  var pool = list ? shuffle(list.slice()) : shuffle(qPool(qz.scope).slice());
  var n = list ? pool.length : (qz.n===0 ? pool.length : Math.min(qz.n, pool.length));
  if(!n) return;
  qz.run = { items: pool.slice(0,n), i:0, picked:0, log:[], scope: list ? 'retry' : qz.scope };
  renderQuiz(); window.scrollTo(0,0);
}
function stemHtml(it, fill){
  var parts = String(it.s).split('（　）'), ans = String(it.o[it.a-1]).split('／'), h = '';
  for(var i=0;i<parts.length;i++){
    h += esc(parts[i]).replace(/\n/g,'<br>');
    if(i<parts.length-1) h += fill ? '<span class="blank filled">'+esc(ans[Math.min(i,ans.length-1)])+'</span>' : '<span class="blank">（　　）</span>';
  }
  return h;
}
function quizSetupHtml(){
  var all = QUIZ.items.length, weak = qPool('weak').length, wrong = qPool('wrong').length, st = lsGet(KEY_STAT, {done:0, right:0});
  if(qz.scope==='wrong' && !wrong) qz.scope = 'all';
  var pool = qPool(qz.scope).length, take = qz.n===0 ? pool : Math.min(qz.n, pool);
  return '<div class="qz"><div class="qz-card">'
    + '<h2>真题小练习</h2><p class="lead">'+esc(QUIZ.intro)+'</p>'
    + chipsRow('范围', chip('全部真题', qz.scope==='all', 'data-qscope="all"', all) + chip('我的弱项', qz.scope==='weak', 'data-qscope="weak"', weak) + chip('错题本', qz.scope==='wrong', 'data-qscope="wrong"'+(wrong?'':' disabled'), wrong))
    + chipsRow('弱项', QUIZ.cats.map(function(c){ return chip(c.label, qz.scope===c.id, 'data-qscope="'+c.id+'"', c.n); }).join(''))
    + chipsRow('题数', [5,10,15,0].map(function(n){ return chip(n ? n+' 题' : '全部', qz.n===n, 'data-qn="'+n+'"'); }).join(''))
    + '<button class="qz-go" type="button" data-qstart>开始练习（'+take+' 题）</button>'
    + '<p class="note">'+(st.done ? '累计做过 '+st.done+' 题，答对 '+st.right+' 题（'+Math.round(st.right/st.done*100)+'%）。' : '')
    + '答错的题会自动进错题本，在错题本里答对后移出。记录只保存在这台设备的浏览器里。</p>'
    + '</div></div>';
}
function quizQuestionHtml(){
  var r = qz.run, it = r.items[r.i], done = r.picked>0, ok = done && r.picked===it.a;
  var h = '<div class="qz"><div class="qz-card">'
    + '<div class="qz-top"><span>第 '+(r.i+1)+' / '+r.items.length+' 题</span><button type="button" data-qquit>结束练习</button></div>'
    + '<span class="track qz-prog" aria-hidden="true"><i style="width:'+((r.i+(done?1:0))/r.items.length*100).toFixed(1)+'%"></i></span>'
    + '<div class="eyebrow">'+esc(fmtYM(it.ym))+' · 文法問題1 · 第'+it.n+'题</div>'
    + '<div class="qz-stem" lang="ja">'+stemHtml(it, done)+'</div>'
    + '<div class="qz-opts'+(done?' done':'')+'">' + it.o.map(function(o, k){
        var n = k+1, cls = 'qz-opt';
        if(done){ if(n===it.a) cls += ' is-ok'; else if(n===r.picked) cls += ' is-bad'; }
        return '<button class="'+cls+'" type="button" data-qopt="'+n+'"><b>'+n+'</b><span lang="ja">'+esc(o)+'</span></button>';
      }).join('') + '</div>';
  if(done){
    var tip = ''; for(var i=0;i<it.c.length;i++){ var c = catById(it.c[i]); if(c && c.tip){ tip = c.tip; break; } }
    h += '<div class="qz-exp '+(ok?'ok':'bad')+'">'
      + '<div class="verdict">'+(ok?'答对了':'答错了')+' · 正确答案 '+it.a+'　<span lang="ja">'+esc(it.o[it.a-1])+'</span></div>'
      + row('考点', '<span class="ttl" lang="ja">'+esc(it.pt)+'</span>')
      + row('解析', '<span class="zh">'+esc(it.ex)+'</span>')
      + (tip ? row('提示', '<span class="zh">'+esc(tip)+'</span>') : '')
      + '<div class="src">'+esc(it.src)+(it.fl ? ' · 本题文字经 OCR 修复，可能与原卷略有出入' : '')+'</div>'
      + '</div>'
      + '<button class="qz-go" type="button" data-qnext>'+(r.i+1<r.items.length ? '下一题' : '看结果')+'</button>';
  }
  return h + '</div></div>';
}
function quizResultHtml(){
  var r = qz.run, total = r.log.length, wrong = r.log.filter(function(x){ return !x.ok; }), right = total - wrong.length;
  var h = '<div class="qz"><div class="qz-card">'
    + '<h2>练习结果</h2>'
    + '<div class="qz-score"><b>'+right+'</b><span>/ '+total+' 题答对</span></div>'
    + (total ? '<span class="track qz-prog" aria-hidden="true"><i style="width:'+(right/total*100).toFixed(1)+'%"></i></span>' : '')
    + (total && !wrong.length ? '<p class="lead">这一组全部答对。</p>' : '')
    + '<div class="qz-actions"><button class="qz-go" type="button" data-qagain>再来一组</button>'
    + (wrong.length ? '<button class="qz-go ghost" type="button" data-qretry>重做这 '+wrong.length+' 道错题</button>' : '')
    + '<button class="qz-go ghost" type="button" data-qsetup>返回设置</button></div>'
    + '</div>';
  if(wrong.length){
    h += '<div class="group-h"><b>这次答错的题</b><span>'+wrong.length+' 道，已加入错题本</span></div>'
      + wrong.map(function(x){ var it = x.it; return '<div class="qz-card">'
        + '<div class="eyebrow">'+esc(fmtYM(it.ym))+' · 文法問題1 · 第'+it.n+'题</div>'
        + '<div class="qz-stem small" lang="ja">'+stemHtml(it, true)+'</div>'
        + '<div class="src">你选的是 '+x.picked+'　<span lang="ja">'+esc(it.o[x.picked-1])+'</span></div>'
        + row('考点', '<span><span lang="ja">'+esc(it.pt)+'</span>　<span class="zh">'+esc(it.ex)+'</span></span>')
        + '</div>'; }).join('');
  }
  return h + '</div>';
}
function renderQuiz(){
  elFilters.innerHTML = ''; elBar.innerHTML = '';
  var r = qz.run;
  elList.innerHTML = !r ? quizSetupHtml() : (r.i >= r.items.length ? quizResultHtml() : quizQuestionHtml());
}
function qPick(n){
  var r = qz.run; if(!r || r.picked || r.i >= r.items.length) return;
  var it = r.items[r.i], ok = n===it.a; r.picked = n;
  r.log.push({it:it, picked:n, ok:ok});
  var st = lsGet(KEY_STAT, {done:0, right:0}); st.done++; if(ok) st.right++; lsSet(KEY_STAT, st);
  var w = lsGet(KEY_WRONG, {});
  if(!ok){ w[it.id] = (w[it.id]||0)+1; lsSet(KEY_WRONG, w); }
  else if(r.scope==='wrong' && w[it.id]){ delete w[it.id]; lsSet(KEY_WRONG, w); }
  renderQuiz();
  var e = elList.querySelector('[data-qnext]'); if(e && e.scrollIntoView){ try{ e.scrollIntoView({block:'nearest', behavior:'smooth'}); }catch(err){} }
}
function quizClick(e){
  var b = e.target.closest('button'); if(!b) return;
  var d = b.dataset, r = qz.run;
  if(d.qscope!=null){ if(!b.disabled){ qz.scope = d.qscope; renderQuiz(); } }
  else if(d.qn!=null){ qz.n = +d.qn; renderQuiz(); }
  else if(d.qstart!=null || d.qagain!=null){ qStart(); }
  else if(d.qopt!=null){ qPick(+d.qopt); }
  else if(d.qnext!=null){ if(r){ r.i++; r.picked = 0; renderQuiz(); window.scrollTo(0,0); } }
  else if(d.qretry!=null){ if(r) qStart(r.log.filter(function(x){ return !x.ok; }).map(function(x){ return x.it; })); }
  else if(d.qsetup!=null){ qz.run = null; renderQuiz(); window.scrollTo(0,0); }
  else if(d.qquit!=null){
    if(r && r.log.length){ r.items = r.items.slice(0, r.log.length); r.i = r.items.length; } else { qz.run = null; }
    renderQuiz(); window.scrollTo(0,0);
  }
}

function render(){
  var t = tabById(state.tab) || TABS[0];
  renderTabs();
  if(t.kind==='quiz'){ renderQuiz(); return; }
  renderFilters(t); renderList(t);
}

/* ---------- events ---------- */
function goTab(id){
  if(!tabById(id) || state.tab===id) return;
  state.tab = id;
  try{ localStorage.setItem('jlpt-tab', state.tab); }catch(err){}
  if(location.hash !== '#'+state.tab) location.hash = state.tab;
  render();
  window.scrollTo(0,0);
}
elTabs.addEventListener('click', function(e){
  var b = e.target.closest('[data-tab]'); if(!b) return;
  goTab(b.dataset.tab);
});
window.addEventListener('hashchange', function(){
  var id = location.hash.slice(1);
  if(tabById(id) && id!==state.tab){ state.tab = id; render(); window.scrollTo(0,0); }
});
elFilters.addEventListener('click', function(e){
  var b = e.target.closest('.chip'); if(!b) return;
  var st = state.f[state.tab], d = b.dataset;
  if(d.pos!=null) st.pos = d.pos;
  if(d.min!=null) st.min = +d.min;
  if(d.sort!=null) st.sort = d.sort;
  if(d.year!=null) st.year = d.year;
  if(d.point!=null) st.point = d.point;
  var t = tabById(state.tab); renderFilters(t); renderList(t);
});
elList.addEventListener('click', function(e){
  if((tabById(state.tab)||{}).kind==='quiz'){ quizClick(e); return; }
  var g = e.target.closest('[data-goto]'); if(g){ goTab(g.dataset.goto); return; }
  if(e.target.closest('[data-more]')){ appendChunk(); return; }
  var b = e.target.closest('.card-head'); if(!b) return;
  var open = b.getAttribute('aria-expanded')==='true';
  b.setAttribute('aria-expanded', String(!open));
  b.nextElementSibling.hidden = open;
});
elBar.addEventListener('click', function(e){
  var b = e.target.closest('[data-expand]'); if(!b) return;
  var open = b.dataset.expand==='1';
  elList.querySelectorAll('.card-head').forEach(function(hd){ hd.setAttribute('aria-expanded', String(open)); hd.nextElementSibling.hidden = !open; });
});
var qTimer;
elQ.addEventListener('input', function(){
  clearTimeout(qTimer);
  qTimer = setTimeout(function(){ state.q = elQ.value; elClr.hidden = !state.q; render(); }, 150);
});
elClr.addEventListener('click', function(){ elQ.value=''; state.q=''; elClr.hidden=true; render(); elQ.focus(); });
elFab.addEventListener('click', function(){ window.scrollTo({top:0, behavior:'smooth'}); });
window.addEventListener('scroll', function(){ elFab.hidden = window.scrollY < 600; }, {passive:true});

/* ---------- boot ---------- */
(function(){
  var id = location.hash.slice(1);
  if(!tabById(id)){ try{ id = localStorage.getItem('jlpt-tab'); }catch(err){ id=null; } }
  if(tabById(id)) state.tab = id;
  render();
})();
})();
</script>
'''

page = TEMPLATE.replace("__DATA__", payload).replace("__TABS__", tabs_json).replace("__LEVEL__", lv).replace("__SUB__", sub)
body_name = f"{lv.lower()}_page.html"
open(body_name, "w", encoding="utf-8").write(page)

standalone = ('<!doctype html>\n<html lang="zh-CN">\n<head>\n<meta charset="utf-8">\n'
  '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
  '<style>:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}img{max-width:100%}[hidden]{display:none!important}</style>\n'
  '</head>\n<body>\n' + page + '\n</body>\n</html>\n')
for name in (f"{lv}高频词汇与考点统计.html", "index.html"):
    open(name, "w", encoding="utf-8").write(standalone)
print(f"{body_name}: {os.path.getsize(body_name)} bytes; index.html: {os.path.getsize('index.html')} bytes")
