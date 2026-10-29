#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全球新闻中文日报 - 抓取脚本
遍历 sources.yaml 中的数据源,抓取 RSS,按区域/产业分组,生成 Markdown 日报。
依赖: pip install feedparser pyyaml requests
"""
import os
import sys
import time
from datetime import datetime, timezone, timedelta

import feedparser
import yaml
import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CFG_PATH = os.path.join(BASE_DIR, "sources.yaml")
DOCS_DIR = os.path.join(BASE_DIR, "docs")

# 中国时区
CN_TZ = timezone(timedelta(hours=8))
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) NewsDigest/1.0"


def load_config():
    with open(CFG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def fetch_feed(url, timeout=15, retries=2):
    """抓取单个 RSS,带重试,返回条目列表。"""
    for attempt in range(retries + 1):
        try:
            resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=timeout)
            resp.raise_for_status()
            feed = feedparser.parse(resp.content)
            return feed.entries
        except Exception as e:
            print(f"[warn] 抓取失败 {url} (第{attempt+1}次): {e}")
            if attempt < retries:
                time.sleep(2)
    return []


def normalize_entry(entry, max_items):
    """提取标题+链接,最多保留 max_items 条。"""
    items = []
    for e in entry:
        title = getattr(e, "title", "").strip()
        link = getattr(e, "link", "").strip()
        if title and link:
            items.append({"title": title, "link": link})
        if len(items) >= max_items:
            break
    return items


def render_md(items):
    """把 (区域/产业, 源名, 新闻列表) 渲染为 Markdown。"""
    now = datetime.now(CN_TZ)
    lines = []
    lines.append(f"# 全球新闻中文日报")
    lines.append(f"")
    lines.append(f"> 更新时间：{now.strftime('%Y-%m-%d %H:%M')} (北京时间) | 自动生成")
    lines.append(f"")

    for group_key, sources in items:
        lines.append(f"## {group_key}")
        lines.append(f"")
        for src_name, news in sources:
            lines.append(f"### {src_name}")
            lines.append(f"")
            for n in news:
                lines.append(f"- [{n['title']}]({n['link']})")
            lines.append(f"")

    lines.append(f"---")
    lines.append(f"*本日报由自动化脚本每日定时生成,数据来源为公开新闻 RSS。*")
    return "\n".join(lines)


def render_html(items):
    """把新闻数据渲染为美观的 HTML 网页版日报。"""
    now = datetime.now(CN_TZ)
    sections = []
    for group_key, sources in items:
        cards = []
        for src_name, news in sources:
            items_html = ""
            if news:
                items_html = "<ul>" + "".join(
                    f'<li><a href="{n["link"]}" target="_blank" rel="noopener">{n["title"]}</a></li>'
                    for n in news
                ) + "</ul>"
            else:
                items_html = '<p class="empty">该源本次未抓取到内容(可能为网络波动,下次自动重试)</p>'
            cards.append(
                f'<div class="src-card"><h3>{src_name}</h3>{items_html}</div>'
            )
        sections.append(
            f'<section><h2>{group_key}</h2><div class="cards">{chr(10).join(cards)}</div></section>'
        )

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>全球新闻中文日报 · {now.strftime('%Y-%m-%d')}</title>
<style>
  :root {{ --bg:#0f172a; --card:#1e293b; --text:#e2e8f0; --muted:#94a3b8; --accent:#38bdf8; }}
  * {{ box-sizing:border-box; margin:0; padding:0; }}
  body {{ background:var(--bg); color:var(--text); font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif; line-height:1.6; }}
  .wrap {{ max-width:960px; margin:0 auto; padding:24px 16px 60px; }}
  header {{ padding:20px 0 8px; border-bottom:2px solid var(--accent); margin-bottom:24px; }}
  h1 {{ font-size:1.6rem; letter-spacing:1px; }}
  .meta {{ color:var(--muted); font-size:.85rem; margin-top:6px; }}
  section {{ margin-bottom:28px; }}
  h2 {{ font-size:1.15rem; color:var(--accent); margin-bottom:12px; padding-left:10px; border-left:4px solid var(--accent); }}
  .cards {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(280px,1fr)); gap:14px; }}
  .src-card {{ background:var(--card); border-radius:10px; padding:14px 16px; }}
  .src-card h3 {{ font-size:.95rem; color:#fbbf24; margin-bottom:10px; }}
  ul {{ list-style:none; }}
  li {{ padding:6px 0; border-bottom:1px dashed #334155; }}
  li:last-child {{ border-bottom:none; }}
  a {{ color:var(--text); text-decoration:none; font-size:.9rem; }}
  a:hover {{ color:var(--accent); }}
  .empty {{ color:var(--muted); font-size:.85rem; }}
  footer {{ margin-top:36px; padding-top:16px; border-top:1px solid #334155; color:var(--muted); font-size:.8rem; text-align:center; }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>🌍 全球新闻中文日报</h1>
    <p class="meta">更新时间：{now.strftime('%Y-%m-%d %H:%M')}（北京时间）· 覆盖中国 / 欧美 / 俄罗斯 / 日韩 + 六大产业</p>
  </header>
  {chr(10).join(sections)}
  <footer>本日报由自动化脚本每日定时生成，数据来源为公开新闻 RSS。· 自动更新</footer>
</div>
</body>
</html>"""
    return html


def main():
    cfg = load_config()
    max_items = cfg.get("max_items_per_source", 6)
    output_file = cfg.get("output_file", "index.md")

    os.makedirs(DOCS_DIR, exist_ok=True)

    result = []

    # 地域新闻
    for region, sources in cfg.get("regions", {}).items():
        grouped = []
        for src in sources:
            entries = fetch_feed(src["url"])
            news = normalize_entry(entries, max_items)
            grouped.append((src["name"], news))
        result.append((region, grouped))

    # 产业新闻
    for ind, urls in cfg.get("industries", {}).items():
        grouped = []
        for i, url in enumerate(urls):
            entries = fetch_feed(url)
            news = normalize_entry(entries, max_items)
            grouped.append((f"产业源{i+1}", news))
        result.append((ind, grouped))

    md = render_md(result)
    html = render_html(result)

    md_path = os.path.join(DOCS_DIR, output_file)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md)

    html_path = os.path.join(DOCS_DIR, "index.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[ok] 已生成日报: {md_path} ({len(md)} 字符)")
    print(f"[ok] 已生成网页: {html_path} ({len(html)} 字符)")


if __name__ == "__main__":
    main()