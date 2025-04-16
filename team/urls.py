from django.urls import path
from . import views

urlpatterns = [
    path('', views.our_team, name='our_team'),
    path('add/', views.add_team_member, name='add_team_member'),
    path('edit/<int:pk>/', views.edit_team_member, name='edit_team_member'),
    path('delete/<int:pk>/', views.delete_team_member, name='delete_team_member'),
]

