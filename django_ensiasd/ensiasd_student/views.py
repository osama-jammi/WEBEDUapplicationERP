"""
Vues pour le portail étudiant ENSIASD
"""
import logging
from datetime import datetime, timedelta

from django.shortcuts import render, redirect
from django.contrib import messages
from django.views import View
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.utils import timezone

from .api_client import get_api_client, OdooAPIError
from .forms import LoginForm, ChangePasswordForm

logger = logging.getLogger(__name__)


class LoginView(View):
    """Vue de connexion"""
    template_name = 'student/login.html'
    
    def get(self, request):
        # Si déjà connecté, rediriger vers le dashboard
        if request.session.get('odoo_token') and request.session.get('student_data'):
            logger.info("User already logged in, redirecting to dashboard")
            return redirect('student:dashboard')
        
        form = LoginForm()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        form = LoginForm(request.POST)
        
        if form.is_valid():
            cne = form.cleaned_data['cne']
            password = form.cleaned_data['password']
            
            logger.info(f"Login attempt for CNE: {cne}")
            
            try:
                client = get_api_client()
                response = client.login(cne, password)
                
                logger.info(f"API response: {response.get('success')}")
                
                if response.get('success'):
                    data = response['data']
                    
                    # Stocker les infos en session
                    request.session['odoo_token'] = data['token']
                    request.session['token_expires'] = data['expires_at']
                    request.session['student_data'] = data['student']
                    
                    # Sauvegarder explicitement la session
                    request.session.modified = True
                    
                    logger.info(f"Login successful for {data['student']['name']}, token stored in session")
                    
                    messages.success(request, f"Bienvenue {data['student']['name']}!")
                    
                    # Redirection explicite
                    return redirect('student:dashboard')
                else:
                    error_msg = response.get('error', {}).get('message', 'Identifiants incorrects')
                    logger.warning(f"Login failed: {error_msg}")
                    messages.error(request, error_msg)
                    
            except OdooAPIError as e:
                logger.error(f"Login API error: {e.message} (status: {e.status_code})")
                if e.status_code == 401:
                    messages.error(request, "CNE ou mot de passe incorrect")
                else:
                    messages.error(request, f"Erreur de connexion: {e.message}")
            except Exception as e:
                logger.exception("Login exception")
                messages.error(request, "Service temporairement indisponible")
        else:
            logger.warning(f"Form validation errors: {form.errors}")
        
        return render(request, self.template_name, {'form': form})


class LogoutView(View):
    """Vue de déconnexion"""
    
    def get(self, request):
        token = request.session.get('odoo_token')
        
        if token:
            try:
                client = get_api_client(token)
                client.logout()
                logger.info("Logout successful")
            except Exception as e:
                logger.warning(f"Logout error: {e}")
                pass  # Ignorer les erreurs de logout
        
        request.session.flush()
        messages.info(request, "Vous êtes déconnecté")
        return redirect('student:login')


class DashboardView(TemplateView):
    """Tableau de bord étudiant"""
    template_name = 'student/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Vérifier d'abord si l'utilisateur est connecté
        if not self.request.session.get('odoo_token'):
            logger.warning("Dashboard accessed without token, redirecting to login")
            # Cette redirection sera gérée par le middleware
            return context
        
        try:
            # Obtenir le client API de différentes façons
            if hasattr(self.request, 'odoo_client'):
                client = self.request.odoo_client
            else:
                # Créer un client directement à partir de la session
                from .api_client import get_api_client
                token = self.request.session.get('odoo_token')
                if not token:
                    logger.error("No token in session")
                    return context
                
                client = get_api_client(token)
            
            logger.info(f"Dashboard loading for: {self.request.session.get('student_data', {}).get('name')}")
            
            # Récupérer les données du dashboard
            profile_response = client.get_profile()
            notes_response = client.get_notes_summary()
            absences_response = client.get_absences_summary()
            
            # Récupérer les données de la session comme fallback
            current_student = self.request.session.get('student_data', {})
            
            context.update({
                'current_student': current_student,
                'today': timezone.now().date(),
                'profile': profile_response.get('data', {}),
                'notes_summary': notes_response.get('data', []),
                'absences_summary': absences_response.get('data', {}),
            })
            
            # Essayer de récupérer l'emploi du temps
            try:
                today = timezone.now().date()
                week_start = today - timedelta(days=today.weekday())
                week_end = week_start + timedelta(days=6)
                
                emploi_temps = client.get_emploi_temps(
                    date_from=week_start.isoformat(),
                    date_to=week_end.isoformat()
                )
                context['seances_semaine'] = emploi_temps.get('data', [])[:5]
            except Exception as e:
                logger.warning(f"Could not load schedule: {e}")
                context['seances_semaine'] = []
            
            logger.info("Dashboard loaded successfully")
            
        except Exception as e:
            logger.error(f"Dashboard error: {str(e)}")
            # Utiliser les données de session comme fallback
            context.update({
                'current_student': self.request.session.get('student_data', {}),
                'today': timezone.now().date(),
                'notes_summary': [],
                'absences_summary': {},
                'seances_semaine': [],
            })
        
        return context
class NotesView(TemplateView):
    """Vue des notes"""
    template_name = 'student/notes.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        client = self.request.odoo_client
        
        try:
            # Récupérer les paramètres de filtre
            annee_id = self.request.GET.get('annee_id')
            module_id = self.request.GET.get('module_id')
            
            # Années disponibles
            annees = client.get_annees()
            context['annees'] = annees.get('data', [])
            
            # Modules de l'étudiant
            modules = client.get_modules()
            context['modules'] = modules.get('data', [])
            
            # Notes avec filtres
            notes = client.get_notes(
                annee_id=int(annee_id) if annee_id else None,
                module_id=int(module_id) if module_id else None
            )
            context['notes'] = notes.get('data', [])
            
            # Résumé par module
            notes_summary = client.get_notes_summary(
                annee_id=int(annee_id) if annee_id else None
            )
            context['notes_summary'] = notes_summary.get('data', [])
            
            # Filtres actuels
            context['current_annee'] = annee_id
            context['current_module'] = module_id
            
        except OdooAPIError as e:
            messages.error(self.request, f"Erreur: {e.message}")
        except Exception as e:
            logger.exception("Notes view error")
            messages.error(self.request, "Erreur lors du chargement des notes")
        
        return context


class AbsencesView(TemplateView):
    """Vue des absences"""
    template_name = 'student/absences.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        client = self.request.odoo_client
        
        try:
            # Récupérer les paramètres de filtre
            annee_id = self.request.GET.get('annee_id')
            date_from = self.request.GET.get('date_from')
            date_to = self.request.GET.get('date_to')
            
            # Années disponibles
            annees = client.get_annees()
            context['annees'] = annees.get('data', [])
            
            # Absences avec filtres
            absences = client.get_absences(
                annee_id=int(annee_id) if annee_id else None,
                date_from=date_from,
                date_to=date_to
            )
            context['absences'] = absences.get('data', [])
            
            # Résumé
            absences_summary = client.get_absences_summary()
            context['absences_summary'] = absences_summary.get('data', {})
            
            # Filtres actuels
            context['current_annee'] = annee_id
            context['current_date_from'] = date_from
            context['current_date_to'] = date_to
            
        except OdooAPIError as e:
            messages.error(self.request, f"Erreur: {e.message}")
        except Exception as e:
            logger.exception("Absences view error")
            messages.error(self.request, "Erreur lors du chargement des absences")
        
        return context


class EmploiTempsView(TemplateView):
    """Vue de l'emploi du temps"""
    template_name = 'student/emploi_temps.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        client = self.request.odoo_client
        
        try:
            # Récupérer la semaine demandée
            week_offset = int(self.request.GET.get('week', 0))
            
            today = timezone.now().date()
            week_start = today - timedelta(days=today.weekday()) + timedelta(weeks=week_offset)
            week_end = week_start + timedelta(days=6)
            
            # Séances de la semaine
            emploi_temps = client.get_emploi_temps(
                date_from=week_start.isoformat(),
                date_to=week_end.isoformat()
            )
            
            # Organiser par jour
            seances_par_jour = {i: [] for i in range(7)}
            for seance in emploi_temps.get('data', []):
                if seance.get('date'):
                    date_obj = datetime.fromisoformat(seance['date']).date()
                    jour = date_obj.weekday()
                    if jour in seances_par_jour:
                        seances_par_jour[jour].append(seance)
            
            # Trier par heure
            for jour in seances_par_jour:
                seances_par_jour[jour].sort(key=lambda x: x.get('heure_debut', 0))
            
            context.update({
                'seances_par_jour': seances_par_jour,
                'week_start': week_start,
                'week_end': week_end,
                'week_offset': week_offset,
                'days': ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche'],
                'today': today,
            })
            
        except OdooAPIError as e:
            messages.error(self.request, f"Erreur: {e.message}")
        except Exception as e:
            logger.exception("Emploi temps view error")
            messages.error(self.request, "Erreur lors du chargement de l'emploi du temps")
        
        return context


class HomeView(TemplateView):
    """Page d'accueil"""
    template_name = 'student/home.html'
    
    def get(self, request):
        # Si déjà connecté, rediriger vers le dashboard
        if request.session.get('odoo_token'):
            logger.info("User already logged in, redirecting to dashboard")
            return redirect('student:dashboard')
        return render(request, self.template_name)
    

class StagesView(TemplateView):
    """Vue des stages"""
    template_name = 'student/stages.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        client = self.request.odoo_client
        
        try:
            stages = client.get_stages()
            context['stages'] = stages.get('data', [])
            
        except OdooAPIError as e:
            messages.error(self.request, f"Erreur: {e.message}")
        except Exception as e:
            logger.exception("Stages view error")
            messages.error(self.request, "Erreur lors du chargement des stages")
        
        return context


class ProfileView(TemplateView):
    """Vue du profil"""
    template_name = 'student/profile.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        client = self.request.odoo_client
        
        try:
            profile = client.get_profile()
            context['profile'] = profile.get('data', {})
            
            inscriptions = client.get_inscriptions()
            context['inscriptions'] = inscriptions.get('data', [])
            
        except OdooAPIError as e:
            messages.error(self.request, f"Erreur: {e.message}")
        except Exception as e:
            logger.exception("Profile view error")
            messages.error(self.request, "Erreur lors du chargement du profil")
        
        return context


class ChangePasswordView(View):
    """Vue de changement de mot de passe"""
    template_name = 'student/change_password.html'
    
    def get(self, request):
        form = ChangePasswordForm()
        return render(request, self.template_name, {'form': form})
    def post(self, request):
        form = LoginForm(request.POST)
        
        if form.is_valid():
            cne = form.cleaned_data['cne']
            password = form.cleaned_data['password']
            
            logger.info(f"Login attempt for CNE: {cne}")
            
            try:
                client = get_api_client()
                response = client.login(cne, password)
                
                logger.info(f"API response: {response.get('success')}")
                
                if response.get('success'):
                    data = response['data']
                    
                    # Stocker les infos en session
                    request.session['odoo_token'] = data['token']
                    request.session['token_expires'] = data['expires_at']
                    request.session['student_data'] = data['student']
                    
                    # Sauvegarder explicitement la session
                    request.session.modified = True
                    
                    logger.info(f"Login successful for {data['student']['name']}, token stored in session")
                    
                    messages.success(request, f"Bienvenue {data['student']['name']}!")
                    
                    # Redirection après login
                    next_url = request.session.pop('next_url', None)
                    if next_url and next_url != '/login/':
                        logger.info(f"Redirecting to requested URL: {next_url}")
                        return redirect(next_url)
                    else:
                        logger.info("Redirecting to default dashboard")
                        return redirect('student:dashboard')
                else:
                    error_msg = response.get('error', {}).get('message', 'Identifiants incorrects')
                    logger.warning(f"Login failed: {error_msg}")
                    messages.error(request, error_msg)
                    
            except OdooAPIError as e:
                logger.error(f"Login API error: {e.message} (status: {e.status_code})")
                if e.status_code == 401:
                    messages.error(request, "CNE ou mot de passe incorrect")
                else:
                    messages.error(request, f"Erreur de connexion: {e.message}")
            except Exception as e:
                logger.exception("Login exception")
                messages.error(request, "Service temporairement indisponible")
        else:
            logger.warning(f"Form validation errors: {form.errors}")
        
        return render(request, self.template_name, {'form': form})

# =============================================================================
# VUES API JSON (pour AJAX)
# =============================================================================

class APINotesView(View):
    """API JSON pour les notes"""
    
    def get(self, request):
        try:
            client = request.odoo_client
            annee_id = request.GET.get('annee_id')
            module_id = request.GET.get('module_id')
            
            notes = client.get_notes(
                annee_id=int(annee_id) if annee_id else None,
                module_id=int(module_id) if module_id else None
            )
            
            return JsonResponse(notes)
            
        except OdooAPIError as e:
            return JsonResponse({'success': False, 'error': e.message}, status=e.status_code or 400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)


class APIEmploiTempsView(View):
    """API JSON pour l'emploi du temps"""
    
    def get(self, request):
        try:
            client = request.odoo_client
            date_from = request.GET.get('date_from')
            date_to = request.GET.get('date_to')
            
            emploi_temps = client.get_emploi_temps(date_from=date_from, date_to=date_to)
            
            return JsonResponse(emploi_temps)
            
        except OdooAPIError as e:
            return JsonResponse({'success': False, 'error': e.message}, status=e.status_code or 400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)