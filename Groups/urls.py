from django.urls import path
from Groups import views


app_name = 'groups'
urlpatterns = [
    # ex: /betting/
    path('', views.groupsHome, name='home'),
    path('search/', views.groupSearch, name='groupSearch'),
    path('create/', views.createGroup, name='createGroup'),
    path('<int:group_id>/', views.group_page, name='groupPage'),
    path('<int:group_id>/lazy_load_games/', views.lazy_load_games, name='lazy_load_posts'),
    path('<int:group_id>/invite/', views.invitePage, name='invitePage'),
    path('<int:group_id>/admin/', views.adminPageOptions, name='adminPage'),
    path('<int:group_id>/admin/games/edit/', views.adminPageEditGames, name='adminPageEditGames'),
    path('<int:group_id>/admin/games/add/', views.adminPageAddGames, name='adminPageAddGames'),
    path('<int:group_id>/admin/tournaments/edit/', views.adminPageEditTournament, name='adminPageEditTournament'),
    path('<int:group_id>/admin/tournaments/add/', views.adminPageAddTournament, name='adminPageAddTournament'),
    path('<int:group_id>/admin/members/', views.adminPageMembers, name='adminPageMembers'),
    path('<int:group_id>/tournaments/', views.tournament_list_view, name='tournament_list_view'),
    path('<int:group_id>/tournaments/<int:tournament_id>/', views.tournament_view, name='tournament_view'),
    path('<int:group_id>/<int:betting_group_id>/', views.detail, name='detail'),
    path('<int:group_id>/completed-games/', views.completed_game_list_view, name='completed_games_list_view'),

]