#!/usr/bin/env python3
import os
import glob
import json
import numpy as np

# --- CONFIGURACIÓN ---
INPUT_DIR = os.getenv("AUDIOS_PATH", os.path.join(os.getcwd(), "AUDIOS", "pruebas"))
PERCENTILE_AVG = 90   # percentil global para marcar revisión de segmentos
PERCENTILE_WORDS = 95 # percentil local por palabras

# Asegurarse de que existan archivos
json_files = glob.glob(os.path.join(INPUT_DIR, "*_web_ready.json"))
if not json_files:
    print(f"[WARN] No se encontraron archivos *_web_ready.json en {INPUT_DIR}")
else:
    print(f"📂 Procesando {len(json_files)} archivos en {INPUT_DIR}...")

for path in json_files:
    try:
        # 1️⃣ Carga del archivo original
        with open(path, "r", encoding="utf-8") as f:
            segments = json.load(f)

        if not segments:
            print(f"[WARN] Archivo vacío o sin segmentos: {os.path.basename(path)}")
            continue

        # 2️⃣ Cálculo del umbral global de avg_logprob
        avg_logprobs = [seg.get("avg_logprob", 0.0) for seg in segments if "avg_logprob" in seg]
        thr_avg = float(np.percentile(avg_logprobs, PERCENTILE_AVG)) if avg_logprobs else 0.0

        # 3️⃣ Marcar segmentos y palabras
        for seg in segments:
            seg["avg_review_threshold"] = thr_avg
            seg["review_timestamp"] = seg.get("avg_logprob", -np.inf) <= thr_avg

            words = seg.get("words", [])
            if words:
                probs = [w.get("probability", 1.0) for w in words]
                thr_w = float(np.percentile(probs, PERCENTILE_WORDS))
                seg["word_review_threshold"] = thr_w
                for w in words:
                    w["review"] = w.get("probability", 1.0) <= thr_w
            else:
                seg["word_review_threshold"] = None

        # 4️⃣ Guardar nuevo archivo
        out_path = path.replace("_web_ready.json", "_new_web_ready.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(segments, f, ensure_ascii=False, indent=2)

        # 5️⃣ Reporte resumen
        print(f"\n✅ Procesado: {os.path.basename(path)} → {os.path.basename(out_path)}")
        print(f"   Umbral global avg_logprob ({PERCENTILE_AVG}%): {thr_avg:.4f}")
        review_count = sum(1 for seg in segments if seg.get("review_timestamp"))
        print(f"   Segmentos marcados para revisión: {review_count}/{len(segments)}")

    except Exception as e:
        print(f"❌ Error procesando {path}: {e}")

print("\n🎯 Proceso completado con éxito.")