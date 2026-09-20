# -*- coding: utf-8 -*-
"""
Test d'intégration bout-en-bout : vérifie qu'une vraie instance Odoo répond
correctement au flux de connexion étudiant. Remplace l'usage "vérification
manuelle rapide" de l'ancien test_connection.py.

Ignoré automatiquement si TEST_STUDENT_CNE/TEST_STUDENT_PASSWORD ne sont
pas définis (dans .env ou l'environnement) — pas d'échec de la suite si
aucune instance Odoo n'est disponible. Utilisez un compte étudiant de TEST
dédié, jamais un compte réel.
"""
import pytest
from decouple import config

TEST_STUDENT_CNE = config('TEST_STUDENT_CNE', default=None)
TEST_STUDENT_PASSWORD = config('TEST_STUDENT_PASSWORD', default=None)

pytestmark = pytest.mark.skipif(
    not TEST_STUDENT_CNE or not TEST_STUDENT_PASSWORD,
    reason=(
        "TEST_STUDENT_CNE/TEST_STUDENT_PASSWORD non définis — ce test "
        "nécessite une vraie instance Odoo et un compte étudiant de test."
    ),
)


@pytest.mark.django_db
def test_full_login_flow_against_real_odoo(client):
    """Connexion réelle : login -> session -> dashboard accessible et affiche le nom de l'étudiant."""
    response = client.get('/dashboard/', follow=True)
    assert response.redirect_chain[-1][0] == '/login/'

    response = client.post('/login/', {
        'cne': TEST_STUDENT_CNE,
        'password': TEST_STUDENT_PASSWORD,
        'remember_me': False,
    })
    assert response.status_code == 302, (
        "Échec de connexion : vérifiez TEST_STUDENT_CNE/TEST_STUDENT_PASSWORD "
        "et qu'Odoo est démarré et joignable (ODOO_API_URL/ODOO_API_KEY)."
    )
    assert 'odoo_token' in client.session
    assert 'student_data' in client.session

    response = client.get('/dashboard/', follow=True)
    assert response.status_code == 200
    student_name = client.session['student_data'].get('name')
    assert student_name
    assert student_name.lower() in response.content.decode('utf-8').lower()
