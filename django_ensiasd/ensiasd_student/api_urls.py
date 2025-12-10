"""
URLs API pour requêtes AJAX
"""
from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    path('notes/', views.APINotesView.as_view(), name='notes'),
    path('emploi-temps/', views.APIEmploiTempsView.as_view(), name='emploi_temps'),
]
