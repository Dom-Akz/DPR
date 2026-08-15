# dashboard/forms.py
from django import forms
from django.contrib.auth.forms import UserChangeForm
from .models import Administrateur


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Administrateur
        fields = [
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "job_title",
        ]
        widgets = {
            "first_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Prénom"}
            ),
            "last_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Nom"}
            ),
            "email": forms.EmailInput(
                attrs={"class": "form-control", "placeholder": "Email professionnel"}
            ),
            "phone_number": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "+212 6XX-XXXXXX"}
            ),
            "job_title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ex: Responsable Cybersécurité",
                }
            ),
        }
        labels = {
            "first_name": "Prénom",
            "last_name": "Nom",
            "email": "Email",
            "phone_number": "Téléphone",
            "job_title": "Fonction/Poste",
        }
