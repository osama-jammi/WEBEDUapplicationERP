"""
Client API pour communiquer avec Odoo ENSIASD
"""
import logging
import httpx
from typing import Optional, Dict, Any, List
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class OdooAPIError(Exception):
    """Exception pour les erreurs API Odoo"""
    def __init__(self, message: str, code: str = None, status_code: int = None):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(self.message)


class OdooAPIClient:
    """Client pour l'API REST ENSIASD sur Odoo"""
    
    def __init__(self):
        self.base_url = settings.ODOO_API_URL.rstrip('/')
        self.api_key = settings.ODOO_API_KEY
        self.timeout = settings.ODOO_API_TIMEOUT
        self._token = None
    
    @property
    def headers(self) -> Dict[str, str]:
        """Headers de base pour les requêtes"""
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-API-Key': self.api_key,
        }
        if self._token:
            headers['Authorization'] = f'Bearer {self._token}'
        return headers
    
    def set_token(self, token: str):
        """Définit le token d'authentification"""
        self._token = token
    
    def _make_request(self, method: str, endpoint: str, data: Dict = None, 
                      params: Dict = None) -> Dict[str, Any]:
        """Effectue une requête HTTP vers l'API Odoo"""
        url = f"{self.base_url}/api/v1{endpoint}"
        
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    json=data,
                    params=params
                )
                
                # Log de la requête
                logger.debug(f"API Request: {method} {url} -> {response.status_code}")
                
                # Parser la réponse
                try:
                    result = response.json()
                except Exception:
                    result = {'success': False, 'error': {'message': response.text}}
                
                # Gérer les erreurs HTTP
                if response.status_code >= 400:
                    error = result.get('error', {})
                    raise OdooAPIError(
                        message=error.get('message', 'Erreur API'),
                        code=error.get('code'),
                        status_code=response.status_code
                    )
                
                return result
                
        except httpx.TimeoutException:
            logger.error(f"API Timeout: {url}")
            raise OdooAPIError("Le serveur ne répond pas", "TIMEOUT", 504)
        except httpx.ConnectError:
            logger.error(f"API Connection Error: {url}")
            raise OdooAPIError("Impossible de se connecter au serveur", "CONNECTION_ERROR", 503)
        except OdooAPIError:
            raise
        except Exception as e:
            logger.exception(f"API Error: {url}")
            raise OdooAPIError(str(e), "UNKNOWN_ERROR", 500)
    
    def get(self, endpoint: str, params: Dict = None) -> Dict[str, Any]:
        """Requête GET"""
        return self._make_request('GET', endpoint, params=params)
    
    def post(self, endpoint: str, data: Dict = None) -> Dict[str, Any]:
        """Requête POST"""
        return self._make_request('POST', endpoint, data=data)
    
    def put(self, endpoint: str, data: Dict = None) -> Dict[str, Any]:
        """Requête PUT"""
        return self._make_request('PUT', endpoint, data=data)
    
    # =========================================================================
    # AUTHENTIFICATION
    # =========================================================================
    
    def login(self, cne: str, password: str) -> Dict[str, Any]:
        """Authentifie un étudiant"""
        response = self.post('/auth/login', {'cne': cne, 'password': password})
        if response.get('success'):
            self._token = response['data']['token']
        return response
    
    def logout(self) -> Dict[str, Any]:
        """Déconnecte l'étudiant"""
        response = self.post('/auth/logout')
        self._token = None
        return response
    
    def refresh_token(self) -> Dict[str, Any]:
        """Rafraîchit le token"""
        response = self.post('/auth/refresh')
        if response.get('success'):
            self._token = response['data']['token']
        return response
    
    # =========================================================================
    # PROFIL
    # =========================================================================
    
    def get_profile(self) -> Dict[str, Any]:
        """Récupère le profil de l'étudiant"""
        cache_key = f"student_profile_{self._token[:16]}" if self._token else None
        
        if cache_key:
            cached = cache.get(cache_key)
            if cached:
                return cached
        
        response = self.get('/me')
        
        if response.get('success') and cache_key:
            cache.set(cache_key, response, 300)  # Cache 5 minutes
        
        return response
    
    def change_password(self, old_password: str, new_password: str) -> Dict[str, Any]:
        """Change le mot de passe"""
        return self.put('/me/password', {
            'old_password': old_password,
            'new_password': new_password
        })
    
    # =========================================================================
    # NOTES
    # =========================================================================
    
    def get_notes(self, annee_id: int = None, module_id: int = None) -> Dict[str, Any]:
        """Récupère les notes"""
        params = {}
        if annee_id:
            params['annee_id'] = annee_id
        if module_id:
            params['module_id'] = module_id
        return self.get('/notes', params=params)
    
    def get_notes_summary(self, annee_id: int = None) -> Dict[str, Any]:
        """Récupère le résumé des notes"""
        params = {}
        if annee_id:
            params['annee_id'] = annee_id
        return self.get('/notes/summary', params=params)
    
    # =========================================================================
    # ABSENCES
    # =========================================================================
    
    def get_absences(self, annee_id: int = None, date_from: str = None, 
                     date_to: str = None) -> Dict[str, Any]:
        """Récupère les absences"""
        params = {}
        if annee_id:
            params['annee_id'] = annee_id
        if date_from:
            params['date_from'] = date_from
        if date_to:
            params['date_to'] = date_to
        return self.get('/absences', params=params)
    
    def get_absences_summary(self) -> Dict[str, Any]:
        """Récupère le résumé des absences"""
        return self.get('/absences/summary')
    
    # =========================================================================
    # EMPLOI DU TEMPS
    # =========================================================================
    
    def get_emploi_temps(self, date_from: str = None, date_to: str = None) -> Dict[str, Any]:
        """Récupère l'emploi du temps"""
        params = {}
        if date_from:
            params['date_from'] = date_from
        if date_to:
            params['date_to'] = date_to
        return self.get('/emploi-temps', params=params)
    
    # =========================================================================
    # INSCRIPTIONS
    # =========================================================================
    
    def get_inscriptions(self, annee_id: int = None) -> Dict[str, Any]:
        """Récupère les inscriptions aux modules"""
        params = {}
        if annee_id:
            params['annee_id'] = annee_id
        return self.get('/inscriptions', params=params)
    
    # =========================================================================
    # STAGES
    # =========================================================================
    
    def get_stages(self) -> Dict[str, Any]:
        """Récupère les stages"""
        return self.get('/stages')
    
    # =========================================================================
    # DONNÉES DE RÉFÉRENCE
    # =========================================================================
    
    def get_annees(self) -> Dict[str, Any]:
        """Liste des années universitaires"""
        cache_key = "ensiasd_annees"
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        response = self.get('/annees')
        if response.get('success'):
            cache.set(cache_key, response, 3600)  # Cache 1 heure
        return response
    
    def get_modules(self) -> Dict[str, Any]:
        """Liste des modules de l'étudiant"""
        return self.get('/modules')
    
    # =========================================================================
    # RÉCLAMATIONS
    # =========================================================================
    
    def get_reclamations(self) -> Dict[str, Any]:
        """Récupère les réclamations de l'étudiant"""
        return self.get('/reclamations')
    
    def create_reclamation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Crée une nouvelle réclamation"""
        return self.post('/reclamations', data=data)

    # =========================================================================
    # UTILITAIRES
    # =========================================================================
    
    def health_check(self) -> bool:
        """Vérifie si l'API est disponible"""
        try:
            response = self.get('/health')
            return response.get('status') == 'ok'
        except Exception:
            return False


# Instance globale
odoo_client = OdooAPIClient()


def get_api_client(token: str = None) -> OdooAPIClient:
    """Retourne un client API configuré"""
    client = OdooAPIClient()
    if token:
        client.set_token(token)
    return client
