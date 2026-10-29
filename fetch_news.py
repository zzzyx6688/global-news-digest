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


def render(items):
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

    md = render(result)

    out_path = os.path.join(DOCS_DIR, output_file)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"[ok] 已生成日报: {out_path} ({len(md)} 字符)")


if __name__ == "__main__":
    main()
