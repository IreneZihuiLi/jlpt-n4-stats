# jlpt-n4-stats

把 `全部真题/N4高频词汇与考点统计.xlsx` 做成手机端可按分类浏览的单文件 HTML。

在线地址（GitHub Pages）：https://irenezihuili.github.io/jlpt-n4-stats/

- `export.py`：读取 xlsx 的全部工作表，导出为 `data.json`（`python3 -I export.py N4`）
- `build.py`：把 `data.json` 嵌进页面模板，生成
  - `index.html` / `N4高频词汇与考点统计.html`：独立可离线打开的完整页面（前者给 GitHub Pages，后者复制到 `全部真题/`）
  - `n4_page.html`：无 doctype/head 骨架的版本，供 Claude Artifact 发布

重新生成：

```bash
python3 -I export.py N4 && python3 -I build.py
```

提交并推送 `index.html` 即自动更新 Pages。脚本在 N2/N3/N4 三个仓库中相同，改动请同步。
