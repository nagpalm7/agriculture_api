from .models import *
from rest_framework import serializers
from django.contrib import auth
from django.utils import timezone
import datetime
from django.db import IntegrityError
from rest_framework.exceptions import ValidationError


# CustomerInformation Serializer
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['pk', 'username', 'type_of_user',]   

class AdminSerializer(serializers.ModelSerializer):
    auth_user = UserSerializer(read_only=True)
    class Meta:
        model = Admin
        fields = '__all__'

class DdaSerializer(serializers.ModelSerializer):
    auth_user = UserSerializer(read_only=True)
    class Meta:
        model = Dda
        fields = '__all__'

class AdoSerializer(serializers.ModelSerializer):
    auth_user = UserSerializer(read_only=True)
    dda = DdaSerializer()
    class Meta:
        model = Ado
        fields = '__all__'


class LocationSerializer(serializers.ModelSerializer):
    ado = AdoSerializer(read_only=True)
    dda = DdaSerializer(read_only=True)
    class Meta:
        model = Location
        fields = '__all__'                        

