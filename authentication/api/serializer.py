from rest_framework import serializers
from ..models import CustomUser


class UserSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(style={'input_type': 'password'}, write_only=True)

    class Meta:
        model = CustomUser
        fields = [
            'email',
            'first_name',
            'last_name',
            'company_name',
            'personal_telephone',
            'office_telephone',
            'address',
            'password',
            'password2',
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'company_name': {'required': False, 'allow_blank': True},
            'personal_telephone': {'required': False, 'allow_blank': True},
            'office_telephone': {'required': False, 'allow_blank': True},
            'address': {'required': False, 'allow_blank': True},
        }

    def save(self, **kwargs):
        user = CustomUser(email=self.validated_data['email'],
                          first_name=self.validated_data['first_name'],
                          last_name=self.validated_data['last_name'],
                          company_name=self.validated_data.get('company_name', ''),
                          personal_telephone=self.validated_data.get('personal_telephone', ''),
                          office_telephone=self.validated_data.get('office_telephone', ''),
                          address=self.validated_data.get('address', ''),)
        password = self.validated_data['password']
        password2 = self.validated_data['password2']
        if password == password2:
            user.set_password(password)
            user.save()
            return user
        else:
            raise serializers.ValidationError({'password': 'Passwords must match.'})


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    confirm_password = serializers.CharField(required=True)
