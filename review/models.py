from django.conf import settings
from django.db import models
from django.utils import timezone

class Audio(models.Model):
    """
    Representa un archivo de audio MP3.
    """
    title = models.CharField(max_length=255, help_text="Título descriptivo del audio")
    file = models.FileField(upload_to='audios/', help_text="Ruta al archivo MP3")
    metadata = models.JSONField(blank=True, null=True, help_text="Metadatos generales en formato JSON")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Fecha de creación del registro")
    updated_at = models.DateTimeField(auto_now=True, help_text="Fecha de última actualización")

    class Meta:
        ordering = ['title']

    def __str__(self):
        return self.title

class Segment(models.Model):
    """
    Representa un segmento de un Audio para revisión.
    """
    audio = models.ForeignKey(Audio, on_delete=models.CASCADE, related_name='segments')
    start = models.FloatField(help_text="Tiempo de inicio en segundos")
    end = models.FloatField(help_text="Tiempo de fin en segundos")
    text = models.TextField(blank=True, help_text="Texto original de la transcripción")
    words = models.JSONField(help_text="Lista de palabras con timestamps, probabilidad y flag de revisión")
    fills = models.JSONField(blank=True, null=True, help_text="Correcciones por palabra en formato JSON {index: palabra}")
    free_text = models.TextField(blank=True, null=True, help_text="Transcripción libre ingresada por el usuario")
    revisado = models.BooleanField(default=False, help_text="Marca si el segmento fue revisado")
    version = models.PositiveIntegerField(default=1, help_text="Versión de la revisión")
    locked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='locked_segments',
        help_text="Usuario que actualmente bloqueó el segmento"
    )
    locked_at = models.DateTimeField(blank=True, null=True, help_text="Fecha y hora del bloqueo")

    class Meta:
        ordering = ['audio', 'start']
        unique_together = [('audio', 'start', 'end')]

    def __str__(self):
        return f"{self.audio.title} [{self.start:.2f}-{self.end:.2f}]"

    def lock(self, user):
        """Bloquea el segmento para edición por un usuario."""
        self.locked_by = user
        self.locked_at = timezone.now()
        self.save(update_fields=['locked_by', 'locked_at'])

    def unlock(self):
        """Desbloquea el segmento."""
        self.locked_by = None
        self.locked_at = None
        self.save(update_fields=['locked_by', 'locked_at'])
