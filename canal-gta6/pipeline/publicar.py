"""Genera miniaturas (1280x720) y fichas de subida (título, descripción con capítulos, etiquetas)."""
import os, json
from PIL import Image, ImageDraw, ImageFilter
import guiones, visual as V

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "videos")

# Horario de publicación recomendado (jueves 19/11/2026, hora peninsular española)
HORARIO = {
    "01": "Jueves 19 · 00:00 (justo al desbloquearse en España; en Latinoamérica aún faltan horas)",
    "02": "Jueves 19 · 00:30",
    "03": "Jueves 19 · 01:00",
    "09": "Jueves 19 · 08:00",
    "08": "Jueves 19 · 10:00",
    "04": "Jueves 19 · 12:00",
    "06": "Jueves 19 · 14:00",
    "07": "Jueves 19 · 16:00",
    "05": "Jueves 19 · 18:00",
    "10": "Jueves 19 · 20:00",
}


def nice(s):
    s = s[:1].upper() + s[1:].lower()
    for a, b in [("ultimate", "Ultimate"), ("gta", "GTA"), ("rockstar", "Rockstar"), ("leonida", "Leonida"), ("¿m", "¿M"), ("¿y", "¿Y"), ("¿c", "¿C"), ("¿t", "¿T"), ("¿q", "¿Q")]:
        s = s.replace(a, b)
    import re
    for a, b in [(r"\bpc\b", "PC"), (r"\bapk\b", "APK"), (r"\bv$", "V"), (r"zelanda", "Zelanda")]:
        s = re.sub(a, b, s)
    return s


def chapter_label(sc):
    t = sc["t"]
    if t == "title":
        return "Intro"
    if t == "outro":
        return "Despedida"
    if t == "map":
        return sc.get("focus") or "Vista general de Leonida"
    if t == "card":
        return sc["name"].title()
    if t == "versus":
        return "Estándar vs Ultimate"
    if t == "big":
        return nice(sc["label"])
    return nice(sc["head"])


def mmss(t):
    t = int(t)
    return f"{t // 60}:{t % 60:02d}"


def thumbnail(v):
    th = V.THEMES[v["theme"]]
    bg = V.background(v["theme"], 10).resize((1280, 720), Image.LANCZOS)
    img = bg.convert("RGBA")
    dark = Image.new("RGBA", img.size, (0, 0, 0, 70))
    img.alpha_composite(dark)
    # degradado lateral para el texto
    grad = Image.new("L", (1280, 720))
    gd = ImageDraw.Draw(grad)
    for x in range(1280):
        gd.line([(x, 0), (x, 720)], fill=int(max(0, 200 - x * 0.22)))
    sh = Image.new("RGBA", img.size, (0, 0, 0, 255))
    sh.putalpha(grad)
    img.alpha_composite(sh)
    # icono con brillo a la derecha
    ic = V.icon(v["thumb_icon"], 320, th["accent2"] + (255,))
    glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    glow.paste(ic, (920, 230), ic)
    glow = glow.filter(ImageFilter.GaussianBlur(25))
    img.alpha_composite(glow)
    img.alpha_composite(glow)
    icw = V.icon(v["thumb_icon"], 320, (255, 255, 255, 255))
    img.paste(icw, (920, 230), icw)
    # texto
    l1, l2 = v["thumb"]
    f1 = V.fit_font("anton", l1, 800, 170)
    f2 = V.fit_font("anton", l2, 780, 170)
    s1 = V.trim(V.text_sprite(l1, f1, fill=V.WHITE, stroke=10), 2)
    s2 = V.trim(V.text_sprite(l2, f2, fill=V.YELLOW, stroke=10, glow=th["accent"]), 10)
    y = 360 - (s1.height + s2.height + 10) // 2 + 40
    img.alpha_composite(s1, (50, y))
    img.alpha_composite(s2, (50 - 10, y + s1.height + 10 - 10))
    # badge
    b = V.pill(v["thumb_badge"], V.font("anton", 64), (230, 30, 40), V.WHITE, padx=34, pady=18)
    b = b.rotate(4, expand=True, resample=Image.BICUBIC)
    img.alpha_composite(b, (60, 40))
    # sello GTA 6
    tag = V.pill("GTA 6", V.font("anton", 56), V.YELLOW, V.BLACK, padx=28, pady=12)
    img.alpha_composite(tag, (1280 - tag.width - 40, 40))
    # marco
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 1279, 719], outline=th["accent"] + (255,), width=10)
    return img.convert("RGB")


DISCLAIMER = ("Canal no oficial. No afiliado a Rockstar Games ni a Take-Two Interactive. "
              "Grand Theft Auto y GTA son marcas de sus respectivos propietarios. "
              "Gráficos, música y voz de este vídeo son de creación propia. "
              "Información comprobada a 17/11/2026: confirma precios y horarios en tu tienda.")

HASHTAGS = "#GTA6 #GTAVI #GrandTheftAuto6"


def description(v, meta):
    first = " ".join(v["scenes"][0]["say"])
    lines = [first, ""]
    lines.append("⏱️ CAPÍTULOS")
    seen = set()
    last = -99
    for (t, ts), sc in zip(meta["scenes"], v["scenes"]):
        lab = chapter_label(sc)
        if lab in seen or (ts - last) < 10:
            continue
        seen.add(lab)
        lines.append(f"{'0:00' if last < 0 else mmss(ts)} {lab}")
        last = ts
    lines += ["", "🔔 Suscríbete para guías de GTA 6 cada día: " + guiones.HANDLE, "",
              "💬 ¿Desde qué país juegas? Te leo en los comentarios.", "", DISCLAIMER, "", HASHTAGS]
    return "\n".join(lines)


def main():
    rows = []
    for v in guiones.VIDEOS:
        base = os.path.join(OUT, f"{v['id']}-{v['slug']}")
        thumbnail(v).save(base + "-miniatura.jpg", quality=92)
        meta = json.load(open(base + ".json")) if os.path.exists(base + ".json") else None
        desc = description(v, meta) if meta else "(renderiza el vídeo para generar capítulos)"
        tags = ", ".join(v["tags"] + ["gta 6 español", "grand theft auto 6", "leonida", "vice city"])
        txt = (f"TÍTULO:\n{v['title']}\n\nDESCRIPCIÓN:\n{desc}\n\nETIQUETAS:\n{tags}\n\n"
               f"PUBLICAR: {HORARIO[v['id']]}\nSUBTÍTULOS: subir {v['id']}-{v['slug']}.srt (Español)\n"
               f"MINIATURA: {v['id']}-{v['slug']}-miniatura.jpg\n"
               f"AJUSTES: No es para niños · Categoría Videojuegos · Idioma Español · Contenido alterado/sintético: SÍ (voz generada)\n")
        open(base + "-ficha.txt", "w", encoding="utf-8").write(txt)
        dur = mmss(meta["duration"]) if meta else "?"
        rows.append((v["id"], v["title"], dur, HORARIO[v["id"]]))
    with open(os.path.join(OUT, "..", "CALENDARIO.md"), "w", encoding="utf-8") as f:
        f.write("# Calendario de publicación (hora peninsular española)\n\n| # | Título | Duración | Publicar |\n|---|---|---|---|\n")
        order = list(HORARIO)
        for r in sorted(rows, key=lambda r: order.index(r[0])):
            f.write(f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} |\n")
    print("ok")


if __name__ == "__main__":
    main()
