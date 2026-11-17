"""Narración con Kokoro (voz em_alex, español) vía sherpa-onnx."""
import re, os
import numpy as np
import sherpa_onnx

MODEL_DIR = os.environ.get("KOKORO_DIR", "/tmp/claude-0/tts/kokoro-multi-lang-v1_0")
SR = 24000
SPEAKER = 29  # em_alex

# Pronunciación: el texto en pantalla se queda igual, la voz lee esto.
PRON = [
    (r"\bGTA\+", "Ge te a plus"), (r"00:00", "doce de la noche"), (r"\b0(\d):00", r"\1 en punto"),
    (r"\bGTA\s*VI\b", "Ge te a seis"), (r"\bGTA\s*6\b", "Ge te a seis"), (r"\bGTA\s*V\b", "Ge te a cinco"),
    (r"\bGTA\s*5\b", "Ge te a cinco"), (r"\bGTA\b", "Ge te a"),
    (r"Vice City", "Váis Síti"), (r"\bJason\b", "Yéison"), (r"\bUltimate\b", "Últimeit"),
    (r"Xbox Series X\|S", "Equis box Series Equis y Ese"), (r"Series X\|S", "Series Equis y Ese"),
    (r"Series S", "Series Ese"), (r"Series X", "Series Equis"), (r"\bXbox\b", "Équis box"),
    (r"\bPS5 Pro\b", "Pé Ése cinco Pro"), (r"\bPS5\b", "Pé Ése cinco"), (r"\bPS4\b", "Pé Ése cuatro"),
    (r"\bPlayStation\b", "Pléisteishon"), (r"\bPC\b", "Pe Ce"), (r"\bGB\b", "gigas"), (r"\bTB\b", "teras"),
    (r"\bSSD\b", "ese ese de"), (r"\bM\.2\b", "eme punto dos"), (r"\bUSB\b", "u ese be"), (r"\bHDR\b", "hache de erre"),
    (r"Rockstar Games", "Rócstar Guéims"), (r"\bRockstar\b", "Rócstar"), (r"Take-Two", "Teik Tu"),
    (r"GTA Online", "Ge te a onlain"), (r"\bOnline\b", "Onlain"), (r"\bonline\b", "onlain"),
    (r"Red Dead Redemption 2", "Red Ded Redémshon dos"), (r"Red Dead Online", "Red Ded onlain"), (r"Red Dead", "Red Ded"),
    (r"\btrailers?\b", "tréiler"), (r"\btráilers?\b", "tréiler"), (r"Social Club", "Sóshal Clab"),
    (r"Leonida Keys", "Leonida Kis"), (r"Port Gellhorn", "Port Guélhorn"), (r"Grassrivers", "Gras Rívers"),
    (r"Mount Kalaga", "Maunt Kalaga"), (r"\bspoilers?\b", "espóiler"), (r"\bstreamers?\b", "estrímer"),
    (r"\bYouTube\b", "Yutub"), (r"\bTikTok\b", "Tictoc"), (r"\bAPK\b", "a pe ca"), (r"\bmalware\b", "málguer"),
    (r"\bfps\b", "efe pe ese"), (r"\bHUD\b", "jud"), (r"\bpack\b", "pac"),
    (r"\bkeys?\b", "claves"), (r"\bDuval\b", "Duval"), (r"\bLos Santos\b", "Los Santos"),
    (r"(\d+),(\d\d) ?€", r"\1 con \2 euros"), (r"(\d+),(\d\d) ?\$", r"\1 con \2 dólares"),
    (r"\$(\d+)\.(\d\d)", r"\1 con \2 dólares"), (r"(\d+) ?€", r"\1 euros"),
    (r"(\d{1,2}):00", r"\1 en punto"),
    (r"&", " y "), (r"\bvs\.?\b", "contra"), (r"%", " por ciento"),
]

def to_speech(text: str) -> str:
    t = text
    for a, b in PRON:
        t = re.sub(a, b, t)
    return t

_tts = None
def engine():
    global _tts
    if _tts is None:
        d = MODEL_DIR
        cfg = sherpa_onnx.OfflineTtsConfig(model=sherpa_onnx.OfflineTtsModelConfig(
            kokoro=sherpa_onnx.OfflineTtsKokoroModelConfig(model=f"{d}/model.onnx", voices=f"{d}/voices.bin",
                tokens=f"{d}/tokens.txt", data_dir=f"{d}/espeak-ng-data", lexicon="", lang="es"),
            num_threads=2))
        _tts = sherpa_onnx.OfflineTts(cfg)
    return _tts

def speak(text: str, speed: float = 1.08) -> np.ndarray:
    a = engine().generate(to_speech(text), sid=SPEAKER, speed=speed)
    x = np.asarray(a.samples, dtype=np.float32)
    # recorta silencios de los extremos
    nz = np.where(np.abs(x) > 0.01)[0]
    if len(nz):
        x = x[max(0, nz[0] - 600): nz[-1] + 1200]
    return x
