# -*- coding: utf-8 -*-
"""
Tests unitaires pour les fonctions pures de résolution de settings sensibles
définies dans config/settings.py : _resolve_secret_key et
_resolve_session_cookie_secure.

On teste ces fonctions directement, avec des arguments contrôlés, plutôt que
de recharger le module settings avec des variables d'environnement
différentes (fragile, difficile à nettoyer proprement entre tests, et à
proscrire pour ne pas perturber les autres tests de la suite).
"""
from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

from config.settings import _resolve_secret_key, _resolve_session_cookie_secure


class TestResolveSecretKey(SimpleTestCase):

    def test_debug_without_value_uses_weak_default(self):
        """En dev (DEBUG=True), sans valeur fournie, le fallback faible est toléré."""
        self.assertEqual(
            _resolve_secret_key(debug=True, value=None),
            'django-insecure-change-me-in-production-xyz123',
        )

    def test_production_without_value_raises(self):
        """En production (DEBUG=False), l'absence de SECRET_KEY doit lever une erreur explicite."""
        with self.assertRaises(ImproperlyConfigured):
            _resolve_secret_key(debug=False, value=None)

    def test_provided_value_is_always_used(self):
        """Une valeur explicite est toujours utilisée telle quelle, que DEBUG soit True ou False."""
        self.assertEqual(_resolve_secret_key(debug=False, value='une-vraie-cle'), 'une-vraie-cle')
        self.assertEqual(_resolve_secret_key(debug=True, value='une-vraie-cle'), 'une-vraie-cle')


class TestResolveSessionCookieSecure(SimpleTestCase):

    def test_production_forces_secure_cookie(self):
        """Le cas qui compte : en production (DEBUG=False), le cookie de session doit être sécurisé."""
        self.assertTrue(_resolve_session_cookie_secure(debug=False))

    def test_dev_does_not_require_https(self):
        """En dev (DEBUG=True), pas d'exigence HTTPS, pour ne pas casser le serveur de développement local."""
        self.assertFalse(_resolve_session_cookie_secure(debug=True))
