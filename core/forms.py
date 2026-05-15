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
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields['group'].queryset = Group.objects.filter(owner=user)

    class Meta:
        model = PlanProposal
        fields = ['group', 'title', 'description', 'voting_ends_at']
        widgets = {
            'group': forms.Select(attrs={'class': 'groups-input'}),
            'title': forms.TextInput(attrs={'class': 'groups-input'}),
            'description': forms.TextInput(attrs={'class': 'groups-input'}),
            'voting_ends_at': forms.DateTimeInput(
                attrs={'class': 'groups-input', 'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M',
            ),
        }


class PlanForm(forms.ModelForm):
    location_latitude = forms.DecimalField(required=False, widget=forms.HiddenInput())
    location_longitude = forms.DecimalField(required=False, widget=forms.HiddenInput())

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields['proposal'].queryset = PlanProposal.objects.filter(created_by=user).select_related("group")

    class Meta:
        model = Plan
        fields = [
            'proposal', 'title', 'description', 'price', 
            'duration_minutes', 'tag', 'image_url', 
            'place_name', 'address', 'scheduled_for'
        ]
        widgets = {
            'proposal': forms.Select(attrs={'class': 'groups-input'}),
            'title': forms.TextInput(attrs={'class': 'groups-input', 'placeholder': 'e.g. Rooftop dinner'}),
            'description': forms.TextInput(attrs={'class': 'groups-input', 'placeholder': 'Short pitch for the group'}),
            'price': forms.NumberInput(attrs={'class': 'groups-input', 'min': '0', 'step': '0.01', 'placeholder': '0.00'}),
            'duration_minutes': forms.NumberInput(attrs={'class': 'groups-input', 'min': '1', 'placeholder': '90'}),
            'tag': forms.TextInput(attrs={'class': 'groups-input', 'placeholder': 'food, culture, sport...'}),
            'image_url': forms.URLInput(attrs={'class': 'groups-input', 'placeholder': 'https://...'}),
            'place_name': forms.TextInput(attrs={
                'class': 'groups-input',
                'autocomplete': 'off',
                'data-location-input': 'true',
                'placeholder': 'Type a city, venue, or address',
            }),
            'address': forms.TextInput(attrs={
                'class': 'groups-input',
                'data-address-input': 'true',
                'placeholder': 'Autofills after selecting a location',
            }),
            'scheduled_for': forms.DateTimeInput(
                attrs={'class': 'groups-input', 'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M',
            ),
        }
