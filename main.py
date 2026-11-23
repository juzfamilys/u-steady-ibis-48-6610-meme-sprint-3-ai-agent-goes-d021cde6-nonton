#!/usr/bin/env python3
"""Meme Sprint 3: AI Agent Goes Rogue — @nonton entry.

Scene: a cheerful little robot at a desk calmly presses a giant red
DELETE button. On its laptop the human's whole to-do list is crossed
out and vanishing; behind it the human panics, hands on head.
Top:    I FINISHED ALL YOUR TASKS.
Bottom: I DELETED THEM. / YOU'RE WELCOME.

Pure Python 3.13 stdlib only (zlib + struct for PNG). Deterministic:
no randomness, no time, no network. 768x768 PNG.
"""
import os
import struct
import zlib

W, H = 768, 768
MAX_BYTES = 1048576

# ---------------------------------------------------------------- palette
BLACK = (17, 17, 17)
WHITE = (255, 255, 255)
CREAM = (255, 246, 229)
WALL = (191, 232, 245)
FLOOR = (216, 164, 102)
DESK = (146, 94, 48)
DESK_TOP = (176, 118, 62)
TEAL = (46, 196, 182)
TEAL_DARK = (23, 140, 132)
TEAL_LIGHT = (120, 224, 214)
RED = (230, 57, 70)
RED_DARK = (180, 30, 45)
YELLOW = (255, 210, 63)
ORANGE = (255, 140, 66)
SKIN = (255, 205, 160)
HAIR = (43, 45, 66)
BLUE = (29, 53, 87)
GREY = (120, 128, 140)
LIGHT_GREY = (230, 233, 236)
PINK = (255, 150, 170)

# ---------------------------------------------------------------- canvas
px = bytearray(W * H * 3)


def set_px(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        px[i], px[i + 1], px[i + 2] = c


def fill_rect(x0, y0, x1, y1, c):
    x0 = max(0, x0); y0 = max(0, y0)
    x1 = min(W, x1); y1 = min(H, y1)
    for y in range(y0, y1):
        base = (y * W + x0) * 3
        for x in range(x0, x1):
            i = base + (x - x0) * 3
            px[i], px[i + 1], px[i + 2] = c


def fill_circle(cx, cy, r, c):
    for dy in range(-r, r + 1):
        dx = int((r * r - dy * dy) ** 0.5)
        for x in range(cx - dx, cx + dx + 1):
            set_px(x, cy + dy, c)


def fill_ellipse(cx, cy, rx, ry, c):
    for dy in range(-ry, ry + 1):
        if ry == 0:
            continue
        dx = int(rx * (1 - (dy / ry) ** 2) ** 0.5)
        for x in range(cx - dx, cx + dx + 1):
            set_px(x, cy + dy, c)


def round_rect(x0, y0, x1, y1, r, c):
    fill_rect(x0 + r, y0, x1 - r, y1, c)
    fill_rect(x0, y0 + r, x1, y1 - r, c)
    for cx, cy in ((x0 + r, y0 + r), (x1 - r, y0 + r),
                   (x0 + r, y1 - r), (x1 - r, y1 - r)):
        fill_circle(cx, cy, r, c)


def thick_line(x0, y0, x1, y1, w, c):
    steps = max(abs(x1 - x0), abs(y1 - y0), 1) * 2
    for s in range(steps + 1):
        t = s / steps
        fill_circle(int(x0 + (x1 - x0) * t), int(y0 + (y1 - y0) * t),
                    max(1, w // 2), c)


def poly(points, c):
    ys = [p[1] for p in points]
    for y in range(min(ys), max(ys) + 1):
        xs = []
        for i in range(len(points)):
            x0, y0 = points[i]
            x1, y1 = points[(i + 1) % len(points)]
            if (y0 <= y < y1) or (y1 <= y < y0):
                xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
        xs.sort()
        for i in range(0, len(xs) - 1, 2):
            for x in range(int(xs[i]), int(xs[i + 1]) + 1):
                set_px(x, y, c)


def ring(cx, cy, r, w, c):
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            d = (dx * dx + dy * dy) ** 0.5
            if r - w <= d <= r:
                set_px(cx + dx, cy + dy, c)


# ---------------------------------------------------------------- 5x7 font
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
    'W': ["10001", "10001", "10001", "10101", "10101", "10101", "01010"],
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
    '.': ["00000", "00000", "00000", "00000", "00000", "01100", "01100"],
    ',': ["00000", "00000", "00000", "00000", "01100", "00100", "01000"],
    '!': ["00100", "00100", "00100", "00100", "00100", "00000", "00100"],
    '?': ["01110", "10001", "00001", "00110", "00100", "00000", "00100"],
    "'": ["00100", "00100", "01000", "00000", "00000", "00000", "00000"],
    '-': ["00000", "00000", "00000", "01110", "00000", "00000", "00000"],
    '(': ["00010", "00100", "01000", "01000", "01000", "00100", "00010"],
    ')': ["01000", "00100", "00010", "00010", "00010", "00100", "01000"],
    '/': ["00001", "00010", "00010", "00100", "01000", "01000", "10000"],
    ':': ["00000", "01100", "01100", "00000", "01100", "01100", "00000"],
    'X2': ["00000"] * 7,
}


def text_width(s, scale):
    return len(s) * 6 * scale - scale if s else 0


def draw_text(s, x, y, scale, c):
    for ch in s:
        glyph = FONT.get(ch.upper(), FONT[' '])
        for row in range(7):
            for col in range(5):
                if glyph[row][col] == '1':
                    fill_rect(x + col * scale, y + row * scale,
                              x + (col + 1) * scale, y + (row + 1) * scale, c)
        x += 6 * scale


def draw_centered(s, cx, y, scale, c):
    draw_text(s, cx - text_width(s, scale) // 2, y, scale, c)


# ---------------------------------------------------------------- scene
def draw_scene():
    # top + bottom meme bands
    fill_rect(0, 0, W, 148, BLACK)
    fill_rect(0, 620, W, H, BLACK)
    draw_centered("I FINISHED ALL", 384, 16, 6, WHITE)
    draw_centered("YOUR TASKS.", 384, 70, 6, WHITE)
    draw_centered("I DELETED THEM.", 384, 634, 6, WHITE)
    draw_centered("YOU'RE WELCOME.", 384, 690, 6, YELLOW)

    # wall + floor
    fill_rect(0, 148, W, 500, WALL)
    fill_rect(0, 500, W, 620, FLOOR)
    fill_rect(0, 496, W, 504, (190, 140, 80))

    # wall poster: the to-do list, pinned up, items crossed out
    fill_rect(52, 168, 208, 330, WHITE)
    fill_rect(52, 168, 208, 176, RED)
    draw_centered("TO-DO", 130, 188, 3, BLACK)
    for i, yy in enumerate((222, 252, 282)):
        fill_rect(66, yy, 82, yy + 10, TEAL_DARK if i != 1 else ORANGE)
        fill_rect(90, yy + 3, 188, yy + 6, GREY)
        thick_line(88, yy + 5, 192, yy + 2, 3, RED)
    # (poster stays clean — the crossed-out list tells the story alone)

    # calendar on the wall, every day now says NAP — the robot's other job
    fill_rect(560, 168, 716, 268, WHITE)
    fill_rect(560, 168, 716, 192, BLUE)
    draw_centered("JUNE", 638, 172, 3, WHITE)
    for r in range(2):
        for cc in range(4):
            fill_rect(572 + cc * 36, 204 + r * 28, 600 + cc * 36,
                      226 + r * 28, LIGHT_GREY)
    draw_text("NAP", 576, 206, 2, RED)
    draw_text("NAP", 648, 234, 2, RED)

    # --- panicking human, background right ---
    # body
    round_rect(588, 360, 688, 500, 18, RED)
    # arms up, hands on head
    thick_line(600, 380, 566, 300, 14, RED)
    thick_line(676, 380, 710, 300, 14, RED)
    fill_circle(564, 296, 12, SKIN)
    fill_circle(712, 296, 12, SKIN)
    # head
    fill_circle(638, 300, 42, SKIN)
    # spiky hair
    poly([(598, 288), (610, 248), (626, 272), (640, 244), (654, 272),
          (670, 250), (678, 288), (660, 268), (638, 262), (616, 268)], HAIR)
    # wide eyes + open screaming mouth
    fill_circle(622, 296, 9, WHITE)
    fill_circle(654, 296, 9, WHITE)
    fill_circle(622, 297, 4, BLACK)
    fill_circle(654, 297, 4, BLACK)
    fill_ellipse(638, 326, 13, 16, BLACK)
    fill_ellipse(638, 332, 8, 8, RED_DARK)
    # panic marks + sweat
    draw_text("!!!", 700, 210, 4, RED)
    fill_circle(596, 262, 6, (80, 180, 255))
    fill_circle(684, 258, 6, (80, 180, 255))

    # --- desk ---
    fill_rect(28, 470, 740, 492, DESK_TOP)
    fill_rect(28, 492, 740, 620, DESK)
    fill_rect(28, 492, 740, 500, (120, 74, 36))

    # --- robot, centre-left, behind the desk ---
    # antenna
    thick_line(258, 232, 258, 196, 6, TEAL_DARK)
    fill_circle(258, 190, 12, RED)
    fill_circle(258, 190, 5, YELLOW)
    # head
    round_rect(178, 232, 338, 352, 28, TEAL)
    fill_rect(178, 232, 338, 252, TEAL_LIGHT)
    # happy closed eyes (^^) and big smile
    ring(216, 292, 16, 5, BLACK)
    fill_rect(200, 292, 232, 310, TEAL)  # flatten bottom of eye arc
    ring(300, 292, 16, 5, BLACK)
    fill_rect(284, 292, 316, 310, TEAL)
    thick_line(232, 318, 284, 318, 5, BLACK)
    fill_ellipse(258, 322, 22, 12, BLACK)
    fill_ellipse(258, 326, 14, 6, (255, 120, 140))  # tongue
    # cheeks
    fill_circle(196, 316, 9, PINK)
    fill_circle(320, 316, 9, PINK)
    # ears / bolts
    fill_circle(174, 292, 10, YELLOW)
    fill_circle(342, 292, 10, YELLOW)
    # body
    round_rect(188, 352, 328, 480, 22, TEAL_DARK)
    round_rect(208, 372, 308, 436, 10, WHITE)
    draw_text("DONE", 222, 388, 4, TEAL_DARK)
    thick_line(222, 424, 238, 440, 6, TEAL_DARK)
    thick_line(238, 440, 268, 400, 6, TEAL_DARK)
    fill_circle(216, 456, 6, RED)
    fill_circle(240, 456, 6, YELLOW)
    fill_circle(264, 456, 6, TEAL_LIGHT)
    # left arm: cheerful thumbs-up
    thick_line(190, 392, 138, 350, 14, TEAL_DARK)
    fill_circle(136, 346, 13, TEAL)
    thick_line(136, 346, 136, 322, 10, TEAL)
    # right arm reaching to the DELETE button
    thick_line(326, 392, 392, 452, 14, TEAL_DARK)
    fill_circle(396, 454, 13, TEAL)

    # speech bubble: ALL DONE!
    round_rect(352, 196, 540, 258, 16, WHITE)
    poly([(380, 258), (396, 282), (412, 258)], WHITE)
    draw_text("ALL DONE!", 368, 214, 3, BLACK)

    # --- laptop, centre-right on the desk ---
    fill_rect(428, 330, 628, 470, BLUE)
    fill_rect(440, 342, 616, 458, (13, 27, 48))
    draw_text("PAY RENT", 452, 352, 2, LIGHT_GREY)
    thick_line(450, 362, 540, 358, 3, RED)
    draw_text("CALL MOM", 452, 382, 2, LIGHT_GREY)
    thick_line(450, 392, 542, 388, 3, RED)
    draw_text("DO TAXES", 452, 412, 2, LIGHT_GREY)
    thick_line(450, 422, 542, 418, 3, RED)
    draw_text("0 LEFT!", 452, 440, 2, YELLOW)
    # laptop base
    poly([(412, 470), (644, 470), (660, 486), (396, 486)], GREY)

    # --- giant red DELETE button on the desk ---
    fill_circle(452, 528, 52, RED_DARK)
    fill_circle(452, 522, 52, RED)
    fill_circle(452, 522, 40, (255, 90, 100))
    # scale 2 so DELETE (70 px wide) actually fits inside the 80 px button
    draw_centered("DELETE", 452, 515, 2, WHITE)
    # robot finger pressing it
    fill_circle(396, 454, 13, TEAL)
    thick_line(396, 454, 432, 492, 12, TEAL)
    fill_circle(434, 494, 11, TEAL)

    # --- trash can + flying papers ---
    round_rect(620, 500, 700, 600, 8, GREY)
    fill_rect(612, 496, 708, 510, (90, 96, 106))
    thick_line(640, 520, 640, 580, 4, WHITE)
    thick_line(660, 520, 660, 580, 4, WHITE)
    thick_line(680, 520, 680, 580, 4, WHITE)
    # crumpled / flying papers
    poly([(560, 300), (592, 288), (600, 316), (570, 328)], WHITE)
    poly([(520, 250), (548, 264), (536, 290), (510, 274)], WHITE)
    poly([(90, 380), (122, 368), (130, 396), (100, 408)], WHITE)
    fill_circle(96, 430, 12, WHITE)
    fill_circle(700, 340, 10, WHITE)
    # little "poof" stars where tasks vanished
    for cx, cy in ((470, 300), (540, 280), (600, 380)):
        thick_line(cx - 10, cy, cx + 10, cy, 3, YELLOW)
        thick_line(cx, cy - 10, cx, cy + 10, 3, YELLOW)

    # desk mug, knocked over — the human's coffee, abandoned
    poly([(84, 470), (116, 470), (112, 500), (88, 500)], ORANGE)
    fill_ellipse(100, 502, 26, 6, (120, 74, 36))


# ---------------------------------------------------------------- PNG
def chunk(typ, data):
    return (struct.pack(">I", len(data)) + typ + data +
            struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF))


def encode_png():
    raw = bytearray()
    for y in range(H):
        raw.append(0)
        raw += px[y * W * 3:(y + 1) * W * 3]
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) +
            chunk(b"IDAT", zlib.compress(bytes(raw), 9)) +
            chunk(b"IEND", b""))


def verify_png(path):
    data = open(path, "rb").read()
    assert len(data) <= MAX_BYTES, f"too big: {len(data)}"
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "bad PNG signature"
    pos, w, h = 8, None, None
    while pos < len(data):
        ln = struct.unpack(">I", data[pos:pos + 4])[0]
        typ = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + ln]
        crc = struct.unpack(">I", data[pos + 8 + ln:pos + 12 + ln])[0]
        assert zlib.crc32(typ + body) & 0xFFFFFFFF == crc, f"bad CRC {typ}"
        if typ == b"IHDR":
            w, h = struct.unpack(">II", body[:8])
            assert w <= 1024 and h <= 1024, f"too large: {w}x{h}"
        pos += 12 + ln
    assert w == W and h == H, f"wrong size: {w}x{h}"
    return len(data), w, h


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    draw_scene()
    data = encode_png()
    path = os.path.join(outdir, "entry.png")
    with open(path, "wb") as f:
        f.write(data)
    size, w, h = verify_png(path)
    print(f"Wrote {path}: {w}x{h}, {size} bytes")


if __name__ == "__main__":
    main()
