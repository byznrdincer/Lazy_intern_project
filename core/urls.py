from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('how-it-works/', views.how_it_works, name='how_it_works'),
    path('for-students/', views.for_students, name='for_students'),
    path('for-companies/', views.for_companies, name='for_companies'),
    path('about/', views.about, name='about'),
]
