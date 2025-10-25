from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Panel de administración
    path('admin/', admin.site.urls),

    # Autenticación con django-allauth (Google OAuth, login, logout, signup…)
    path('accounts/', include('allauth.urls')),

    # Tu app de revisión en la raíz del sitio
    path('', include('review.urls', namespace='review')),
]

# Servir archivos de media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)