#!/usr/bin/env python3

import argparse
import math
import random
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, ImageOps

BG = (13, 17, 23)
CARD = (22, 27, 34)
BORDER = (48, 54, 61)
GRID = (24, 29, 37)
TEXT = (201, 209, 217)
MUTED = (125, 133, 144)

VIOLET_900 = (76, 29, 149)
VIOLET_700 = (109, 40, 217)
VIOLET_500 = (139, 92, 246)
VIOLET_400 = (167, 139, 250)
VIOLET_200 = (221, 214, 254)
BLUE = (96, 165, 250)
GREEN = (74, 222, 128)
YELLOW = (250, 204, 21)
PINK = (244, 143, 177)

FUR_DARK = (17, 17, 23)
FUR_MID = (30, 30, 40)
FUR_LIGHT = (62, 58, 82)
FUR_WHITE = (244, 244, 248)
FUR_WHITE_SHADE = (198, 198, 214)

W, H = 780, 300
S = 3
LEFT_W = 330
CX = 165
GROUND = 266


def sc(v):
    return int(round(v * S))


_FONT_BOLD = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf",
    "/Library/Fonts/Menlo.ttc",
    "C:/Windows/Fonts/consolab.ttf",
    "C:/Windows/Fonts/CascadiaCode.ttf",
    "DejaVuSansMono-Bold.ttf",
]
_FONT_REG = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
    "/Library/Fonts/Menlo.ttc",
    "C:/Windows/Fonts/consola.ttf",
    "DejaVuSansMono.ttf",
]


def load_font(size, bold=False):
    for path in (_FONT_BOLD if bold else _FONT_REG):
        try:
            return ImageFont.truetype(path, sc(size))
        except Exception:
            continue
    try:
        return ImageFont.load_default(sc(size))
    except TypeError:
        return ImageFont.load_default()


def layer(w, h):
    return Image.new("RGBA", (sc(w), sc(h)), (0, 0, 0, 0))


def mask_of(size):
    return Image.new("L", size, 0)


def m_ellipse(size, cx, cy, rx, ry):
    m = mask_of(size)
    ImageDraw.Draw(m).ellipse([sc(cx - rx), sc(cy - ry), sc(cx + rx), sc(cy + ry)], fill=255)
    return m


def m_poly(size, pts):
    m = mask_of(size)
    ImageDraw.Draw(m).polygon([(sc(x), sc(y)) for x, y in pts], fill=255)
    return m


def m_round_rect(size, x0, y0, x1, y1, r):
    m = mask_of(size)
    ImageDraw.Draw(m).rounded_rectangle([sc(x0), sc(y0), sc(x1), sc(y1)], radius=sc(r), fill=255)
    return m


def union(*masks):
    out = masks[0]
    for m in masks[1:]:
        out = ImageChops.lighter(out, m)
    return out


def soften(m, r=0.7):
    return m.filter(ImageFilter.GaussianBlur(sc(r)))


def v_gradient(size, top, bottom):
    g = Image.linear_gradient("L").resize(size, Image.BILINEAR)
    return ImageOps.colorize(g, top, bottom).convert("RGBA")


def r_gradient(size, inner, outer, radius, cx=None, cy=None):
    d = int(radius * 2 * 1.4142)
    g = Image.radial_gradient("L").resize((d, d), Image.BILINEAR)
    g = g.point(lambda v: min(255, int(v * 255 / 179)))
    col = ImageOps.colorize(g, inner, outer).convert("RGBA")
    base = Image.new("RGBA", size, outer + (255,))
    cx = size[0] // 2 if cx is None else cx
    cy = size[1] // 2 if cy is None else cy
    base.paste(col, (cx - d // 2, cy - d // 2))
    return base


def fill(lay, mask, paint):
    if isinstance(paint, tuple):
        paint = Image.new("RGBA", lay.size, paint + ((255,) if len(paint) == 3 else ()))
    lay.paste(paint, (0, 0), mask)


def over(base, top, x=0, y=0):
    ox, oy = sc(x), sc(y)
    if ox == 0 and oy == 0 and top.size == base.size:
        return Image.alpha_composite(base, top)
    shifted = Image.new("RGBA", base.size, (0, 0, 0, 0))
    shifted.paste(top, (ox, oy))
    return Image.alpha_composite(base, shifted)


def rim_light(lay, strength=0.75, d=2.0):
    a = lay.getchannel("A")
    k = sc(d)
    top = ImageChops.subtract(a, ImageChops.offset(a, 0, k))
    left = ImageChops.subtract(a, ImageChops.offset(a, k, 0))
    right = ImageChops.subtract(a, ImageChops.offset(a, -k, 0))
    ring = ImageChops.lighter(top, ImageChops.lighter(left.point(lambda v: v * 6 // 10),
                                                      right.point(lambda v: v * 6 // 10)))
    ring = ring.filter(ImageFilter.GaussianBlur(sc(0.55)))
    ring = ImageChops.multiply(ring, a)
    ring = ring.point(lambda v: int(v * strength))
    glow = Image.new("RGBA", lay.size, VIOLET_400 + (0,))
    glow.putalpha(ring)
    return Image.alpha_composite(lay, glow)


def fur_strokes(lay, mask, rng, n, cx, cy, spread, length, colors, width=1.1,
                direction="radial", bias=0.0):
    tmp = Image.new("RGBA", lay.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(tmp)
    for _ in range(n):
        x = cx + rng.uniform(-spread[0], spread[0])
        y = cy + rng.uniform(-spread[1], spread[1])
        if direction == "radial":
            ang = math.atan2(y - cy, x - cx) + rng.uniform(-0.4, 0.4)
        else:
            ang = math.radians(direction) + rng.uniform(-0.35, 0.35)
        ang += bias
        ln = length * rng.uniform(0.6, 1.2)
        bend = rng.uniform(-0.35, 0.35)
        pts = []
        for i in range(7):
            t = i / 6
            a2 = ang + bend * t
            pts.append((sc(x + math.cos(a2) * ln * t), sc(y + math.sin(a2) * ln * t)))
        col = rng.choice(colors)
        d.line(pts, fill=col, width=max(1, int(sc(width))), joint="curve")
    clip = ImageChops.multiply(tmp.getchannel("A"), mask)
    tmp.putalpha(clip)
    return Image.alpha_composite(lay, tmp)


HEAD_CY = 118
HEAD_RX = 84
HEAD_RY = 62
EYE_DX = 34
EYE_Y = 120
EYE_RX = 19.5
EYE_RY = 22

LW, LH = LEFT_W, H


def build_body():
    rng = random.Random(11)
    size = (sc(LW), sc(LH))
    lay = layer(LW, LH)

    body = union(
        m_ellipse(size, CX, 214, 66, 56),
        m_ellipse(size, CX - 50, 238, 40, 29),
        m_ellipse(size, CX + 50, 238, 40, 29),
        m_round_rect(size, CX - 46, 196, CX - 20, 254, 12),
        m_round_rect(size, CX + 20, 196, CX + 46, 254, 12),
    )
    body = soften(body, 0.6)
    fill(lay, body, v_gradient(size, FUR_MID, FUR_DARK))
    lay = fur_strokes(lay, body, rng, 260, CX, 225, (70, 40), 14,
                      [FUR_LIGHT + (150,), FUR_MID + (200,), (8, 8, 12, 170)], 1.0, direction=100)

    chest = union(
        m_ellipse(size, CX, 206, 33, 50),
        m_poly(size, [(CX - 26, 160), (CX + 26, 160), (CX + 34, 205), (CX - 34, 205)]),
    )
    chest = soften(chest, 0.8)
    fill(lay, chest, v_gradient(size, FUR_WHITE, FUR_WHITE_SHADE))
    lay = fur_strokes(lay, chest, rng, 230, CX, 205, (30, 48), 12,
                      [FUR_WHITE + (200,), FUR_WHITE_SHADE + (190,), (170, 170, 190, 120)], 0.9, direction=90)

    for sx in (-1, 1):
        px = CX + sx * 30
        paw = soften(m_ellipse(size, px, GROUND - 9, 22, 11.5), 0.5)
        fill(lay, paw, v_gradient(size, FUR_WHITE, FUR_WHITE_SHADE))
        dr = ImageDraw.Draw(lay)
        for off in (-7, 0, 7):
            dr.line([sc(px + off), sc(GROUND - 9), sc(px + off), sc(GROUND - 1.5)],
                    fill=(150, 150, 170, 200), width=sc(0.9))
    return rim_light(lay, 0.55, 2.0)


def build_head():
    rng = random.Random(23)
    size = (sc(LW), sc(LH))
    lay = layer(LW, LH)

    base = m_ellipse(size, CX, HEAD_CY, HEAD_RX, HEAD_RY)
    spikes = mask_of(size)
    sd = ImageDraw.Draw(spikes)
    for side in (-1, 1):
        for i in range(7):
            ang = math.radians(-6 + i * 11)
            a0, a1 = ang - 0.11, ang + 0.11
            r0 = 0.94
            p0 = (CX + side * math.cos(a0) * HEAD_RX * r0, HEAD_CY + math.sin(a0) * HEAD_RY * r0)
            p1 = (CX + side * math.cos(a1) * HEAD_RX * r0, HEAD_CY + math.sin(a1) * HEAD_RY * r0)
            tip_r = 1.0 + 0.10 + (0.04 if i % 2 else 0.0)
            tp = (CX + side * math.cos(ang + 0.03) * HEAD_RX * tip_r,
                  HEAD_CY + math.sin(ang + 0.03) * HEAD_RY * tip_r + 3.5)
            sd.polygon([(sc(p0[0]), sc(p0[1])), (sc(tp[0]), sc(tp[1])), (sc(p1[0]), sc(p1[1]))], fill=255)
    head = soften(union(base, spikes), 0.6)
    fill(lay, head, v_gradient(size, FUR_MID, FUR_DARK))
    lay = fur_strokes(lay, head, rng, 380, CX, HEAD_CY - 6, (80, 50), 13,
                      [FUR_LIGHT + (150,), FUR_MID + (200,), (8, 8, 12, 150)], 1.0)

    blaze = soften(m_poly(size, [(CX - 4, 62), (CX + 4, 62), (CX + 7, 78), (CX + 10, 98), (CX + 12, 120),
                                 (CX + 18, 134), (CX - 18, 134), (CX - 12, 120), (CX - 10, 98), (CX - 7, 78)]), 1.2)
    muzzle = soften(union(
        m_ellipse(size, CX - 15, 148, 24, 17),
        m_ellipse(size, CX + 15, 148, 24, 17),
        m_ellipse(size, CX, 168, 25, 13),
        m_ellipse(size, CX, 140, 14, 9),
    ), 1.0)
    white = union(blaze, muzzle)
    fill(lay, white, v_gradient(size, FUR_WHITE, FUR_WHITE_SHADE))
    lay = fur_strokes(lay, white, rng, 300, CX, 120, (30, 52), 9,
                      [FUR_WHITE + (210,), FUR_WHITE_SHADE + (180,), (175, 175, 195, 110)], 0.9, direction=90)

    d = ImageDraw.Draw(lay)
    nose = m_poly(size, [(CX - 7, 136.5), (CX + 7, 136.5), (CX, 145)])
    nose = soften(nose, 0.9).point(lambda v: 255 if v > 110 else 0)
    nose = nose.filter(ImageFilter.GaussianBlur(sc(0.4)))
    fill(lay, nose, v_gradient(size, (252, 168, 188), (214, 108, 132)))
    nl = soften(m_ellipse(size, CX - 2, 138.5, 2.4, 1.1), 0.3)
    fill(lay, nl, (255, 220, 228, 255))

    mouth_col = (92, 70, 82, 255)
    d.line([sc(CX), sc(145), sc(CX), sc(150.5)], fill=mouth_col, width=sc(1.3))
    for sx in (-1, 1):
        pts = []
        for i in range(12):
            t = i / 11
            x = CX + sx * (t * 12)
            y = 150.5 + math.sin(t * math.pi) * 4.2 - t * 1.2
            pts.append((sc(x), sc(y)))
        d.line(pts, fill=mouth_col, width=sc(1.3), joint="curve")

    for sx in (-1, 1):
        blush = Image.new("RGBA", lay.size, PINK + (0,))
        blush.putalpha(soften(m_ellipse(size, CX + sx * 54, 146, 13, 7), 4).point(lambda v: v // 5))
        lay = Image.alpha_composite(lay, blush)
    return rim_light(lay, 0.7, 2.0)


def build_ear(side):
    rng = random.Random(41 + side)
    size = (sc(LW), sc(LH))
    lay = layer(LW, LH)
    s = side
    outer = [(CX + s * 84, 108), (CX + s * 91, 34), (CX + s * 40, 68)]
    m = soften(m_poly(size, outer), 3.0).point(lambda v: 255 if v > 120 else int(v * 255 / 120))
    m = m.filter(ImageFilter.GaussianBlur(sc(0.45)))
    fill(lay, m, v_gradient(size, FUR_MID, FUR_DARK))
    inner = [(CX + s * 78, 99), (CX + s * 83, 49), (CX + s * 50, 75)]
    mi = soften(m_poly(size, inner), 2.2).point(lambda v: 255 if v > 120 else int(v * 255 / 120))
    mi = mi.filter(ImageFilter.GaussianBlur(sc(0.5)))
    g = r_gradient(size, (246, 170, 186), (176, 98, 120), sc(40), sc(CX + s * 72), sc(92))
    fill(lay, mi, g)
    lay = fur_strokes(lay, mi, rng, 55, CX + s * 66, 82, (10, 18), 11,
                      [(255, 222, 228, 150), (255, 196, 208, 140)], 0.9, direction=-90 + s * 12)
    lay = rim_light(lay, 0.7, 2.0)
    pivot = (sc(CX + s * 64), sc(98))
    return lay, pivot


def draw_eye(cx, cy, look, blink, happy):
    pad = 6
    w = EYE_RX * 2 + pad * 2
    h = EYE_RY * 2 + pad * 2
    tile = layer(w, h)
    size = tile.size
    ex, ey = w / 2, h / 2

    if happy > 0.5:
        d = ImageDraw.Draw(tile)
        pts = []
        for i in range(21):
            t = i / 20
            x = ex - EYE_RX * 0.85 + t * EYE_RX * 1.7
            y = ey + 4 - math.sin(t * math.pi) * 11
            pts.append((sc(x), sc(y)))
        d.line(pts, fill=VIOLET_200 + (255,), width=sc(3.4), joint="curve")
        for p in (pts[0], pts[-1]):
            d.ellipse([p[0] - sc(1.7), p[1] - sc(1.7), p[0] + sc(1.7), p[1] + sc(1.7)], fill=VIOLET_200 + (255,))
        return tile, (cx - w / 2, cy - h / 2)

    rim = soften(m_ellipse(size, ex, ey, EYE_RX + 1.6, EYE_RY + 1.6), 0.4)
    fill(tile, rim, (10, 10, 14, 255))
    eye_m = soften(m_ellipse(size, ex, ey, EYE_RX, EYE_RY), 0.35)

    iris = r_gradient(size, (206, 196, 62), (70, 66, 14), sc(EYE_RX + 3),
                      sc(ex + look[0] * 0.5), sc(ey + look[1] * 0.5 - 1))
    fill(tile, eye_m, iris)

    ring = ImageChops.subtract(eye_m, soften(m_ellipse(size, ex, ey, EYE_RX - 2.2, EYE_RY - 2.2), 1.2))
    fill(tile, ring, (24, 22, 6, 255))

    px, py = ex + look[0], ey + look[1]
    pup = soften(m_ellipse(size, px, py, EYE_RX * 0.55, EYE_RY * 0.64), 0.3)
    fill(tile, ImageChops.multiply(pup, eye_m), (6, 6, 8, 255))

    shade = Image.new("RGBA", size, (0, 0, 0, 0))
    sa = Image.linear_gradient("L").resize(size, Image.BILINEAR).point(lambda v: max(0, 150 - v * 2))
    shade.putalpha(ImageChops.multiply(sa, eye_m))
    tile = Image.alpha_composite(tile, shade)

    hx, hy = look[0] * 0.35, look[1] * 0.35
    hl = soften(m_ellipse(size, ex - 6.2 + hx, ey - 7.2 + hy, 5.4, 5.8), 0.3)
    fill(tile, hl, (255, 255, 255, 255))
    hl2 = soften(m_ellipse(size, ex + 6.6 + hx, ey + 8 + hy, 2.8, 2.8), 0.3)
    fill(tile, hl2, (255, 255, 255, 230))
    hl3 = soften(m_ellipse(size, ex + 8, ey - 2 + hx * 0.2, 1.3, 1.3), 0.3)
    fill(tile, hl3, (255, 255, 255, 170))

    if blink > 0.02:
        k = max(0.07, 1 - blink)
        nh = max(2, int(tile.size[1] * k))
        sq = tile.resize((tile.size[0], nh), Image.BILINEAR)
        out = Image.new("RGBA", tile.size, (0, 0, 0, 0))
        out.paste(sq, (0, (tile.size[1] - nh) // 2))
        if blink > 0.85:
            d = ImageDraw.Draw(out)
            y = sc(ey + 1)
            d.line([sc(ex - EYE_RX + 1), y, sc(ex), y + sc(1.6), sc(ex + EYE_RX - 1), y],
                   fill=(70, 66, 90, 255), width=sc(1.6), joint="curve")
        tile = out
    return tile, (cx - w / 2, cy - h / 2)


def draw_whiskers(lay, wave):
    d = ImageDraw.Draw(lay)
    for side in (-1, 1):
        for i, (dy, drop) in enumerate(((-3, -9), (4, 2), (11, 13))):
            pts = []
            x0, y0 = CX + side * 27, 148 + dy
            L = 62 + i * 3
            for k in range(16):
                t = k / 15
                x = x0 + side * t * L
                y = y0 + drop * t ** 1.4 + math.sin(t * math.pi) * (wave * (1 + i * 0.3))
                pts.append((sc(x), sc(y)))
            alpha = 235 - i * 18
            d.line(pts, fill=(246, 246, 252, alpha), width=max(2, sc(0.95)), joint="curve")


def draw_tail(sway, flick):
    size_w, size_h = 140, 190
    lay = layer(size_w, size_h)
    ox, oy = 196, 100
    p0 = (CX + 56 - ox, 252 - oy)
    p1 = (CX + 110 - ox, 262 - oy)
    p2 = (CX + 118 + sway * 10 - ox, 196 - oy)
    p3 = (CX + 98 + sway * 26 - ox, 150 + flick * 5 - oy)

    def bez(t):
        u = 1 - t
        x = u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0]
        y = u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1]
        return x, y

    m = mask_of(lay.size)
    md = ImageDraw.Draw(m)
    n = 80
    for i in range(n + 1):
        t = i / n
        x, y = bez(t)
        r = 11.5 - 4.2 * t
        md.ellipse([sc(x - r), sc(y - r), sc(x + r), sc(y + r)], fill=255)
    m = soften(m, 0.5)
    fill(lay, m, v_gradient(lay.size, FUR_MID, FUR_DARK))
    rng = random.Random(5)
    lay = fur_strokes(lay, m, rng, 60, 60, 100, (45, 80), 10,
                      [FUR_LIGHT + (140,), (8, 8, 12, 150)], 0.9, direction=-80)
    lay = rim_light(lay, 1.0, 2.2)
    return lay, (ox, oy)


def draw_background():
    img = Image.new("RGBA", (sc(W), sc(H)), BG + (255,))
    d = ImageDraw.Draw(img)
    for x in range(22, W - 10, 26):
        for y in range(20, H - 10, 26):
            d.ellipse([sc(x) - 2, sc(y) - 2, sc(x) + 2, sc(y) + 2], fill=GRID + (255,))
    return img


def glow_layer(t):
    pulse = 0.5 + 0.5 * math.sin(t)
    size = (sc(LEFT_W), sc(H))
    dsz = sc(310 + 12 * pulse)
    dist = Image.radial_gradient("L").resize((dsz, dsz), Image.BILINEAR)
    dist = dist.point(lambda v: max(0, int((1 - min(1, v / 179)) ** 1.6 * (78 + 18 * pulse))))
    alpha = Image.new("L", size, 0)
    alpha.paste(dist, (sc(CX) - dsz // 2, sc(150) - dsz // 2))
    g = Image.new("RGBA", size, VIOLET_700 + (0,))
    g.putalpha(alpha)
    return g


def draw_floor(t):
    size = (sc(LEFT_W), sc(H))
    sh = soften(m_ellipse(size, CX, GROUND + 1, 92, 9), 3.5)
    shadow = Image.new("RGBA", size, (0, 0, 0, 0))
    shadow.putalpha(sh.point(lambda v: int(v * 0.85)))
    ring = ImageChops.subtract(m_ellipse(size, CX, GROUND + 1, 118, 15), m_ellipse(size, CX, GROUND + 1, 116, 13.8))
    ring = ring.filter(ImageFilter.GaussianBlur(sc(0.6)))
    rl = Image.new("RGBA", size, VIOLET_500 + (0,))
    pulse = 0.55 + 0.25 * math.sin(t)
    rl.putalpha(ring.point(lambda v: int(v * pulse)))
    return Image.alpha_composite(shadow, rl)


def draw_floaters(img, f, n, fonts):
    d = ImageDraw.Draw(img)
    items = [
        ("</> ", 40, 0.00, 0, VIOLET_400),
        ("{ }", 292, 0.33, 1, BLUE),
        ("git", 22, 0.62, 2, GREEN),
        ("PR", 300, 0.88, 3, YELLOW),
        ("</> ", 262, 0.18, 4, VIOLET_400),
        ("{ }", 62, 0.48, 5, BLUE),
    ]
    for txt, x, phase, i, col in items:
        p = (f / n + phase) % 1.0
        y = 250 - p * 215
        x2 = x + math.sin((p + i * 0.17) * math.tau) * 6
        a = int(150 * math.sin(p * math.pi) ** 1.2)
        if a > 4:
            d.text((sc(x2), sc(y)), txt, font=fonts["small"], fill=col + (a,), anchor="mm")
    stars = [(70, 50, 0), (258, 40, 2), (298, 128, 1), (30, 150, 3), (92, 238, 5), (240, 244, 4)]
    for x, y, k in stars:
        tw = 0.5 + 0.5 * math.sin(f / n * math.tau * 2 + k * 1.3)
        r = 1.2 + 1.5 * tw
        a = int(70 + 150 * tw)
        d.polygon([(sc(x), sc(y - r * 2.2)), (sc(x + r * 0.5), sc(y - r * 0.5)), (sc(x + r * 2.2), sc(y)),
                   (sc(x + r * 0.5), sc(y + r * 0.5)), (sc(x), sc(y + r * 2.2)), (sc(x - r * 0.5), sc(y + r * 0.5)),
                   (sc(x - r * 2.2), sc(y)), (sc(x - r * 0.5), sc(y - r * 0.5))], fill=VIOLET_200 + (a,))


def orb_pos(f, n):
    a = f / n * math.tau + 0.6
    x = CX + math.cos(a) * 128
    y = 150 + math.sin(a) * 44 + math.sin(a * 2) * 10
    return x, y, math.sin(a)


def draw_orb(img, x, y, depth, trail):
    size = 1.0 + 0.35 * depth
    d = ImageDraw.Draw(img)
    for i, (tx, ty, td) in enumerate(trail):
        k = (i + 1) / (len(trail) + 1)
        r = (0.6 + 1.9 * k) * (1.0 + 0.3 * td)
        d.ellipse([sc(tx - r), sc(ty - r), sc(tx + r), sc(ty + r)], fill=VIOLET_400 + (int(80 * k),))
    halo = Image.new("RGBA", img.size, (0, 0, 0, 0))
    hd = ImageDraw.Draw(halo)
    for rr, aa in ((13, 28), (9, 55), (6, 95)):
        r = rr * size
        hd.ellipse([sc(x - r), sc(y - r), sc(x + r), sc(y + r)], fill=VIOLET_400 + (aa,))
    halo = halo.filter(ImageFilter.GaussianBlur(sc(2.2)))
    img.alpha_composite(halo)
    d = ImageDraw.Draw(img)
    r = 3.8 * size
    d.ellipse([sc(x - r), sc(y - r), sc(x + r), sc(y + r)], fill=VIOLET_200 + (255,))
    r2 = 1.8 * size
    d.ellipse([sc(x - r2), sc(y - r2), sc(x + r2), sc(y + r2)], fill=(255, 255, 255, 255))


def draw_heart(img, x, y, size, alpha):
    d = ImageDraw.Draw(img)
    pts = []
    for i in range(60):
        t = i / 60 * math.tau
        hx = 16 * math.sin(t) ** 3
        hy = -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
        pts.append((sc(x + hx * size / 16), sc(y + hy * size / 16)))
    d.polygon(pts, fill=PINK + (alpha,))
    d.line([(sc(x - size * 0.45), sc(y - size * 0.2)), (sc(x - size * 0.3), sc(y - size * 0.45))],
           fill=(255, 255, 255, int(alpha * 0.8)), width=sc(1.2))


PX, PY = 352, 16
PW, PH = W - PX - 18, H - 32


def row_layout():
    top = PY + 82
    avail = PH - 82 - 34
    step = avail / 4
    return [top + i * step for i in range(4)]


def stats_items(stats):
    return [
        ("Commits", stats.get("commits", 0), VIOLET_400, 60, "commit"),
        ("Pull Reqs", stats.get("prs", 0), BLUE, 12, "pr"),
        ("Repos", stats.get("repos", 0), GREEN, 15, "repo"),
        ("Stars", stats.get("stars", 0), YELLOW, 10, "star"),
    ]


def draw_icon(d, kind, x, y, color):
    c = color + (255,)
    w = sc(1.6)
    if kind == "commit":
        d.line([sc(x - 9), sc(y), sc(x - 4.5), sc(y)], fill=c, width=w)
        d.line([sc(x + 4.5), sc(y), sc(x + 9), sc(y)], fill=c, width=w)
        d.ellipse([sc(x - 4.5), sc(y - 4.5), sc(x + 4.5), sc(y + 4.5)], outline=c, width=w)
    elif kind == "pr":
        d.ellipse([sc(x - 6.5), sc(y - 7), sc(x - 2.5), sc(y - 3)], outline=c, width=w)
        d.ellipse([sc(x - 6.5), sc(y + 3), sc(x - 2.5), sc(y + 7)], outline=c, width=w)
        d.ellipse([sc(x + 3), sc(y + 3), sc(x + 7), sc(y + 7)], outline=c, width=w)
        d.line([sc(x - 4.5), sc(y - 3), sc(x - 4.5), sc(y + 3)], fill=c, width=w)
        d.line([sc(x + 5), sc(y + 3), sc(x + 5), sc(y - 4), sc(x + 1.5), sc(y - 4)], fill=c, width=w, joint="curve")
    elif kind == "repo":
        d.rounded_rectangle([sc(x - 6), sc(y - 7), sc(x + 6), sc(y + 7)], radius=sc(2), outline=c, width=w)
        d.line([sc(x - 6), sc(y + 3), sc(x + 6), sc(y + 3)], fill=c, width=w)
        d.line([sc(x - 2), sc(y - 4), sc(x + 2), sc(y - 4)], fill=c, width=w)
    elif kind == "star":
        pts = []
        for i in range(10):
            r = 8 if i % 2 == 0 else 3.4
            a = -math.pi / 2 + i * math.pi / 5
            pts.append((sc(x + math.cos(a) * r), sc(y + math.sin(a) * r + 0.6)))
        d.polygon(pts, fill=color + (60,))
        d.line(pts + [pts[0]], fill=c, width=w, joint="curve")


def build_panel_static(fonts, stats):
    size = (sc(W), sc(H))
    lay = layer(W, H)

    sh = soften(m_round_rect(size, PX, PY + 4, PX + PW, PY + PH + 4, 14), 6)
    shadow = Image.new("RGBA", size, (0, 0, 0, 0))
    shadow.putalpha(sh.point(lambda v: int(v * 0.5)))
    lay = Image.alpha_composite(lay, shadow)

    card_m = m_round_rect(size, PX, PY, PX + PW, PY + PH, 14)
    fill(lay, card_m, v_gradient(size, (24, 29, 38), (17, 21, 28)))
    d = ImageDraw.Draw(lay)
    d.rounded_rectangle([sc(PX), sc(PY), sc(PX + PW), sc(PY + PH)], radius=sc(14),
                        outline=BORDER + (255,), width=sc(1.2))

    top = Image.new("RGBA", size, (0, 0, 0, 0))
    td = ImageDraw.Draw(top)
    span = sc(PW - 60)
    for i in range(span):
        a = int(200 * math.sin(i / span * math.pi))
        td.line([(sc(PX + 30) + i, sc(PY) + 1), (sc(PX + 30) + i, sc(PY) + 2)], fill=VIOLET_500 + (a,))
    lay = Image.alpha_composite(lay, top)
    d = ImageDraw.Draw(lay)

    for i, c in enumerate(((255, 95, 86), (255, 189, 46), (39, 201, 63))):
        cx0 = PX + 18 + i * 15
        d.ellipse([sc(cx0 - 4.5), sc(PY + 17.5), sc(cx0 + 4.5), sc(PY + 26.5)], fill=c + (230,))
    d.text((sc(PX + 78), sc(PY + 22)), "github.com/Danilo167", font=fonts["small"], fill=MUTED + (255,), anchor="lm")
    d.line([sc(PX + 16), sc(PY + 40), sc(PX + PW - 16), sc(PY + 40)], fill=BORDER + (255,), width=sc(1))
    d.text((sc(PX + 18), sc(PY + 60)), "GitHub Activity", font=fonts["title"], fill=VIOLET_400 + (255,), anchor="lm")

    rows = row_layout()
    for (label, value, color, _ref, icon), ry in zip(stats_items(stats), rows):
        draw_icon(d, icon, PX + 30, ry + 9, color)
        d.text((sc(PX + 48), sc(ry + 9)), label.upper(), font=fonts["label"], fill=MUTED + (255,), anchor="lm")
        d.text((sc(PX + PW - 20), sc(ry + 11)), f"{value}", font=fonts["num"], fill=color + (255,), anchor="rm")
        by = ry + 26
        track = soften(m_round_rect(size, PX + 20, by, PX + PW - 20, by + 6, 3), 0.25)
        fill(lay, track, (38, 44, 54, 255))
        d = ImageDraw.Draw(lay)

    d.line([sc(PX + 16), sc(PY + PH - 28), sc(PX + PW - 16), sc(PY + PH - 28)], fill=BORDER + (255,), width=sc(1))
    d.text((sc(PX + 18), sc(PY + PH - 14)), "auto-updated · GitHub Actions", font=fonts["tiny"],
           fill=MUTED + (255,), anchor="lm")
    return lay


def draw_bars(img, stats, f, n):
    size = img.size
    for i, ((label, value, color, ref, icon), ry) in enumerate(zip(stats_items(stats), row_layout())):
        by = ry + 26
        track_w = PW - 40
        frac = max(1 - math.exp(-value / ref), 0.025)
        breathe = 1 + 0.012 * math.sin(f / n * math.tau + i)
        fw = max(6, track_w * min(frac * breathe, 1.0))

        m = soften(m_round_rect(size, PX + 20, by, PX + 20 + fw, by + 6, 3), 0.25)
        grad = Image.new("RGBA", size, (0, 0, 0, 0))
        gd = ImageDraw.Draw(grad)
        x0, x1 = sc(PX + 20), sc(PX + 20 + fw)
        dark = tuple(int(c * 0.55) for c in color)
        for x in range(x0, x1, 2):
            t = (x - x0) / max(1, x1 - x0)
            col = tuple(int(dark[k] + (color[k] - dark[k]) * t) for k in range(3))
            gd.line([(x, sc(by)), (x, sc(by + 6))], fill=col + (255,), width=2)
        bar = Image.new("RGBA", size, (0, 0, 0, 0))
        bar.paste(grad, (0, 0), m)

        ph = (f / n + i * 0.18) % 1.0
        sx = PX + 20 + (ph * 1.5 - 0.25) * track_w
        shine = Image.new("RGBA", size, (0, 0, 0, 0))
        sd = ImageDraw.Draw(shine)
        for k in range(-16, 17, 2):
            a = int(120 * (1 - abs(k) / 16) ** 1.5)
            sd.line([(sc(sx + k) + sc(4), sc(by)), (sc(sx + k) - sc(4), sc(by + 6))],
                    fill=(255, 255, 255, a), width=3)
        shine.putalpha(ImageChops.multiply(shine.getchannel("A"), m))
        bar = Image.alpha_composite(bar, shine)

        endx = PX + 20 + fw
        glow = Image.new("RGBA", size, (0, 0, 0, 0))
        pr = 4.6 + 1.2 * math.sin(f / n * math.tau * 2 + i)
        ImageDraw.Draw(glow).ellipse([sc(endx - pr), sc(by + 3 - pr), sc(endx + pr), sc(by + 3 + pr)],
                                     fill=color + (90,))
        glow = glow.filter(ImageFilter.GaussianBlur(sc(1.6)))
        bar = Image.alpha_composite(bar, glow)
        ImageDraw.Draw(bar).ellipse([sc(endx - 2.2), sc(by + 0.8), sc(endx + 2.2), sc(by + 5.2)],
                                    fill=(255, 255, 255, 235))
        img.alpha_composite(bar)


def draw_live_dot(img, f, n):
    k = 0.5 + 0.5 * math.sin(f / n * math.tau * 2)
    x, y = PX + PW - 22, PY + 22
    halo = Image.new("RGBA", img.size, (0, 0, 0, 0))
    r = 4 + 4 * k
    ImageDraw.Draw(halo).ellipse([sc(x - r), sc(y - r), sc(x + r), sc(y + r)], fill=GREEN + (int(110 * (1 - k)),))
    img.alpha_composite(halo)
    ImageDraw.Draw(img).ellipse([sc(x - 3), sc(y - 3), sc(x + 3), sc(y + 3)], fill=GREEN + (255,))


def smooth_pulse(f, start, length):
    k = (f - start) / length
    if k < 0 or k > 1:
        return 0.0
    return math.sin(k * math.pi)


def render_frame(f, n, ctx):
    t = f / n * math.tau
    fonts = ctx["fonts"]
    img = ctx["bg_panel"].copy()

    img.alpha_composite(glow_layer(t), (0, 0))
    img.alpha_composite(draw_floor(t), (0, 0))
    draw_floaters(img, f, n, fonts)

    ox, oy, od = orb_pos(f, n)
    trail = [orb_pos((f - k) % n, n) for k in range(9, 0, -1)]
    if od < 0:
        draw_orb(img, ox, oy, od, trail)

    bob = math.sin(t) * 1.1
    sway = math.sin(t * 2)
    flick = math.sin(t * 4 + 1.2)
    blink = max(smooth_pulse(f, 14, 5), smooth_pulse(f, 56, 5))
    happy = smooth_pulse(f, 33, 14)
    twitch_r = smooth_pulse(f, 4, 8)
    twitch_l = smooth_pulse(f, 44, 7)

    dx, dy = ox - CX, oy - EYE_Y
    dist = math.hypot(dx, dy) or 1
    look = (dx / dist * 3.6, max(-3.0, min(3.2, dy / dist * 3.4)))
    head_shift = max(-2.5, min(2.5, dx / 60))

    cat = layer(LW, LH)
    tail, (tox, toy) = draw_tail(sway, flick)
    cat = over(cat, tail, tox, toy)
    cat = over(cat, ctx["body"], 0, bob * 0.35)

    for lay_, piv, ang in ((ctx["ear_l"], ctx["piv_l"], twitch_l * 7), (ctx["ear_r"], ctx["piv_r"], -twitch_r * 7)):
        a = ang - head_shift * 0.6
        rot = lay_.rotate(a, center=piv, resample=Image.BICUBIC) if abs(a) > 0.01 else lay_
        cat = over(cat, rot, head_shift * 0.4, bob)
    cat = over(cat, ctx["head"], head_shift * 0.4, bob)

    for side in (-1, 1):
        tile, (ex, ey) = draw_eye(CX + side * EYE_DX + head_shift * 0.55, EYE_Y, look, blink, happy)
        cat.alpha_composite(tile, (max(0, sc(ex)), max(0, sc(ey + bob))))

    wl = layer(LW, LH)
    draw_whiskers(wl, math.sin(t * 2 + 0.8) * 1.1)
    cat = over(cat, wl, head_shift * 0.4, bob)

    img.alpha_composite(cat, (0, 0))

    if happy > 0.02:
        rise = (f - 33) / 14
        draw_heart(img, CX + 14 + math.sin(rise * 5) * 3, 44 - rise * 24, 9 + happy * 4,
                   int(235 * min(1, happy * 1.6)))
        draw_heart(img, CX - 20 + math.sin(rise * 4) * 3, 52 - rise * 20, 5 + happy * 2.5,
                   int(190 * min(1, happy * 1.6)))

    if od >= 0:
        draw_orb(img, ox, oy, od, trail)

    draw_bars(img, ctx["stats"], f, n)
    draw_live_dot(img, f, n)

    ImageDraw.Draw(img).rounded_rectangle([sc(1), sc(1), sc(W - 2), sc(H - 2)], radius=sc(16),
                                          outline=BORDER + (255,), width=sc(1.4))
    return img.convert("RGB").resize((W, H), Image.LANCZOS)


def encode_gif(frames, output, colors=255, tol_scene=9, tol_panel=3, duration=55):
    n = len(frames)
    step = max(1, n // 12)
    picks = frames[::step][:12]
    sample = Image.new("RGB", (W, H * len(picks)))
    for i, fr in enumerate(picks):
        sample.paste(fr, (0, i * H))
    pal = sample.quantize(colors=colors, method=Image.FASTOCTREE, dither=Image.NONE)
    palette = (pal.getpalette() + [0] * 768)[:768]
    transp = 255

    quant = []
    for fr in frames:
        q = fr.quantize(palette=pal, dither=Image.NONE)
        q.putpalette(palette)
        quant.append(q)

    region = Image.new("L", (W, H), 0)
    ImageDraw.Draw(region).rectangle([0, 0, LEFT_W + 8, H], fill=255)

    out = [quant[0]]
    recon = quant[0].convert("RGB")
    for i in range(1, n):
        dr, dg, db = ImageChops.difference(frames[i], recon).split()
        diff = ImageChops.lighter(dr, ImageChops.lighter(dg, db))
        same_scene = diff.point(lambda v: 255 if v <= tol_scene else 0)
        same_panel = diff.point(lambda v: 255 if v <= tol_panel else 0)
        same = Image.composite(same_scene, same_panel, region)
        fr = quant[i].copy()
        fr.paste(transp, mask=same)
        fr.info["transparency"] = transp
        out.append(fr)
        recon = Image.composite(recon, quant[i].convert("RGB"), same)

    Path(output).parent.mkdir(parents=True, exist_ok=True)
    out[0].save(output, save_all=True, append_images=out[1:], loop=0, duration=duration,
                optimize=False, disposal=1, transparency=transp)
    print(f"GIF gerado: {output} ({n} frames, {W}x{H}px, {Path(output).stat().st_size // 1024} KB)")


def generate_gif(stats, output, n_frames=72):
    fonts = {
        "title": load_font(15, True),
        "label": load_font(10.5),
        "num": load_font(22, True),
        "small": load_font(10.5),
        "tiny": load_font(9),
    }
    ear_l, piv_l = build_ear(-1)
    ear_r, piv_r = build_ear(1)
    bg = draw_background()
    ctx = {
        "fonts": fonts,
        "stats": stats,
        "body": build_body(),
        "head": build_head(),
        "ear_l": ear_l, "piv_l": piv_l,
        "ear_r": ear_r, "piv_r": piv_r,
        "bg_panel": Image.alpha_composite(bg, build_panel_static(fonts, stats)),
    }

    frames = [render_frame(f, n_frames, ctx) for f in range(n_frames)]

    encode_gif(frames, output)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Gera o GIF do gatinho com stats do GitHub")
    ap.add_argument("--commits", type=int, default=0)
    ap.add_argument("--prs", type=int, default=0)
    ap.add_argument("--repos", type=int, default=0)
    ap.add_argument("--stars", type=int, default=0)
    ap.add_argument("--output", type=str, default="assets/cat_interactions.gif")
    ap.add_argument("--frames", type=int, default=72)
    args = ap.parse_args()

    generate_gif(
        {"commits": args.commits, "prs": args.prs, "repos": args.repos, "stars": args.stars},
        args.output, args.frames,
    )
