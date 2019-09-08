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
        fields = '__all__'

class LocationSerializer(serializers.ModelSerializer):
    ado = UserSerializer()
    dda = UserSerializer()
    
    class Meta:
        model = Location
        fields = '__all__'   

class AdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Admin
        fields = '__all__'

class AdoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ado
        fields = '__all__'

class DdaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dda
        fields = '__all__'                             

