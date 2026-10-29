# 全球新闻中文日报平台

每天定时自动聚合 **中国、欧美、俄罗斯、日韩** 及各大产业新闻,生成中文日报。

## 特性
- 🌍 覆盖区域:中国 / 欧美 / 俄罗斯 / 日韩
- 🏭 产业板块:科技AI、新能源、半导体、医药、金融、能源等
- ⏰ 每日 06:00(北京时间)自动更新
- 🆓 零服务器成本,全靠 GitHub Actions 免费定时运行
- 📄 输出 Markdown 日报,可直接托管为网页

## 如何修改数据源
编辑 `sources.yaml`:
- `regions`:按区域配置新闻源(Google News RSS 中文搜索)
- `industries`:产业新闻的关键词源
- `max_items_per_source`:每个源保留的条数

## 运行方式
### 本地测试
```bash
pip install -r requirements.txt
python fetch_news.py
# 生成 docs/index.md
```

### 自动定时(已配置)
`.github/workflows/daily.yml` 已配置每日自动运行并推送更新,
推送后即可用 **GitHub Pages** 免费把日报发布成网站:
仓库 Settings → Pages → Source 选 `main` 分支的 `/docs` 目录。

## 目录结构
```
news-digest/
├── sources.yaml          # 数据源配置(改这里)
├── fetch_news.py         # 抓取脚本
├── requirements.txt      # Python 依赖
├── docs/index.md         # 生成的日报
└── .github/workflows/daily.yml  # 每日定时任务
```
