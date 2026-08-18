#!/usr/bin/env python3
"""生成 index.html。

    python3 tools/build_page.py

注意：这个脚本会**整体覆盖** index.html。
日常只是改文字（姓名、日期、地点）的话，直接编辑 index.html 就行，不用跑这个。
只有在换照片、改分组、调整页面结构时才需要改下面的 CONTENT 再重新生成。
"""

import json
import os

# ──────────────────────────────────────────────────────────
# 内容配置
# ──────────────────────────────────────────────────────────

SITE_URL = "https://aotaiyi.github.io/wedding/"

COUPLE = {
    "groom": "李文祥",
    "bride": "武宇峰",
}

WEDDING = {
    "kicker": "婚礼请柬",
    "date_dot": "2026.09.12",
    "date_cn": "公历二〇二六年九月十二日",
    # 农历经 lunardate 与 zhdate 两个库交叉验证：2026-09-12 = 丙午年八月初二，星期六
    "lunar": "农历丙午年八月初二",
    "weekday": "星期六",
    "hall": "朔州市朔城区艺龙万国酒店",
    "room": "奥斯卡厅",
    "venue": "朔州市朔城区艺龙万国酒店 · 奥斯卡厅",
    "ceremony": "11:50",  # 开礼
    "banquet": "12:18",  # 开席
    # 开喜门。地点与婚礼同址，页面上不再重复一遍场地名
    "ximen_time": "九月十一日 晚 19:00",
    # 详细地址就是酒店名本身，与上方场地完全重复，所以不在页面上单独列一行，
    # 只用于「复制地址」按钮。若日后拿到具体街道门牌，填在这里就会自动显示出来。
    "address": "",
    "copy_text": "朔州市朔城区艺龙万国酒店 · 奥斯卡厅",
    # 用关键词搜索而不是写死经纬度：酒店的精确坐标我无从得知，
    # 编一个坐标会让导航指到错误位置，比留占位更糟。
    # 拿到精确坐标后可换成 https://uri.amap.com/marker?position=经度,纬度&name=...
    "amap": "https://uri.amap.com/search?keyword=%E6%9C%94%E5%B7%9E%E8%89%BA%E9%BE%99%E4%B8%87%E5%9B%BD%E9%85%92%E5%BA%97&city=%E6%9C%94%E5%B7%9E%E5%B8%82",
}

SHARE = {
    "title": "李文祥 & 武宇峰 婚礼请柬",
    "desc": "2026.09.12 农历八月初二　朔州艺龙万国酒店 · 奥斯卡厅　敬备喜筵，恭请光临。",
}

# 章节：标题、副题、封面图、封面焦点、照片列表
CHAPTERS = [
    {
        "no": "CHAPTER ONE",
        "title": "开篇 · 中式",
        "sub": "一袭红妆，一诺千金。故事从这里开始。",
        # 这组是横构图棚拍，人物分居画面两侧，竖屏裁切会切掉一个人，
        # 所以用宣纸衬底 + 完整照片的方式呈现。
        "style": "paper",
        "plate": "0.2",
        "photos": ["0.2", "0", "0.1"],
    },
    {
        "no": "CHAPTER TWO",
        "title": "日常 · 生活",
        "sub": "异乡的街道、河畔的黄昏，还有我们的 Kolen。",
        "cover": "1.1",
        "focus": "50% 40%",
        "photos": ["1.1", "1.2", "1.3", "1.4", "1.5"],
    },
    {
        "no": "CHAPTER THREE",
        "title": "此时 · 浪漫",
        "sub": "白墙、蓝窗、拱廊与海。我们在地中海边说好了余生。",
        "cover": "2.5",
        "focus": "52% 38%",
        "photos": ["2", "2.1", "2.2", "2.3", "2.4", "2.5", "2.6", "2.7"],
    },
    {
        "no": "CHAPTER FOUR",
        "title": "回归 · 平凡",
        "sub": "脱下礼服，只是两个在旧街巷里贪玩的人。",
        "cover": "3.2",
        "focus": "50% 42%",
        "photos": ["3", "3.1", "3.2", "3.3", "3.4", "3.5"],
    },
]

HERO = {"img": "0.2", "focus": "50% 40%"}
OUTRO = {"img": "2", "focus": "50% 62%"}

# ──────────────────────────────────────────────────────────

HEAD = """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no,viewport-fit=cover">
<meta name="theme-color" content="#1c1917">
<meta name="format-detection" content="telephone=no">

<!-- 【微信分享卡片】标题取自 <title>，描述取自 description，缩略图取自 og:image -->
<title>{share_title}</title>
<meta name="description" content="{share_desc}">
<meta property="og:type" content="website">
<meta property="og:title" content="{share_title}">
<meta property="og:description" content="{share_desc}">
<meta property="og:image" content="{site}img/share.jpg">
<meta property="og:url" content="{site}">
<link rel="icon" href="img/share.jpg">

<link rel="preload" as="image" href="img/lg/{hero}.webp" type="image/webp">
<link rel="stylesheet" href="assets/css/style.css">
</head>
<body>

<!-- 启幕 -->
<div id="curtain"><div class="curtain-seal">囍</div></div>

<!-- 背景音乐：把文件放到 assets/audio/bgm.mp3 即可；没有文件时按钮会自动隐藏 -->
<audio id="bgm" src="assets/audio/bgm.mp3" loop preload="auto" playsinline webkit-playsinline></audio>
<button id="music" class="muted" aria-label="播放音乐">
  <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3v10.55A4 4 0 1 0 14 17V7h4V3h-6z"/></svg>
</button>

<nav id="dots" aria-hidden="true"></nav>

<main class="deck">
"""

FOOT = """</main>

<!-- 灯箱 -->
<div id="lightbox" role="dialog" aria-label="照片查看">
  <button id="lb-close" aria-label="关闭">&times;</button>
  <div id="lb-track"></div>
  <div id="lb-count"></div>
</div>

<script src="assets/js/main.js"></script>
</body>
</html>
"""


def bg(name, focus, lqip, eager=False):
    """全幅背景图，WebP 优先，带模糊占位。"""
    loading = "eager" if eager else "lazy"
    fetch = ' fetchpriority="high"' if eager else ""
    return f"""    <div class="bg" style="--focus:{focus}">
      <picture>
        <source srcset="img/lg/{name}.webp" type="image/webp">
        <img src="img/lg/{name}.jpg" alt="" loading="{loading}"{fetch}
             style="background:url({lqip}) center/cover">
      </picture>
    </div>"""


def strip(photos, lqips):
    items = []
    for p in photos:
        items.append(
            f"""        <button type="button" data-full="img/lg/{p}.jpg" data-alt="婚纱照 {p}">
          <img src="img/sm/{p}.jpg" alt="婚纱照 {p}" loading="lazy"
               style="background-image:url({lqips[p]['lqip']})">
        </button>"""
        )
    return "\n".join(items)


def main():
    with open("img/lqip.json", encoding="utf-8") as f:
        lq = json.load(f)

    out = [
        HEAD.format(
            share_title=SHARE["title"],
            share_desc=SHARE["desc"],
            site=SITE_URL,
            hero=HERO["img"],
        )
    ]

    # ── 封面 ──
    h = HERO["img"]
    out.append(
        f"""
  <!-- ═══ 1. 封面 ═══ 【改这里】新人姓名、日期、地点 -->
  <section class="scene cover">
    <div class="cover-photo" style="--focus:{HERO['focus']}">
      <picture>
        <source srcset="img/lg/{h}.webp" type="image/webp">
        <img src="img/lg/{h}.jpg" alt="新人合影" fetchpriority="high"
             style="background:url({lq[h]['lqip']}) center/cover">
      </picture>
    </div>
    <div class="seal">囍</div>
    <div class="cover-card">
      <p class="kicker rise"><span>{WEDDING['kicker']}</span></p>
      <h1 class="names rise">{COUPLE['groom']}<span class="amp">&amp;</span>{COUPLE['bride']}</h1>
      <div class="rule rise"></div>
      <p class="date rise">{WEDDING['date_dot']}</p>
      <p class="place rise">{WEDDING['venue']}</p>
      <div class="hint"><i></i><span>下滑</span></div>
    </div>
  </section>
"""
    )

    # ── 邀请函 ──
    # 地址只在填了内容时才输出，避免空标签留下一段空白
    addr_row = (
        f'\n      <p class="row-sub">{WEDDING["address"]}</p>'
        if WEDDING["address"]
        else ""
    )
    out.append(
        f"""
  <!-- ═══ 2. 邀请函 ═══ 【改这里】邀请文案、开礼/开席/喜门时间 -->
  <section class="scene paper invite">
    <div class="frame"></div>
    <h2 class="vtitle rise"><span>邀</span><span>请</span><span>函</span></h2>
    <div class="invite-body rise">
      <p>
        谨定于<br>
        <strong>{WEDDING['date_cn']}</strong><br>
        {WEDDING['lunar']}　{WEDDING['weekday']}
      </p>
      <p>
        <strong>{WEDDING['hall']}</strong><br>
        <strong>{WEDDING['room']}</strong>
      </p>
      <p>
        为 <b>{COUPLE['groom']}</b> 先生<br>
        与 <b>{COUPLE['bride']}</b> 女士<br>
        举行结婚典礼
      </p>
      <p class="salute">敬备喜筵　恭请光临</p>
    </div>
    <div class="invite-detail rise">
      <p class="row">
        <span class="lab">开礼</span><b>{WEDDING['ceremony']}</b>
        <i></i>
        <span class="lab">开席</span><b>{WEDDING['banquet']}</b>
      </p>
      <p class="row">
        <span class="lab">喜门</span><b>{WEDDING['ximen_time']}</b>
      </p>{addr_row}
    </div>
    <div class="actions rise">
      <a class="btn solid" href="{WEDDING['amap']}" target="_blank" rel="noopener">地图导航</a>
      <button class="btn" type="button" data-copy="{WEDDING['copy_text']}">复制地址</button>
    </div>
  </section>
"""
    )

    # ── 章节 ──
    for i, c in enumerate(CHAPTERS, start=3):
        paper = c.get("style") == "paper"
        if paper:
            p = c["plate"]
            backdrop = '    <div class="frame"></div>'
            plate = f"""    <div class="plate rise">
      <picture>
        <source srcset="img/lg/{p}.webp" type="image/webp">
        <img src="img/lg/{p}.jpg" alt="{c['title']}" loading="lazy"
             style="background:url({lq[p]['lqip']}) center/cover">
      </picture>
    </div>
"""
        else:
            backdrop = bg(c["cover"], c["focus"], lq[c["cover"]]["lqip"])
            plate = ""

        out.append(
            f"""
  <!-- ═══ {i}. {c['title']} ═══ -->
  <section class="scene chapter{' paper' if paper else ''}">
{backdrop}
{plate}    <div class="chapter-head">
      <p class="chapter-no rise">{c['no']}</p>
      <h2 class="chapter-title rise">{c['title']}</h2>
      <p class="chapter-sub rise">{c['sub']}</p>
    </div>
    <div class="chapter-foot rise">
      <p class="strip-note">轻触查看大图 · 共 {len(c['photos'])} 张</p>
      <div class="strip">
{strip(c['photos'], lq)}
      </div>
    </div>
  </section>
"""
        )

    # ── 结尾 ──
    # 原本独立的「婚礼信息」一屏已并入第 2 屏邀请函：
    # 日期、农历、星期、开礼、开席、喜门、场地在两屏之间完全重复，
    # 真正独有的只是详细地址和三个操作按钮。
    out.append(
        f"""
  <!-- ═══ 7. 结尾 ═══ -->
  <section class="scene outro">
{bg(OUTRO['img'], OUTRO['focus'], lq[OUTRO['img']]['lqip'])}
    <p class="word rise">敬候光临</p>
    <p class="who rise">{COUPLE['groom']}　{COUPLE['bride']}</p>
  </section>
"""
    )

    out.append(FOOT)

    html = "".join(out)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

    n = sum(len(c["photos"]) for c in CHAPTERS)
    print(f"index.html 已生成：{len(CHAPTERS) + 3} 屏，{n} 张照片，{len(html) / 1024:.0f} KB")


if __name__ == "__main__":
    main()
