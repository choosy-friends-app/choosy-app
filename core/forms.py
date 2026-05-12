from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Group, PlanProposal, Plan

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user

class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name', 'description', 'mission_statement', 'hero_image_url', 'interests']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'groups-input', 'placeholder': 'Group title'}),
            'description': forms.Textarea(attrs={'class': 'groups-textarea', 'rows': 3}),
            'mission_statement': forms.TextInput(attrs={'class': 'groups-input'}),
            'hero_image_url': forms.URLInput(attrs={'class': 'groups-input'}),
            'interests': forms.TextInput(attrs={'class': 'groups-input', 'placeholder': 'e.g. ["sports", "music"]'}),
        }

class PlanProposalForm(forms.ModelForm):
    class Meta:
        model = PlanProposal
        fields = ['group', 'title', 'description', 'voting_ends_at']
        widgets = {
            'group': forms.Select(attrs={'class': 'groups-input'}),
            'title': forms.TextInput(attrs={'class': 'groups-input'}),
            'description': forms.TextInput(attrs={'class': 'groups-input'}),
            'voting_ends_at': forms.DateTimeInput(attrs={'class': 'groups-input', 'type': 'datetime-local'}),
        }

class PlanForm(forms.ModelForm):
    class Meta:
        model = Plan
        fields = [
            'proposal', 'title', 'description', 'price', 
            'duration_minutes', 'tag', 'image_url', 
            'place_name', 'address', 'scheduled_for'
        ]
        widgets = {
            'proposal': forms.Select(attrs={'class': 'groups-input'}),
            'title': forms.TextInput(attrs={'class': 'groups-input'}),
            'description': forms.TextInput(attrs={'class': 'groups-input'}),
            'price': forms.NumberInput(attrs={'class': 'groups-input'}),
            'duration_minutes': forms.NumberInput(attrs={'class': 'groups-input'}),
            'tag': forms.TextInput(attrs={'class': 'groups-input'}),
            'image_url': forms.URLInput(attrs={'class': 'groups-input'}),
            'place_name': forms.TextInput(attrs={'class': 'groups-input'}),
            'address': forms.TextInput(attrs={'class': 'groups-input'}),
            'scheduled_for': forms.DateTimeInput(attrs={'class': 'groups-input', 'type': 'datetime-local'}),
        }
