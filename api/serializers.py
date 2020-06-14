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

class AddAdoReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdoReport
        fields = '__all__'

class ImageSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Image
        fields = ('image',)

class AddImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = '__all__'

# CustomerInformation Serializer
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['pk', 'username', 'type_of_user',]   

class DistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = District
        fields = '__all__'

class VillageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Village
        fields = '__all__'

class AdminSerializer(serializers.ModelSerializer):
    auth_user = UserSerializer()
    class Meta:
        model = Admin
        fields = '__all__'

class DdaSerializer(serializers.ModelSerializer):
    auth_user = UserSerializer()
    district = DistrictSerializer()
    class Meta:
        model = Dda
        fields = '__all__'

class AdoSerializer(serializers.ModelSerializer):
    auth_user = UserSerializer()
    village = VillageSerializer(many=True)
    dda = DdaSerializer()
    class Meta:
        model = Ado
        fields = '__all__'

class DCSerializer(serializers.ModelSerializer):
    class Meta:
        model = DC
        fields = '__all__'

class SPSerializer(serializers.ModelSerializer):
    class Meta:
        model = SP
        fields = '__all__'

class LocationSerializer(serializers.ModelSerializer):
    ado = AdoSerializer()
    dda = DdaSerializer()
    class Meta:
        model = Location
        fields = '__all__'

class MapSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = '__all__'                    

class AdoReportSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()
    location = LocationSerializer()

    class Meta:
        model = AdoReport
        fields = '__all__'

    def get_images(self, obj):
        images = Image.objects.filter(report = obj).order_by('-pk')
        return ImageSerializer(images, many=True, context={'request':self.context.get('request')}).data

class AppVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppVersion
        fields = '__all__'


class CompareDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompareData
        fields = '__all__'

        
###################################changes #######################################
class AdoSerializer_location(serializers.ModelSerializer):  
    auth_user = UserSerializer()
    class Meta:
        model = Ado
        exclude =['village','dda']

class DdaSerializer_location(serializers.ModelSerializer):
    auth_user = UserSerializer()
    
    class Meta:
        model = Dda
        exclude = ['district']

class LocationSerializer_location(serializers.ModelSerializer):
    ado = AdoSerializer_location()
    dda = DdaSerializer_location()

    class Meta:
        model = Location
        fields = '__all__'
#########################################################################
