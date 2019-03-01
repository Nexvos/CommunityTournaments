from django.urls import path
from . import views


app_name = 'profiles'
urlpatterns = [
    # ex: /betting/
    path('join/', views.landingPage, name='landingPage'),
    path('profile/', views.profile_details_default, name='profileDetailsDefault'),
    path('profile/<int:group_id>/', views.profile_details_group, name='profileDetailsGroup'),
]