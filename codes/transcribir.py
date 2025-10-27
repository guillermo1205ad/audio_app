#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Transcriptor por lotes con Whisper (chunked) — versión uv + ffmpeg embebido
---------------------------------------------------------------------------
Lee todos los .mp3 desde AUDIOS_PATH, genera JSON, TXT y CSV con timestamps.
No requiere ffmpeg del sistema: usa imageio-ffmpeg embebido (sin sudo).

Variables de entorno útiles:
----------------------------
WHISPER_MODEL_NAME=large-v3
CUDA_VISIBLE_DEVICES=2         # 0 o 2 → RTX 6000 Ada, 1 → Blackwell
MAX_WORKERS=2                  # Número de hilos simultáneos
"""

import os
import gc
import csv
import json
import logging
import threading
import tempfile
import stat
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

import torch
import whisper
import imageio_ffmpeg


# ======================================================
# 1️⃣ CONFIGURACIÓN GENERAL (variables de entorno)
# ======================================================

# --- Integrar ffmpeg embebido desde imageio-ffmpeg (sin sudo) ---
ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

# Crear wrapper ejecutable temporal (alias "ffmpeg")
wrapper_dir = os.path.join(tempfile.gettempdir(), "ffmpeg_wrapper")
os.makedirs(wrapper_dir, exist_ok=True)
wrapper_path = os.path.join(wrapper_dir, "ffmpeg")

with open(wrapper_path, "w", encoding="utf-8") as f:
    f.write(f"#!/usr/bin/env bash\n\"{ffmpeg_exe}\" \"$@\"\n")

# Hacer ejecutable el wrapper
os.chmod(wrapper_path, os.stat(wrapper_path).st_mode | stat.S_IEXEC)

# Inyectar al PATH
os.environ["PATH"] = wrapper_dir + os.pathsep + os.path.dirname(ffmpeg_exe) + os.pathsep + os.environ.get("PATH", "")

# Validar ffmpeg embebido
if not os.path.exists(ffmpeg_exe):
    sys.exit(f"❌ No se encontró ffmpeg embebido: {ffmpeg_exe}")
print(f"✅ ffmpeg embebido cargado: {ffmpeg_exe}")

# Fijar GPU por defecto (Ada = 0)
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "0")

# Variables de entorno
AUDIO_INPUT_DIR = os.getenv("AUDIOS_PATH", os.path.join(os.getcwd(), "pruebas"))
MODEL_DIR       = os.getenv("WHISPER_PATH", os.path.join(os.getcwd(), "large-v3"))
MODEL_NAME      = os.getenv("WHISPER_MODEL_NAME", "large-v3")
MAX_WORKERS     = int(os.getenv("MAX_WORKERS", "2"))

# Torch config
torch.set_float32_matmul_precision("high")
torch.backends.cudnn.benchmark = False
torch.backends.cudnn.enabled   = False
torch.backends.cuda.matmul.allow_tf32 = False
torch.backends.cudnn.allow_tf32        = False

device = "cuda" if torch.cuda.is_available() else "cpu"

# Crear carpeta si no existe
os.makedirs(AUDIO_INPUT_DIR, exist_ok=True)


# ======================================================
# 2️⃣ CARGA DEL MODELO (FP32)
# ======================================================
def load_whisper_model():
    """Carga el modelo Whisper (FP32) desde WHISPER_PATH."""
    model = whisper.load_model(MODEL_NAME, device=device, download_root=MODEL_DIR)
    return model.to(device).float()


model = load_whisper_model()
transcribe_lock = threading.Lock()


# ======================================================
# 3️⃣ TRANSCRIPCIÓN DE UN ARCHIVO
# ======================================================
def transcribe_file(filename: str) -> str:
    """
    Transcribe un .mp3 en chunks (~30s) y genera:
      - .json (texto + segments)
      - _timestamps.txt (por segmento + palabra)
      - .txt (texto limpio)
      - _timestamps.csv (métricas por segmento)
      - _timestamps_distribution-word.csv (palabra, probabilidad)
    """
    base = os.path.splitext(filename)[0]

    json_path        = os.path.join(AUDIO_INPUT_DIR, f"{base}.json")
    ts_txt_path      = os.path.join(AUDIO_INPUT_DIR, f"{base}_timestamps.txt")
    text_path        = os.path.join(AUDIO_INPUT_DIR, f"{base}.txt")
    seg_csv_path     = os.path.join(AUDIO_INPUT_DIR, f"{base}_timestamps.csv")
    words_csv_path   = os.path.join(AUDIO_INPUT_DIR, f"{base}_timestamps_distribution-word.csv")

    # Saltar si ya existe todo
    if all(os.path.exists(p) for p in [json_path, ts_txt_path, text_path, seg_csv_path, words_csv_path]):
        return f"{filename} → ya procesado."

    # Cargar audio
    audio_path = os.path.join(AUDIO_INPUT_DIR, filename)
    audio      = whisper.load_audio(audio_path)

    chunk_sz   = int(30 * whisper.audio.SAMPLE_RATE)
    all_segs   = []
    full_text  = []

    for start in range(0, audio.shape[0], chunk_sz):
        chunk = whisper.pad_or_trim(audio[start:start + chunk_sz])
        with transcribe_lock:
            res = model.transcribe(
                chunk,
                task="transcribe",
                verbose=False,
                word_timestamps=True,
                temperature=0.0,
                length_penalty=1.0
            )
        if not res or "segments" not in res:
            raise RuntimeError(f"Transcribe devolvió None/segments ausente en {filename}")

        offset = start / whisper.audio.SAMPLE_RATE
        for seg in res["segments"]:
            seg["start"] = float(seg["start"]) + offset
            seg["end"]   = float(seg["end"])   + offset
            all_segs.append(seg)
        full_text.append(res.get("text", "").strip())

        del res
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        gc.collect()

    # Generar salida
    output = {"text": " ".join(full_text).strip(), "segments": all_segs}

    # JSON
    with open(json_path, "w", encoding="utf-8") as f_json:
        json.dump(output, f_json, ensure_ascii=False, indent=2)

    # TXT (timestamps)
    with open(ts_txt_path, "w", encoding="utf-8") as f_ts:
        for seg in all_segs:
            f_ts.write(
                f"[{seg['start']:.2f}s–{seg['end']:.2f}s] "
                f"avg_logprob={float(seg.get('avg_logprob', float('nan'))):.3f} "
                f"compression_ratio={float(seg.get('compression_ratio', float('nan'))):.3f} "
                f"no_speech_prob={float(seg.get('no_speech_prob', float('nan'))):.3f} "
            )
            for w in seg.get("words", []):
                word = (w.get("word") or "").strip()
                prob = float(w.get("probability", float("nan")))
                f_ts.write(f"{word}({prob:.3f}) ")
            f_ts.write("\n")

    # TXT (texto limpio)
    with open(text_path, "w", encoding="utf-8") as f_txt:
        f_txt.write(output["text"])

    # CSV (segmentos)
    with open(seg_csv_path, "w", newline="", encoding="utf-8") as f_csv:
        writer = csv.writer(f_csv)
        writer.writerow(["start", "end", "avg_logprob", "compression_ratio", "no_speech_prob"])
        for seg in all_segs:
            writer.writerow([
                float(seg["start"]),
                float(seg["end"]),
                seg.get("avg_logprob"),
                seg.get("compression_ratio"),
                seg.get("no_speech_prob"),
            ])

    # CSV (palabras)
    with open(words_csv_path, "w", newline="", encoding="utf-8") as f_csv:
        writer = csv.writer(f_csv)
        writer.writerow(["start", "end", "word", "probability"])
        for seg in all_segs:
            for w in seg.get("words", []):
                writer.writerow([
                    float(seg["start"]),
                    float(seg["end"]),
                    (w.get("word") or "").strip(),
                    w.get("probability"),
                ])

    return f"{filename} → completado."


# ======================================================
# 4️⃣ MAIN
# ======================================================
if __name__ == "__main__":
    mp3_files = sorted(f for f in os.listdir(AUDIO_INPUT_DIR) if f.lower().endswith(".mp3"))
    total = len(mp3_files)

    logging.basicConfig(
        filename=os.path.join(AUDIO_INPUT_DIR, "transcription.log"),
        filemode="w",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    logging.info(f"Inicio de transcripción de {total} archivos en: {AUDIO_INPUT_DIR}")
    logging.info(f"Modelo: {MODEL_NAME} | Dir modelo: {MODEL_DIR} | device: {device}")
    logging.info(f"CUDA_VISIBLE_DEVICES = {os.environ.get('CUDA_VISIBLE_DEVICES')}")
    logging.info(f"FFmpeg embebido: {ffmpeg_exe}")
    logging.info(f"PATH activo: {os.environ['PATH']}")

    if total == 0:
        msg = f"No se encontraron .mp3 en: {AUDIO_INPUT_DIR}"
        print(msg)
        logging.warning(msg)
        raise SystemExit(0)

    completados = 0
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(transcribe_file, fn): fn for fn in mp3_files}
        for fut in as_completed(futures):
            fn = futures[fut]
            completados += 1
            try:
                result = fut.result()
                print(f"[{completados}/{total}] {result}")
                logging.info(f"[{completados}/{total}] {result}")
            except Exception as e:
                err = f"Error en {fn}: {type(e).__name__}: {e}"
                print(f"⚠️ [{completados}/{total}] {err}")
                logging.error(err, exc_info=True)