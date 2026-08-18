# 背景音乐 bgm.mp3

当前文件：**2.7 MB / 2:57**，128 kbps CBR 立体声 44.1 kHz。

两段钢琴独奏各取前 90 秒，3 秒交叉淡化拼成一条循环：

| 段落 | 出处 | 区间 |
|---|---|---|
| 1 | Beethoven Sonate op. 109 | 0:00 – 1:30 |
| 2 | Brahms Klavierstücke op. 118 | 0:00 – 1:30 |

首段 1.5 秒淡入、末尾 3 秒淡出，避免循环接缝突兀。

## 重新生成

源 WAV 在仓库根的 `music/`（24-bit/48 kHz，共 664 MB），已被 `.gitignore` 排除，只存本地。
需要 ffmpeg（含 libmp3lame）。改区间就改两处 `atrim` 的起止秒数：

```bash
ffmpeg -y \
  -i "music/Beethoven Sonate op.109 - V2.wav" \
  -i "music/Brahms Klavierstücke op.118.wav" \
  -filter_complex "\
[0:a]atrim=0:90,asetpts=N/SR/TB,afade=t=in:st=0:d=1.5[a0];\
[1:a]atrim=0:90,asetpts=N/SR/TB[a1];\
[a0][a1]acrossfade=d=3:c1=tri:c2=tri[m];\
[m]afade=t=out:st=174:d=3[o]" \
  -map "[o]" -ar 44100 -ac 2 -c:a libmp3lame -b:a 128k \
  -map_metadata -1 -id3v2_version 3 \
  assets/audio/bgm.mp3
```

总长 = 两段之和 − 交叉淡化时长（90 + 90 − 3 = 177 秒）。
`afade=t=out` 的 `st` 必须等于总长 − 3，改时长时记得一起改。

## 体积参考

128 kbps ≈ 0.94 MB/分钟。GitHub 单文件硬上限 100 MB，这里离得很远；
因为 `preload="none"` 不阻塞首屏，体积主要影响流量而非打开速度。

音乐版权请自行确认。
