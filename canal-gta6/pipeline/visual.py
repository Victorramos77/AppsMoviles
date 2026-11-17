"""Gráficos originales: fondos synthwave animados, escenas infográficas y subtítulos."""
import math, os, random
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1920, 1080
FPS = 30
HERE = os.path.dirname(os.path.abspath(__file__))
FD = os.path.join(HERE, "fonts")

YELLOW = (255, 212, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

THEMES = {
    "sunset": dict(sky=[(18, 4, 45), (120, 20, 110), (255, 70, 120), (255, 170, 80)], sun=[(255, 230, 90), (255, 60, 140)],
                   grid=(255, 60, 200), floor=(20, 2, 35), accent=(255, 60, 160), accent2=(0, 230, 255), city=(25, 5, 40)),
    "night":  dict(sky=[(3, 4, 20), (20, 10, 60), (80, 20, 130), (160, 50, 180)], sun=[(255, 120, 220), (120, 40, 255)],
                   grid=(0, 220, 255), floor=(5, 5, 25), accent=(0, 220, 255), accent2=(255, 60, 200), city=(8, 6, 30)),
    "ocean":  dict(sky=[(2, 15, 40), (10, 70, 110), (40, 170, 180), (255, 180, 110)], sun=[(255, 210, 120), (255, 90, 90)],
                   grid=(60, 240, 220), floor=(2, 20, 35), accent=(40, 230, 210), accent2=(255, 140, 80), city=(4, 18, 36)),
    "money":  dict(sky=[(5, 20, 12), (20, 70, 40), (140, 150, 40), (255, 200, 70)], sun=[(255, 235, 120), (255, 150, 30)],
                   grid=(120, 255, 140), floor=(4, 18, 10), accent=(255, 200, 40), accent2=(80, 255, 150), city=(6, 22, 12)),
    "alert":  dict(sky=[(10, 0, 5), (60, 0, 20), (180, 20, 40), (255, 100, 50)], sun=[(255, 200, 60), (255, 30, 60)],
                   grid=(255, 50, 70), floor=(15, 0, 6), accent=(255, 50, 70), accent2=(255, 200, 40), city=(18, 2, 8)),
}


@lru_cache(None)
def font(name, size):
    if name == "anton":
        return ImageFont.truetype(os.path.join(FD, "Anton-Regular.ttf"), size)
    if name == "bebas":
        return ImageFont.truetype(os.path.join(FD, "BebasNeue-Regular.ttf"), size)
    f = ImageFont.truetype(os.path.join(FD, "Montserrat[wght].ttf"), size)
    f.set_variation_by_name({"mx": "ExtraBold", "mb": "Bold", "ms": "SemiBold", "mk": "Black"}[name])
    return f


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(len(a)))


def ease_out(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def ease_back(t):
    t = max(0.0, min(1.0, t))
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2


# ------------------------------------------------------------------ fondo
HORIZON = 650


def _palm(d, x, y, h, col, lean=0.15, seed=0):
    r = random.Random(seed)
    pts = []
    for i in range(40):
        t = i / 39
        px = x + lean * h * t ** 1.6
        py = y - h * t
        pts.append((px, py))
    for i, (px, py) in enumerate(pts):
        w = 26 - 12 * (i / 39)
        d.ellipse([px - w / 2, py - w / 2, px + w / 2, py + w / 2], fill=col)
    tx, ty = pts[-1]
    for k in range(9):
        ang = -math.pi / 2 + (k - 4) * 0.42 + r.uniform(-0.1, 0.1)
        L = h * r.uniform(0.38, 0.5)
        leaf = []
        for j in range(16):
            t = j / 15
            droop = 0.9 * t * t
            ax = tx + math.cos(ang) * L * t
            ay = ty + math.sin(ang) * L * t + droop * L * 0.6
            leaf.append((ax, ay))
        upper = [(ax, ay - 16 * math.sin(math.pi * (j / 15))) for j, (ax, ay) in enumerate(leaf)]
        d.polygon(upper + leaf[::-1], fill=col)
    d.ellipse([tx - 18, ty - 18, tx + 18, ty + 18], fill=col)


def _vgrad(w, h, stops):
    ys = np.linspace(0, 1, h)[:, None]
    n = len(stops) - 1
    out = np.zeros((h, 1, 3))
    for i in range(n):
        a, b = np.array(stops[i]), np.array(stops[i + 1])
        lo, hi = i / n, (i + 1) / n
        m = (ys >= lo) & (ys <= hi)
        t = (ys - lo) / (hi - lo)
        seg = a + (b - a) * t[..., None]
        out = np.where(m[..., None], seg, out)
    return np.repeat(out, w, axis=1).astype(np.uint8)


@lru_cache(None)
def background_static(theme):
    th = THEMES[theme]
    rnd = random.Random(hash(theme) % 1000)
    sky = Image.fromarray(_vgrad(W, HORIZON, th["sky"]))
    img = Image.new("RGB", (W, H), th["floor"])
    img.paste(sky, (0, 0))
    d = ImageDraw.Draw(img, "RGBA")
    # estrellas
    for _ in range(160):
        x, y = rnd.randrange(W), rnd.randrange(int(HORIZON * 0.55))
        s = rnd.choice([1, 1, 2, 2, 3])
        d.ellipse([x, y, x + s, y + s], fill=(255, 255, 255, rnd.randrange(80, 220)))
    # sol con franjas
    R = 300
    cx, cy = W // 2, HORIZON - 70
    sun = Image.fromarray(_vgrad(2 * R, 2 * R, [th["sun"][0], th["sun"][1]])).convert("RGBA")
    mask = Image.new("L", (2 * R, 2 * R), 0)
    md = ImageDraw.Draw(mask)
    md.ellipse([0, 0, 2 * R - 1, 2 * R - 1], fill=255)
    y = R + 10
    gap = 5
    while y < 2 * R:
        md.rectangle([0, y, 2 * R, y + gap], fill=0)
        y += gap + 30
        gap += 4
    sun.putalpha(mask)
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([cx - R - 60, cy - R - 60, cx + R + 60, cy + R + 60], fill=th["sun"][1] + (140,))
    glow = glow.filter(ImageFilter.GaussianBlur(70))
    img.paste(glow, (0, 0), glow)
    img.paste(sun, (cx - R, cy - R), sun)
    # montañas / skyline
    d = ImageDraw.Draw(img, "RGBA")
    pts = [(0, HORIZON)]
    x = 0
    while x < W:
        x += rnd.randrange(60, 160)
        pts.append((x, HORIZON - rnd.randrange(20, 120)))
    pts += [(W, HORIZON)]
    d.polygon(pts, fill=lerp(th["city"], th["sky"][2], 0.35))
    x = 80
    while x < W - 80:
        bw = rnd.randrange(40, 110)
        bh = rnd.randrange(60, 330) * (1.4 if abs(x - W / 2) < 500 else 0.7)
        d.rectangle([x, HORIZON - bh, x + bw, HORIZON], fill=th["city"])
        for wy in range(int(HORIZON - bh + 12), HORIZON - 10, 18):
            for wx in range(x + 8, x + bw - 8, 16):
                if rnd.random() < 0.18:
                    d.rectangle([wx, wy, wx + 6, wy + 8], fill=th["sun"][0] + (150,))
        x += bw + rnd.randrange(0, 20)
    # línea del horizonte
    d.rectangle([0, HORIZON - 2, W, HORIZON + 2], fill=th["grid"] + (255,))
    # palmeras
    palm_col = (8, 2, 12)
    _palm(d, 120, H + 20, 760, palm_col, 0.22, 1)
    _palm(d, 300, H + 60, 560, palm_col, 0.35, 2)
    _palm(d, W - 140, H + 20, 720, palm_col, -0.25, 3)
    _palm(d, W - 330, H + 60, 500, palm_col, -0.4, 4)
    return img


@lru_cache(None)
def grid_frames(theme, n=45):
    """Capas RGBA del suelo con rejilla en movimiento (ciclo de n frames)."""
    th = THEMES[theme]
    frames = []
    vx = W / 2
    for i in range(n):
        p = i / n
        layer = Image.new("RGBA", (W, H - HORIZON), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        hh = H - HORIZON
        for k in range(-26, 27):
            x_bottom = vx + k * 170
            d.line([(vx + k * 8, 0), (x_bottom, hh)], fill=th["grid"] + (170,), width=2)
        for j in range(0, 22):
            z = j + 1 - p
            y = 0 + 260 / z * 1.0
            if y > hh:
                continue
            a = int(min(255, 40 + 600 / (z + 1)))
            d.line([(0, y), (W, y)], fill=th["grid"] + (min(200, a),), width=2 if y > 60 else 1)
        frames.append(layer)
    return frames


@lru_cache(None)
def palms_overlay(theme):
    """Las palmeras por delante del suelo (se redibujan encima de la rejilla)."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    palm_col = (8, 2, 12, 255)
    _palm(d, 120, H + 20, 760, palm_col, 0.22, 1)
    _palm(d, 300, H + 60, 560, palm_col, 0.35, 2)
    _palm(d, W - 140, H + 20, 720, palm_col, -0.25, 3)
    _palm(d, W - 330, H + 60, 500, palm_col, -0.4, 4)
    return layer


@lru_cache(None)
def vignette():
    y, x = np.mgrid[0:H, 0:W]
    r = np.sqrt(((x - W / 2) / (W / 2)) ** 2 + ((y - H / 2) / (H / 2)) ** 2)
    a = np.clip((r - 0.7) / 0.7, 0, 1) * 170
    v = np.zeros((H, W, 4), np.uint8)
    v[..., 3] = a.astype(np.uint8)
    return Image.fromarray(v, "RGBA")


def background(theme, frame_idx):
    img = background_static(theme).copy()
    g = grid_frames(theme)[frame_idx % 45]
    img.paste(g, (0, HORIZON), g)
    p = palms_overlay(theme)
    img.paste(p, (0, 0), p)
    v = vignette()
    img.paste(v, (0, 0), v)
    return img


# ------------------------------------------------------------------ utilidades de texto
def text_sprite(text, fnt, fill=WHITE, stroke=0, stroke_fill=BLACK, shadow=0, glow=None, spacing=0, align="center"):
    lines = text.split("\n")
    asc, desc = fnt.getmetrics()
    lh = asc + desc + spacing
    widths = [fnt.getbbox(l, stroke_width=stroke)[2] for l in lines]
    pad = stroke + shadow + (40 if glow else 4)
    w = max(widths) + 2 * pad
    h = lh * len(lines) + 2 * pad
    img = Image.new("RGBA", (int(w), int(h)), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    def draw_all(dr, col, off=(0, 0), sw=0, sf=None):
        for i, l in enumerate(lines):
            lw = widths[i]
            x = pad + ((max(widths) - lw) / 2 if align == "center" else 0)
            dr.text((x + off[0], pad + i * lh + off[1]), l, font=fnt, fill=col, stroke_width=sw, stroke_fill=sf)

    if glow:
        gl = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw_all(ImageDraw.Draw(gl), glow + (255,), sw=stroke + 6, sf=glow + (255,))
        gl = gl.filter(ImageFilter.GaussianBlur(18))
        img.alpha_composite(gl)
    if shadow:
        draw_all(d, (0, 0, 0, 160), off=(shadow, shadow), sw=stroke, sf=(0, 0, 0, 160))
    draw_all(d, fill, sw=stroke, sf=stroke_fill)
    return img


def trim(img, pad=0):
    bb = img.getchannel("A").getbbox()
    if not bb:
        return img
    l, t, r, b = bb
    return img.crop((max(0, l - pad), max(0, t - pad), min(img.width, r + pad), min(img.height, b + pad)))


def stack(heights, gaps, cy):
    total = sum(heights) + sum(gaps)
    y = cy - total / 2
    out = []
    for i, h in enumerate(heights):
        out.append(int(y + h / 2))
        y += h + (gaps[i] if i < len(gaps) else 0)
    return out


def fit_font(name, text, max_w, start, min_size=20):
    s = start
    while s > min_size:
        f = font(name, s)
        if max(f.getbbox(l)[2] for l in text.split("\n")) <= max_w:
            return f
        s -= 4
    return font(name, min_size)


def panel(w, h, fill=(10, 6, 25, 205), outline=None, radius=28, width=4):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=radius, fill=fill, outline=outline, width=width)
    return img


def pill(text, fnt, bg, fg=BLACK, padx=34, pady=14):
    bb = fnt.getbbox(text)
    w, h = bb[2] - bb[0] + 2 * padx, bb[3] - bb[1] + 2 * pady
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=h // 2, fill=bg)
    d.text((padx - bb[0], pady - bb[1]), text, font=fnt, fill=fg)
    return img


# ------------------------------------------------------------------ elementos
class El:
    def __init__(self, img, x, y, t0, anim="rise", dur=0.45, pop=True):
        self.img, self.x, self.y, self.t0, self.anim, self.dur, self.pop = img, int(x), int(y), t0, anim, dur, pop

    def draw(self, frame, t):
        if t < self.t0:
            return
        p = (t - self.t0) / self.dur
        img, x, y = self.img, self.x, self.y
        if p < 1:
            a = ease_out(p)
            if self.anim == "rise":
                y += int((1 - a) * 60)
            elif self.anim == "left":
                x -= int((1 - a) * 140)
            elif self.anim == "right":
                x += int((1 - a) * 140)
            elif self.anim == "pop":
                s = max(0.05, ease_back(p) * 0.25 + 0.75 if p > 0 else 0.75)
                s = 0.75 + 0.25 * ease_back(p)
                nw, nh = max(1, int(img.width * s)), max(1, int(img.height * s))
                img = img.resize((nw, nh), Image.BILINEAR)
                x += (self.img.width - nw) // 2
                y += (self.img.height - nh) // 2
            if a < 1:
                al = img.getchannel("A").point(lambda v: int(v * a))
                img = img.copy()
                img.putalpha(al)
        frame.paste(img, (x, y), img)


def centered(img, cy, t0, anim="rise", cx=W // 2):
    return El(img, cx - img.width // 2, cy - img.height // 2, t0, anim)


# ------------------------------------------------------------------ iconos
def icon(kind, size, col):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    s = size
    lw = max(6, s // 14)
    if kind == "clock":
        d.ellipse([lw, lw, s - lw, s - lw], outline=col, width=lw)
        c = s / 2
        d.line([(c, c), (c, s * 0.2)], fill=col, width=lw)
        d.line([(c, c), (s * 0.72, c)], fill=col, width=lw)
        d.ellipse([c - lw, c - lw, c + lw, c + lw], fill=col)
    elif kind == "money":
        d.ellipse([lw, lw, s - lw, s - lw], outline=col, width=lw)
        f = font("anton", int(s * 0.62))
        d.text((s / 2, s / 2), "€", font=f, fill=col, anchor="mm")
    elif kind == "disk":
        d.rounded_rectangle([lw, s * 0.2, s - lw, s * 0.8], radius=s // 10, outline=col, width=lw)
        f = font("anton", int(s * 0.28))
        d.text((s / 2, s / 2), "GB", font=f, fill=col, anchor="mm")
    elif kind == "globe":
        d.ellipse([lw, lw, s - lw, s - lw], outline=col, width=lw)
        d.ellipse([s * 0.3, lw, s * 0.7, s - lw], outline=col, width=lw)
        d.line([(lw, s / 2), (s - lw, s / 2)], fill=col, width=lw)
        d.line([(s * 0.12, s * 0.3), (s * 0.88, s * 0.3)], fill=col, width=lw // 2)
        d.line([(s * 0.12, s * 0.7), (s * 0.88, s * 0.7)], fill=col, width=lw // 2)
    elif kind == "pc":
        d.rounded_rectangle([lw, s * 0.12, s - lw, s * 0.68], radius=s // 20, outline=col, width=lw)
        d.rectangle([s * 0.42, s * 0.68, s * 0.58, s * 0.82], fill=col)
        d.rounded_rectangle([s * 0.25, s * 0.82, s * 0.75, s * 0.9], radius=6, fill=col)
        f = font("anton", int(s * 0.3))
        d.text((s / 2, s * 0.4), "?", font=f, fill=col, anchor="mm")
    elif kind == "duo":
        for cx, sc in ((s * 0.36, 1.0), (s * 0.66, 0.92)):
            r = s * 0.13 * sc
            d.ellipse([cx - r, s * 0.18, cx + r, s * 0.18 + 2 * r], fill=col)
            d.pieslice([cx - s * 0.24 * sc, s * 0.48, cx + s * 0.24 * sc, s * 1.1], 180, 360, fill=col)
    elif kind == "map":
        d.ellipse([s * 0.22, s * 0.05, s * 0.78, s * 0.61], outline=col, width=lw)
        d.polygon([(s * 0.27, s * 0.48), (s * 0.73, s * 0.48), (s / 2, s * 0.95)], fill=col)
        d.ellipse([s * 0.22 + lw, s * 0.05 + lw, s * 0.78 - lw, s * 0.61 - lw], fill=col)
        d.ellipse([s * 0.4, s * 0.2, s * 0.6, s * 0.4], fill=(0, 0, 0, 255))
    elif kind == "check":
        d.rounded_rectangle([lw, lw, s - lw, s - lw], radius=s // 6, outline=col, width=lw)
        d.line([(s * 0.25, s * 0.52), (s * 0.43, s * 0.7), (s * 0.77, s * 0.3)], fill=col, width=int(lw * 1.6), joint="curve")
    elif kind == "list":
        for i in range(3):
            y = s * (0.25 + 0.25 * i)
            d.ellipse([s * 0.1, y - lw, s * 0.1 + 2 * lw, y + lw], fill=col)
            d.line([(s * 0.3, y), (s * 0.9, y)], fill=col, width=lw)
    elif kind == "warning":
        d.polygon([(s / 2, s * 0.06), (s * 0.96, s * 0.9), (s * 0.04, s * 0.9)], outline=col, fill=None, width=lw)
        f = font("anton", int(s * 0.5))
        d.text((s / 2, s * 0.58), "!", font=f, fill=col, anchor="mm")
    return img


# ------------------------------------------------------------------ escenas
REGIONS = {
    "Port Gellhorn": ((0.27, 0.215), "Puerto venido a menos", ["Costa del golfo", "Ambiente decadente"]),
    "Mount Kalaga": ((0.60, 0.25), "Parque Nacional", ["Bosques y montaña", "Caza y todoterreno"]),
    "Ambrosia": ((0.67, 0.55), "Interior rural e industrial", ["Refinería de azúcar", "Bandas de moteros"]),
    "Grassrivers": ((0.70, 0.83), "Pantanos", ["Inspirado en los Everglades", "Caimanes e hidrodeslizadores"]),
    "Vice City": ((0.885, 0.70), "La gran ciudad", ["Versión de Miami", "Playas, neón y crimen"]),
    "Leonida Keys": ((0.70, 0.965), "Los Cayos", ["Islas y puentes", "Donde trabaja Jason"]),
}

FL = [(0.00, 0.10), (0.45, 0.10), (0.47, 0.155), (0.70, 0.14), (0.72, 0.13), (0.735, 0.25), (0.78, 0.40), (0.84, 0.55),
      (0.885, 0.68), (0.895, 0.80), (0.87, 0.88), (0.81, 0.92), (0.75, 0.90), (0.70, 0.82), (0.645, 0.72), (0.605, 0.62),
      (0.585, 0.50), (0.555, 0.40), (0.50, 0.33), (0.45, 0.275), (0.38, 0.245), (0.25, 0.23), (0.10, 0.225), (0.00, 0.21)]


@lru_cache(None)
def map_base(theme, mw, mh):
    th = THEMES[theme]
    img = Image.new("RGBA", (mw, mh), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pts = [(x * mw, y * mh) for x, y in FL]
    glow = Image.new("RGBA", (mw, mh), (0, 0, 0, 0))
    ImageDraw.Draw(glow).line(pts + [pts[0]], fill=th["accent"] + (255,), width=18)
    glow = glow.filter(ImageFilter.GaussianBlur(14))
    img.alpha_composite(glow)
    d.polygon(pts, fill=(14, 10, 32, 235), outline=th["accent"] + (255,), width=5)
    # lago
    d.ellipse([0.70 * mw, 0.60 * mh, 0.76 * mw, 0.66 * mh], fill=th["accent2"] + (90,), outline=th["accent2"] + (200,), width=3)
    # cayos
    for i in range(9):
        t = i / 8
        x = (0.83 - 0.25 * t) * mw
        y = (0.94 + 0.05 * math.sin(t * 2.6)) * mh
        d.ellipse([x - 12, y - 6, x + 12, y + 6], fill=(14, 10, 32, 255), outline=th["accent"] + (255,), width=3)
    f = font("ms", 22)
    d.text((0.06 * mw, 0.40 * mh), "GOLFO", font=f, fill=(255, 255, 255, 110))
    d.text((0.93 * mw, 0.30 * mh), "OCÉANO", font=f, fill=(255, 255, 255, 110), anchor="mm")
    return img


class Scene:
    def __init__(self, spec, theme, t_start, t_end, sent_times):
        self.spec, self.theme, self.ts, self.te, self.st = spec, theme, t_start, t_end, sent_times
        self.th = THEMES[theme]
        self.els = []
        self.dyn = None
        self.pops = []
        getattr(self, "build_" + spec["t"])()

    def at(self, i):
        i = max(0, min(i, len(self.st) - 1))
        return self.st[i][0]

    def add(self, el, pop=True):
        self.els.append(el)
        if pop and el.t0 > self.ts + 0.2:
            self.pops.append(el.t0)

    def draw(self, frame, t):
        if self.dyn:
            self.dyn(frame, t)
        for e in self.els:
            e.draw(frame, t)

    # ---- tipos
    def build_title(self):
        s = self.spec
        th = self.th
        k = pill(s["kicker"], font("bebas", 54), th["accent"], (255, 255, 255))
        title = trim(text_sprite(s["title"], fit_font("anton", s["title"], 1500, 190), fill=WHITE, stroke=8, glow=th["accent"], spacing=-10), 24)
        sub = trim(text_sprite(s["sub"], font("mx", 46), fill=YELLOW, stroke=5), 6)
        ys = stack([k.height, title.height, sub.height], [10, 20], 470)
        self.add(centered(k, ys[0], self.ts + 0.05, "pop"))
        self.add(centered(title, ys[1], self.ts + 0.2, "pop"))
        self.add(centered(sub, ys[2], self.ts + 0.6, "rise"))

    def build_big(self):
        s = self.spec
        th = self.th
        p = panel(1400, 660, outline=th["accent"] + (255,))
        self.add(centered(p, 480, self.ts, "fade"), pop=False)
        val = trim(text_sprite(s["value"], fit_font("anton", s["value"], 1200, 250), fill=YELLOW, stroke=6, glow=th["accent"]), 24)
        lab = trim(text_sprite(s["label"], fit_font("mk", s["label"], 1250, 62), fill=WHITE), 4)
        hs = [val.height, lab.height]
        n = None
        if s.get("note"):
            n = pill(s["note"], fit_font("ms", s["note"], 1150, 36), th["accent2"], BLACK)
            hs.append(n.height)
        ys = stack(hs, [10, 40], 480)
        self.add(centered(val, ys[0], self.ts + 0.15, "pop"))
        self.add(centered(lab, ys[1], self.ts + 0.45, "rise"))
        if n:
            self.add(centered(n, ys[2], self.at(1) if len(self.st) > 1 else self.ts + 0.8, "rise"))

    def _head(self, text, y=150):
        h = text_sprite(text, fit_font("anton", text, 1500, 96), fill=WHITE, stroke=6, glow=self.th["accent"])
        self.add(centered(h, y, self.ts + 0.05, "pop"), pop=False)

    def build_bullets(self):
        s = self.spec
        items = s["items"]
        n = len(items)
        self._head(s["head"])
        offset = 1 if len(self.st) > n else 0
        rowh = min(120, int(640 / n))
        top = 250 + (640 - rowh * n) // 2
        f = fit_font("mx", max(items, key=len), 1180, 56 if n <= 4 else 48)
        for i, it in enumerate(items):
            row = panel(1300, rowh - 18, fill=(10, 6, 25, 215), outline=self.th["accent"] + (200,), radius=22, width=3)
            d = ImageDraw.Draw(row)
            d.rounded_rectangle([0, 0, 22, rowh - 19], radius=10, fill=self.th["accent"])
            d.text((60, (rowh - 18) / 2), it, font=f, fill=WHITE, anchor="lm")
            self.add(El(row, (W - 1300) // 2, top + i * rowh, self.at(i + offset), "left"))

    def build_alert(self):
        s = self.spec
        red = (255, 45, 60)
        items = s["items"]
        p = panel(1440, 700, fill=(25, 0, 6, 225), outline=red + (255,), width=6)
        d = ImageDraw.Draw(p)
        for x in range(0, 1440, 60):
            d.polygon([(x, 0), (x + 30, 0), (x + 10, 26), (x - 20, 26)], fill=(255, 210, 0, 255))
        self.add(centered(p, 480, self.ts, "fade"), pop=False)
        ic = icon("warning", 130, (255, 210, 0, 255))
        self.add(El(ic, 300, 175, self.ts + 0.1, "pop"))
        h = text_sprite(s["head"], fit_font("anton", s["head"], 1000, 92), fill=WHITE, stroke=5)
        self.add(El(h, 460, 240 - h.height // 2, self.ts + 0.1, "left"), pop=False)
        n = len(items)
        f = fit_font("mx", max(items, key=len), 1150, 52)
        sent_per = max(1, len(self.st) // n)
        for i, it in enumerate(items):
            row = Image.new("RGBA", (1280, 110), (0, 0, 0, 0))
            d = ImageDraw.Draw(row)
            d.text((0, 55), "✕" if False else "×", font=font("mk", 80), fill=red, anchor="lm")
            d.text((80, 55), it, font=f, fill=WHITE, anchor="lm")
            t0 = self.at(min(i * sent_per, len(self.st) - 1)) + (0.3 if i == 0 else 0)
            self.add(El(row, 330, 340 + i * 130, t0, "left"))

    def build_table(self):
        s = self.spec
        th = self.th
        self._head(s["head"], 130)
        rows, cols = s["rows"], s["cols"]
        cw = [760, 380, 340]
        tw = sum(cw)
        x0 = (W - tw) // 2
        rh = min(98, int(660 / (len(rows) + 1)))
        hdr = panel(tw, rh - 10, fill=th["accent"] + (255,), radius=18)
        d = ImageDraw.Draw(hdr)
        fx = font("mk", 36)
        cx = 0
        for c, wv in zip(cols, cw):
            d.text((cx + 34, (rh - 10) / 2), c, font=fx, fill=WHITE, anchor="lm")
            cx += wv
        self.add(El(hdr, x0, 220, self.ts + 0.2, "rise"), pop=False)
        f = fit_font("mx", max((r[0] for r in rows), key=len), cw[0] - 60, 42)
        fb = font("anton", 50)
        for i, r in enumerate(rows):
            row = panel(tw, rh - 10, fill=(10, 6, 25, 220), outline=th["accent"] + (150,), radius=18, width=2)
            d = ImageDraw.Draw(row)
            cx = 0
            for j, (c, wv) in enumerate(zip(r, cw)):
                if j == 0:
                    d.text((cx + 34, (rh - 10) / 2), c, font=f, fill=WHITE, anchor="lm")
                else:
                    ff = fit_font("anton", c, wv - 50, 50) if j == len(r) - 1 else fit_font("ms", c, wv - 50, 38)
                    d.text((cx + 34, (rh - 10) / 2), c, font=ff, fill=YELLOW if j == len(r) - 1 else (220, 220, 235), anchor="lm")
                cx += wv
            at = s.get("at", list(range(len(rows))))[i]
            self.add(El(row, x0, 220 + (i + 1) * rh, self.at(at), "left"))

    def build_timeline(self):
        s = self.spec
        th = self.th
        self._head(s["head"], 140)
        items = s["items"]
        n = len(items)
        offset = 1 if len(self.st) > n else 0
        y0 = 270
        step = min(170, int(560 / n))
        line = Image.new("RGBA", (10, step * (n - 1) + 20), th["accent"] + (255,))
        self.add(El(line, 345, y0 + 40, self.ts + 0.3, "fade"), pop=False)
        fd = font("anton", 64)
        f = fit_font("mx", max((b for a, b in items), key=len), 1150, 46)
        for i, (date, txt) in enumerate(items):
            row = Image.new("RGBA", (1600, 120), (0, 0, 0, 0))
            d = ImageDraw.Draw(row)
            d.ellipse([10, 30, 70, 90], fill=th["accent"], outline=WHITE, width=6)
            d.text((110, 60), date, font=fd, fill=YELLOW, anchor="lm", stroke_width=3, stroke_fill=BLACK)
            dw = fd.getbbox(date)[2]
            pnl_x = 110 + max(dw, 260) + 40
            bb = f.getbbox(txt)
            d.rounded_rectangle([pnl_x - 24, 18, pnl_x + bb[2] + 30, 102], radius=20, fill=(10, 6, 25, 220))
            d.text((pnl_x, 60), txt, font=f, fill=WHITE, anchor="lm")
            self.add(El(row, 310, y0 + i * step, self.at(i + offset), "left"))

    def build_versus(self):
        s = self.spec
        th = self.th
        for side, (spec, x, col) in enumerate([(s["left"], 200, th["accent2"]), (s["right"], 1000, th["accent"])]):
            p = panel(720, 700, outline=col + (255,), width=6)
            d = ImageDraw.Draw(p)
            d.text((360, 90), spec["name"], font=font("anton", 90), fill=WHITE, anchor="mm")
            d.text((360, 215), spec["price"], font=font("anton", 120), fill=YELLOW, anchor="mm", stroke_width=4, stroke_fill=BLACK)
            for i, it in enumerate(spec["items"]):
                d.text((70, 360 + i * 95), "✓" if False else "+", font=font("mk", 56), fill=col, anchor="lm")
                d.text((130, 360 + i * 95), it, font=fit_font("mx", it, 540, 46), fill=WHITE, anchor="lm")
            t0 = self.ts + 0.1 if side == 0 else self.at(2)
            self.add(El(p, x, 120, t0, "left" if side == 0 else "right"))
        vs = text_sprite("VS", font("anton", 150), fill=YELLOW, stroke=8, glow=th["accent"])
        self.add(centered(vs, 470, self.at(2) + 0.3, "pop"))

    def build_card(self):
        s = self.spec
        th = self.th
        col = {"pink": (255, 60, 160), "cyan": (0, 220, 255)}[s["color"]]
        # silueta genérica (sin parecido a nadie)
        sil = Image.new("RGBA", (560, 720), (0, 0, 0, 0))
        d = ImageDraw.Draw(sil)
        d.rounded_rectangle([0, 0, 559, 719], radius=30, fill=(10, 6, 25, 230), outline=col + (255,), width=6)
        grad = Image.fromarray(_vgrad(548, 708, [col, (20, 10, 40)])).convert("RGBA")
        m = Image.new("L", (548, 708), 0)
        md = ImageDraw.Draw(m)
        md.ellipse([174, 120, 374, 340], fill=255)
        md.pieslice([64, 330, 484, 860], 180, 360, fill=255)
        md.rectangle([64, 595, 484, 708], fill=255)
        grad.putalpha(m)
        sil.paste(grad, (6, 6), grad)
        f = font("anton", 140)
        ImageDraw.Draw(sil).text((280, 250), "?", font=f, fill=(255, 255, 255, 60), anchor="mm")
        self.add(El(sil, 170, 150, self.ts + 0.05, "left"))
        role = pill(s["role"].upper(), font("bebas", 46), col, BLACK)
        self.add(El(role, 800, 170, self.ts + 0.2, "right"), pop=False)
        nm = text_sprite(s["name"], fit_font("anton", s["name"], 1000, 130), fill=WHITE, stroke=6, glow=col, align="left")
        self.add(El(nm, 760, 230, self.ts + 0.3, "right"), pop=False)
        f = fit_font("mx", max(s["traits"], key=len), 900, 46)
        for i, tr in enumerate(s["traits"]):
            row = panel(980, 100, fill=(10, 6, 25, 220), outline=col + (200,), radius=20, width=3)
            d = ImageDraw.Draw(row)
            d.text((40, 50), tr, font=f, fill=WHITE, anchor="lm")
            self.add(El(row, 800, 470 + i * 120, self.at(min(i, len(self.st) - 1)) + (0.6 if i == 0 else 0), "right"))

    def build_map(self):
        s = self.spec
        th = self.th
        focus = s.get("focus")
        mw, mh = 860, 690
        mx, my = 120 if focus else 530, 120
        base = map_base(self.theme, mw, mh)
        self.add(El(base, mx, my, self.ts, "fade" if focus else "pop"), pop=False)
        f = font("mx", 30)
        names = list(REGIONS.keys())
        for i, name in enumerate(names):
            (rx, ry), sub, kw = REGIONS[name]
            px, py = mx + rx * mw, my + ry * mh
            on = (name == focus)
            lab = Image.new("RGBA", (420, 60), (0, 0, 0, 0))
            d = ImageDraw.Draw(lab)
            dot = th["accent2"] if on else YELLOW
            d.ellipse([4, 14, 36, 46], fill=dot, outline=BLACK, width=3)
            d.text((48, 30), name, font=f, fill=WHITE if (on or not focus) else (200, 200, 210), anchor="lm", stroke_width=4, stroke_fill=BLACK)
            lx = px - 20
            if rx > 0.8:
                lx = px - 20 - (f.getbbox(name)[2] + 50) + 40
                lab = lab.transpose(Image.FLIP_LEFT_RIGHT)
                lab = Image.new("RGBA", (420, 60), (0, 0, 0, 0))
                d = ImageDraw.Draw(lab)
                tw = f.getbbox(name)[2]
                d.text((4, 30), name, font=f, fill=WHITE, anchor="lm", stroke_width=4, stroke_fill=BLACK)
                d.ellipse([tw + 16, 14, tw + 48, 46], fill=dot, outline=BLACK, width=3)
                lx = px - (tw + 32)
            t0 = (self.ts + 0.3 + i * 0.35) if not focus else self.ts
            self.add(El(lab, lx, py - 30, t0, "pop" if not focus else "none"), pop=not focus)
        if focus:
            (rx, ry), sub, kw = REGIONS[focus]
            px, py = mx + rx * mw, my + ry * mh
            col = th["accent2"]

            def dyn(frame, t, px=px, py=py, col=col):
                if t < self.ts:
                    return
                d = ImageDraw.Draw(frame, "RGBA")
                for k in range(2):
                    ph = ((t - self.ts) * 0.9 + k * 0.5) % 1.0
                    r = 20 + 90 * ph
                    a = int(255 * (1 - ph))
                    d.ellipse([px - r, py - r, px + r, py + r], outline=col + (a,), width=6)
            self.dyn = dyn
            card = panel(760, 560, outline=col + (255,), width=5)
            d = ImageDraw.Draw(card)
            d.text((50, 70), sub.upper(), font=font("bebas", 52), fill=col, anchor="lm")
            fn = fit_font("anton", focus.upper(), 660, 110)
            d.text((50, 170), focus.upper(), font=fn, fill=WHITE, anchor="lm", stroke_width=3, stroke_fill=BLACK)
            for i, k in enumerate(kw):
                d.rounded_rectangle([50, 280 + i * 110, 710, 370 + i * 110], radius=18, fill=(255, 255, 255, 25))
                d.text((80, 325 + i * 110), k, font=fit_font("mx", k, 600, 42), fill=WHITE, anchor="lm")
            self.add(El(card, 1060, 220, self.ts + 0.15, "right"))
        else:
            note = pill("Esquema orientativo · no es el mapa oficial", font("ms", 30), (255, 255, 255), BLACK)
            self.add(centered(note, 160, self.ts + 0.5, "rise"), pop=False)

    def build_outro(self):
        th = self.th
        t = text_sprite("¡SUSCRÍBETE!", font("anton", 190), fill=WHITE, stroke=8, glow=th["accent"])
        self.add(centered(t, 330, self.ts + 0.05, "pop"))
        b = pill("ACTIVA LA CAMPANA 🔔".replace(" 🔔", ""), font("anton", 70), (230, 30, 40), WHITE, padx=60, pady=24)
        self.add(centered(b, 560, self.ts + 0.4, "pop"))
        c = text_sprite("Guías de GTA 6 cada día · ¿Desde qué país juegas?", font("mx", 44), fill=YELLOW, stroke=4)
        self.add(centered(c, 700, self.at(1), "rise"))


# ------------------------------------------------------------------ subtítulos
def caption_chunks(sentence, t0, t1, maxw=6, maxc=34):
    words = sentence.split()
    chunks, cur = [], []
    for w in words:
        if cur and (len(cur) >= maxw or len(" ".join(cur + [w])) > maxc):
            chunks.append(cur)
            cur = []
        cur.append(w)
        if w.endswith((",", ".", "?", "!", ":")) and len(cur) >= 3:
            chunks.append(cur)
            cur = []
    if cur:
        chunks.append(cur)
    total = sum(len(w) + 1 for w in words)
    out = []
    t = t0
    for ch in chunks:
        wt = []
        for w in ch:
            dt = (t1 - t0) * (len(w) + 1) / total
            wt.append((w, t, t + dt))
            t += dt
        out.append(wt)
    return out


@lru_cache(maxsize=256)
def caption_img(words, hi):
    f = font("mk", 58)
    parts = list(words)
    sp = f.getbbox(" ")[2]
    ws = [f.getbbox(w)[2] for w in parts]
    tw = sum(ws) + sp * (len(parts) - 1)
    img = Image.new("RGBA", (tw + 40, 110), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    x = 20
    for i, w in enumerate(parts):
        col = YELLOW if i == hi else WHITE
        d.text((x, 55), w, font=f, fill=col, anchor="lm", stroke_width=8, stroke_fill=BLACK)
        x += ws[i] + sp
    return img


def draw_caption(frame, chunks_flat, t):
    for ch in chunks_flat:
        if ch[0][1] <= t < ch[-1][2] + 0.05:
            hi = 0
            for i, (w, a, b) in enumerate(ch):
                if a <= t:
                    hi = i
            img = caption_img(tuple(w for w, a, b in ch), hi)
            frame.paste(img, ((W - img.width) // 2, 960 - img.height // 2), img)
            return


@lru_cache(None)
def watermark(channel):
    f = font("bebas", 40)
    img = pill(channel, f, (0, 0, 0, 150), WHITE, padx=24, pady=10)
    return img
