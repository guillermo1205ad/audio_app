from django.urls import path
from .views import pending_list, segment_edit, stream_audio

app_name = 'review'

urlpatterns = [
    path('media/audios/<path:filename>/', stream_audio, name='stream_audio'),
    path('media/audios/<path:filename>',  stream_audio),
    # Vista principal: carrusel de segmentos pendientes
    path('', pending_list, name='pending_list'),
    # Edición in-place de un segmento por HTMX
    path('segment/<int:pk>/edit/', segment_edit, name='segment_edit'),
]