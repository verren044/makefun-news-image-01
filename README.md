# news-image-01 — THE WORLD, Friday 13 November 2026

Entry for [make.fun/bounty/news-image-01](https://make.fun/bounty/news-image-01)
— "Sum up 13 November's world news in one image", $250 USDC escrowed, ends
Sun 15 Nov 2026 03:00 WIB (Sat 14 Nov 20:00 UTC).

## Concept

The judge has no news feed, so the image itself must carry the news: a
newspaper front page — masthead + dateline + four illustrated panels, each
with a headline and a picture of the story. The four stories are the ones
every 13 Nov 2026 briefing led with:

1. **Ukraine** — ~1,200 drones fired at Russia; Europe joins the peace talks.
2. **Hormuz** — tankers struck in the Strait; US downs Iranian drones.
3. **Nvidia** — founder/CEO Jensen Huang resigns; stocks slip.
4. **Microsoft** — the global Microsoft 365 outage enters its second day.

Headlines use a hand-checked 5x7 bitmap font (every glyph verified as ASCII
art before use); scenes are bold flat shapes that read at ~300 px.

## How to run

Python 3.13, standard library only. No network, no randomness.

```sh
python3 main.py   # writes /output/entry.png (or $MAKEFUN_OUTPUT_DIR/entry.png)
```

## Validation (2026-11-14 ~07:45 WIB)

- PNG 46,895 bytes (< 1 MiB), 1024x1024.
- Two runs byte-identical (sha256
  `01f353697984f4851120944c899a0737d3369d3ec0a31fa370528c4a960c886f`).
- ~1.1 s/run (limit 60 s).
- Pixel spot-checks confirm the page: masthead ink, dateline, all four
  header strips, night sky + drones, tanker + sea, green chip + red arrow,
  cloud + "365" + red OFFLINE banner.

## Status

Entry complete and validated locally. GitHub repo + bundle + submission NOT
done — needs chief's go-ahead.
