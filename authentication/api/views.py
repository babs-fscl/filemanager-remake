from rest_framework import status
from rest_framework.response import Response
from django.contrib.auth import authenticate
from ..models import CustomUser
from rest_framework.authtoken.models import Token
from .serializer import UserSerializer
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from django.views.decorators.csrf import csrf_protect


@csrf_protect
@api_view(['POST', ])
@permission_classes([])
@authentication_classes([])
def create_user(request):
    if request.method == 'POST':
        data = {}
        email = request.data.get('email', '0').lower()
        if validate_email(email) is not None:
            data['error_message'] = 'That email is already in use.'
            data['response'] = 'Error'
            return Response(data)

        serializer = UserSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()
            data['response'] = 'successfully registered new user.'
            data['email'] = user.email
            data['first_name'] = user.first_name
            data['last_name'] = user.last_name
            data['company_name'] = user.company_name
            data['pk'] = user.pk
            token = Token.objects.get(user=user).key
            data['token'] = token
            return Response(data, status=status.HTTP_201_CREATED)
        else:
            data = serializer.errors
            return Response(data, status=status.HTTP_400_BAD_REQUEST)


def validate_email(email):
    try:
        user = CustomUser.objects.get(email=email)
    except CustomUser.DoesNotExist:
        return None
    if user is not None:
        return email


class ObtainAuthTokenView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        data = {}
        email = request.POST.get('email')
        password = request.POST.get('password')
        account = authenticate(email=email, password=password)
        if account:
            try:
                token = Token.objects.get(user=account)
            except Token.DoesNotExist:
                token = Token.objects.create(user=account)
            data['response'] = 'Successfully authenticated.'
            data['pk'] = account.pk
            data['email'] = email.lower()
            data['token'] = token.key
            return Response(data, status=status.HTTP_200_OK)
        else:
            data['response'] = 'Error'
            data['error_message'] = 'Invalid credentials'
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
