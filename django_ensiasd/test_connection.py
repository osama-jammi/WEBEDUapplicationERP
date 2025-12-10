"""
Test simplifié du flux de connexion
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from django.test import Client

print("="*60)
print("TEST SIMPLIFIÉ DU LOGIN")
print("="*60)

client = Client()

# 1. Tenter d'accéder au dashboard sans être connecté
print("\n1. Accès dashboard sans login:")
response = client.get('/dashboard/', follow=True)
print(f"   Status: {response.status_code}")
print(f"   Redirigé vers: {response.redirect_chain[-1][0] if response.redirect_chain else 'N/A'}")

# 2. Se connecter
print("\n2. Connexion:")
response = client.post('/login/', {
    'cne': 'R130189241',
    'password': 'admin1',
    'remember_me': False
}, follow=False)

print(f"   Status: {response.status_code}")
print(f"   Redirection: {response.url if hasattr(response, 'url') else 'None'}")

if response.status_code == 302:
    # 3. Suivre la redirection vers dashboard
    print("\n3. Accès dashboard après login:")
    response = client.get('/dashboard/', follow=True)
    print(f"   Status: {response.status_code}")
    
    # Vérifier le contenu
    if response.status_code == 200:
        print("   ✓ Dashboard accessible!")
        # Vérifier si le nom de l'étudiant est dans la page
        content = response.content.decode('utf-8')
        if 'jammi osama' in content:
            print("   ✓ Nom de l'étudiant trouvé!")
        else:
            print("   ✗ Nom de l'étudiant non trouvé")
            print(f"   Contenu (premières 1000 chars): {content[:1000]}")
    else:
        print(f"   ✗ Dashboard inaccessible (status: {response.status_code})")
        
        # Vérifier les redirections
        for redirect in response.redirect_chain:
            print(f"   Redirection: {redirect[0]} (status: {redirect[1]})")

# 4. Vérifier la session
print("\n4. Session après connexion:")
session = client.session
print(f"   Session key: {session.session_key}")
print(f"   Token: {'odoo_token' in session}")
print(f"   Student data: {'student_data' in session}")
if 'student_data' in session:
    print(f"   Student name: {session['student_data'].get('name')}")

print("\n" + "="*60)
print("TEST TERMINÉ")