from django.urls import path
from .views import create_user, ObtainAuthTokenView
from rest_framework.urlpatterns import format_suffix_patterns

app_name = 'authentication'

urlpatterns = [
    path('create/', create_user, name='register_user'),
    path('login/', ObtainAuthTokenView.as_view(), name='token_view'),
]

urlpatterns = format_suffix_patterns(urlpatterns)