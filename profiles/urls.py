from django.urls import path
from . import views

urlpatterns = [
    path('redirect/', views.profile_redirect, name='profile_redirect'),

    path('profile/<str:username>/edit/', views.profile_edit, name='profile_edit'),
    path('profile/<str:username>/', views.profile_detail, name='profile_detail'),

    path('company/<slug:slug>/', views.company_profile, name='company_profile'),

    # Öğrenci herkese açık profil
    path('student/<int:user_id>/', views.student_profile_view, name='student_profile_view'),

    # Profil görüntüleme sayacı (POST)
    path('student/<int:user_id>/increment-profile-views/',
         views.increment_profile_views,
         name='increment_profile_views'),

    # Bookmark toggle (POST)
    path('bookmark/<int:student_id>/toggle/',
         views.toggle_bookmark,
         name='toggle_bookmark'),
]
