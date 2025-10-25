import os
import json
from django.conf import settings
from django.utils import timezone
from review.models import Segment

def version_audio(audio):
    """
    Genera un JSON y un TXT versionado para todos los segmentos de 'audio'.
    """
    # Directorio para guardar versiones
    version_dir = os.path.join(settings.MEDIA_ROOT, 'versiones')
    os.makedirs(version_dir, exist_ok=True)

    # Recuperar y serializar segmentos
    segs = Segment.objects.filter(audio=audio).order_by('start')
    serial = []
    for seg in segs:
        serial.append({
            'start': seg.start,
            'end': seg.end,
            'text': seg.text,
            'words': seg.words,
            'fills': seg.fills,
            'free_text': seg.free_text,
            'revisado': seg.revisado,
        })

    # Timestamp para versiones
    ts = timezone.now().strftime('%Y%m%d_%H%M%S')
    base = audio.title.replace(' ', '_')

    # Guardar JSON
    json_path = os.path.join(version_dir, f"{base}_modificado_{ts}.json")
    with open(json_path, 'w', encoding='utf-8') as jf:
        json.dump({'segments': serial}, jf, ensure_ascii=False, indent=2)

    # Guardar TXT
    txt_path = os.path.join(version_dir, f"{base}_final_{ts}.txt")
    with open(txt_path, 'w', encoding='utf-8') as tf:
        for seg in segs:
            if seg.revisado:
                if seg.free_text:
                    # Si hay texto libre, lo usamos directamente
                    tf.write(seg.free_text.strip() + "\n")
                elif seg.fills:
                    # Normalizar claves de fills (strings) a enteros
                    fills_norm = {int(k): v for k, v in seg.fills.items()}
                    words = []
                    for idx_w, w in enumerate(seg.words):
                        if w.get('review'):
                            # Usar la corrección correspondiente
                            words.append(fills_norm.get(idx_w, "").strip())
                        else:
                            words.append(w.get('word', "").strip())
                    tf.write(" ".join(words) + "\n")
                else:
                    # Sin correcciones, usar el texto original
                    tf.write(seg.text.strip() + "\n")
            else:
                # No revisado, usar el texto original
                tf.write(seg.text.strip() + "\n")