from django.urls import path
from . import views


app_name = 'profiles'
urlpatterns = [
    # ex: /betting/
    path('join/', views.landingPage, name='landingPage'),

]