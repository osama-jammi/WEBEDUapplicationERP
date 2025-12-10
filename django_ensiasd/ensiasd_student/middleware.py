"""
Middleware pour la gestion des tokens Odoo
"""
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages

from .api_client import get_api_client, OdooAPIError


class OdooTokenMiddleware:
    """Middleware pour injecter le client API avec le token de session"""
    
    # URLs exemptées de l'authentification
    EXEMPT_URLS = [
        '/login/',
        '/logout/',
        '/api/',
        '/static/',
        '/media/',
        '/admin/',
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Vérifier si l'URL est exemptée
        path = request.path
        
        if any(path.startswith(url) for url in self.EXEMPT_URLS):
            return self.get_response(request)
        
        # Récupérer le token de session
        token = request.session.get('odoo_token')
        student_data = request.session.get('student_data')
        
        if token and student_data:
            # Créer le client API avec le token
            request.odoo_client = get_api_client(token)
            request.student = student_data
        else:
            # Rediriger vers la page de login
            if path != '/':
                messages.warning(request, "Veuillez vous connecter pour accéder à cette page.")
            return redirect('student:login')
        
        # Traiter la requête
        response = self.get_response(request)
        
        return response


class OdooAPIErrorMiddleware:
    """Middleware pour gérer les erreurs API globalement"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        return self.get_response(request)
    
    def process_exception(self, request, exception):
        """Gère les exceptions API"""
        if isinstance(exception, OdooAPIError):
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
