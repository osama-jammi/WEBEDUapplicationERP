"""
URL configuration for ENSIASD Student Portal
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin Django (optionnel)
    path('admin/', admin.site.urls),
    
    # Application étudiants
    path('', include('ensiasd_student.urls', namespace='student')),
    
    # API interne (optionnel)
    path('api/', include('ensiasd_student.api_urls', namespace='api')),
]

# Fichiers statiques en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
