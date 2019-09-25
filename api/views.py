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
from agriculture.settings import MEDIA_ROOT
from django.core.files.storage import FileSystemStorage
import os
from django.db.models import Q

class UserList(APIView):
    permission_classes = []
    def get(self, request, format = None):
        users = User.objects.all().order_by('-pk')
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

    def post(self, request, format = None):
        data = request.data
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

# VIEWS FOR DISTRICT
class DistrictList(APIView):
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
    # filter_backends = (filters.SearchFilter, )
    # search_fields = ('centre__location', 'course__title', 'first_name', 'last_name', '=contact_number', 'user__email')

    def get_queryset(self):
        villages = Village.objects.all().order_by('-pk')
        return villages

class VillageList(APIView):
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
            locations = Location.objects.filter(status='pending', ado=None).order_by('district', 'block_name', 'village_name')
        elif stat == 'assigned':
            locations = Location.objects.filter(status='pending').exclude(ado=None).order_by('district', 'block_name', 'village_name')
        else:
            locations = Location.objects.filter(status=stat).order_by('district', 'block_name', 'village_name')
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
            locations = Location.objects.filter(status=stat, ado=user).order_by('district', 'block_name', 'village_name')
        elif stat == 'completed':
            locations = Location.objects.filter(status__in=['completed', 'ongoing'], ado=user).order_by('district', 'block_name', 'village_name')
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
            locations = Location.objects.filter(status='pending', dda=user ,ado=None).order_by('district', 'block_name', 'village_name')
        elif stat == 'assigned':
            locations = Location.objects.filter(status='pending', dda=user).exclude(ado=None).order_by('district', 'block_name', 'village_name')
        elif stat == 'ongoing':
            locations = Location.objects.filter(status=stat, dda=user).order_by('district', 'block_name', 'village_name')
        elif stat == 'completed':
            locations = Location.objects.filter(status=stat, dda=user).order_by('district', 'block_name', 'village_name')
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
        ados = Ado.objects.filter(dda = dda).order_by('-pk')
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
                request.data['acq_date'] = datetime.datetime.strptime(data[6], '%d/%m/%Y').strftime('%Y-%m-%d')
                request.data['acq_time'] = data[7].split('.')[0]
                # request.data['csv_file'] = MEDIA_ROOT + 'locationCSVs/' + request.data['location_csv'].name
                try:
                    dda = Dda.objects.get(district__district=data[1].upper())
                    request.data['dda'] = dda.pk
                except Dda.DoesNotExist:
                    if 'dda' in request.data:
                        del request.data['dda']

                try:
                    ado = Ado.objects.get(village__village=data[3].upper())
                    request.data['ado'] = ado.pk
                except Ado.DoesNotExist:
                    if 'ado' in request.data:
                        del request.data['ado']
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
            locations = Location.objects.filter(status=stat, ado=user).order_by('district', 'block_name', 'village_name')
        elif stat == 'completed':
            locations = Location.objects.filter(status__in=['completed', 'ongoing'], ado=user).order_by('district', 'block_name', 'village_name')
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
            locations = Location.objects.filter(status='pending', dda=user ,ado=None).order_by('district', 'block_name', 'village_name')
        elif stat == 'assigned':
            locations = Location.objects.filter(status='pending', dda=user).exclude(ado=None).order_by('district', 'block_name', 'village_name')
        elif stat == 'ongoing':
            locations = Location.objects.filter(status=stat, dda=user).order_by('district', 'block_name', 'village_name')
        elif stat == 'completed':
            locations = Location.objects.filter(status=stat, dda=user).order_by('district', 'block_name', 'village_name')
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