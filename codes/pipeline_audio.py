#!/usr/bin/env python3
"""
🎧 Pipeline de procesamiento de audios para MemorIAnet
Autor: Guillermo Peralta
Flujo automatizado: JSON Whisper → web_ready → métricas → colecta final
"""

import os
import subprocess
from datetime import datetime

# ================================
# CONFIGURACIÓN PRINCIPAL
# ================================

# 📁 Directorio base de audios (configurable por entorno)
BASE_DIR = os.getenv("AUDIOS_BASE_DIR", os.path.join(os.getcwd(), "AUDIOS"))

# 📂 Subcarpetas derivadas
PRUEBAS_DIR = os.getenv("AUDIOS_PATH", os.path.join(BASE_DIR, "pruebas"))
NEW_WEB_READY_DIR = os.getenv("AUDIOS_OUTPUT_PATH", os.path.join(BASE_DIR, "_new_web_ready"))

# 🧾 Log del pipeline
LOG_FILE = os.path.join(PRUEBAS_DIR, "pipeline.log")

# ⚙️ Scripts del pipeline (usando ruta dinámica basada en este archivo)
CODES_DIR = os.path.join(os.path.dirname(__file__))
SCRIPTS = {
    "agregar_audio": os.path.join(CODES_DIR, "agregar_audio_a_json.py"),
    "metricas": os.path.join(CODES_DIR, "metricas_correcciones.py"),
    "collect": os.path.join(CODES_DIR, "collect_new_web_ready.py"),
}

# ================================
# FUNCIONES AUXILIARES
# ================================
def log(msg):
    """Escribe una línea en el log y la muestra en pantalla."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def run_step(name, script_path):
    """Ejecuta un paso del pipeline y registra resultado."""
    log(f"⏳ Iniciando paso: {name}")
    if not os.path.exists(script_path):
        log(f"❌ ERROR: No se encontró el script {script_path}")
        return False
    try:
        subprocess.run(["python3", script_path], check=True)
        log(f"✅ Paso completado: {name}")
        return True
    except subprocess.CalledProcessError as e:
        log(f"❌ Error en {name}: {e}")
        return False


def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)
        log(f"📂 Carpeta creada: {path}")


# ================================
# EJECUCIÓN DEL PIPELINE
# ================================
if __name__ == "__main__":
    print("🎧 Iniciando pipeline de procesamiento de audios...\n")

    # Crea carpetas necesarias
    ensure_dir(PRUEBAS_DIR)
    ensure_dir(NEW_WEB_READY_DIR)

    # Inicia log
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write("\n" + "=" * 60 + "\n")
        f.write(f"🚀 EJECUCIÓN PIPELINE: {datetime.now()}\n")
        f.write("=" * 60 + "\n")

    steps = [
        ("Agregar audios a JSON", SCRIPTS["agregar_audio"]),
        ("Cálculo de métricas de revisión", SCRIPTS["metricas"]),
        ("Colecta final _new_web_ready", SCRIPTS["collect"]),
    ]

    for name, path in steps:
        ok = run_step(name, path)
        if not ok:
            log(f"⚠️ Pipeline detenido por error en: {name}")
            break

    log("🎯 Pipeline completado.")
    log(f"📦 Archivos finales en: {NEW_WEB_READY_DIR}")
    print("\n✅ Proceso finalizado. Revisa el log en:")
    print(f"   {LOG_FILE}")