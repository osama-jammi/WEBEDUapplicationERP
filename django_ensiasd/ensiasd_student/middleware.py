"""
Middleware pour la gestion des tokens Odoo
"""
import logging
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages

from .api_client import get_api_client, OdooAPIError

logger = logging.getLogger(__name__)

class OdooTokenMiddleware:
    """Middleware pour injecter le client API avec le token de session"""
    
    # URLs exemptées de l'authentification (ACCESSIBLES SANS LOGIN)
    EXEMPT_URLS = [
        '/',            # Page d'accueil uniquement
        '/login/',      # Page de connexion
        '/logout/',     # Déconnexion
        '/admin/',      # Admin Django
    ]

    # Préfixes d'URLs exemptés (pour les fichiers statiques, etc.)
    EXEMPT_PREFIXES = [
        '/static/',     # Fichiers statiques
        '/media/',      # Fichiers média
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path_info

        logger.debug(f"Middleware checking path: {path}, method: {request.method}")

        # Vérifier si c'est une URL exemptée EXACTE
        if path in self.EXEMPT_URLS:
            logger.debug(f"Path {path} is exempt (exact match)")
            return self.get_response(request)

        # Vérifier si c'est un préfixe exempté (static, media, etc.)
        for prefix in self.EXEMPT_PREFIXES:
            if path.startswith(prefix):
                logger.debug(f"Path {path} is exempt (prefix match: {prefix})")
                return self.get_response(request)

        # Tous les autres chemins nécessitent une authentification
        token = request.session.get('odoo_token')
        student_data = request.session.get('student_data')

        logger.debug(f"Protected path {path} - Token: {bool(token)}, Student: {bool(student_data)}")

        if token and student_data:
            try:
                # IMPORTANT : Créer le client API et l'attacher à la requête
                request.odoo_client = get_api_client(token)
                request.student = student_data
                logger.debug(f"API client attached for {student_data.get('name')}")

                # Continuer le traitement de la requête
                response = self.get_response(request)
                return response

            except Exception as e:
                logger.error(f"Error creating API client: {str(e)}")
                messages.error(request, "Erreur de session. Veuillez vous reconnecter.")
                request.session.flush()
                return redirect('student:login')
        else:
            # Pas de token - rediriger vers le login
            logger.debug(f"No auth for {path}, redirecting to login")
            messages.warning(request, "Veuillez vous connecter pour accéder à cette page.")

            # Sauvegarder l'URL demandée pour rediriger après login
            if path not in ['/login/', '/logout/', '/']:
                request.session['next_url'] = path

            return redirect('student:login')


class OdooAPIErrorMiddleware:
    """Middleware pour gérer les erreurs API globalement"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        return self.get_response(request)
    
    def process_exception(self, request, exception):
        """Gère les exceptions API"""
        if isinstance(exception, OdooAPIError):
            logger.error(f"API Error: {exception.message} (status: {exception.status_code})")
            if exception.status_code == 401:
                # Token expiré ou invalide
                request.session.flush()
                messages.error(request, "Votre session a expiré. Veuillez vous reconnecter.")
                return redirect('student:login')
            elif exception.status_code == 503:
                messages.error(request, "Le service est temporairement indisponible.")
            else:
                messages.error(request, f"Erreur: {exception.message}")
        return None