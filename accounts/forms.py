from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

# -------------------------------
# Kayıt formu
# -------------------------------
class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

# -------------------------------
# Email ile login formu
# -------------------------------
class EmailLoginForm(forms.Form):
    email = forms.EmailField(label="Email", max_length=254)
    password = forms.CharField(label="Password", widget=forms.PasswordInput)
