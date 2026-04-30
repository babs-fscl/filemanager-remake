from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_user, name='login'),
    path('logout_user/', views.logout_user, name='logout_user'),
    path('register/', views.register_user, name='register'),
    path('select/', views.selectionPage, name='select'),
    path('organization/members/', views.organization_members, name='organization_members'),
]