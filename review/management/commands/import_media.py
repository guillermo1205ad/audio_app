

import os
import json
import shutil
from django.conf import settings
from django.core.management.base import BaseCommand
from review.models import Audio, Segment

class Command(BaseCommand):
    help = 'Importa JSON *_new_web_ready.json y MP3 a Audio/Segment'

    def add_arguments(self, parser):
        parser.add_argument('path', type=str, help='Carpeta con JSON y MP3')

    def handle(self, *args, **opts):
        folder = opts['path']
        # Preparar carpeta de destino en media/audios
        dest_dir = os.path.join(settings.MEDIA_ROOT, 'audios')
        os.makedirs(dest_dir, exist_ok=True)

        # Primero, procesa todos los MP3
        for fname in os.listdir(folder):
            if fname.endswith('.mp3'):
                src_path = os.path.join(folder, fname)
                dst_path = os.path.join(dest_dir, fname)
                shutil.copy(src_path, dst_path)

                title = os.path.splitext(fname)[0]
                audio_obj, created = Audio.objects.get_or_create(
                    title=title,
                    defaults={'file': os.path.join('audios', fname)}
                )
                if not created:
                    audio_obj.file = os.path.join('audios', fname)
                    audio_obj.save()
                else:
                    self.stdout.write(f'Audio creado: {title}')

        # Luego procesa los JSON
        for fname in os.listdir(folder):
            if fname.endswith('_new_web_ready.json'):
                jpath = os.path.join(folder, fname)
                title = fname.replace('_new_web_ready.json', '')
                try:
                    audio_obj = Audio.objects.get(title=title)
                except Audio.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f'Audio no encontrado para JSON {fname}'))
                    continue

                loaded = json.load(open(jpath, 'r', encoding='utf-8'))
                if isinstance(loaded, list):
                    segments = loaded
                else:
                    segments = loaded.get('segments', [])

                for seg in segments:
                    seg_obj, created = Segment.objects.update_or_create(
                        audio=audio_obj,
                        start=seg.get('start', 0),
                        end=seg.get('end', 0),
                        defaults={
                            'text': seg.get('text', ''),
                            'words': seg.get('words', []),
                        }
                    )
                    if created:
                        self.stdout.write(f'  Segmento creado: {audio_obj.title} [{seg_obj.start}-{seg_obj.end}]')

        self.stdout.write(self.style.SUCCESS('Importación completada.'))