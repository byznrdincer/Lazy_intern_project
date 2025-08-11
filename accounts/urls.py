from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),

    # Company e-posta doğrulama giriş (slug'lı verify'e yönlendirir)
    path('company/verify-email/', views.company_verify_entry, name='company_verify_email'),

    # Kod gönder & doğrulama (view'lar artık accounts.views içinde)
    path('company/<slug:slug>/send-code/', views.company_send_verification_code, name='company_send_verification_code'),
    path('company/<slug:slug>/verify/',     views.company_email_verify,          name='company_email_verify'),
]
