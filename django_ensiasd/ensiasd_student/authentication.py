"""
Authentification personnalisée pour Django REST Framework
"""
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from .api_client import get_api_client, OdooAPIError


class OdooTokenAuthentication(BaseAuthentication):
    """Authentification via token Odoo"""
    
    keyword = 'Bearer'
    
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if not auth_header or not auth_header.startswith(f'{self.keyword} '):
            return None
        
        token = auth_header[len(self.keyword) + 1:]
        
        if not token:
            return None
        
        try:
            client = get_api_client(token)
            response = client.get_profile()
            
            if response.get('success'):
                # Créer un objet utilisateur simple
                student_data = response['data']
                user = SimpleUser(student_data)
                return (user, token)
            else:
                raise AuthenticationFailed('Token invalide')
                
        except OdooAPIError as e:
            raise AuthenticationFailed(e.message)
        except Exception as e:
            raise AuthenticationFailed(str(e))
    
    def authenticate_header(self, request):
        return self.keyword


class SimpleUser:
    """Classe utilisateur simple pour DRF"""
    
    def __init__(self, data):
        self.id = data.get('id')
        self.cne = data.get('cne')
        self.name = data.get('name')
        self.email = data.get('email')
        self.is_authenticated = True
        self.is_active = True
        self._data = data
    
    def __str__(self):
        return self.name or self.cne
    
    @property
    def data(self):
        return self._data
