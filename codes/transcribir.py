#!/usr/bin/env python3
import os
import logging
import gc
import json
import csv
import whisper
import torch
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# ================================
# 1️⃣ CONFIGURACIÓN GENERAL
# ================================

# 📦 Ruta base (variable de entorno o valor por defecto)
BASE_DIR = os.getenv("AUDIOS_PATH", os.path.join(os.getcwd(), "AUDIOS", "pruebas"))
MODEL_DIR = os.getenv("WHISPER_MODEL_DIR", os.path.join(os.getcwd(), "models"))

# 🎧 Modelo Whisper (por variable de entorno)
WHISPER_MODEL_NAME = os.getenv("WHISPER_MODEL_NAME", "large-v3")

# ⚙️ GPU / CPU setup
torch.set_float32_matmul_precision("high")
torch.backends.cudnn.benchmark = False
torch.backends.cudnn.enabled = False
torch.backends.cuda.matmul.allow_tf32 = False
torch.backends.cudnn.allow_tf32 = False
device = "cuda" if torch.cuda.is_available() else "cpu"

# 🧠 Cargar modelo en FP32
model = whisper.load_model(WHISPER_MODEL_NAME, device=device, download_root=MODEL_DIR)
model = model.to(device).float()

# 🔒 Lock para evitar saturación de GPU
transcribe_lock = threading.Lock()


# ================================
# 2️⃣ FUNCIÓN DE TRANSCRIPCIÓN
# ================================
def transcribe_file(fn):
    base = os.path.splitext(fn)[0]
    json_path = os.path.join(BASE_DIR, f"{base}.json")
    ts_path = os.path.join(BASE_DIR, f"{base}_timestamps.txt")
    txt_path = os.path.join(BASE_DIR, f"{base}.txt")
    csv_metrics_path = os.path.join(BASE_DIR, f"{base}_timestamps.csv")
    csv_dist_path = os.path.join(BASE_DIR, f"{base}_timestamps_distribution-word.csv")

    # Saltar si ya existen los archivos finales
    if all(os.path.exists(p) for p in [json_path, ts_path, txt_path, csv_metrics_path, csv_dist_path]):
        return f"{fn} → ya procesado."

    # --- Transcripción chunked ---
    audio = whisper.load_audio(os.path.join(BASE_DIR, fn))
    chunk_sz = int(30 * whisper.audio.SAMPLE_RATE)
    all_segs, full_text = [], []

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
            raise RuntimeError(f"Transcribe devolvió None en {fn}")

        offset = start / whisper.audio.SAMPLE_RATE
        for seg in res["segments"]:
            seg["start"] += offset
            seg["end"] += offset
            all_segs.append(seg)
        full_text.append(res["text"].strip())

        # Limpieza de memoria
        del res
        torch.cuda.empty_cache()
        gc.collect()

    output = {"text": " ".join(full_text).strip(), "segments": all_segs}

    # Guardar resultados
    with open(json_path, "w", encoding="utf-8") as f_json:
        json.dump(output, f_json, ensure_ascii=False, indent=2)

    with open(ts_path, "w", encoding="utf-8") as f_ts:
        for seg in all_segs:
            f_ts.write(
                f"[{seg['start']:.2f}s–{seg['end']:.2f}s] "
                f"avg_logprob={seg.get('avg_logprob', float('nan')):.3f} "
                f"compression_ratio={seg.get('compression_ratio', float('nan')):.3f} "
                f"no_speech_prob={seg.get('no_speech_prob', float('nan')):.3f} "
            )
            for w in seg.get("words", []):
                f_ts.write(f"{w['word'].strip()}({w.get('probability', float('nan')):.3f}) ")
            f_ts.write("\n")

    with open(txt_path, "w", encoding="utf-8") as f_txt:
        f_txt.write(output["text"])

    with open(csv_metrics_path, "w", newline="", encoding="utf-8") as f_csv:
        writer = csv.writer(f_csv)
        writer.writerow(['start', 'end', 'avg_logprob', 'compression_ratio', 'no_speech_prob'])
        for seg in all_segs:
            writer.writerow([
                seg['start'], seg['end'],
                seg.get('avg_logprob'), seg.get('compression_ratio'),
                seg.get('no_speech_prob')
            ])

    with open(csv_dist_path, "w", newline="", encoding="utf-8") as f_csv:
        writer = csv.writer(f_csv)
        writer.writerow(['start', 'end', 'word', 'probability'])
        for seg in all_segs:
            for w in seg.get("words", []):
                writer.writerow([seg['start'], seg['end'], w["word"].strip(), w.get("probability", None)])

    return f"{fn} → completado."


# ================================
# 3️⃣ MAIN
# ================================
if __name__ == "__main__":
    mp3_files = sorted(f for f in os.listdir(BASE_DIR) if f.lower().endswith(".mp3"))
    total = len(mp3_files)
    completados = 0

    logging.basicConfig(
        filename=os.path.join(BASE_DIR, "transcription.log"),
        filemode="w",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    logging.info(f"Inicio de transcripción de {total} archivos")

    with ThreadPoolExecutor(max_workers=2) as executor:
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