#!/usr/bin/env python3
import os
import shutil

# 🗂️ Lista de carpetas de origen (puedes agregar más si quieres)
source_dirs = [
    os.getenv("AUDIOS_PATH", os.path.join(os.getcwd(), "AUDIOS", "pruebas")),
]

# 📦 Carpeta de destino final (puede configurarse por variable de entorno)
dest_dir = os.getenv("AUDIOS_OUTPUT_PATH", os.path.join(os.getcwd(), "AUDIOS", "_new_web_ready"))
os.makedirs(dest_dir, exist_ok=True)

def find_matching_mp3(src_dir, json_name):
    """
    Busca el archivo MP3 correspondiente al JSON,
    eliminando sufijos como '_new_web_ready' o '_web_ready'.
    """
    base = os.path.splitext(json_name)[0]
    clean_base = base.replace("_new_web_ready", "").replace("_web_ready", "")
    mp3_candidate = os.path.join(src_dir, f"{clean_base}.mp3")
    return mp3_candidate if os.path.exists(mp3_candidate) else None

# 🚀 Recorre todas las carpetas fuente
for src in source_dirs:
    if not os.path.isdir(src):
        print(f"[WARN] Directorio no encontrado: {src}")
        continue

    print(f"\n📂 Procesando carpeta: {src}")
    for fname in sorted(os.listdir(src)):
        if not fname.endswith("_new_web_ready.json"):
            continue

        json_src = os.path.join(src, fname)
        mp3_src = find_matching_mp3(src, fname)

        # Copiar JSON
        try:
            shutil.copy2(json_src, os.path.join(dest_dir, fname))
            print(f"✔ Copiado JSON: {fname}")
        except Exception as e:
            print(f"❌ Error copiando JSON {fname}: {e}")
            continue

        # Copiar MP3 relacionado
        if mp3_src:
            mp3_name = os.path.basename(mp3_src)
            try:
                shutil.copy2(mp3_src, os.path.join(dest_dir, mp3_name))
                print(f"🎵 Copiado MP3:  {mp3_name}")
            except Exception as e:
                print(f"❌ Error copiando MP3 {mp3_name}: {e}")
        else:
            print(f"[WARN] No se encontró el MP3 para: {fname}")

print("\n✅ Proceso completado.")