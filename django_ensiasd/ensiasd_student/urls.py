"""
URLs pour le portail étudiant
"""
from django.urls import path
from . import views

app_name = 'student'

urlpatterns = [
    # Authentification
    path('', views.LoginView.as_view(), name='home'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    
    # Dashboard
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    
    # Notes
    path('notes/', views.NotesView.as_view(), name='notes'),
    
    # Absences
    path('absences/', views.AbsencesView.as_view(), name='absences'),
    
    # Emploi du temps
    path('emploi-temps/', views.EmploiTempsView.as_view(), name='emploi_temps'),
    
    # Stages
    path('stages/', views.StagesView.as_view(), name='stages'),
    
    # Profil
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/password/', views.ChangePasswordView.as_view(), name='change_password'),
]
