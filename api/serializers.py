from .models import *
from rest_framework import serializers
from django.contrib import auth
from django.utils import timezone
import datetime
from django.db import IntegrityError
from rest_framework.exceptions import ValidationError

# Nested Serializers
class AddUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['pk', 'username', 'type_of_user',]   

class AddAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Admin
        fields = '__all__'

class AddDdaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dda
        fields = '__all__'

class AddAdoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ado
        fields = '__all__'

class AddLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = '__all__'

# CustomerInformation Serializer
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['pk', 'username', 'type_of_user',]   

class AdminSerializer(serializers.ModelSerializer):
    auth_user = UserSerializer()
    class Meta:
        model = Admin
        fields = '__all__'

class DdaSerializer(serializers.ModelSerializer):
    auth_user = UserSerializer()
    class Meta:
        model = Dda
        fields = '__all__'

class AdoSerializer(serializers.ModelSerializer):
    auth_user = UserSerializer()
    dda = DdaSerializer()
    class Meta:
        model = Ado
        fields = '__all__'


class LocationSerializer(serializers.ModelSerializer):
    ado = AdoSerializer()
    dda = DdaSerializer()
    class Meta:
        model = Location
        fields = '__all__'                        
