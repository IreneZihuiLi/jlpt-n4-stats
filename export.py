import openpyxl, json, collections, sys
src = "/Users/ireneli/Documents/2026Spring/日语材料/全部真题/N4高频词汇与考点统计.xlsx"
wb = openpyxl.load_workbook(src, data_only=True)
out = {}
for ws in wb.worksheets:
    rows = list(ws.iter_rows(values_only=True))
    title = rows[0][0]; subtitle = rows[1][0]
    headers = [h for h in rows[4] if h is not None]
    data = []
    for r in rows[5:]:
        if all(c is None for c in r): continue
        rec = {}
        for h, c in zip(headers, r):
            if c is None: continue
            s = str(c).strip() if not isinstance(c, (int, float)) else c
            rec[h] = s
        data.append(rec)
    out[ws.title] = {"title": title, "subtitle": subtitle, "headers": headers, "rows": data}
    print(ws.title, len(data), "rows; headers:", headers)
json.dump(out, open("data.json","w",encoding="utf-8"), ensure_ascii=False)
import os
print("JSON bytes:", os.path.getsize("data.json"))
# distributions
for name in ["笔试高频词汇","听力高频词汇","旧题词汇参考"]:
    rows = out[name]["rows"]
    print("--", name)
    print(" 词性:", collections.Counter(r.get("词性／类别") for r in rows).most_common())
    print(" 频次:", sorted(collections.Counter(r.get("考试频次") for r in rows).items(), key=lambda x: -int(x[0])))
    print(" max excerpt len:", max(len(str(r.get("原文摘录（含选项）",""))) for r in rows))
for name in ["笔试语法考点","听力考点统计","听力语法表达"]:
    rows = out[name]["rows"]
    print("--", name, "频次:", sorted(collections.Counter(r.get("考试频次") for r in rows).items(), key=lambda x: -int(x[0])))
for name in ["语法逐题明细","听力逐题明细"]:
    rows = out[name]["rows"]
    print("--", name, "年月:", sorted(collections.Counter(r.get("考试年月") for r in rows).items()))
    print("  考点 unique:", len(set(r.get("日语考点") or r.get("考点") for r in rows)))
    print("  状态:", collections.Counter(r.get("识别依据／状态") for r in rows).most_common(5))
    print("  max 摘录 len:", max(len(str(r.get("题目摘录") or r.get("对话摘录") or "")) for r in rows))
# types of 频次 values
print(type(out["笔试高频词汇"]["rows"][0]["考试频次"]))
