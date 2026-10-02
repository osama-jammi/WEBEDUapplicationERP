from django.urls import path
from .views import (
    HomeView, LoginView, LogoutView, DashboardView, 
    NotesView, AbsencesView, EmploiTempsView, 
    StagesView, ProfileView, ChangePasswordView,
    ReclamationsView
)

app_name = 'student'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),  # Page d'accueil
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('notes/', NotesView.as_view(), name='notes'),
    path('absences/', AbsencesView.as_view(), name='absences'),
    path('emploi-temps/', EmploiTempsView.as_view(), name='emploi_temps'),
    path('stages/', StagesView.as_view(), name='stages'),
    path('reclamations/', ReclamationsView.as_view(), name='reclamations'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
]