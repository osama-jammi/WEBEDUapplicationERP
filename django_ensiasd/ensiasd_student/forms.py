"""
Formulaires pour le portail étudiant
"""
from django import forms
from django.core.validators import MinLengthValidator


class LoginForm(forms.Form):
    """Formulaire de connexion"""
    cne = forms.CharField(
        label='CNE',
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Votre CNE',
            'autofocus': True,
        })
    )
    password = forms.CharField(
        label='Mot de passe',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Votre mot de passe',
        })
    )
    remember_me = forms.BooleanField(
        label='Se souvenir de moi',
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        })
    )


class ChangePasswordForm(forms.Form):
    """Formulaire de changement de mot de passe"""
    old_password = forms.CharField(
        label='Mot de passe actuel',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Mot de passe actuel',
        })
    )
    new_password = forms.CharField(
        label='Nouveau mot de passe',
        min_length=8,
        validators=[MinLengthValidator(8)],
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nouveau mot de passe (min. 8 caractères)',
        })
    )
    confirm_password = forms.CharField(
        label='Confirmer le mot de passe',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirmer le nouveau mot de passe',
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if new_password and confirm_password:
            if new_password != confirm_password:
                raise forms.ValidationError("Les mots de passe ne correspondent pas")
        
        return cleaned_data


class DateRangeForm(forms.Form):
    """Formulaire de sélection de période"""
    date_from = forms.DateField(
        label='Du',
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
        })
    )
    date_to = forms.DateField(
        label='Au',
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        
        if date_from and date_to and date_from > date_to:
            raise forms.ValidationError("La date de fin doit être après la date de début")
        
        return cleaned_data


class ReclamationForm(forms.Form):
    """Formulaire de soumission d'une réclamation"""
    CATEGORIES = [
        ('note', 'Contestation de note'),
        ('absence', 'Erreur sur absence'),
        ('pedagogique', 'Pédagogique / Cours'),
        ('administratif', 'Administratif'),
        ('autre', 'Autre'),
    ]
    PRIORITES = [
        ('0', 'Normale'),
        ('1', 'Urgente'),
    ]
    
    categorie = forms.ChoiceField(
        label='Catégorie',
        choices=CATEGORIES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    priorite = forms.ChoiceField(
        label='Priorité',
        choices=PRIORITES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    sujet = forms.CharField(
        label='Objet / Sujet',
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex: Contestation de la note du module Machine Learning',
        })
    )
    description = forms.CharField(
        label='Description détaillée',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Précisez votre demande, le module concerné, la date...',
        })
    )

