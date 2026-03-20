from django import forms

from .models import Car, Client


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ["name", "phone", "note"]


class CarForm(forms.ModelForm):
    class Meta:
        model = Car
        fields = ["brand", "model", "license_plate", "vin", "note"]