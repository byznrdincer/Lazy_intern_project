from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.utils.crypto import get_random_string
from django.contrib.auth import get_user_model

User = get_user_model()

class NoPromptAccountAdapter(DefaultAccountAdapter):
    def generate_unique_username(self, txts, regex=None):
        # varsayılanı üret
        base = super().generate_unique_username(txts, regex)
        # varsa kısa bir rastgele ekle
        if User.objects.filter(username=base).exists():
            base = f"{base}-{get_random_string(6).lower()}"
        return base

class NoPromptSocialAdapter(DefaultSocialAccountAdapter):
    def is_auto_signup_allowed(self, request, sociallogin):
        # Her zaman otomatik kayıt (Google e-postası doğrulanmış geliyor)
        return True
