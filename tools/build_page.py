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
    "groom": "新郎姓名",
    "bride": "新娘姓名",
    "groom_en": "GROOM",
    "bride_en": "BRIDE",
}

WEDDING = {
    "date_dot": "2026.10.01",
    "date_cn": "公历 二〇二六年十月一日",
    "lunar": "农历 丙午年八月廿一",
    "weekday": "星期四",
    "time": "中午 12:00 恭候  12:30 入席",
    "venue": "酒店名称 · 宴会厅名称",
    "address": "省份 城市 区县 某某路 123 号",
    "amap": "https://uri.amap.com/marker?position=116.397428,39.90923&name=%E5%A9%9A%E7%A4%BC%E5%9C%BA%E5%9C%B0",
    "phone": "13800138000",
}

SHARE = {
    "title": "我们要结婚啦 · 诚邀您见证",
    "desc": "2026.10.01　从中国到德国，再到地中海的海边——这一天，我们想和您一起度过。",
}

# 章节：标题、副题、封面图、封面焦点、照片列表
CHAPTERS = [
    {
        "no": "CHAPTER ONE",
        "title": "缘起 · 中国",
        "sub": "一袭红妆，一诺千金。故事从这里开始。",
        # 这组是横构图棚拍，人物分居画面两侧，竖屏裁切会切掉一个人，
        # 所以用宣纸衬底 + 完整照片的方式呈现。
        "style": "paper",
        "plate": "0",
        "photos": ["0", "0.1"],
    },
    {
        "no": "CHAPTER TWO",
        "title": "日常 · 德国",
        "sub": "异乡的街道、河畔的黄昏，还有一只跟前跟后的柯基。",
        "cover": "1.1",
        "focus": "50% 40%",
        "photos": ["1.1", "1.2", "1.3", "1.4"],
    },
    {
        "no": "CHAPTER THREE",
        "title": "誓约 · 巴塞罗那",
        "sub": "白墙、蓝窗、拱廊与海。我们在地中海边说好了余生。",
        "cover": "2.5",
        "focus": "52% 38%",
        "photos": ["2", "2.1", "2.2", "2.3", "2.4", "2.5", "2.6", "2.7"],
    },
    {
        "no": "CHAPTER FOUR",
        "title": "漫游 · 老城",
        "sub": "脱下礼服，只是两个在旧街巷里贪玩的人。",
        "cover": "3.2",
        "focus": "50% 42%",
        "photos": ["3", "3.1", "3.2", "3.3", "3.4", "3.5"],
    },
]

HERO = {"img": "0", "focus": "59% 34%"}
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
      <p class="kicker rise">We are getting married</p>
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
    out.append(
        f"""
  <!-- ═══ 2. 邀请函 ═══ 【改这里】邀请文案 -->
  <section class="scene paper">
    <div class="frame"></div>
    <h2 class="vtitle rise"><span>邀</span><span>请</span><span>函</span></h2>
    <div class="invite-body rise">
      谨定于<br>
      <strong>{WEDDING['date_cn']}</strong><br>
      {WEDDING['lunar']}　{WEDDING['weekday']}<br><br>
      假座 <strong>{WEDDING['venue']}</strong><br>
      为 <strong>{COUPLE['groom']}</strong> 先生<br>
      与 <strong>{COUPLE['bride']}</strong> 女士<br>
      举行结婚典礼<br><br>
      敬备喜筵　恭请光临
    </div>
    <p class="signature rise">— 敬邀 —</p>
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

    # ── 婚礼信息 ──
    out.append(
        f"""
  <!-- ═══ 7. 婚礼信息 ═══ 【改这里】时间、地址、导航链接、电话 -->
  <section class="scene paper info">
    <div class="frame"></div>
    <p class="big-date rise">{WEDDING['date_dot']}</p>
    <p class="weekday rise">{WEDDING['weekday']}　{WEDDING['lunar']}</p>
    <dl class="rise">
      <dt>时间</dt>
      <dd>{WEDDING['time']}</dd>
      <dt>地点</dt>
      <dd>{WEDDING['venue']}<small>{WEDDING['address']}</small></dd>
    </dl>
    <div class="actions rise">
      <a class="btn solid" href="{WEDDING['amap']}" target="_blank" rel="noopener">地图导航</a>
      <button class="btn" type="button" data-copy="{WEDDING['address']}">复制地址</button>
      <a class="btn" href="tel:{WEDDING['phone']}">联系我们</a>
    </div>
  </section>
"""
    )

    # ── 结尾 ──
    out.append(
        f"""
  <!-- ═══ 8. 结尾 ═══ -->
  <section class="scene outro">
{bg(OUTRO['img'], OUTRO['focus'], lq[OUTRO['img']]['lqip'])}
    <p class="word rise">敬候光临</p>
    <p class="who rise">{COUPLE['groom']}　{COUPLE['bride']}</p>
    <p class="tiny rise">{WEDDING['date_dot']}　{WEDDING['venue']}</p>
  </section>
"""
    )

    out.append(FOOT)

    html = "".join(out)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

    n = sum(len(c["photos"]) for c in CHAPTERS)
    print(f"index.html 已生成：{len(CHAPTERS) + 4} 屏，{n} 张照片，{len(html) / 1024:.0f} KB")


if __name__ == "__main__":
    main()
