from rest_framework import status
from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import *
from .serializers import *
from .permissions import *
import datetime
from agriculture.settings import MEDIA_ROOT
from django.core.files.storage import FileSystemStorage
import os

class UserList(APIView):
    def get(self, request, format = None):
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

    def post(self, request, format = None):
        username = request.data.get('username')
        password = request.data.get('password') 
        request.data.pop('username')
        request.data.pop('password')
        try:
            django_user_obj = DjangoUser.objects.create(username=username)
        except IntegrityError as e:
            raise ValidationError(str(e))
        django_user_obj.set_password(password)
        django_user_obj.save()
        request.data['auth_user'] = django_user_obj
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserDetail(APIView):
    def get_object(self, pk):
        try:
            return User.objects.get(pk=pk)
        except User.DoesNotExist:
            raise Http404

    def get(self, request, pk, format = None):
        user = self.get_object(pk)
        serializer = UserSerializer(user)
        return Response(serializer.data)

    def put(self, request, pk, format = None):
        user = self.get_object(pk)
        serializer = UserSerializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format = None):
        user = self.get_object(pk)
        user.delete()
        return Response(status=HTTP_204_NO_CONTENT)

class GetUser(APIView):
    permission_classes = [IsAuthenticated,]
    def get(self, request, format = None):
        print(request.user)
        user = User.objects.get(auth_user = request.user.pk)
        serializer = UserSerializer(user)
        return Response(serializer.data)

class LocationList(APIView):
    permission_classes = []
    def get(self, request, format = None):
        Location = Location.objects.all()
        serializer = LocationSerializer(Location, many=True)
        return Response(serializer.data)

    def post(self, request, format = None):
        directory = MEDIA_ROOT + '/locationCSVs/'
        if not os.path.exists(directory):
            os.makedirs(directory)

        locations = []
        count = 0
        if 'location_csv' in request.data:
            if not request.data['location_csv'].name.endswith('.csv'):
                return Response({'location_csv': ['Please upload a valid document ending with .csv']},
                    status = HTTP_400_BAD_REQUEST)
            fs = FileSystemStorage()
            fs.save(directory + request.data['location_csv'].name, request.data['location_csv'])
            csvFile = open(directory + request.data['location_csv'].name, 'r')
            for line in csvFile.readlines():
                locations.append(line)
            
            locations.pop(0);

            for data in locations:
                data = data.split(',')
                request.data['state']  = data[0]
                request.data['district'] = data[1]
                request.data['block_name'] = data[2]
                request.data['village_name'] = data[3]
                request.data['longitude'] = data[4]
                request.data['latitude'] = data[5]
                request.data['acq_date'] = datetime.datetime.strptime(data[6], '%d/%m/%Y').strftime('%Y-%m-%d')
                request.data['acq_time'] = data[7].split('.')[0]
                # request.data['csv_file'] = MEDIA_ROOT + 'locationCSVs/' + request.data['location_csv'].name
                try:
                    dda = User.objects.get(typeOfUser = 'dda', district=data[1].lower())
                    request.data['dda'] = dda.pk
                except User.DoesNotExist:
                    if 'dda' in request.data:
                        del request.data['dda']
                # print("dda", request.data['csv_file'])
                serializer = LocationSerializer(data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    count = count + 1;
                    print("added", count)
            return Response({'status': 'success', 'count': count}, status=status.HTTP_201_CREATED)
        return Response({'error': 'invalid'}, status=status.HTTP_400_BAD_REQUEST)