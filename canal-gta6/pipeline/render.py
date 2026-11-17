"""Renderiza un vídeo completo: python render.py 01 [--preview]"""
import os, sys, json, hashlib, subprocess, time
import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw

import guiones, tts, audio, visual as V

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "videos")
CACHE = os.environ.get("TTS_CACHE", "/tmp/claude-0/tts_cache")
os.makedirs(CACHE, exist_ok=True)
os.makedirs(OUT, exist_ok=True)

GAP_SENT = 0.32
GAP_SCENE = 0.55
LEAD_IN = 0.5
TAIL = 1.6


def voice_for(sentence):
    key = hashlib.md5(("v3|" + sentence).encode()).hexdigest()
    p = os.path.join(CACHE, key + ".wav")
    if not os.path.exists(p):
        x = tts.speak(sentence)
        sf.write(p, x, tts.SR)
    x, sr = sf.read(p, dtype="float32")
    return audio.to_sr(x, sr)


def build_timeline(video):
    """Devuelve escenas con tiempos y la pista de voz."""
    t = LEAD_IN
    chunks = []
    scenes = []
    for sc in video["scenes"]:
        ts = t
        st = []
        for s in sc["say"]:
            x = voice_for(s)
            d = len(x) / audio.SR
            st.append((t, t + d, s))
            chunks.append((t, x))
            t += d + GAP_SENT
        t += GAP_SCENE - GAP_SENT
        scenes.append((sc, ts, st))
    total = t + TAIL
    voice = np.zeros(int(total * audio.SR) + 1)
    for t0, x in chunks:
        p = int(t0 * audio.SR)
        voice[p:p + len(x)] += x * 0.95
    out = []
    for i, (sc, ts, st) in enumerate(scenes):
        te = scenes[i + 1][1] if i + 1 < len(scenes) else total
        out.append((sc, ts, te, st))
    return out, voice, total


def srt_time(t):
    h, r = divmod(t, 3600)
    m, s = divmod(r, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int((s % 1) * 1000):03d}"


def write_srt(path, caps):
    with open(path, "w", encoding="utf-8") as f:
        for i, ch in enumerate(caps, 1):
            f.write(f"{i}\n{srt_time(ch[0][1])} --> {srt_time(ch[-1][2])}\n{' '.join(w for w, a, b in ch)}\n\n")


def progress_bar(frame, t, total, col):
    d = ImageDraw.Draw(frame)
    d.rectangle([0, 0, V.W, 8], fill=(0, 0, 0))
    d.rectangle([0, 0, int(V.W * t / total), 8], fill=col)


def render(vid, preview=False):
    video = next(v for v in guiones.VIDEOS if v["id"] == vid)
    theme = video["theme"]
    t_start = time.time()
    tl, voice, total = build_timeline(video)
    scenes = [V.Scene(sc, theme, ts, te, st) for sc, ts, te, st in tl]
    caps = []
    for sc, ts, te, st in tl:
        for a, b, s in st:
            caps += V.caption_chunks(s, a, b)
    base = os.path.join(OUT, f"{vid}-{video['slug']}")
    write_srt(base + ".srt", caps)

    whoosh_at = [ts for sc, ts, te, st in tl][1:]
    pops = sorted(p for s in scenes for p in s.pops)
    mix = audio.mix(voice, total, theme if theme in audio.STYLES else "sunset", whoosh_at, pops)
    wav = f"/tmp/claude-0/{vid}_mix.wav"
    sf.write(wav, mix, audio.SR)

    nframes = int(total * V.FPS)
    if preview:
        os.makedirs(base + "_preview", exist_ok=True)
        for s in scenes:
            t = min(s.te - 0.1, max((e.t0 for e in s.els), default=s.ts) + 0.8)
            fr = frame_at(scenes, caps, theme, t, total, video)
            fr.save(os.path.join(base + "_preview", f"{int(s.ts*10):05d}_{s.spec['t']}.jpg"), quality=85)
        print("preview ok", total)
        return
    out_mp4 = base + ".mp4"
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{V.W}x{V.H}", "-r", str(V.FPS),
           "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
           "-profile:v", "high", "-movflags", "+faststart", "-c:a", "aac", "-b:a", "192k",
           "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "48000", "-shortest", out_mp4]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(nframes):
        fr = frame_at(scenes, caps, theme, i / V.FPS, total, video, i)
        p.stdin.write(fr.tobytes())
    p.stdin.close()
    p.wait()
    meta = {"id": vid, "duration": round(total, 2), "scenes": [(sc["t"], round(ts, 2)) for sc, ts, te, st in tl],
            "render_s": round(time.time() - t_start, 1)}
    json.dump(meta, open(base + ".json", "w"), ensure_ascii=False, indent=1)
    print(vid, "OK", round(total, 1), "s en", meta["render_s"], "s")


def frame_at(scenes, caps, theme, t, total, video, idx=None):
    idx = int(t * V.FPS) if idx is None else idx
    fr = V.background(theme, idx)
    th = V.THEMES[theme]
    # oscurecer para legibilidad
    dark = _dark()
    fr.paste(dark, (0, 0), dark)
    cur = None
    for s in scenes:
        if s.ts <= t < s.te:
            cur = s
    if cur is None:
        cur = scenes[-1]
    cur.draw(fr, t)
    # flash de transición
    dt = t - cur.ts
    if cur is not scenes[0] and dt < 0.22:
        a = int(170 * (1 - dt / 0.22))
        fl = Image.new("RGBA", (V.W, V.H), (255, 255, 255, a))
        fr.paste(fl, (0, 0), fl)
    V.draw_caption(fr, caps, t)
    wm = V.watermark(guiones.CANAL)
    fr.paste(wm, (40, 34), wm)
    progress_bar(fr, t, total, th["accent"])
    return fr


_D = None
def _dark():
    global _D
    if _D is None:
        _D = Image.new("RGBA", (V.W, V.H), (0, 0, 0, 125))
    return _D


if __name__ == "__main__":
    vid = sys.argv[1]
    render(vid, preview="--preview" in sys.argv)
