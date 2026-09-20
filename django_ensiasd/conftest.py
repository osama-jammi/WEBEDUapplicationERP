# -*- coding: utf-8 -*-
"""
Configuration pytest globale au projet.

CompressedManifestStaticFilesStorage (whitenoise) exige que collectstatic
ait été exécuté pour générer le manifeste des fichiers statiques ; sans ça,
tout template utilisant {% static %} lève une erreur. On l'exécute une fois
pour toute la session de tests, dans STATIC_ROOT (déjà ignoré par Git).
"""
import pytest
from django.core.management import call_command


@pytest.fixture(scope='session', autouse=True)
def collect_static_once():
    call_command('collectstatic', verbosity=0, interactive=False)
