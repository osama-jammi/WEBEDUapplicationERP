"""
Context processors pour les templates
"""
from django.conf import settings


def student_context(request):
    """Ajoute les données de l'étudiant au contexte global"""
    context = {
        'SCHOOL_NAME': 'ENSIASD',
        'SCHOOL_FULL_NAME': "École Nationale Supérieure de l'Intelligence Artificielle et Sciences des Données",
    }
    
    # Ajouter les données de l'étudiant si connecté
    if hasattr(request, 'student') and request.student:
        context['current_student'] = request.student
    else:
        context['current_student'] = request.session.get('student_data')
    
    return context
