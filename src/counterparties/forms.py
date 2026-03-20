from django import forms

from .models import Car, Client


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ["name", "phone", "note"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Имя клиента"}),
            "phone": forms.TextInput(attrs={"placeholder": "+7 (999) 000-00-00"}),
            "note": forms.Textarea(attrs={"rows": 4, "placeholder": "Комментарий для кассы"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name"].widget.attrs.setdefault("autocomplete", "name")
        self.fields["phone"].widget.attrs.setdefault("autocomplete", "tel")


class CarForm(forms.ModelForm):
    class Meta:
        model = Car
        fields = ["brand", "model", "license_plate", "vin", "note"]
        widgets = {
            "brand": forms.TextInput(attrs={"placeholder": "Марка"}),
            "model": forms.TextInput(attrs={"placeholder": "Модель"}),
            "license_plate": forms.TextInput(attrs={"placeholder": "А123АА777"}),
            "vin": forms.TextInput(attrs={"placeholder": "VIN"}),
            "note": forms.Textarea(attrs={"rows": 4, "placeholder": "Комментарий по автомобилю"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["vin"].widget.attrs.setdefault("maxlength", 17)
