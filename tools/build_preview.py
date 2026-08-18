#!/usr/bin/env python3
"""把 index.html 打包成一个自包含的单文件，用于发布预览链接。

    python3 tools/build_preview.py

CSS、JS、全部照片和背景音乐都内联进去（照片转成 WebP 的 data URI），
生成的文件不依赖任何外部资源，随便丢到哪都能打开。

音频缺失时会自动去掉音乐按钮，不留一个点不动的按钮。
"""

import base64
import os
import re

OUT = "/tmp/claude-0/-home-user-wedding/1881ba2a-95da-545d-8eb5-4a8d28a911fd/scratchpad/preview.html"
TITLE = "从中国到地中海"


AUDIO = "assets/audio/bgm.mp3"


def data_uri(path, mime="image/webp"):
    with open(path, "rb") as f:
        return f"data:{mime};base64," + base64.b64encode(f.read()).decode()


def main():
    html = open("index.html", encoding="utf-8").read()
    css = open("assets/css/style.css", encoding="utf-8").read()
    js = open("assets/js/main.js", encoding="utf-8").read()

    # 只取 <body> 里的内容：Artifact 会自己包 doctype/html/head/body
    body = html.split("<body>", 1)[1].rsplit("</body>", 1)[0]

    # 外链的 script 标签换成文末内联，避免残留一个取不到的相对路径
    body = re.sub(r"\s*<script src=\"assets/js/main\.js\"></script>\n?", "", body)

    # 背景音乐一并内联；没有音频文件时才去掉音频元素和音乐按钮
    if os.path.exists(AUDIO):
        body = body.replace(f'src="{AUDIO}"', f'src="{data_uri(AUDIO, "audio/mpeg")}"')
    else:
        body = re.sub(r"<audio id=\"bgm\".*?</audio>\n?", "", body, flags=re.S)
        body = re.sub(r"<button id=\"music\".*?</button>\n?", "", body, flags=re.S)

    # <source> 里的 WebP 和 <img> 里的 JPG 指向同一张图，
    # 全部收敛到 WebP 一份，避免同一张图在文件里出现两次
    body = re.sub(r"\s*<source srcset=\"[^\"]+\" type=\"image/webp\">\n?", "", body)

    cache = {}

    def uri(size, name):
        key = (size, name)
        if key not in cache:
            cache[key] = data_uri(f"img/{size}/{name}.webp")
        return cache[key]

    body = re.sub(
        r'src="img/(lg|sm)/([^"]+)\.jpg"',
        lambda m: f'src="{uri(m.group(1), m.group(2))}"',
        body,
    )
    body = re.sub(
        r'data-full="img/lg/([^"]+)\.jpg"',
        lambda m: f'data-full="{uri("lg", m.group(1))}"',
        body,
    )

    doc = (
        f"<title>{TITLE}</title>\n"
        f"<style>\n{css}\n</style>\n"
        f"{body}\n"
        f"<script>\n{js}\n</script>\n"
    )

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(doc)

    left = re.findall(r'(?:src|srcset|href)="(?!data:|#)([^"]+)"', doc)
    audio = "，含背景音乐" if os.path.exists(AUDIO) else "，无音频"
    print(f"{OUT}  {len(doc) / 1048576:.1f} MB，内联 {len(cache)} 张图{audio}")
    print("残留的外部引用:", left or "无")


if __name__ == "__main__":
    main()
