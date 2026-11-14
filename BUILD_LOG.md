# news-image-01 — build log

- Started: 2026-11-14 ~07:40 WIB (00:40 UTC). Deadline: 2026-11-14T20:00:00Z
  (Sun 15 Nov 03:00 WIB).
- Kit: downloaded 2026-11-14 from https://make.fun/c/news-image-01/kit,
  unpacked to ~/workspace/makefun/kits/news-image-01/.
- Rules read: bounty page + competition.yaml. Entry: Python 3.13 main.py at
  repo root, stdlib only, no network, deterministic. Writes
  /output/entry.png (PNG/JPEG, <=1 MiB, <=1024x1024), runs twice, identical
  bytes. Judge has no news feed — it judges by what the image itself shows,
  as a careful picture editor would. Prize table: $50 / $20 / $10 / $5 x7 /
  $1.50 x90, top 100 share $250.
- Concept: newspaper front page "THE WORLD, FRIDAY 13 NOVEMBER 2026" with
  four illustrated panels — Ukraine drones + Europe at talks; tankers hit
  in Hormuz; Nvidia CEO quits; Microsoft 365 down day 2. Stories taken from
  the 13 Nov 2026 briefings (Raisina Post, Level Headlines, Open Chronicle,
  Zark News). Headlines in a hand-checked 5x7 bitmap font (all glyphs
  verified as ASCII art before use).
- Renderer: pure-stdlib Python PNG encoder (zlib + struct + CRC32); shapes
  painted into a pixel buffer (rects, ellipses, polygons, thick lines,
  radial glows). No PIL, no randomness.
- Validation (2026-11-14 ~07:45 WIB): PNG 46,895 bytes (<1 MiB),
  1024x1024. Two runs byte-identical (sha256
  01f353697984f4851120944c899a0737d3369d3ec0a31fa370528c4a960c886f),
  1.1 s/run (limit 60 s). Pixel spot-checks confirm the page (masthead,
  dateline, four header strips, drones + skyline, tanker + sea, green chip
  + red arrow, cloud + "365" + red OFFLINE banner).
- Status: entry complete and validated locally. Bundle + check and GitHub
  repo + submission NOT done — needs chief's go-ahead.
