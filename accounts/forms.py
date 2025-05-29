from django.forms import ModelForm
from django import forms
from .models import Account, UserProfile


class RegisterForm(ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"placeholder": "Enter password", "class": "form-control"}
        )
    )

    confirm_password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"placeholder": "Confirm password", "class": "form-control"}
        )
    )

    class Meta:
        model = Account
        fields = ["first_name", "last_name", "phone_number", "email", "password"]

    def clean(self):
        cleaned_data = super(RegisterForm, self).clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError("Password does not match!")

    def __init__(self, *args, **kwargs):
        super(RegisterForm, self).__init__(*args, **kwargs)
        placeholders = {
            "first_name": "Enter First Name",
            "last_name": "Enter last Name",
            "phone_number": "Enter Phone Number",
            "email": "Enter Email Address",
        }
        print(
            "🐍 File: accounts/forms.py | Line: 38 | __init__ ~ self.fields",
            self.fields,
        )
        for field_name, field in self.fields.items():
            field.widget.attrs["class"] = "form-control"

            if field_name in placeholders:
                field.widget.attrs["placeholder"] = placeholders[field_name]
