#!/usr/bin/env python3
"""把 photo/ 里的原图转成网页用的压缩版，输出到 img/。

原图不会被修改。每次运行都会覆盖 img/ 下的产物，可重复执行。

    python3 tools/build_images.py

产物：
    img/lg/<name>.jpg   长边 1600，全屏展示用
    img/lg/<name>.webp  同上的 WebP（体积约小 30%）
    img/sm/<name>.jpg   长边 720，相册缩略图用
    img/sm/<name>.webp
    img/share.jpg       800x800 方图，微信分享卡片缩略图
    img/lqip.json       每张图 24px 的 base64 占位图，用于加载时的模糊过渡
"""

import base64
import io
import json
import os
import shutil
import sys

from PIL import Image, ImageOps

SRC = "photo"
OUT = "img"

LG_EDGE = 1600
SM_EDGE = 720
JPEG_Q_LG = 82
JPEG_Q_SM = 78
WEBP_Q_LG = 78
WEBP_Q_SM = 72
LQIP_EDGE = 24

# 分享卡片用哪张图，以及裁剪时以哪个点为中心（0~1 的相对坐标）
SHARE_SRC = "0.jpg"
SHARE_FOCUS = (0.62, 0.38)
SHARE_SIZE = 800


def sort_key(name):
    return [int(x) for x in os.path.splitext(name)[0].split(".")]


def load(path):
    im = Image.open(path)
    im = ImageOps.exif_transpose(im)
    return im.convert("RGB")


def fit(im, edge):
    w, h = im.size
    scale = edge / max(w, h)
    if scale >= 1:
        return im.copy()
    return im.resize((round(w * scale), round(h * scale)), Image.LANCZOS)


def square_crop(im, focus, size):
    w, h = im.size
    side = min(w, h)
    cx, cy = focus[0] * w, focus[1] * h
    left = min(max(cx - side / 2, 0), w - side)
    top = min(max(cy - side / 2, 0), h - side)
    box = im.crop((round(left), round(top), round(left + side), round(top + side)))
    return box.resize((size, size), Image.LANCZOS)


def lqip(im):
    small = fit(im, LQIP_EDGE)
    buf = io.BytesIO()
    small.save(buf, "JPEG", quality=40)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def main():
    if not os.path.isdir(SRC):
        sys.exit(f"找不到 {SRC}/ 目录，请在仓库根目录运行")

    names = sorted(
        (n for n in os.listdir(SRC) if n.lower().endswith((".jpg", ".jpeg"))),
        key=sort_key,
    )
    if not names:
        sys.exit(f"{SRC}/ 里没有找到 jpg 文件")

    for sub in ("lg", "sm"):
        shutil.rmtree(os.path.join(OUT, sub), ignore_errors=True)
        os.makedirs(os.path.join(OUT, sub), exist_ok=True)

    placeholders = {}
    total_src = total_out = 0

    for name in names:
        src = os.path.join(SRC, name)
        stem = os.path.splitext(name)[0]
        im = load(src)
        total_src += os.path.getsize(src)

        for sub, edge, jq, wq in (
            ("lg", LG_EDGE, JPEG_Q_LG, WEBP_Q_LG),
            ("sm", SM_EDGE, JPEG_Q_SM, WEBP_Q_SM),
        ):
            resized = fit(im, edge)
            jpg = os.path.join(OUT, sub, stem + ".jpg")
            webp = os.path.join(OUT, sub, stem + ".webp")
            resized.save(jpg, "JPEG", quality=jq, optimize=True, progressive=True)
            resized.save(webp, "WEBP", quality=wq, method=6)
            total_out += os.path.getsize(jpg) + os.path.getsize(webp)

        placeholders[stem] = {"lqip": lqip(im), "w": im.width, "h": im.height}
        print(f"  {name:<10} {im.width}x{im.height}")

    share_src = SHARE_SRC if SHARE_SRC in names else names[0]
    share = square_crop(load(os.path.join(SRC, share_src)), SHARE_FOCUS, SHARE_SIZE)
    share_path = os.path.join(OUT, "share.jpg")
    share.save(share_path, "JPEG", quality=85, optimize=True, progressive=False)
    total_out += os.path.getsize(share_path)

    with open(os.path.join(OUT, "lqip.json"), "w", encoding="utf-8") as f:
        json.dump(placeholders, f, ensure_ascii=False, indent=0)

    mb = 1024 * 1024
    print(f"\n{len(names)} 张：原图 {total_src / mb:.0f} MB → 网页版 {total_out / mb:.1f} MB")
    print(f"分享缩略图取自 {share_src}")


if __name__ == "__main__":
    main()
