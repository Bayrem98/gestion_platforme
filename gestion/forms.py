from django import forms
from .models import *
from django.core.exceptions import ValidationError
from .models import PlanningSimple
from datetime import datetime, timedelta

class EmployeForm(forms.ModelForm):
    class Meta:
        model = Employe
        fields = '__all__'
        widgets = {
            'date_naissance': forms.DateInput(
                attrs={
                    'type': 'date', 
                    'class': 'form-control',
                    'value': '{{ form.date_naissance.value|date:"Y-m-d" }}'  # Format pour l'affichage
                },
                format='%Y-%m-%d'
            ),
            'date_embauche': forms.DateInput(
                attrs={
                    'type': 'date', 
                    'class': 'form-control',
                    'value': '{{ form.date_embauche.value|date:"Y-m-d" }}'
                },
                format='%Y-%m-%d'
            ),
            'adresse': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'matricule': forms.TextInput(attrs={'class': 'form-control'}),
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'prenom': forms.TextInput(attrs={'class': 'form-control'}),
            'cin': forms.TextInput(attrs={'class': 'form-control'}),
            'type_contrat': forms.Select(attrs={'class': 'form-control'}),
            'salaire_base': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'poste_choice': forms.Select(attrs={
                'class': 'form-control', 
                'id': 'id_poste_choice'
            }),
            'poste_autre': forms.TextInput(attrs={
                'class': 'form-control', 
                'id': 'id_poste_autre',
                'placeholder': 'Saisissez le poste personnalisé'
            }),
        }

def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Rendre poste_autre non requis par défaut
        self.fields['poste_autre'].required = False

        # Formatage des dates pour l'affichage
        if self.instance and self.instance.pk:
            # Si c'est une modification, pré-remplir les dates
            if self.instance.date_naissance:
                self.initial['date_naissance'] = self.instance.date_naissance.strftime('%Y-%m-%d')
            if self.instance.date_embauche:
                self.initial['date_embauche'] = self.instance.date_embauche.strftime('%Y-%m-%d')
    
def clean(self):
        cleaned_data = super().clean()
        poste_choice = cleaned_data.get('poste_choice')
        poste_autre = cleaned_data.get('poste_autre')
        
        # Validation : si 'AUTRE' est choisi, poste_autre doit être rempli
        if poste_choice == 'AUTRE' and not poste_autre:
            self.add_error('poste_autre', 'Veuillez préciser le poste')
        
        return cleaned_data

        
class FreelancerForm(forms.ModelForm):
    class Meta:
        model = Freelancer
        fields = '__all__'
        widgets = {
            'adresse': forms.Textarea(attrs={'rows': 3}),
        }

class ChantierForm(forms.ModelForm):
    class Meta:
        model = Chantier
        fields = '__all__'
        widgets = {
            'date_debut': forms.DateInput(attrs={'type': 'date'}),
            'date_fin': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 4}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = '__all__'
        widgets = {
            'date_transaction': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        type_transaction = cleaned_data.get('type_transaction')
        montant = cleaned_data.get('montant')
        
        if montant and montant <= 0:
            raise ValidationError("Le montant doit être supérieur à 0")
        
        return cleaned_data

class AffectationChantierForm(forms.ModelForm):
    class Meta:
        model = AffectationChantier
        fields = ['employe', 'heures_travaillees']

class PrimeForm(forms.ModelForm):
    class Meta:
        model = Prime
        fields = ['employe', 'chantier', 'montant', 'mois', 'annee', 'description']
        widgets = {
            'mois': forms.NumberInput(attrs={'min': 1, 'max': 12}),
            'annee': forms.NumberInput(attrs={'min': 2020}),
        }

class RecuForm(forms.ModelForm):
    class Meta:
        model = Recu
        fields = ['beneficiaire', 'motif']
        widgets = {
            'beneficiaire': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom du bénéficiaire'}),
            'motif': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Description détaillée du paiement'}),
        }
        labels = {
            'beneficiaire': 'Bénéficiaire',
            'motif': 'Motif du paiement',
        }        

class PlanningSimpleForm(forms.ModelForm):
    class Meta:
        model = PlanningSimple
        fields = ['date', 'heure_debut', 'heure_fin', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'heure_debut': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'heure_fin': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'notes': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Matinée, Après-midi...'}),
        }