"""Export <LEVEL>高频词汇与考点统计.xlsx to data.json.  Usage: python3 -I export.py N4"""
import openpyxl, json, os, sys
lv = (sys.argv[1] if len(sys.argv) > 1 else "N4").upper()
src = f"/Users/ireneli/Documents/2026Spring/日语材料/全部真题/{lv}高频词汇与考点统计.xlsx"
wb = openpyxl.load_workbook(src, data_only=True)
out = {"_level": lv, "_source": os.path.basename(src)}
for ws in wb.worksheets:
    rows = list(ws.iter_rows(values_only=True))
    title, subtitle = rows[0][0], rows[1][0]
    headers = [h for h in rows[4] if h is not None]
    data = []
    for r in rows[5:]:
        if all(c is None for c in r):
            continue
        rec = {}
        for h, c in zip(headers, r):
            if c is None:
                continue
            rec[h] = c if isinstance(c, (int, float)) else str(c).strip()
        data.append(rec)
    out[ws.title] = {"title": title, "subtitle": subtitle, "headers": headers, "rows": data}
    print(f"{ws.title}: {len(data)} rows")
json.dump(out, open("data.json", "w", encoding="utf-8"), ensure_ascii=False)
print("data.json bytes:", os.path.getsize("data.json"))
