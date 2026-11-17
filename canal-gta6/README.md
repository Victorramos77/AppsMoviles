# Canal GTA 6 · "MODO LEONIDA": 10 vídeos de lanzamiento

Diez vídeos en español pensados para el lanzamiento de GTA 6 (jueves 19/11/2026). Cada uno responde a una de las búsquedas que más se disparan ese día.

## Qué hay en `videos/`

Para cada vídeo hay:

| Archivo | Qué es |
|---|---|
| `NN-tema.mp4` | Vídeo final 1920×1080, 30 fps, H.264 + AAC, audio normalizado a -14 LUFS (el nivel de YouTube) |
| `NN-tema-miniatura.jpg` | Miniatura 1280×720 |
| `NN-tema.srt` | Subtítulos en español para subirlos a YouTube (además, el vídeo ya los lleva incrustados) |
| `NN-tema-ficha.txt` | Título, descripción con capítulos, etiquetas, hora de publicación y ajustes para subirlo |

Otros documentos:
- `CALENDARIO.md`: el orden y la hora de publicación de cada vídeo.
- `GUIONES.md`: los 10 guiones completos.
- `FUENTES.md`: de dónde sale cada dato y qué conviene volver a comprobar.

## Los 10 vídeos

1. ¿A qué hora sale GTA 6? Horario por país
2. Precio y ediciones: ¿Estándar o Ultimate?
3. ¿Cuánto ocupa? Cómo liberar espacio en PS5 y Xbox
4. ¿Tiene online?
5. ¿Sale en PC?
6. Lucía y Jason, y los personajes confirmados
7. El mapa de Leonida, región por región
8. 10 cosas que hacer antes de jugar
9. Todo lo que sabemos en 5 minutos
10. Estafas de GTA 6 (APK, PC gratis, claves…)

## Al subirlos a YouTube

- **Contenido alterado o sintético: marca "Sí".** La voz está generada por síntesis (Kokoro TTS). YouTube pide declararlo.
- Ninguno es "contenido para niños". La categoría es "Videojuegos".
- Todo lo que se ve y se oye es de creación propia: los gráficos, la música (sintetizada por código) y la voz. **No se ha usado material de Rockstar** (ni tráileres, ni capturas, ni logotipos), así que no debería haber reclamaciones de Content ID.
- Antes de publicar, repasa en `FUENTES.md` los datos marcados con ⚠️.

## Cómo regenerarlos (si cambia algún dato)

Edita `pipeline/guiones.py` y vuelve a renderizar:

```bash
cd pipeline
pip install sherpa-onnx==1.12.40 soundfile scipy pillow numpy
# Modelo de voz: kokoro-multi-lang-v1_0 (releases "tts-models" de k2-fsa/sherpa-onnx en GitHub)
export KOKORO_DIR=/ruta/a/kokoro-multi-lang-v1_0
python render.py 01 --preview   # fotogramas de prueba, en segundos
python render.py 01             # vídeo final (unos minutos)
python publicar.py              # miniaturas, fichas y calendario
```

- La pronunciación de las palabras en inglés (GTA, Vice City, PS5…) se ajusta en `pipeline/tts.py`, en `PRON`.
- El nombre del canal se cambia en `pipeline/guiones.py`, en `CANAL` y `HANDLE`.

Fuentes tipográficas: Anton, Bebas Neue y Montserrat (licencia SIL OFL, incluida en `pipeline/fonts/`).
