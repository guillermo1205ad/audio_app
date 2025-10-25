import os
import re
import mimetypes
from wsgiref.util import FileWrapper

from django.conf import settings
from django.http import StreamingHttpResponse, FileResponse, Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseBadRequest
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.urls import reverse

from review.services.versioning import version_audio
from .models import Segment


@login_required(login_url='/accounts/login/')
def pending_list(request):
    """
    Muestra el carrusel de segmentos pendientes de revisión.
    """
    pendientes_qs = Segment.objects.filter(
        revisado=False,
        words__contains=[{'review': True}]
    ).order_by('audio__title', 'start')
    pendientes = list(pendientes_qs)
    return render(request, 'review/pending_list.html', {
        'pendientes': pendientes
    })


@login_required(login_url='/accounts/login/')
def segment_edit(request, pk):
    """
    GET: Renderiza el fragmento HTML para editar el segmento identificado por pk.
    POST: Procesa y guarda los cambios, versionado y desbloqueo.
    """
    segment = get_object_or_404(Segment, pk=pk)

    # Calcular navegación previa y siguiente
    pendientes_ids = list(
        Segment.objects.filter(
            revisado=False,
            words__contains=[{'review': True}]
        )
        .order_by('audio__title', 'start')
        .values_list('pk', flat=True)
    )
    idx = pendientes_ids.index(segment.pk) if segment.pk in pendientes_ids else None
    prev_pk = pendientes_ids[idx-1] if idx is not None and idx > 0 else None
    next_pk = pendientes_ids[idx+1] if idx is not None and idx < len(pendientes_ids)-1 else None

    # Construir URL de streaming
    filename = os.path.basename(segment.audio.file.name)
    stream_url = reverse('review:stream_audio', args=[filename])

    if request.method == 'GET':
        return render(request, 'review/segment_edit.html', {
            's': segment,
            'prev_pk': prev_pk,
            'next_pk': next_pk,
            'stream_url': stream_url,
        })

    # POST
    try:
        start = float(request.POST.get('start'))
        end = float(request.POST.get('end'))
    except (TypeError, ValueError):
        return HttpResponseBadRequest("Start y end deben ser números válidos.")

    # Evitar edición concurrente
    if segment.locked_by and segment.locked_by != request.user:
        return JsonResponse({'error': 'Segmento bloqueado por otro usuario.'}, status=409)

    # Bloquear para el usuario actual
    segment.lock(request.user)

    # Actualizar campos
    segment.start = start
    segment.end = end
    segment.revisado = bool(request.POST.get('revisado'))

    if request.POST.get('use_free'):
        segment.free_text = request.POST.get('free_text', '').strip()
        segment.fills = None
    else:
        fills = {}
        for key, val in request.POST.items():
            if key.startswith('fill_'):
                idx_w = key.split('_')[1]
                fills[int(idx_w)] = val.strip()
        segment.fills = fills
        segment.free_text = ''

    # Versionado y desbloqueo atómico
    with transaction.atomic():
        segment.version += 1
        segment.save()
        version_audio(segment.audio)
        segment.unlock()

    context = {
        's': segment,
        'prev_pk': prev_pk,
        'next_pk': next_pk,
        'stream_url': stream_url,
    }

    # Para peticiones HTMX, enviamos el fragmento y forzamos reload del cliente
    if request.META.get('HTTP_HX_REQUEST') == 'true':
        response = render(request, 'review/segment_edit.html', context)
        response['HX-Refresh'] = 'true'
        return response

    # Para peticiones normales, volvemos a la lista de pendientes
    return redirect('review:pending_list')


def stream_audio(request, filename):
    """
    Responde peticiones HTTP Range para archivos en MEDIA_ROOT/audios/
    """
    media_dir = os.path.join(settings.MEDIA_ROOT, 'audios')
    path = os.path.join(media_dir, filename)
    if not os.path.exists(path):
        raise Http404("Audio no encontrado")

    file_size = os.path.getsize(path)
    content_type, _ = mimetypes.guess_type(path)
    content_type = content_type or 'application/octet-stream'

    range_header = request.META.get('HTTP_RANGE', '')
    range_match = re.match(r'bytes=(\d+)-(\d*)', range_header)

    if range_match:
        start = int(range_match.group(1))
        end = int(range_match.group(2)) if range_match.group(2) else file_size - 1
        if end >= file_size:
            end = file_size - 1
        length = end - start + 1

        response = StreamingHttpResponse(
            FileWrapper(open(path, 'rb')),
            status=206,
            content_type=content_type
        )
        response['Content-Range'] = f'bytes {start}-{end}/{file_size}'
        response['Accept-Ranges'] = 'bytes'
        response['Content-Length'] = str(length)

        fp = open(path, 'rb')
        fp.seek(start)
        response.streaming_content = iter(lambda: fp.read(8192), b'')

        return response

    # Si no hay header Range, devolvemos todo el fichero
    return FileResponse(open(path, 'rb'), content_type=content_type)