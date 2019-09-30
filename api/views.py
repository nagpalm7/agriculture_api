from rest_framework import status
from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import viewsets, filters
from .models import *
from .serializers import *
from .permissions import *
from .paginators import *
import datetime
from agriculture.settings import MEDIA_ROOT, DOMAIN
from django.core.files.storage import FileSystemStorage
import os
from django.db.models import Q
import http.client
import uuid

class UserList(APIView):
    permission_classes = []
    def get(self, request, format = None):
        users = User.objects.all().order_by('-pk')
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

    def post(self, request, format = None):
        data = request.data.copy()
        username = data.get('username')
        password = data.get('password') 
        type_of_user = data.get('type_of_user')
        try:
            django_user_obj = User.objects.create(username=username, type_of_user=type_of_user)
        except IntegrityError as e:
            raise ValidationError(str(e))
        django_user_obj.set_password(password)
        django_user_obj.save()
        data['auth_user'] = django_user_obj.pk
        del data['type_of_user']
        del data['username']
        del data['password']
        serializer = []
        villages = []
        if type_of_user == 'admin':
            serializer = AddAdminSerializer(data=data)
        elif type_of_user == 'dda':
            serializer = AddDdaSerializer(data=data)
        elif type_of_user == 'ado':
            serializer = AddAdoSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserDetail(APIView):
    def get_object(self, pk):
        try:
            return User.objects.get(pk=pk)
        except User.DoesNotExist:
            raise Http404

    def get(self, request, pk, format = None):
        user = self.get_object(pk)
        type_of_user = user.type_of_user
        data = []
        serializer = []
        if type_of_user == 'admin':
            data = Admin.objects.get(auth_user=pk)
            serializer = AdminSerializer(data)
        elif type_of_user == 'dda':
            data = Dda.objects.get(auth_user=pk)
            serializer = DdaSerializer(data)
        elif type_of_user == 'ado':
            data = Ado.objects.get(auth_user=pk)
            serializer = AdoSerializer(data)        
        return Response(serializer.data)

    def put(self, request, pk, format = None):
        user = self.get_object(pk)
        type_of_user = user.type_of_user
        data = []
        serializer = []
        if type_of_user == 'admin':
            data = Admin.objects.get(auth_user=pk)
            serializer = AddAdminSerializer(data, request.data, partial=True)
        elif type_of_user == 'dda':
            data = Dda.objects.get(auth_user=pk)
            serializer = AddDdaSerializer(data, request.data, partial=True)
        elif type_of_user == 'ado':
            data = Ado.objects.get(auth_user=pk)
            serializer = AddAdoSerializer(data, request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format = None):
        user = self.get_object(pk)
        type_of_user = user.type_of_user
        if type_of_user == 'admin':
            data = Admin.objects.get(auth_user=pk)
        elif type_of_user == 'dda':
            data = Dda.objects.get(auth_user=pk)
        elif type_of_user == 'ado':
            data = Ado.objects.get(auth_user=pk)
        data.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)            

# DDA List
class DDAList(APIView):
    permission_classes = []
    def get(self, request, format = None):
        ddas = Dda.objects.all().order_by('name')
        serializer = DdaSerializer(ddas, many=True)
        return Response(serializer.data)

# VIEWS FOR DISTRICT
class DistrictList(APIView):
    permission_classes = []
    def get(self, request, format = None):
        districts = District.objects.all().order_by('-pk')
        serializer = DistrictSerializer(districts, many=True)
        return Response(serializer.data)

    def post(self, request, format = None):
        serializer = DistrictSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DistrictDetail(APIView):
    def get_object(self, pk):
        try:
            return District.objects.get(pk=pk)
        except District.DoesNotExist:
            raise Http404

    def get(self, request, pk, format = None):
        district = self.get_object(pk)
        data = District.objects.get(pk=pk)
        serializer = DistrictSerializer(data)         
        return Response(serializer.data)

    def put(self, request, pk, format = None):
        district = self.get_object(pk)
        serializer = DistrictSerializer(district, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format = None):
        district = self.get_object(pk)
        district.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

# VIEWS FOR Village
# Shows list of ado for specific dda logged in
class VillageViewSet(viewsets.ReadOnlyModelViewSet):
    model = Village
    serializer_class = VillageSerializer
    permission_classes = (IsAuthenticated, )
    pagination_class = StandardResultsSetPagination
    # Making endpoint searchable
    filter_backends = (filters.SearchFilter, )
    search_fields = ('village', )

    def get_queryset(self):
        villages = Village.objects.all().order_by('-pk')
        return villages

class VillageList(APIView):
    permission_classes = []
    def get(self, request, format = None):
        villages = Village.objects.all().order_by('village')
        serializer = VillageSerializer(villages, many=True)
        return Response(serializer.data)

    def post(self, request, format = None):
        serializer = VillageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VillageDetail(APIView):
    def get_object(self, pk):
        try:
            return Village.objects.get(pk=pk)
        except Village.DoesNotExist:
            raise Http404

    def get(self, request, pk, format = None):
        village = self.get_object(pk)
        data = Village.objects.get(pk=pk)
        serializer = VillageSerializer(data)         
        return Response(serializer.data)

    def put(self, request, pk, format = None):
        village = self.get_object(pk)
        serializer = VillageSerializer(village, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format = None):
        village = self.get_object(pk)
        village.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

# Shows list of Admins
class AdminViewSet(viewsets.ReadOnlyModelViewSet):
    model = Admin
    serializer_class = AdminSerializer
    permission_classes = (IsAuthenticated, )
    pagination_class = StandardResultsSetPagination
    # Making endpoint searchable
    # filter_backends = (filters.SearchFilter, )
    # search_fields = ('centre__location', 'course__title', 'first_name', 'last_name', '=contact_number', 'user__email')

    def get_queryset(self):
        admins = Admin.objects.all().order_by('-pk')
        return admins

# Shows list of Ddas
class DdaViewSet(viewsets.ReadOnlyModelViewSet):
    model = Dda
    serializer_class = DdaSerializer
    permission_classes = (IsAuthenticated, )
    pagination_class = StandardResultsSetPagination
    # Making endpoint searchable
    # filter_backends = (filters.SearchFilter, )
    # search_fields = ('centre__location', 'course__title', 'first_name', 'last_name', '=contact_number', 'user__email')

    def get_queryset(self):
        ddas = Dda.objects.all().order_by('-pk')
        return ddas

# Shows list of Ados
class AdosViewSet(viewsets.ReadOnlyModelViewSet):
    model = Ado
    serializer_class = AdoSerializer
    permission_classes = (IsAuthenticated, )
    pagination_class = StandardResultsSetPagination
    # Making endpoint searchable
    # filter_backends = (filters.SearchFilter, )
    # search_fields = ('centre__location', 'course__title', 'first_name', 'last_name', '=contact_number', 'user__email')

    def get_queryset(self):
        ados = Ado.objects.all().order_by('-pk')
        return ados

# Details of particular location and edit location in order to set ado
class LocationDetail(APIView):
    permission_classes = []
    def get_object(self, pk):
        try:
            return Location.objects.get(pk=pk)
        except Location.DoesNotExist:
            raise Http404

    def get(self, request, pk, format = None):
        location = self.get_object(pk)
        serializer = LocationSerializer(location)
        return Response(serializer.data)

    def patch(self, request, pk, format = None):
        location = self.get_object(pk)
        serializer = AddLocationSerializer(location, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format = None):
        location = self.get_object(pk)
        location.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class GetUser(APIView):
    permission_classes = [IsAuthenticated,]
    def get(self, request, format = None):
        type_of_user = request.user.type_of_user
        data = []
        serializer = []
        if type_of_user == 'admin':
            data = Admin.objects.get(auth_user=request.user.pk)
            serializer = AdminSerializer(data)
        elif type_of_user == 'dda':
            data = Dda.objects.get(auth_user=request.user.pk)
            serializer = DdaSerializer(data)
        elif type_of_user == 'ado':
            data = Ado.objects.get(auth_user=request.user.pk)
            serializer = AdoSerializer(data)        
        return Response(serializer.data)

# Shows list of locations unassigned, assigned, ongoing, pending for admin
class LocationViewSet(viewsets.ReadOnlyModelViewSet):
    model = Location
    serializer_class = LocationSerializer
    # permission_classes = (permissions.IsAuthenticated, IsSuperadmin, )
    pagination_class = StandardResultsSetPagination
    # Making endpoint searchable
    # filter_backends = (filters.SearchFilter, )
    # search_fields = ('centre__location', 'course__title', 'first_name', 'last_name', '=contact_number', 'user__email')

    def get_queryset(self):
        stat = self.kwargs['status']
        if stat == 'unassigned':
            locations = Location.objects.filter(status='pending', ado=None).order_by('village_name', 'block_name', 'district')
        elif stat == 'assigned':
            locations = Location.objects.filter(status='pending').exclude(ado=None).order_by('village_name', 'block_name', 'district')
        else:
            locations = Location.objects.filter(status=stat).order_by('village_name', 'block_name', 'district')
        return locations

# Shows list of locations for specific ado logged in
class LocationViewSetAdo(viewsets.ReadOnlyModelViewSet):
    model = Location
    serializer_class = LocationSerializer
    permission_classes = (IsAuthenticated, )
    pagination_class = StandardResultsSetPagination
    # Making endpoint searchable
    # filter_backends = (filters.SearchFilter, )
    # search_fields = ('centre__location', 'course__title', 'first_name', 'last_name', '=contact_number', 'user__email')

    def get_queryset(self):
        try:
            user = Ado.objects.get(auth_user=self.request.user.pk)
        except Ado.DoesNotExist:
            raise Http404
        stat = self.kwargs['status']
        locations = []
        if stat == 'pending':
            locations = Location.objects.filter(status=stat, ado=user).order_by('village_name', 'block_name', 'district')
        elif stat == 'completed':
            locations = Location.objects.filter(status__in=['completed', 'ongoing'], ado=user).order_by('village_name', 'block_name', 'district')
        return locations

# Shows list of locations for specific dda
class LocationViewSetDda(viewsets.ReadOnlyModelViewSet):
    model = Location
    serializer_class = LocationSerializer
    permission_classes = (IsAuthenticated, )
    pagination_class = StandardResultsSetPagination
    # Making endpoint searchable
    # filter_backends = (filters.SearchFilter, )
    # search_fields = ('centre__location', 'course__title', 'first_name', 'last_name', '=contact_number', 'user__email')

    def get_queryset(self):
        try:
            user = Dda.objects.get(auth_user=self.request.user.pk)
        except Dda.DoesNotExist:
            raise Http404
        stat = self.kwargs['status']
        locations = []
        if stat == 'unassigned':
            locations = Location.objects.filter(status='pending', dda=user ,ado=None).order_by('village_name', 'block_name', 'district')
        elif stat == 'assigned':
            locations = Location.objects.filter(status='pending', dda=user).exclude(ado=None).order_by('village_name', 'block_name', 'district')
        elif stat == 'ongoing':
            locations = Location.objects.filter(status=stat, dda=user).order_by('village_name', 'block_name', 'district')
        elif stat == 'completed':
            locations = Location.objects.filter(status=stat, dda=user).order_by('village_name', 'block_name', 'district')
        return locations

# Shows list of ado for specific dda logged in
class AdoViewSet(viewsets.ReadOnlyModelViewSet):
    model = Ado
    serializer_class = AdoSerializer
    permission_classes = (IsAuthenticated, )
    pagination_class = StandardResultsSetPagination
    # Making endpoint searchable
    # filter_backends = (filters.SearchFilter, )
    # search_fields = ('centre__location', 'course__title', 'first_name', 'last_name', '=contact_number', 'user__email')

    def get_queryset(self):
        try:
            dda = Dda.objects.get(auth_user=self.request.user.pk)
        except Dda.DoesNotExist:
            raise Http404
        ados = Ado.objects.filter(dda = dda).order_by('dda__district__district')
        return ados

# Upload CSV
class LocationList(APIView):
    permission_classes = []

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
                request.data['acq_date'] = datetime.datetime.strptime(data[6], '%m/%d/%Y').strftime('%Y-%m-%d')
                request.data['acq_time'] = data[7].split('.')[0]
                # request.data['csv_file'] = MEDIA_ROOT + 'locationCSVs/' + request.data['location_csv'].name
                dda = Location.objects.filter(district__district=data[1].rstrip().upper())
                if(len(dda)>=1):
                    request.data['dda'] = dda[0].pk

                ado = Ado.objects.get(village__village__icontains=data[3].rstrip().upper())
                if len(ado)>=1:
                    request.data['ado'] = ado[0].pk
                # print("dda", request.data['csv_file'])
                serializer = AddLocationSerializer(data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    count = count + 1;
            return Response({'status': 'success', 'count': count}, status=status.HTTP_201_CREATED)
        print("error", request.data.location_csv)
        return Response({'error': 'invalid'}, status=status.HTTP_400_BAD_REQUEST)

# Shows list of locations for specific ado for admin
class LocationViewSetAdoForAdmin(viewsets.ReadOnlyModelViewSet):
    model = Location
    serializer_class = LocationSerializer
    permission_classes = (IsAuthenticated, )
    pagination_class = StandardResultsSetPagination
    # Making endpoint searchable
    # filter_backends = (filters.SearchFilter, )
    # search_fields = ('centre__location', 'course__title', 'first_name', 'last_name', '=contact_number', 'user__email')

    def get_queryset(self):
        try:
            user = Ado.objects.get(id=self.kwargs['pk'])
        except Ado.DoesNotExist:
            raise Http404
        stat = self.kwargs['status']
        locations = []
        if stat == 'pending':
            locations = Location.objects.filter(status=stat, ado=user).order_by('village_name', 'block_name', 'district')
        elif stat == 'completed':
            locations = Location.objects.filter(status__in=['completed', 'ongoing'], ado=user).order_by('village_name', 'block_name', 'district')
        return locations

# Shows list of locations for specific dda for admin
class LocationViewSetDdaForAdmin(viewsets.ReadOnlyModelViewSet):
    model = Location
    serializer_class = LocationSerializer
    permission_classes = (IsAuthenticated, )
    pagination_class = StandardResultsSetPagination
    # Making endpoint searchable
    # filter_backends = (filters.SearchFilter, )
    # search_fields = ('centre__location', 'course__title', 'first_name', 'last_name', '=contact_number', 'user__email')

    def get_queryset(self):
        try:
            user = Dda.objects.get(id=self.kwargs['pk'])
        except Dda.DoesNotExist:
            raise Http404
        stat = self.kwargs['status']
        locations = []
        if stat == 'unassigned':
            locations = Location.objects.filter(status='pending', dda=user ,ado=None).order_by('village_name', 'block_name', 'district')
        elif stat == 'assigned':
            locations = Location.objects.filter(status='pending', dda=user).exclude(ado=None).order_by('village_name', 'block_name', 'district')
        elif stat == 'ongoing':
            locations = Location.objects.filter(status=stat, dda=user).order_by('village_name', 'block_name', 'district')
        elif stat == 'completed':
            locations = Location.objects.filter(status=stat, dda=user).order_by('village_name', 'block_name', 'district')
        return locations

# Location district wise
# Shows list of Ados
class LocationDistrictWiseViewSet(viewsets.ReadOnlyModelViewSet):
    model = Location
    serializer_class = LocationSerializer
    permission_classes = ( )
    pagination_class = StandardResultsSetPagination
    # Making endpoint searchable
    # filter_backends = (filters.SearchFilter, )
    # search_fields = ('centre__location', 'course__title', 'first_name', 'last_name', '=contact_number', 'user__email')

    def get_queryset(self):
        try:
            district = District.objects.get(id=self.kwargs['pk'])
        except District.DoesNotExist:
            raise Http404
        stat = self.kwargs['status']
        locations = []
        if stat == 'unassigned':
            locations = Location.objects.filter(status='pending', ado=None, district=district.district).order_by('village_name', 'block_name', 'district')
        elif stat == 'assigned':
            locations = Location.objects.filter(status='pending', district=district.district).exclude(ado=None).order_by('village_name', 'block_name', 'district')
        elif stat == 'ongoing':
            locations = Location.objects.filter(status=stat, district=district.district).order_by('village_name', 'block_name', 'district')
        elif stat == 'completed':
            locations = Location.objects.filter(status=stat, district=district.district).order_by('village_name', 'block_name', 'district')
        return locations

# Add images with ado reports
class ImageView(APIView):

    def get(self, request, format = None):
        images = Image.objects.all().order_by('-pk')
        serializer = ImageSerializer(images, many=True)
        return Response(serializer.data)

    def post(self, request, format = None):
        print(request.data)
        serializer = AddImageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# ADO reports Views
class AddAdoReport(APIView):

    def post(self, request, format = None):
        serializer = AddAdoReportSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            print(request.data)
            location = Location.objects.get(pk=request.data['location'])
            location.status = 'ongoing'
            location.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AdoReportDetail(APIView):
    # Helper function
    def get_object(self, pk):
        try:
            return AdoReport.objects.get(pk=pk)
        except AdoReport.DoesNotExist:
            raise Http404

    def get(self, request, pk, format = None):
        try:
            report = AdoReport.objects.get(location=pk)
        except AdoReport.DoesNotExist:
            raise Http404
        serializer = AdoReportSerializer(report, context={'request': request})        
        return Response(serializer.data)

    def put(self, request, pk, format = None):
        report = self.get_object(pk)
        serializer = AddAdoReportSerializer(report, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format = None):
        report = self.get_object(pk)
        report.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

# Trigger sms notification for locations
class TriggerSMS(APIView):

    def get(self, request, status, format = None):
        locations = Location.objects.filter(status=status)
        for location in locations:
            if location.dda:
                conn = http.client.HTTPSConnection("api.msg91.com")
                conn.request(
                    "GET",
                    "/api/sendhttp.php?mobiles=" + location.dda.number + "&authkey=296120Ad3QCLsOkZI5d8d6bd5&route=4" +
                    "&sender=GNSCOA&message=You have some pending locations Please check the app for more details" + "&country=91"
                )
                res = conn.getresponse()
            if location.ado:
                conn = http.client.HTTPSConnection("api.msg91.com")
                conn.request(
                    "GET",
                    "/api/sendhttp.php?mobiles=" + location.ado.number + "&authkey=296120Ad3QCLsOkZI5d8d6bd5&route=4" +
                    "&sender=GNSCOA&message=You have some pending locations Please check the app for more details" + "&country=91"
                )
                res = conn.getresponse()
        return Response({'status':200, 'result':'SMS sent successfully'})

# BULK ADD VILLAGE
class BulkAddVillage(APIView):

    def post(self, request, format = None):
            directory = MEDIA_ROOT + '/villageCSV/'
            if not os.path.exists(directory):
                os.makedirs(directory)

            villages = []
            count = 0
            if 'village_csv' in request.data:
                if not request.data['village_csv'].name.endswith('.csv'):
                    return Response({'village_csv': ['Please upload a valid document ending with .csv']},
                        status = HTTP_400_BAD_REQUEST)
                fs = FileSystemStorage()
                fs.save(directory + request.data['village_csv'].name, request.data['village_csv'])
                csvFile = open(directory + request.data['village_csv'].name, 'r')
                for line in csvFile.readlines():
                    villages.append(line)
                
                villages.pop(0);

                for data in villages:
                    data = data.split(',')
                    request.data['village']  = data[0]
                    request.data['village_code'] = data[1]
                    district = District.objects.filter(district_code=data[2].strip()) | District.objects.filter(district__icontains=data[2].upper().strip())
                    if len(district) == 1:
                        request.data['district'] = district[0].id
                    serializer = VillageSerializer(data=request.data)
                    if serializer.is_valid():
                        serializer.save()
                        count = count + 1;
                return Response({'status': 'success', 'count': count}, status=status.HTTP_201_CREATED)
            return Response({'error': 'invalid'}, status=status.HTTP_400_BAD_REQUEST)

# BULK ADD District
class BulkAddDistrict(APIView):

    def post(self, request, format = None):
            directory = MEDIA_ROOT + '/districtCSV/'
            if not os.path.exists(directory):
                os.makedirs(directory)

            districts = []
            count = 0
            if 'district_csv' in request.data:
                if not request.data['district_csv'].name.endswith('.csv'):
                    return Response({'district_csv': ['Please upload a valid document ending with .csv']},
                        status = HTTP_400_BAD_REQUEST)
                fs = FileSystemStorage()
                fs.save(directory + request.data['district_csv'].name, request.data['district_csv'])
                csvFile = open(directory + request.data['district_csv'].name, 'r')
                for line in csvFile.readlines():
                    districts.append(line)
                
                districts.pop(0);

                for data in districts:
                    data = data.split(',')
                    request.data['district']  = data[0]
                    request.data['district_code'] = data[1]
                    serializer = DistrictSerializer(data=request.data)
                    if serializer.is_valid():
                        serializer.save()
                        count = count + 1;
                return Response({'status': 'success', 'count': count}, status=status.HTTP_201_CREATED)
            return Response({'error': 'invalid'}, status=status.HTTP_400_BAD_REQUEST)

# BULK ADD DDA
class BulkAddDda(APIView):

    def post(self, request, format = None):
            directory = MEDIA_ROOT + '/ddaCSVs/'
            if not os.path.exists(directory):
                os.makedirs(directory)

            ddas = []
            count = 0
            if 'dda_csv' in request.data:
                if not request.data['dda_csv'].name.endswith('.csv'):
                    return Response({'dda_csv': ['Please upload a valid document ending with .csv']},
                        status = HTTP_400_BAD_REQUEST)
                fs = FileSystemStorage()
                fs.save(directory + request.data['dda_csv'].name, request.data['dda_csv'])
                csvFile = open(directory + request.data['dda_csv'].name, 'r')
                for line in csvFile.readlines():
                    ddas.append(line)
                
                ddas.pop(0);
                # Create a unique filename
                filename = str(uuid.uuid4()) + '.csv'
                csvFile = open(directory + filename, 'w')
                csvFile.write('Name,Username,Password\n')
                for data in ddas:
                    data = data.split(',')
                    request.data['name']  = data[0]
                    request.data['number'] = data[1]
                    request.data['email'] = data[2]
                    district = None
                    try:
                        district = District.objects.get(district=data[3].upper().strip())
                    except District.DoesNotExist:
                        pass

                    try:
                        district = District.objects.get(district_code=data[3].strip())
                    except District.DoesNotExist:
                        pass

                    if district != None:
                        request.data['district'] = district.id

                    existing = [user['username'] for user in User.objects.values('username')]
                    username = data[4].strip()
                    if username in existing:
                        # Provide random username if username 
                        # of the form Ado<pk> already exists
                        username = uuid.uuid4().hex[:8]
                        while username in existing:
                            username = uuid.uuid4().hex[:8]

                    # Create user of type student
                    user = User.objects.create(username=username, type_of_user="dda")
                    password = uuid.uuid4().hex[:8].lower()
                    user.set_password(password)
                    user.save()
                    request.data['auth_user'] = user.pk
                    serializer = AddDdaSerializer(data=request.data)
                    if serializer.is_valid():
                        serializer.save()
                        csvFile.write(data[0] + ',' + username + ',' + password + '\n')
                        count = count + 1;
                    else:
                        print(serializer.errors)
                csvFile.close()
                absolute_path = DOMAIN + 'media/ddaCSVs/'+ filename
                return Response({'status': 'success', 'count': count, 'csvFile':absolute_path}, status=status.HTTP_201_CREATED)
            return Response({'error': 'invalid'}, status=status.HTTP_400_BAD_REQUEST)

# BULK ADD ADO
class BulkAddAdo(APIView):

    def post(self, request, format = None):
            directory = MEDIA_ROOT + '/adoCSVs/'
            if not os.path.exists(directory):
                os.makedirs(directory)

            ados = []
            count = 0
            if 'ado_csv' in request.data:
                if not request.data['ado_csv'].name.endswith('.csv'):
                    return Response({'ado_csv': ['Please upload a valid document ending with .csv']},
                        status = HTTP_400_BAD_REQUEST)
                fs = FileSystemStorage()
                fs.save(directory + request.data['ado_csv'].name, request.data['ado_csv'])
                csvFile = open(directory + request.data['ado_csv'].name, 'r')
                for line in csvFile.readlines():
                    ados.append(line)
                
                ados.pop(0);
                # Create a unique filename
                filename = str(uuid.uuid4()) + '.csv'
                csvFile = open(directory + filename, 'w')
                csvFile.write('Name,Username,Password\n')
                for data in ados:
                    data = data.split(',')
                    request.data['name']  = data[0]
                    request.data['number'] = data[2]
                    request.data['email'] = data[3]

                    try:
                        dda = Dda.objects.get(district__district_code=data[4].strip())
                    except Dda.DoesNotExist:
                        pass
                    if dda:
                        request.data['dda'] = dda.id
                    existing = [user['username'] for user in User.objects.values('username')]
                    username = data[5].rstrip()
                    if(len(username)<1):
                        username = uuid.uuid4().hex[:8]
                    if username in existing:
                        # Provide random username if username 
                        # of the form Ado<pk> already exists
                        username = uuid.uuid4().hex[:8]
                        while username in existing:
                            username = uuid.uuid4().hex[:8]

                    # Create user of type ado
                    user = User.objects.create(username=username, type_of_user="ado")
                    password = uuid.uuid4().hex[:8].lower()
                    user.set_password(password)
                    user.save()
                    request.data['auth_user'] = user.pk
                    serializer = AddAdoSerializer(data=request.data)
                    if serializer.is_valid():
                        serializer.save()
                        try:
                            ado = Ado.objects.get(id = serializer.data['id'])
                        except Ado.DoesNotExist:
                            ado = None
                        if ado:
                            arr = []
                            villages = data[1].split('|')
                            for village in villages:
                                print(data[0], village)
                                if len(village.split('(')) > 1:
                                    obj = Village.objects.filter(village__icontains=village.upper().strip()) | Village.objects.filter(village__icontains=village.split('(')[1].upper().strip(), district__district_code=data[4])
                                else:
                                    obj = Village.objects.filter(village__icontains=village.upper().strip())
                                print(obj)
                                if(len(obj) == 1):
                                    arr.append(int(obj[0].id))
                            print(arr)
                            ado.village.set(arr)
                            ado.save()
                        csvFile.write(data[0] + ',' + username + ',' + password + '\n')
                        count = count + 1;
                    else:
                        print(serializer.errors)
                csvFile.close()
                absolute_path = DOMAIN + 'media/adoCSVs/'+ filename
                return Response({'status': 'success', 'count': count, 'csvFile':absolute_path}, status=status.HTTP_201_CREATED)
            return Response({'error': 'invalid'}, status=status.HTTP_400_BAD_REQUEST)
