# jlpt-n4-html

把 `全部真题/N4高频词汇与考点统计.xlsx` 做成手机端可按分类浏览的单文件 HTML。

在线地址（GitHub Pages）：https://irenezihuili.github.io/jlpt-n4-stats/

- `export.py`：读取 xlsx 的 10 个工作表，导出为 `data.json`
- `build.py`：把 `data.json` 嵌进页面模板，生成
  - `n4_page.html`：Artifact 发布用（无 doctype/head 骨架）
  - `N4高频词汇与考点统计.html`：独立可离线打开的完整 HTML（已复制到 `全部真题/`）
  - `index.html`：同上，GitHub Pages 用的副本

重新生成：

```bash
python3 -I export.py && python3 -I build.py
```

然后 `cp N4高频词汇与考点统计.html index.html`，提交推送即自动更新 Pages；同时把它复制回 `全部真题/`，并用 Artifact 工具以同一 URL 重新发布 `n4_page.html`。
