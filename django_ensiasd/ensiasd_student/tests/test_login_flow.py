# -*- coding: utf-8 -*-
"""
Tests automatisés du flux de connexion étudiant, avec l'API Odoo simulée
(aucun réseau, aucune instance Odoo requise) — remplace les vérifications
manuelles de l'ancien test_connection.py.

Pour un test de bout en bout contre une vraie instance Odoo, voir
test_login_integration.py.
"""
from unittest.mock import patch

import pytest


FAKE_STUDENT = {
    'id': 1,
    'cne': 'TESTCNE01',
    'name': 'Étudiant Test',
    'email': 'etudiant.test@example.com',
    'niveau': '1',
    'groupe': None,
    'state': 'actif',
}


def _fake_make_request(self, method, endpoint, data=None, params=None):
    """Simule les réponses de l'API Odoo pour les besoins du flux dashboard."""
    if endpoint == '/auth/login':
        return {
            'success': True,
            'data': {
                'token': 'fake-token-abc123',
                'expires_at': '2030-01-01T00:00:00',
                'student': FAKE_STUDENT,
            },
        }
    if endpoint == '/me':
        return {'success': True, 'data': FAKE_STUDENT}
    if endpoint == '/notes/summary':
        return {'success': True, 'data': []}
    if endpoint == '/absences/summary':
        return {'success': True, 'data': {}}
    if endpoint == '/emploi-temps':
        return {'success': True, 'data': []}
    raise AssertionError(f"Endpoint non simulé dans ce test: {endpoint}")


@pytest.mark.django_db
@patch('ensiasd_student.api_client.OdooAPIClient._make_request', _fake_make_request)
def test_dashboard_redirects_when_not_logged_in(client):
    """Accéder au dashboard sans session doit rediriger vers la page de connexion."""
    response = client.get('/dashboard/', follow=True)

    assert response.status_code == 200
    assert response.redirect_chain
    assert response.redirect_chain[-1][0] == '/login/'


@pytest.mark.django_db
@patch('ensiasd_student.api_client.OdooAPIClient._make_request', _fake_make_request)
def test_login_sets_session_and_redirects_to_dashboard(client):
    """Une connexion réussie doit stocker le token/l'étudiant en session et rediriger vers le dashboard."""
    response = client.post('/login/', {
        'cne': FAKE_STUDENT['cne'],
        'password': 'peu-importe-ici-le-mock-ne-verifie-pas',
        'remember_me': False,
    })

    assert response.status_code == 302
    assert response.url == '/dashboard/'
    assert client.session['odoo_token'] == 'fake-token-abc123'
    assert client.session['student_data']['name'] == FAKE_STUDENT['name']


@pytest.mark.django_db
@patch('ensiasd_student.api_client.OdooAPIClient._make_request', _fake_make_request)
def test_dashboard_accessible_after_login_and_shows_student_name(client):
    """Après connexion, le dashboard doit être accessible et afficher le nom de l'étudiant."""
    client.post('/login/', {
        'cne': FAKE_STUDENT['cne'],
        'password': 'peu-importe-ici-le-mock-ne-verifie-pas',
        'remember_me': False,
    })

    response = client.get('/dashboard/', follow=True)

    assert response.status_code == 200
    assert FAKE_STUDENT['name'] in response.content.decode('utf-8')
