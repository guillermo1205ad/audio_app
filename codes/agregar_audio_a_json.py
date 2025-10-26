import os
import json

# Ruta a la carpeta donde están los .json y .mp3
carpeta = os.getenv("AUDIOS_PATH", os.path.join(os.getcwd(), "AUDIOS", "pruebas"))

# Recorre todos los archivos en la carpeta
for archivo in os.listdir(carpeta):
    if archivo.endswith(".json"):
        ruta_json = os.path.join(carpeta, archivo)

        try:
            with open(ruta_json, "r", encoding="utf-8") as f:
                contenido = json.load(f)

            # Verifica si tiene estructura Whisper
            if "segments" in contenido:
                nombre_base = os.path.splitext(archivo)[0]
                nombre_audio = nombre_base + ".mp3"
                ruta_audio = os.path.join(carpeta, nombre_audio)

                if os.path.exists(ruta_audio):
                    print(f"✔ Procesando: {archivo} + {nombre_audio}")
                    for seg in contenido["segments"]:
                        seg["audio"] = nombre_audio

                    # Guardar nuevo archivo con "_web_ready" al final
                    salida = os.path.join(carpeta, nombre_base + "_web_ready.json")
                    with open(salida, "w", encoding="utf-8") as f:
                        json.dump(contenido["segments"], f, ensure_ascii=False, indent=2)
                else:
                    print(f"⚠ No se encontró audio para: {archivo}")

        except Exception as e:
            print(f"❌ Error procesando {archivo}: {e}")