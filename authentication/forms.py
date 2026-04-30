from .admin import UserCreationForm, UserChangeForm
from django import forms
from .models import CustomUser


class UserRegisterForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = (
            'first_name', 'last_name', 'company_name', 'email', 'personal_telephone', 'office_telephone', 'address',)


class UserEditForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = (
            'first_name', 'last_name', 'company_name', 'email', 'personal_telephone', 'office_telephone', 'address', 'role')
