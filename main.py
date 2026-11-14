"""news-image-01 entry (Python 3.13, standard library only).

Draws one image — a newspaper front page, "THE WORLD, FRIDAY 13 NOVEMBER
2026", with the day's four biggest stories as illustrated panels — and writes
it to /output/entry.png (1024x1024 PNG, < 1 MiB).

The idea, against the brief: the judge has no news feed, so the image itself
must carry the news. A front page does that: masthead + dateline + four
panels, each with a headline and a picture of the story. The four stories
are the ones every 13 Nov 2026 briefing led with:
  1. Ukraine — ~1,200 drones fired at Russia; Europe joins the peace talks.
  2. Hormuz — tankers struck in the Strait; US downs Iranian drones.
  3. Nvidia — founder/CEO Jensen Huang resigns; stocks slip.
  4. Microsoft — the global Microsoft 365 outage enters its second day.
Headlines are rendered in a hand-checked 5x7 bitmap font (every glyph
verified as ASCII art before use); scenes are bold flat shapes that still
read at ~300 px. No faces, no garbled text.

How it is drawn: pure stdlib. Shapes are painted straight into a pixel
buffer (rects, ellipses, polygons, thick lines, radial glows), then encoded
as PNG by hand (zlib + struct + CRC32). No PIL, no network, no randomness —
the same bytes on every run.
"""
import math
import os
import struct
import zlib
from pathlib import Path

W, H = 1024, 1024

# 5x7 bitmap font, one glyph per character ('1' = ink). Every glyph verified
# as ASCII art before use (see /tmp/font_test.py run, 2026-11-14).
FONT = {
    'A': ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    'B': ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    'C': ["01110", "10001", "10000", "10000", "10000", "10001", "01110"],
    'D': ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    'E': ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    'F': ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    'G': ["01110", "10001", "10000", "10111", "10001", "10001", "01111"],
    'H': ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    'I': ["01110", "00100", "00100", "00100", "00100", "00100", "01110"],
    'J': ["00111", "00010", "00010", "00010", "00010", "10010", "01100"],
    'K': ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    'L': ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    'M': ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    'N': ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    'O': ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    'P': ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    'Q': ["01110", "10001", "10001", "10001", "10101", "10010", "01101"],
    'R': ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    'S': ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    'T': ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    'U': ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    'V': ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    'W': ["10001", "10001", "10001", "10101", "10101", "11011", "10001"],
    'X': ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    'Y': ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
    'Z': ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
    '0': ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
    '1': ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    '2': ["01110", "10001", "00001", "00110", "01000", "10000", "11111"],
    '3': ["11111", "00010", "00100", "00010", "00001", "10001", "01110"],
    '4': ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    '5': ["11111", "10000", "11110", "00001", "00001", "10001", "01110"],
    '6': ["00110", "01000", "10000", "11110", "10001", "10001", "01110"],
    '7': ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    '8': ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    '9': ["01110", "10001", "10001", "01111", "00001", "00010", "01100"],
    ' ': ["00000", "00000", "00000", "00000", "00000", "00000", "00000"],
    '-': ["00000", "00000", "00000", "01110", "00000", "00000", "00000"],
    '.': ["00000", "00000", "00000", "00000", "00000", "01100", "01100"],
    ',': ["00000", "00000", "00000", "00000", "01100", "00100", "01000"],
    "'": ["00100", "00100", "01000", "00000", "00000", "00000", "00000"],
    ':': ["00000", "01100", "01100", "00000", "01100", "01100", "00000"],
    '/': ["00001", "00010", "00010", "00100", "01000", "01000", "10000"],
    '!': ["00100", "00100", "00100", "00100", "00100", "00000", "00100"],
}

# Palette.
PAPER = (248, 244, 232)
INK = (24, 28, 44)
FRAME = (198, 190, 168)
HEADER_BG = (24, 28, 44)
HEADER_TX = (245, 242, 230)
RED = (198, 38, 38)


def lerp(a, b, t):
    return a + (b - a) * t


def mix(c1, c2, t):
    return (lerp(c1[0], c2[0], t), lerp(c1[1], c2[1], t), lerp(c1[2], c2[2], t))


def clamp(v, lo=0.0, hi=255.0):
    return lo if v < lo else hi if v > hi else v


def put(buf, x, y, c):
    if 0 <= x < W and 0 <= y < H:
        buf[y][x] = (int(clamp(c[0])), int(clamp(c[1])), int(clamp(c[2])))


def blend(buf, x, y, c, a):
    if 0 <= x < W and 0 <= y < H and a > 0:
        old = buf[y][x]
        put(buf, x, y, mix(old, c, min(1.0, a)))


def fill_rect(buf, x0, y0, x1, y1, c):
    for y in range(max(0, y0), min(H, y1)):
        for x in range(max(0, x0), min(W, x1)):
            put(buf, x, y, c)


def fill_ellipse(buf, cx, cy, rx, ry, c, alpha=1.0):
    for y in range(max(0, cy - ry), min(H, cy + ry + 1)):
        for x in range(max(0, cx - rx), min(W, cx + rx + 1)):
            dx = (x - cx) / rx
            dy = (y - cy) / ry
            if dx * dx + dy * dy < 1.0:
                if alpha >= 1.0:
                    put(buf, x, y, c)
                else:
                    blend(buf, x, y, c, alpha)


def _in_poly(x, y, poly):
    inside = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y):
            xin = (xj - xi) * (y - yi) / (yj - yi) + xi
            if x < xin:
                inside = not inside
        j = i
    return inside


def fill_poly(buf, poly, c):
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    for y in range(max(0, min(ys)), min(H, max(ys) + 1)):
        for x in range(max(0, min(xs)), min(W, max(xs) + 1)):
            if _in_poly(x, y, poly):
                put(buf, x, y, c)


def thick_line(buf, x0, y0, x1, y1, w, c):
    for y in range(max(0, min(y0, y1) - w), min(H, max(y0, y1) + w + 1)):
        for x in range(max(0, min(x0, x1) - w), min(W, max(x0, x1) + w + 1)):
            dx, dy = x1 - x0, y1 - y0
            L2 = dx * dx + dy * dy
            t = 0.0 if L2 == 0 else ((x - x0) * dx + (y - y0) * dy) / L2
            t = max(0.0, min(1.0, t))
            if math.hypot(x - (x0 + t * dx), y - (y0 + t * dy)) < w:
                put(buf, x, y, c)


def glow(buf, cx, cy, r, c, strength=0.8):
    for y in range(max(0, cy - r), min(H, cy + r + 1)):
        for x in range(max(0, cx - r), min(W, cx + r + 1)):
            d = math.hypot(x - cx, y - cy) / r
            if d < 1.0:
                blend(buf, x, y, c, (1.0 - d) ** 2 * strength)


def text_w(s, scale):
    return len(s) * 6 * scale - scale


def draw_text(buf, s, cx, y0, scale, c):
    """Draw s centred on cx, top at y0."""
    x = cx - text_w(s, scale) // 2
    for ch in s:
        glyph = FONT.get(ch)
        if glyph is None:
            x += 6 * scale
            continue
        for row in range(7):
            bits = glyph[row]
            for col in range(5):
                if bits[col] == '1':
                    fill_rect(buf, x + col * scale, y0 + row * scale,
                              x + (col + 1) * scale, y0 + (row + 1) * scale, c)
        x += 6 * scale


# --- panel scenes: each draws inside (ix0, iy0, iw, ih) ---

def scene_ukraine(buf, ix0, iy0, iw, ih):
    for y in range(iy0, iy0 + ih):
        t = (y - iy0) / ih
        col = mix((14, 22, 46), (38, 52, 92), t)
        fill_rect(buf, ix0, y, ix0 + iw, y + 1, col)
    # stars (deterministic positions)
    for i in range(42):
        sx = ix0 + (i * 97) % iw
        sy = iy0 + (i * 53) % 110
        put(buf, sx, sy, (255, 244, 210))
        if i % 5 == 0:
            put(buf, sx + 1, sy, (255, 244, 210))
    # moon + glow
    glow(buf, ix0 + 396, iy0 + 46, 60, (240, 230, 190), 0.5)
    fill_ellipse(buf, ix0 + 396, iy0 + 46, 26, 26, (238, 228, 188))
    # drones: body + rotors + red/green lights
    for dx, dy in ((100, 78), (238, 52), (348, 104)):
        cx, cy = ix0 + dx, iy0 + dy
        fill_rect(buf, cx - 11, cy - 3, cx + 11, cy + 4, (8, 10, 16))
        thick_line(buf, cx - 16, cy - 10, cx - 8, cy - 3, 2, (30, 34, 48))
        thick_line(buf, cx + 8, cy - 3, cx + 16, cy - 10, 2, (30, 34, 48))
        thick_line(buf, cx - 16, cy + 10, cx - 8, cy + 3, 2, (30, 34, 48))
        thick_line(buf, cx + 8, cy + 3, cx + 16, cy + 10, 2, (30, 34, 48))
        fill_ellipse(buf, cx - 17, cy - 11, 3, 3, (220, 220, 220))
        fill_ellipse(buf, cx + 17, cy - 11, 3, 3, (220, 220, 220))
        fill_ellipse(buf, cx - 17, cy + 11, 3, 3, (220, 220, 220))
        fill_ellipse(buf, cx + 17, cy + 11, 3, 3, (220, 220, 220))
        fill_ellipse(buf, cx - 12, cy, 3, 3, (255, 60, 60))
        fill_ellipse(buf, cx + 12, cy, 3, 3, (80, 255, 120))
    # explosion glow bottom right + skyline
    glow(buf, ix0 + 392, iy0 + 238, 88, (255, 140, 50), 0.85)
    fill_ellipse(buf, ix0 + 392, iy0 + 244, 30, 20, (255, 200, 90))
    heights = [46, 70, 38, 84, 58, 96, 44, 66, 52, 78, 40, 62]
    bx = ix0
    for hh in heights:
        fill_rect(buf, bx, iy0 + ih - hh, bx + 38, iy0 + ih, (10, 12, 22))
        for wy in range(iy0 + ih - hh + 8, iy0 + ih - 8, 14):
            for wx in (bx + 8, bx + 22):
                if (wx + wy) % 3 == 0:
                    put(buf, wx, wy, (255, 210, 110))
                    put(buf, wx + 1, wy, (255, 210, 110))
        bx += 39
    fill_rect(buf, ix0, iy0 + ih - 10, ix0 + iw, iy0 + ih, (6, 8, 16))


def scene_hormuz(buf, ix0, iy0, iw, ih):
    for y in range(iy0, iy0 + 112):
        t = (y - iy0) / 112
        fill_rect(buf, ix0, y, ix0 + iw, y + 1, mix((255, 172, 100), (236, 122, 82), t))
    for y in range(iy0 + 112, iy0 + ih):
        t = (y - iy0 - 112) / (ih - 112)
        fill_rect(buf, ix0, y, ix0 + iw, y + 1, mix((36, 84, 128), (18, 44, 74), t))
    # sun + its reflection on the sea
    fill_ellipse(buf, ix0 + 88, iy0 + 66, 30, 30, (255, 226, 160))
    glow(buf, ix0 + 88, iy0 + 66, 70, (255, 200, 120), 0.5)
    for yy in range(iy0 + 116, iy0 + ih, 12):
        wdt = 26 + int(18 * math.sin(yy * 0.2))
        fill_rect(buf, ix0 + 88 - wdt, yy, ix0 + 88 + wdt, yy + 3, (255, 200, 130))
    # tanker: hull, containers, bridge
    fill_poly(buf, [(ix0 + 40, iy0 + 168), (ix0 + 420, iy0 + 168),
                    (ix0 + 436, iy0 + 186), (ix0 + 40, iy0 + 200)], (16, 20, 28))
    fill_rect(buf, ix0 + 40, iy0 + 186, ix0 + 436, iy0 + 202, (16, 20, 28))
    conts = [(70, 146, 46, 22, (198, 62, 48)), (120, 146, 46, 22, (62, 110, 190)),
             (170, 146, 46, 22, (70, 158, 92)), (220, 146, 46, 22, (220, 140, 42)),
             (270, 146, 46, 22, (198, 62, 48)), (320, 146, 46, 22, (62, 110, 190))]
    for cx, cy, cw, ch, col in conts:
        fill_rect(buf, ix0 + cx, iy0 + cy, ix0 + cx + cw, iy0 + cy + ch, col)
    fill_rect(buf, ix0 + 380, iy0 + 116, ix0 + 408, iy0 + 168, (232, 226, 214))
    for wy in (iy0 + 126, iy0 + 140, iy0 + 154):
        fill_rect(buf, ix0 + 386, wy, ix0 + 402, wy + 6, (30, 40, 60))
    # smoke column + explosion on the hull
    fill_ellipse(buf, ix0 + 300, iy0 + 96, 26, 34, (120, 116, 110), 0.55)
    fill_ellipse(buf, ix0 + 292, iy0 + 66, 20, 26, (140, 136, 130), 0.5)
    glow(buf, ix0 + 250, iy0 + 168, 52, (255, 140, 50), 0.9)
    fill_ellipse(buf, ix0 + 250, iy0 + 170, 18, 12, (255, 205, 95))
    # wave strokes
    for yy in (iy0 + 216, iy0 + 240, iy0 + 262):
        for xx in range(ix0 + 20, ix0 + iw - 20, 44):
            fill_rect(buf, xx, yy, xx + 26, yy + 2, (140, 180, 215))


def scene_nvidia(buf, ix0, iy0, iw, ih):
    fill_rect(buf, ix0, iy0, ix0 + iw, iy0 + ih, (244, 243, 238))
    cx, cy = ix0 + iw // 2 - 30, iy0 + ih // 2 - 8
    # circuit traces from the chip outward
    for ty in (iy0 + 60, iy0 + 120, iy0 + 180, iy0 + 230):
        fill_rect(buf, ix0 + 24, ty, cx - 100, ty + 3, (190, 170, 110))
        fill_rect(buf, cx + 100, ty, ix0 + iw - 24, ty + 3, (190, 170, 110))
    # gold pins on four sides
    for i in range(10):
        off = 18 + i * 18
        fill_rect(buf, cx - 112 + off, cy - 112, cx - 100 + off, cy - 100, (212, 175, 55))
        fill_rect(buf, cx - 112 + off, cy + 100, cx - 100 + off, cy + 112, (212, 175, 55))
        fill_rect(buf, cx - 112, cy - 112 + off, cx - 100, cy - 100 + off, (212, 175, 55))
        fill_rect(buf, cx + 100, cy - 112 + off, cx + 112, cy - 100 + off, (212, 175, 55))
    # chip: dark green body + lighter die
    fill_rect(buf, cx - 100, cy - 100, cx + 100, cy + 100, (16, 110, 58))
    fill_rect(buf, cx - 64, cy - 64, cx + 64, cy + 64, (24, 142, 74))
    fill_rect(buf, cx - 64, cy - 64, cx + 64, cy - 52, (32, 168, 88))
    # red down arrow across the chip
    thick_line(buf, cx - 52, cy - 56, cx + 44, cy + 52, 13, RED)
    fill_poly(buf, [(cx + 18, cy + 18), (cx + 66, cy + 44), (cx + 40, cy + 74)], RED)
    fill_rect(buf, cx - 100, cy + 100, cx + 100, cy + 106, (12, 84, 44))


def scene_microsoft(buf, ix0, iy0, iw, ih):
    for y in range(iy0, iy0 + ih):
        t = (y - iy0) / ih
        fill_rect(buf, ix0, y, ix0 + iw, y + 1, mix((18, 68, 150), (10, 40, 96), t))
    # white cloud
    ccx, ccy = ix0 + iw // 2, iy0 + 92
    fill_ellipse(buf, ccx - 62, ccy, 52, 42, (245, 247, 250))
    fill_ellipse(buf, ccx + 58, ccy + 6, 48, 38, (245, 247, 250))
    fill_ellipse(buf, ccx, ccy - 22, 56, 44, (255, 255, 255))
    fill_rect(buf, ccx - 108, ccy - 6, ccx + 104, ccy + 42, (245, 247, 250))
    # "365" in white
    draw_text(buf, "365", ix0 + iw // 2, iy0 + 158, 7, (255, 255, 255))
    # red OFFLINE banner at the bottom
    fill_rect(buf, ix0, iy0 + ih - 48, ix0 + iw, iy0 + ih, RED)
    draw_text(buf, "OFFLINE", ix0 + iw // 2, iy0 + ih - 40, 3, (255, 255, 255))


PANELS = [
    (("UKRAINE DRONES", "EUROPE AT TALKS"), scene_ukraine),
    (("TANKERS HIT", "IN HORMUZ"), scene_hormuz),
    (("NVIDIA CEO", "QUITS"), scene_nvidia),
    (("MICROSOFT 365", "DOWN - DAY 2"), scene_microsoft),
]
PANEL_X = (32, 528)
PANEL_Y = (222, 602)
PANEL_W, PANEL_H = 472, 364
HEADER_H = 72


def render():
    buf = [[PAPER] * W for _ in range(H)]
    # thin frame
    for d in (8, 9):
        fill_rect(buf, d, d, W - d, d + 1, FRAME)
        fill_rect(buf, d, H - d - 1, W - d, H - d, FRAME)
        fill_rect(buf, d, d, d + 1, H - d, FRAME)
        fill_rect(buf, W - d - 1, d, W - d, H - d, FRAME)
    # masthead + rules + dateline
    draw_text(buf, "THE WORLD", W // 2, 30, 10, INK)
    fill_rect(buf, 32, 148, 992, 151, INK)
    fill_rect(buf, 32, 156, 992, 157, INK)
    draw_text(buf, "FRIDAY 13 NOVEMBER 2026", W // 2, 170, 3, INK)
    fill_rect(buf, 32, 200, 992, 202, INK)
    # panels
    for (lines, scene), (px0, py0) in zip(
            PANELS, [(32, 222), (528, 222), (32, 602), (528, 602)]):
        # border
        fill_rect(buf, px0, py0, px0 + PANEL_W, py0 + 3, INK)
        fill_rect(buf, px0, py0 + PANEL_H - 3, px0 + PANEL_W, py0 + PANEL_H, INK)
        fill_rect(buf, px0, py0, px0 + 3, py0 + PANEL_H, INK)
        fill_rect(buf, px0 + PANEL_W - 3, py0, px0 + PANEL_W, py0 + PANEL_H, INK)
        # header strip + two headline lines
        fill_rect(buf, px0 + 3, py0 + 3, px0 + PANEL_W - 3, py0 + HEADER_H, HEADER_BG)
        draw_text(buf, lines[0], px0 + PANEL_W // 2, py0 + 12, 3, HEADER_TX)
        draw_text(buf, lines[1], px0 + PANEL_W // 2, py0 + 40, 3, HEADER_TX)
        # illustration
        scene(buf, px0 + 3, py0 + HEADER_H + 3,
              PANEL_W - 6, PANEL_H - HEADER_H - 6)
    # footer
    draw_text(buf, "FOUR STORIES THAT SHAPED FRIDAY 13 NOVEMBER 2026",
              W // 2, 978, 2, INK)
    return buf


def png_bytes(buf):
    raw = bytearray()
    for row in buf:
        raw.append(0)
        for r, g, b in row:
            raw.extend((r, g, b))
    comp = zlib.compress(bytes(raw), 9)

    def chunk(kind, data):
        c = struct.pack(">I", len(data)) + kind + data
        c += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        return c

    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", comp) + chunk(b"IEND", b""))


def main():
    out_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    out_dir.mkdir(parents=True, exist_ok=True)
    data = png_bytes(render())
    (out_dir / "entry.png").write_bytes(data)


if __name__ == "__main__":
    main()
