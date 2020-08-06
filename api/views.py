from rest_framework import status,generics
from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import viewsets, filters
from .models import *
from .serializers import *
from .permissions import *
from .paginators import *
from django.core.mail import send_mail, EmailMessage
import datetime
from agriculture.settings import MEDIA_ROOT, DOMAIN, EMAIL_HOST_USER
from django.core.files.storage import FileSystemStorage
import os
from django.db.models import Q,Count
import http.client
import uuid
import xlrd
import logging
import pandas as pd
import csv
import shutil
from datetime import timedelta 
from io import BytesIO
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse
from django.template.loader import get_template
import xhtml2pdf.pisa as pisa
from easy_pdf.rendering import render_to_pdf

logger = logging.getLogger(__name__)

# Helper function to send email
def send_email(subject, content, recipient_list, path=None):
    email_from = EMAIL_HOST_USER
    mail = EmailMessage(subject, content, email_from, recipient_list)
    mail.content_subtype = 'html'
    if path:
        mail.attach_file(path)
    mail.send()

class CheckVersion(APIView):
    permission_classes = []
    def get(self,request,format = None):
        version = AppVersion.objects.latest('version')
        serializer = AppVersionSerializer(version)   
        return Response(serializer.data)    
           
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
        user.delete()
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
    filter_backends = (filters.SearchFilter, DjangoFilterBackend, )
    search_fields = ('village', 'village_code', 'district__district',)
    filterset_fields = ['district']

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
        serializer = VillageSerializer(village)         
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

# DC Views
class DCList(APIView):
    permission_classes = []
    def get(self, request, format = None):
        dcs = DC.objects.all().order_by('name')
        serializer = DCSerializer(dcs, many=True)
        return Response(serializer.data)

    def post(self, request, format = None):
        serializer = DCSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DCDetail(APIView):
    def get_object(self, pk):
        try:
            return DC.objects.get(pk=pk)
        except DC.DoesNotExist:
            raise Http404

    def get(self, request, pk, format = None):
        dc = self.get_object(pk)
        serializer = DCSerializer(dc)         
        return Response(serializer.data)

    def put(self, request, pk, format = None):
        dc = self.get_object(pk)
        serializer = DCSerializer(dc, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format = None):
        dc = self.get_object(pk)
        dc.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

# SP VIEWS
class SPList(APIView):
    permission_classes = []
    def get(self, request, format = None):
        sps = SP.objects.all().order_by('name')
        serializer = SPSerializer(sps, many=True)
        return Response(serializer.data)

    def post(self, request, format = None):
        serializer = SPSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# SP VIEWS
class SPDetail(APIView):
    def get_object(self, pk):
        try:
            return SP.objects.get(pk=pk)
        except SP.DoesNotExist:
            raise Http404

    def get(self, request, pk, format = None):
        sp = self.get_object(pk)
        serializer = SPSerializer(sp)         
        return Response(serializer.data)

    def put(self, request, pk, format = None):
        sp = self.get_object(pk)
        serializer = SPSerializer(sp, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format = None):
        sp = self.get_object(pk)
        sp.delete()
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
    filter_backends = (filters.SearchFilter, )
    search_fields = ('name', 'number', 'email', 'district__district',)

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
    filter_backends = (filters.SearchFilter, DjangoFilterBackend, )
    search_fields = ( 'name', 'number', 'email', 'dda__district__district', 'village__village',)
    filterset_fields = [ 'dda' ]
    def get_queryset(self):
        ados = Ado.objects.all().order_by('dda__district__district', 'name')
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
    
class LocationDatewise(viewsets.ReadOnlyModelViewSet):
    model = Location
    serializer_class =LocationDateWiseSerializer
    pagination_class = StandardResultsSetPagination
    
    # Making endpoint searchable
    filter_backends = (filters.SearchFilter,) #, DjangoFilterBackend,
    filterset_fields = [ 'dda', 'ado', 'status',]
    search_fields = ('state', 'block_name', 'village_name', 'dda__name', 'ado__name', 'status', 'district',)

    def get_queryset(self):
        status = self.kwargs['status']    
        
        if status == 'unassigned':
            locations = Location.objects.filter(status='pending', ado=None).order_by('-acq_date', 'district', 'block_name', 'village_name')
        elif status == 'assigned':
            locations = Location.objects.filter(status='pending').exclude(ado=None).order_by('-acq_date', 'district', 'block_name', 'village_name')
        else:
            locations = Location.objects.filter(status=status).order_by('-acq_date', 'district', 'block_name', 'village_name')
            

        dates =[]
        lis = []
        for location in locations:
            date= location.acq_date.strftime('%Y-%m-%d')
            if date not in dates:
                dates.append(date)

        for date in dates:
            lildict=dict()
            data = locations.filter(acq_date=date)
            
            lildict['date']=date
            lildict['locations']= data
            
            lis.append(lildict)


        return lis


  
  
    
# Shows list of locations unassigned, assigned, ongoing, pending for admin
class LocationViewSet(viewsets.ReadOnlyModelViewSet):
    model = Location
    serializer_class = LocationSerializer_location
    # permission_classes = (permissions.IsAuthenticated, IsSuperadmin, )
    pagination_class = StandardResultsSetPagination
    # Making endpoint searchable
    filter_backends = (filters.SearchFilter, DjangoFilterBackend, )
    filterset_fields = [ 'dda', 'ado', 'status']
    search_fields = ('state', 'block_name', 'village_name', 'dda__name', 'ado__name', 'status', 'district',)

    def get_queryset(self):
        stat = self.kwargs['status']
        if stat == 'unassigned':
            locations = Location.objects.filter(status='pending', ado=None).order_by('-acq_date', 'district', 'block_name', 'village_name')
        elif stat == 'assigned':
            locations = Location.objects.filter(status='pending').exclude(ado=None).order_by('-acq_date', 'district', 'block_name', 'village_name')
        else:
            locations = Location.objects.filter(status=stat).order_by('-acq_date', 'district', 'block_name', 'village_name')
        return locations

# Shows list of locations for specific ado logged in
class LocationViewSetAdo(viewsets.ReadOnlyModelViewSet):
    model = Location
    serializer_class = LocationSerializer
    permission_classes = (IsAuthenticated, )
    pagination_class = StandardResultsSetPagination
    # Making endpoint searchable
    filter_backends = (filters.SearchFilter, )
    search_fields = ('state', 'block_name', 'village_name', 'ado__name', 'status', 'district',)

    def get_queryset(self):
        try:
            user = Ado.objects.get(auth_user=self.request.user.pk)
        except Ado.DoesNotExist:
            raise Http404
        stat = self.kwargs['status']
        locations = []
        if stat == 'pending':
            locations = Location.objects.filter(status=stat, ado=user).order_by('-acq_date', 'district', 'block_name', 'village_name')
        elif stat == 'completed':
            locations = Location.objects.filter(status__in=['completed', 'ongoing'], ado=user).order_by('-acq_date', 'district', 'block_name', 'village_name')
        return locations

# Shows list of locations for specific dda
class LocationViewSetDda(viewsets.ReadOnlyModelViewSet):
    model = Location
    serializer_class = LocationSerializer
    permission_classes = (IsAuthenticated, )
    pagination_class = StandardResultsSetPagination
    # Making endpoint searchable
    filter_backends = (filters.SearchFilter, DjangoFilterBackend, )
    filterset_fields = [ 'ado', 'status']
    search_fields = ('state', 'block_name', 'village_name', 'ado__name', 'status', 'district',)

    def get_queryset(self):
        try:
            user = Dda.objects.get(auth_user=self.request.user.pk)
        except Dda.DoesNotExist:
            raise Http404
        stat = self.kwargs['status']
        locations = []
        if stat == 'unassigned':
            locations = Location.objects.filter(status='pending', dda=user ,ado=None).order_by('-acq_date', 'district', 'block_name', 'village_name')
        elif stat == 'assigned':
            locations = Location.objects.filter(status='pending', dda=user).exclude(ado=None).order_by('-acq_date', 'district', 'block_name', 'village_name')
        else:
            locations = Location.objects.filter(status=stat, dda=user).order_by('-acq_date', 'district', 'block_name', 'village_name')
        return locations

# Shows list of ado for specific dda logged in
class AdoViewSet(viewsets.ReadOnlyModelViewSet):
    model = Ado
    serializer_class = AdoSerializer
    permission_classes = (IsAuthenticated, )
    pagination_class = StandardResultsSetPagination
    # Making endpoint searchable
    filter_backends = (filters.SearchFilter, DjangoFilterBackend, )
    filterset_fields = [ 'dda']
    search_fields = ('dda__district__district', 'village__village', 'number', 'name', 'email', 'dda__name',)

    def get_queryset(self):
        try:
            dda = Dda.objects.get(auth_user=self.request.user.pk)
        except Dda.DoesNotExist:
            raise Http404
        ados = Ado.objects.filter(dda = dda).order_by('name')
        return ados

# Upload CSV
class LocationList(APIView):
    permission_classes = []

    def get(self, request, format = None):
        locations = []
        start = request.GET.get('start',None)
        end = request.GET.get('end', None)
        district = request.GET.get('district', None)
        status = request.GET.get('status', None)
        dda = request.GET.get('dda', None)
        if dda:
            if start and end:
                start = datetime.datetime.strptime(start, '%Y-%m-%d').strftime('%Y-%m-%d')
                end = datetime.datetime.strptime(end, '%Y-%m-%d').strftime('%Y-%m-%d')
                if district:
                    if status:
                        locations = Location.objects.filter(district=district.upper(), status=status, acq_date__range=[start,end], dda__pk=int(dda)).order_by('-pk')
                    else:
                        locations = Location.objects.filter(district=district.upper(), acq_date__range=[start,end], dda__pk=int(dda)).order_by('-pk')
                else:
                    if status:
                        locations = Location.objects.filter(status=status, acq_date__range=[start,end], dda__pk=int(dda)).order_by('-pk')
                    else:
                        locations = Location.objects.filter(acq_date__range=[start,end], dda__pk=int(dda)).order_by('-pk')
            else:
                if district:
                    if status:
                        locations = Location.objects.filter(district=district.upper(), status=status, dda__pk=int(dda)).order_by('-pk')
                    else:
                        locations = Location.objects.filter(district=district.upper(), dda__pk=int(dda)).order_by('-pk')
                else:
                    if status:
                        locations = Location.objects.filter(status=status, dda__pk=int(dda)).order_by('-pk')
                    else:
                        locations = Location.objects.filter(dda__pk=int(dda)).order_by('-pk')
        else:
            if start and end:
                start = datetime.datetime.strptime(start, '%Y-%m-%d').strftime('%Y-%m-%d')
                end = datetime.datetime.strptime(end, '%Y-%m-%d').strftime('%Y-%m-%d')
                if district:
                    if status:
                        locations = Location.objects.filter(district=district.upper(), status=status, acq_date__range=[start,end]).order_by('-pk')
                    else:
                        locations = Location.objects.filter(district=district.upper(), acq_date__range=[start,end]).order_by('-pk')
                else:
                    if status:
                        locations = Location.objects.filter(status=status, acq_date__range=[start,end]).order_by('-pk')
                    else:
                        locations = Location.objects.filter(acq_date__range=[start,end]).order_by('-pk')
            else:
                if district:
                    if status:
                        locations = Location.objects.filter(district=district.upper(), status=status).order_by('-pk')
                    else:
                        locations = Location.objects.filter(district=district.upper()).order_by('-pk')
                else:
                    if status:
                        locations = Location.objects.filter(status=status).order_by('-pk')
                    else:
                        locations = Location.objects.all().order_by('-pk')
        serializer = MapSerializer(locations, many=True, context={'request':request})
        return Response(serializer.data)

    def post(self, request, format = None):
        directory = MEDIA_ROOT + '/locationCSVs/'
        if not os.path.exists(directory):
            os.makedirs(directory)

        locations = []
        count = 0
        if 'location_csv' in request.data:
            if not request.data['location_csv'].name.endswith('.csv'):
                return Response({'location_csv': ['Please upload a valid document ending with .xlsx or xls']},
                    status = HTTP_400_BAD_REQUEST)
            fs = FileSystemStorage()
            fs.save(directory + request.data['location_csv'].name, request.data['location_csv'])
            # file = pd.read_excel(directory + request.data['location_csv'].name, sheetname="Sheet1")

            csvFile = open(directory + request.data['location_csv'].name, 'r')
            for line in csvFile.readlines():
                locations.append(line)
            
            locations.pop(0);
            MAILING_LIST = {}
            directory = MEDIA_ROOT + '/mailing/'
            if not os.path.exists(directory):
                os.makedirs(directory)
            for data in locations:
                index = locations.index(data)
                data = data.split(',')
                request.data['state']  = data[0]
                request.data['district'] = data[1].upper()
                request.data['block_name'] = data[2].upper()
                request.data['village_name'] = data[3].upper()
                request.data['longitude'] = data[4]
                request.data['latitude'] = data[5]
                request.data['acq_date'] = datetime.datetime.strptime(data[6], '%m/%d/%Y').strftime('%Y-%m-%d')
                request.data['acq_time'] = data[7].split('.')[0]
                # request.data['csv_file'] = MEDIA_ROOT + 'locationCSVs/' + request.data['location_csv'].name
                dda = []
                dda = Dda.objects.filter(district__district=data[1].rstrip().upper())
                if(len(dda)==1):
                    request.data['dda'] = dda[0].pk
                else:
                    request.data['dda'] = None
                ado = []
                ado = Ado.objects.filter(village__village=data[3].rstrip().upper(), dda__district__district=data[1].rstrip().upper())
                if len(ado)==1:
                    request.data['ado'] = ado[0].pk
                else:
                    request.data['ado'] = None
                # print("dda", request.data['csv_file'])
                serializer = AddLocationSerializer(data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    count = count + 1;
            return Response({'status': 'success', 'count': count}, status=status.HTTP_201_CREATED)
        return Response({'error': 'invalid'}, status=status.HTTP_400_BAD_REQUEST)

# helper function
def floatHourToTime(fh):
    h, r = divmod(fh, 1)
    m, r = divmod(r*60, 1)
    return (
        int(h),
        int(m),
        int(r*60),
    )

# Upload CSV for FIR
class MailView(APIView):
    permission_classes = []

    def post(self, request, format = None):
        directory = MEDIA_ROOT + '/FIR/'
        if not os.path.exists(directory):
            os.makedirs(directory)

        locations = []
        count = 0
        if 'location_csv' in request.data:
            if not request.data['location_csv'].name.endswith('.xlsx') and not request.data['location_csv'].name.endswith('.xls'):
                return Response({'location_csv': ['Please upload a valid document ending with .xlsx or xls']},
                    status = status.HTTP_400_BAD_REQUEST)
            fs = FileSystemStorage()
            fs.save(directory + request.data['location_csv'].name, request.data['location_csv'])
            wb = xlrd.open_workbook(directory + request.data['location_csv'].name) 
            sheet = wb.sheet_by_index(0) 
            rows = sheet.nrows
            locations = []
            for index in range(rows):
                locations.append(sheet.row_values(index))

            locations.pop(0);
            MAILING_LIST = {}
            directory = MEDIA_ROOT + '/mailing/'
            if not os.path.exists(directory):
                os.makedirs(directory)
            mail_data = {}
            for data in locations:
                del data[0]
                owners = str(data[9]).rstrip()
                data[9] = owners
                # Create mail data district wise
                count += 1
                district = data[0].rstrip().upper()
                dt = datetime.datetime.fromordinal(datetime.datetime(1900, 1, 1).toordinal() + int(data[5]) - 2)
                hour, minute, second = floatHourToTime(data[5] % 1)
                dt = dt.replace(hour=hour, minute=minute, second=second)
                data[5] = str(dt).split(' ')[0]
                if str(district) in mail_data:
                    mail_data[str(district)].append(data)
                else:
                    mail_data[str(district)] = []
                    mail_data[str(district)].append(data)
            index = -1
            for mail in mail_data:
                logger.info("The value of var is %s", mail)
                index += 1
                new_table = {}
                owners = []
                officers_mail_id = DC.objects.filter(district__district = str(mail).upper()).values('email')
                email = []
                for e in officers_mail_id:
                    email.append(e['email'])
                for row in mail_data[str(mail)]:
                    owners.append(row[9])
                    ind = mail_data[str(mail)].index(row)
                    del mail_data[str(mail)][ind][9]
                table = mail_data[str(mail)]
                new_table = []
                for row in table:
                    obj = {
                        "data": row,
                        "owners": owners[table.index(row)]
                    }
                    new_table.append(obj)
                district_mail_data = {
                    'data': new_table,
                    'date': str(datetime.date.today().strftime("%d / %m / %Y")),
                    'sno': '00' + str(index + 1)
                }
                content = render_to_pdf('mail_dc.html',district_mail_data, encoding = 'utf-8')
                with open(directory + str(mail) + '.pdf', 'wb') as f:
                    f.write(content)

                # Send mail to DC
                subject = "Stubble Burning Reporting"
                content = """
                    Respected Sir/Madam,<br><br>
                    Please find the attachment(s) containing data of AFL detected by HARSAC and list of owners and details of their Land.<br><br>
                    <b>Thank you</b><br>
                    <b>Department of Agriculture and Farmers Welfare, Haryana</b><br>
                """
                # email += ['akash.akashdepsharma@gmail.com']
                logger.info("The value of var is ", email)
                send_email(subject, content, email, directory + str(mail) + '.pdf')   # Send mail
            return Response({'status': 'success', 'count': index+1}, status=status.HTTP_201_CREATED)
        return Response({'error': 'invalid'}, status=status.HTTP_400_BAD_REQUEST)

# Shows list of locations for specific ado for admin
class LocationViewSetAdoForAdmin(viewsets.ReadOnlyModelViewSet):
    model = Location
    serializer_class = LocationSerializer
    permission_classes = (IsAuthenticated, )
    pagination_class = StandardResultsSetPagination
    # Making endpoint searchable
    filter_backends = (filters.SearchFilter, DjangoFilterBackend, )
    filterset_fields = [ 'dda', 'ado', 'status']
    search_fields = ('state', 'block_name', 'village_name', 'ado__name', 'status', 'district',)

    def get_queryset(self):
        try:
            user = Ado.objects.get(id=self.kwargs['pk'])
        except Ado.DoesNotExist:
            raise Http404
        stat = self.kwargs['status']
        locations = []
        if stat == 'pending':
            locations = Location.objects.filter(status=stat, ado=user).order_by('-acq_date', 'district', 'block_name', 'village_name')
        elif stat == 'completed':
            locations = Location.objects.filter(status__in=['completed', 'ongoing'], ado=user).order_by('-acq_date', 'district', 'block_name', 'village_name')
        return locations

# Shows list of locations for specific dda for admin
class LocationViewSetDdaForAdmin(viewsets.ReadOnlyModelViewSet):
    model = Location
    serializer_class = LocationSerializer
    permission_classes = (IsAuthenticated, )
    pagination_class = StandardResultsSetPagination
    # Making endpoint searchable
    filter_backends = (filters.SearchFilter, DjangoFilterBackend, )
    filterset_fields = [ 'dda', 'ado', 'status']
    search_fields = ('state', 'block_name', 'village_name', 'ado__name', 'status', 'district',)

    def get_queryset(self):
        try:
            user = Dda.objects.get(id=self.kwargs['pk'])
        except Dda.DoesNotExist:
            raise Http404
        stat = self.kwargs['status']
        locations = []
        if stat == 'unassigned':
            locations = Location.objects.filter(status='pending', dda=user ,ado=None).order_by('-acq_date', 'district', 'block_name', 'village_name')
        elif stat == 'assigned':
            locations = Location.objects.filter(status='pending', dda=user).exclude(ado=None).order_by('-acq_date', 'district', 'block_name', 'village_name')
        elif stat == 'ongoing':
            locations = Location.objects.filter(status=stat, dda=user).order_by('-acq_date', 'district', 'block_name', 'village_name')
        elif stat == 'completed':
            locations = Location.objects.filter(status=stat, dda=user).order_by('-acq_date', 'district', 'block_name', 'village_name')
        return locations

# Location district wise
class LocationDistrictWiseViewSet(viewsets.ReadOnlyModelViewSet):
    model = Location
    serializer_class = LocationSerializer
    permission_classes = ( )
    pagination_class = StandardResultsSetPagination
    # Making endpoint searchable
    filter_backends = (filters.SearchFilter, )
    search_fields = ('state', 'block_name', 'village_name', 'ado__name', 'status', 'district',)

    def get_queryset(self):
        try:
            district = District.objects.get(id=self.kwargs['pk'])
        except District.DoesNotExist:
            raise Http404
        stat = self.kwargs['status']
        locations = []
        if stat == 'unassigned':
            locations = Location.objects.filter(status='pending', ado=None, district=district.district).order_by('-acq_date', 'district', 'block_name', 'village_name')
        elif stat == 'assigned':
            locations = Location.objects.filter(status='pending', district=district.district).exclude(ado=None).order_by('-acq_date', 'district', 'block_name', 'village_name')
        elif stat == 'ongoing':
            locations = Location.objects.filter(status=stat, district=district.district).order_by('-acq_date', 'district', 'block_name', 'village_name')
        elif stat == 'completed':
            locations = Location.objects.filter(status=stat, district=district.district).order_by('-acq_date', 'district', 'block_name', 'village_name')
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

# List of villages district wise and filtered
class VillagesDistrictWiseViewSet(viewsets.ReadOnlyModelViewSet):

    model = Village
    serializer_class = VillageSerializer
    permission_classes = ( )
    pagination_class = StandardResultsSetPagination
    # Making endpoint searchable
    filter_backends = (filters.SearchFilter, )
    search_fields = ('village',)

    def get_queryset(self):
        try:
            district = District.objects.get(id=self.kwargs['pk'])
        except District.DoesNotExist:
            raise Http404
        villages = Village.objects.filter(district = district).order_by('village')
        return villages

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
                    village = []
                    village = data[0].split('(')
                    request.data['village']  = village[0].strip()
                    if len(village) > 1:
                        request.data['village_subcode'] = village[1].split(')')[0].strip()
                    else:
                        request.data['village_subcode'] = ''
                    request.data['village_code'] = data[1].strip()
                    district = District.objects.filter(district_code=data[2].rstrip())
                    if len(district) == 1:
                        request.data['district'] = district[0].id
                    else:
                        request.data['district'] = None
                    del village
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
                filename = 'filename.csv'
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
                filename = 'filename.csv'
                csvFile = open(directory + filename, 'w')
                csvFile.write('Name,Username,Password\n')
                for data in ados:
                    data = data.split(',')
                    request.data['name']  = data[0]
                    request.data['number'] = data[2]
                    request.data['email'] = data[3]
                    dda = None
                    try:
                        dda = Dda.objects.get(district__district_code=data[4].rstrip())
                    except Dda.DoesNotExist:
                        pass
                    if dda != None:
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
                            villages = []
                            villages = data[1].split('|')
                            for village in villages:
                                obj = []
                                if len(village.split('(')) > 1:
                                    obj = Village.objects.filter(village_subcode=village.split('(')[1].split(')')[0].upper().strip(), district__district_code=data[4].rstrip())
                                if len(obj) != 1:
                                    obj = Village.objects.filter(village=village.split('(')[0].upper().strip(), district__district_code=data[4].rstrip())
                                if(len(obj) == 1):
                                    arr.append(int(obj[0].id))
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


def ExportAdoPdf(request):
    dictV ={}
    AdoObjects = Ado.objects.all()
    dictV['objects'] = AdoObjects
    print('starting')
    content = render_to_pdf('AdoExportPdf.html',dictV)
    print('ending')
    return HttpResponse(content,content_type = "application/pdf")

class GetListAdo(APIView):

    def get(self, request, format = None):
        directory = MEDIA_ROOT + '/list/'
        if not os.path.exists(directory):
            os.makedirs(directory)
        filename = 'list.csv'
        csvFile = open(directory + filename, 'w')
        csvFile.write('Name,Email,Number, DDA, Villages\n')
        ados = Ado.objects.all().order_by('dda__district__district', 'name')
        for ado in ados:
            name = ado.name
            email = ado.email
            number = ado.number
            dda_name = ''
            district = ''
            if ado.dda:
                dda_name = ado.dda.name
                if ado.dda.district:
                    district = ado.dda.district.district
            villages = []
            dda = dda_name + '(' + district + ')'
            objects = ado.village.all()
            for village in objects:
                villages.append(village.village)
            villages = '|'.join(villages)
            csvFile.write(name + ',' + email + ',' + number + ',' + dda + ',' + villages + '\n')
        csvFile.close()
        absolute_path = DOMAIN + 'media/list/'+ filename
        return Response({'status': 200, 'csvFile':absolute_path})

class GeneratePasswordsForAdo(APIView):

    def get(self, request, format = None):
        directory = MEDIA_ROOT + '/password/'
        if not os.path.exists(directory):
            os.makedirs(directory)
        filename = 'password.csv'
        csvFile = open(directory + filename, 'w')
        csvFile.write('District, Name,Username,Password\n')
        ados = Ado.objects.all()
        for ado in ados:
            user = ado.auth_user
            password = uuid.uuid4().hex[:8].lower()
            user.set_password(password)
            user.save()
            district = ''
            if ado.dda:
                district = ado.dda.district.district
            csvFile.write(district + ',' + ado.name + ',' + ado.auth_user.username + ',' + password + '\n')
        csvFile.close()
        absolute_path = DOMAIN + 'media/password/'+ filename
        return Response({'status': 200, 'csvFile':absolute_path})

class GenerateLocationReport(APIView):
    def get(self, request, format = None):
        directory = MEDIA_ROOT + '/status_report/'
        if not os.path.exists(directory):
            os.makedirs(directory)
        # get params district and range
        start = datetime.datetime.strptime(request.GET.get('start'), '%Y-%m-%d').strftime('%Y-%m-%d')
        end = datetime.datetime.strptime(request.GET.get('end'), '%Y-%m-%d').strftime('%Y-%m-%d')
        district = request.GET.get('district', None)
        status = request.GET.get('status', None)
        village = request.GET.get('village',None)
        ado = request.GET.get('ado',None)
        locations = []
        if district:
            if status and village:
                locations = Location.objects.filter(  
                      created_on__range=[start, end],
                      district=district.upper(),
                      status=status,
                      village_name=village.upper()
                )   
                filename = 'location_report_' + status + '_' + district + '_' + village + '.csv'
            elif status and ado:
                locations = Location.objects.filter(
                     created_on__range=[start, end],
                     status=status,
                     district=district.upper(),
                     ado__name=ado.upper(),
                )
                filename = 'location_report_' + status + '_' + district + '_' + ado + '.csv' 
            elif status:  
                locations = Location.objects.filter(
                     created_on__range=[start, end],
                     district=district.upper(),
                     status=status 
                )
                filename = 'location_report_' + status + '_' + district + '.csv'
            elif village:
                locations = Location.objects.filter(
                     created_on__range=[start, end],
                     district = district.upper(),
                     village_name=village.upper(),   
                )
                filename = 'location_report_' + district + '_' + village + '.csv'  
            elif ado:
                locations = Location.objects.filter( 
                     created_on__range=[start, end],
                     district = district.upper(),
                     ado__name = ado.upper(),
                )
                filename = 'location_report_' + district + '_' +ado + '.csv'         
            else:
                locations = Location.objects.filter( 
                     created_on__range=[start, end],
                     district=district.upper(),
                )
                filename = 'location_report_' + district + '.csv'
        elif status and village:
            locations = Location.objects.filter(
                 created_on__range=[start, end],
                 status=status,
                 village_name=village_name.upper(),
             )
            filename = 'location_report_' + status + '_' + village + '.csv'
        elif status and ado:
            locations = Location.objects.filter(
                 created_on__range=[start, end],
                 status=status,
                 ado__name=ado.upper(),
            )
            filename = 'location_report_' + status + '_' + ado + '.csv'    
        elif status:
            locations = Location.objects.filter(
                 created_on__range=[start, end],
                 status=status
            )
            filename = 'location_report_' + status + '.csv'   
        else:
            locations = Location.objects.filter(
                 created_on__range=[start, end],
             )
            filename = 'location_report_all.csv' 
        if len(locations) == 0:
            return Response({'status' : 204})
        else:    
            csvFile = open(directory + filename, 'w')
            csvFile.write('Sno, District, Block, Village, Longitude, Latitude, Acquired Date, Dda Details, Ado Details\n')
            sno = 0
            for location in locations:
                sno += 1
                dis = ''
                if location.district:
                    dis = str(location.district)

                block = ''
                if location.block_name:
                    block = str(location.block_name)

                village = ''
                if location.village_name:
                    village = str(location.village_name)

                longitude = ''
                if location.longitude:
                    longitude = str(location.longitude)
            
                latitude = ''
                if location.latitude:
                    latitude = str(location.latitude)
            
                acq_date = ''
                if location.acq_date:
                    acq_date = str(location.acq_date) 
           
                dda = ''
                if location.dda:
                    dda = str(location.dda.name)

                ado = ''
                if location.ado:
                    ado = str(location.ado.name)   

                csvFile.write(
                    str(sno) + ',' 
                  + str(dis) + ',' 
                  + str(block) + ',' 
                  + str(village) + ','
                  + str(longitude) + ',' 
                  + str(latitude) + ',' 
                  + str(acq_date) + ',' 
                  + str(dda) + ','
                  + str(ado) + ','
                  + '\n') 
            csvFile.close()
            absolute_path = DOMAIN + 'media/status_report/'+ filename
            return Response({'status': 200,'csvFile':absolute_path})          

class GenerateReport(APIView):
     def get(self, request, format = None):
        directory = MEDIA_ROOT + '/reports/'
        if not os.path.exists(directory):
            os.makedirs(directory)
        # get params district and range
        start = datetime.datetime.strptime(request.GET.get('start'), '%Y-%m-%d').strftime('%Y-%m-%d')
        end = datetime.datetime.strptime(request.GET.get('end'), '%Y-%m-%d').strftime('%Y-%m-%d')
        district = request.GET.get('district', None)
        status = request.GET.get('status', None)
        village = request.GET.get('village',None)
        ado = request.GET.get('ado',None)
        reports = []
        if district:
             if status and village:  
                  reports = AdoReport.objects.filter(  
                      created_on_ado__range=[start, end],
                      location__district=district.upper(),
                      location__status=status,
                      village__village=village.upper()
                  )   
                  filename = 'report_' + status + '_' + district + '_' + village + '.csv'
             elif status and ado:
                 reports = AdoReport.objects.filter(
                     created_on_ado__range=[start, end],
                     location__status=status,
                     location__district=district.upper(),
                     location__ado__name=ado.upper(),
                 )
                 filename = 'report_' + status + '_' + district + '_' + ado + '.csv' 
             elif status:  
                 reports = AdoReport.objects.filter(
                     created_on_ado__range=[start, end],
                     location__district=district.upper(),
                     location__status=status 
                 )
                 filename = 'report_all_' + status + '_' + district + '.csv'
             elif village:
                 reports = AdoReport.objects.filter(
                     created_on_ado__range=[start, end],
                     location__district = district.upper(),
                     village__village=village.upper(),   
                 )
                 filename = 'report_all_' + district + '_' + village + '.csv'  
             elif ado:
                 reports = AdoReport.objects.filter( 
                     created_on_ado__range=[start, end],
                     location__district = district.upper(),
                     location__ado__name = ado.upper(),
                 )
                 filename = 'report_all_' + district + '_' +ado + '.csv'         
             else:
                 reports = AdoReport.objects.filter( 
                     created_on_ado__range=[start, end],
                     location__district=district.upper(),
                 )
                 filename = 'report_all_' + district + '.csv'
        elif status and village:
            reports = AdoReport.objects.filter(
                 created_on_ado__range=[start, end],
                 location__status=status,
                 village__village=village.upper(),
             )
            filename = 'report_' + status + '_' + village + '.csv'
        elif status and ado:
            reports = AdoReport.objects.filter(
                 created_on_ado__range=[start, end],
                 location__status=status,
                 location__ado__name=ado.upper(),
             )
            filename = 'report_' + status + '_' + ado + '.csv'    
        elif status:
            reports = AdoReport.objects.filter(
                 created_on_ado__range=[start, end],
                 location__status=status
             )
            filename = 'report_all_' + status + '.csv'   
        else:
            reports = AdoReport.objects.filter(
                 created_on_ado__range=[start, end],
             )
            filename = 'report_all.csv'
        
        if len(reports) == 0:
            return Response({'status' : 204})  
        else:    
            csvFile = open(directory + filename, 'w')
            csvFile.write('Sno,District, Block Name, Village Name, Village Code, Longitude, Latitude, Acquired Date, Acquired Time, DDA Details, ADO Details, Farmer Name, Father Name, Kila Number, Murabba Number, Incident Reason, Remarks, Ownership/Lease, Action, Images\n')
            sno = 0
            for report in reports:
                sno += 1
                dis = ''
                if report.location.district:
                    dis = str(report.location.district)

                block = ''
                if report.location.block_name:
                    block = str(report.location.block_name)

                village = ''
                if report.village:
                    village = str(report.village.village)
                village_code = ''
                if report.village_code:
                    village_code = str(report.village_code)

                longitude = ''
                if report.location.longitude:
                    longitude = str(report.location.longitude)

                latitude = ''
                if report.location.latitude:
                    latitude = str(report.location.latitude)

                acq_date = ''
                if report.location.acq_date:
                    acq_date = str(report.location.acq_date)

                acq_time = ''
                if report.location.acq_time:
                    acq_time = str(report.location.acq_time)

                dda = ''
                if report.location.dda:
                    dda = str(report.location.dda.name)

                ado = ''
                if report.location.ado:
                    ado = str(report.location.ado.name)

                farmer_name = ''
                if report.farmer_name:
                    farmer_name = str(report.farmer_name)

                father_name = ''
                if report.father_name:
                    father_name = str(report.father_name)

                kila_num = ''
                if report.kila_num:
                    kila_num = str(report.kila_num)

                murrabba_num = ''
                if report.murrabba_num:
                    murrabba_num = str(report.murrabba_num)

                incident_reason = '' 
                if report.incident_reason:
                    incident_reason = str(report.incident_reason)

                remarks = ''
                if report.remarks:
                     remarks = str(report.remarks)

                ownership = ''
                if report.ownership:
                    ownership = str(report.ownership)

                action = ''
                if report.action:
                    action = str(report.action)

                images = Image.objects.filter(report = report).order_by('-pk')
                if len(images) > 0:
                    img = [DOMAIN + 'media/' + str(i.image) for i in images ]
                else:
                    img = []
                csvFile.write(
                    str(sno) + ',' 
                  + str(dis) + ',' 
                  + str(block) + ',' 
                  + str(village) + ',' 
                  + str(village_code) + ',' 
                  + str(longitude) + ',' 
                  + str(latitude) + ',' 
                  + str(acq_date).replace(',' , '/') + ',' 
                  + str(acq_time).replace(',' , '/') + ',' 
                  + str(dda) + ',' 
                  + str(ado) + ',' 
                  + str(farmer_name) + ',' 
                  + str(father_name) + ',' 
                  + str(kila_num).replace(',' , '/') + ',' 
                  + str(murrabba_num).replace(',' , '/') + ',' 
                  + str(incident_reason).replace(',' , '/') + ',' 
                  + str(remarks).replace(',' , '/') + ',' 
                  + str(ownership).replace(',' , '/') + ',' 
                  + str(action).replace(',' , '/') + ',' 
                  + str(' | '.join(img)) + ','
                  + '\n')
            csvFile.close()
            absolute_path = DOMAIN + 'media/reports/'+ filename
            return Response({'status': 200, 'csvFile':absolute_path})

class CountOfReports(APIView):

    def get(self, request, format = None):
        data = {}
        date = request.GET.get('date',None)
        if date:
            date = datetime.datetime.strptime(date, '%Y-%m-%d').strftime('%Y-%m-%d')
            pending_count = Location.objects.filter(status='pending', acq_date=date).count()
            ongoing_count = Location.objects.filter(status='ongoing', acq_date=date).count()
            completed_count = Location.objects.filter(status='completed', acq_date=date).count()
            districts = District.objects.all()
            for district in districts:
                data[str(district.district)] = {}
                data[str(district.district)]['pending'] = Location.objects.filter(district=district.district, acq_date=date, status='pending').count()
                data[str(district.district)]['ongoing'] = Location.objects.filter(district=district.district, acq_date=date, status='ongoing').count()
                data[str(district.district)]['completed'] = Location.objects.filter(district=district.district, acq_date=date, status='completed').count()
        else:
            pending_count = Location.objects.filter(status='pending').count()
            ongoing_count = Location.objects.filter(status='ongoing').count()
            completed_count = Location.objects.filter(status='completed').count()
            districts = District.objects.all()
            for district in districts:
                data[str(district.district)] = {}
                data[str(district.district)]['pending'] = Location.objects.filter(district=district.district, status='pending').count()
                data[str(district.district)]['ongoing'] = Location.objects.filter(district=district.district, status='ongoing').count()
                data[str(district.district)]['completed'] = Location.objects.filter(district=district.district, status='completed').count()
        return Response({
                'status': 200, 
                'pending_count': pending_count, 
                'ongoing_count': ongoing_count, 
                'completed_count': completed_count ,
                'results':data
            })

class CountOfReportsbtwdates(APIView):
    
    def get(self, request, format = None):
        data ={}
        startdate = request.GET.get('start_date',None)
        enddate= request.GET.get('end_date',None)
        points_to_plot = int(request.GET.get('points',20))
        
        if startdate and enddate:            
            a= datetime.datetime.strptime(startdate,"%Y-%m-%d")
            b= datetime.datetime.strptime(enddate,"%Y-%m-%d")        
            days_per_point = int((b-a).days+1)/points_to_plot 
            
            if days_per_point <1:
                days_per_point = 1
                points_to_plot =int((b-a).days+1)*days_per_point

            startdate = datetime.datetime.strptime(startdate, '%Y-%m-%d').strftime('%Y-%m-%d')
            enddate = datetime.datetime.strptime(enddate, '%Y-%m-%d').strftime('%Y-%m-%d')

            pending_count = Location.objects.filter(status='pending', acq_date__range=[startdate,enddate])
            ongoing_count = Location.objects.filter(status='ongoing', acq_date__range=[startdate,enddate])
            completed_count = Location.objects.filter(status='completed', acq_date__range=[startdate,enddate])
            p=[]
            o=[]
            c=[]

            for x in range(0,points_to_plot):
                
                s=a+timedelta(days=days_per_point*x)
                e=s+timedelta(days=days_per_point-1)
                s=s.strftime('%Y-%m-%d')
                e=e.strftime('%Y-%m-%d')

                p.append({'start': s, 'end' : e, 'data': pending_count.filter(status='pending', acq_date__range=[s,e]).count()})
                o.append({'start': s, 'end' : e, 'data': ongoing_count.filter(status='ongoing', acq_date__range=[s,e]).count()})
                c.append({'start': s, 'end' : e, 'data': completed_count.filter(status='completed', acq_date__range=[s,e]).count()})


          
            districts = District.objects.all()
            for district in districts:
                data[str(district.district)] = {}
                data[str(district.district)]['pending'] = Location.objects.filter(district=district.district, acq_date__range=[startdate,enddate], status='pending').count()
                data[str(district.district)]['ongoing'] = Location.objects.filter(district=district.district, acq_date__range=[startdate,enddate], status='ongoing').count()
                data[str(district.district)]['completed'] = Location.objects.filter(district=district.district, acq_date__range=[startdate,enddate], status='completed').count()
            
            return Response({
                    'status': 200, 
                    'pending_count': p, 
                    'ongoing_count': o, 
                    'completed_count': c,
                    'results':data
                })
        else:
            return Response({
                'Error': "Dates not provided"
                })



def return_excel_data_points(initial_date):
    file_path = os.path.join(MEDIA_ROOT, "firedata", initial_date, "harsac", "file.xlsx")
    df_one = pd.read_excel(file_path)
    date = initial_date.split('-')
    date = date[0]+"-"+date[2]+"-"+date[1]
    df_two = df_one[df_one['Acq_Date']==date]
    df_two = df_two.query('Latitude >=27.616667 and Latitude<=30.583333 and Longitude>74.46667 and Longitude<77.6')
    df_two = df_two[['Latitude', 'Longitude']]
    df_two.columns = ['latitude', 'longitude']
    df_two.to_csv(os.path.join(MEDIA_ROOT, "firedata", initial_date, "harsac", "report.csv"))
    return [tuple(x) for x in df_two.values]

def return_data_points(date, dataset):
    file_path = os.path.join(MEDIA_ROOT, "firedata", date, dataset, "file.csv")
    df_one = pd.read_csv(file_path)
    df_two = df_one[df_one['acq_date']==date]
    df_two = df_two.query('latitude >=27.616667 and latitude<=30.583333 and longitude>74.46667 and longitude<77.6')
    df_two = df_two[['latitude', 'longitude']]
    df_two.to_csv(os.path.join(MEDIA_ROOT, "firedata", date, dataset, "report.csv"))
    return [tuple(x) for x in df_two.values]

def generate_report(date):
    datasets = ['harsac', 'modis', 'viirs_noaa', 'viirs_npp1']
    report_data = {}
    for dataset in datasets:
        file_path = os.path.join(MEDIA_ROOT, "firedata", date, dataset, "report.csv")
        df_one = pd.read_csv(file_path)
        df_one = df_one[['latitude', 'longitude']]
        df_one.columns = [dataset+'_latitude', dataset+'_longitude']
        report_data[dataset+'_points'] = [tuple(x) for x in df_one.values]
    return report_data

class CompareFireDataReport(APIView):
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = []

    def get(self, request, *args, **kwargs):
        date = request.query_params.get('date', None)
        if date:
            if (os.path.isdir(os.path.join(MEDIA_ROOT, "firedata", date))):
                report = generate_report(date)
                return Response(report, status=status.HTTP_200_OK)
            return Response("Files for this date NOT FOUND", status=status.HTTP_404_NOT_FOUND)
        return Response("Invalid Date", status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, *args, **kwargs):
        serializer = CompareDataSerializer(data=request.data)
        try:
            if (request.POST['force-update'] == "True"):
                if (os.path.isdir(os.path.join(MEDIA_ROOT, "firedata", serializer.initial_data['date']))):
                    shutil.rmtree(os.path.join(MEDIA_ROOT, "firedata",serializer.initial_data['date']))
        except:
            pass
            
        if serializer.is_valid() and not (os.path.isdir(os.path.join(MEDIA_ROOT, "firedata",serializer.initial_data['date']))):
            serializer.save()
            harsac_points = return_excel_data_points(initial_date=serializer.initial_data['date'])
            modis_points = return_data_points(date=serializer.initial_data['date'], dataset="modis")
            viirs_noaa_points = return_data_points(date=serializer.initial_data['date'], dataset="viirs_noaa")
            virrs_npp1_points = return_data_points(date=serializer.initial_data['date'], dataset="viirs_npp1")
            return Response({"harsac_points": harsac_points, "modis_points": modis_points, "viirs_noaa_points": viirs_noaa_points, "viirs_npp1_points": virrs_npp1_points}, status=200)
        return Response({"error": "data already exists"}, status=400)   
    class LocationList_map(APIView):
        permission_classes = []

        def get(self, request, format = None):
            locations = []
            start = request.GET.get('start',None)
            end = request.GET.get('end', None)
            district = request.GET.get('district', None)
            status = request.GET.get('status', None)
            dda = request.GET.get('dda', None)
            if dda:
                if start and end:
                    start = datetime.datetime.strptime(start, '%Y-%m-%d').strftime('%Y-%m-%d')
                    end = datetime.datetime.strptime(end, '%Y-%m-%d').strftime('%Y-%m-%d')
                    if district:
                        if status:
                            locations = Location.objects.filter(district=district.upper(), status=status, acq_date__range=[start,end], dda__pk=int(dda)).order_by('-pk')
                        else:
                            locations = Location.objects.filter(district=district.upper(), acq_date__range=[start,end], dda__pk=int(dda)).order_by('-pk')
                    else:
                        if status:
                            locations = Location.objects.filter(status=status, acq_date__range=[start,end], dda__pk=int(dda)).order_by('-pk')
                        else:
                            locations = Location.objects.filter(acq_date__range=[start,end], dda__pk=int(dda)).order_by('-pk')
                else:
                    if district:
                        if status:
                            locations = Location.objects.filter(district=district.upper(), status=status, dda__pk=int(dda)).order_by('-pk')
                        else:
                            locations = Location.objects.filter(district=district.upper(), dda__pk=int(dda)).order_by('-pk')
                    else:
                        if status:
                            locations = Location.objects.filter(status=status, dda__pk=int(dda)).order_by('-pk')
                        else:
                            locations = Location.objects.filter(dda__pk=int(dda)).order_by('-pk')
            else:
                if start and end:
                    start = datetime.datetime.strptime(start, '%Y-%m-%d').strftime('%Y-%m-%d')
                    end = datetime.datetime.strptime(end, '%Y-%m-%d').strftime('%Y-%m-%d')
                    if district:
                        if status:
                            locations = Location.objects.filter(district=district.upper(), status=status, acq_date__range=[start,end]).order_by('-pk')
                        else:
                            locations = Location.objects.filter(district=district.upper(), acq_date__range=[start,end]).order_by('-pk')
                    else:
                        if status:
                            locations = Location.objects.filter(status=status, acq_date__range=[start,end]).order_by('-pk')
                        else:
                            locations = Location.objects.filter(acq_date__range=[start,end]).order_by('-pk')
                else:
                    if district:
                        if status:
                            locations = Location.objects.filter(district=district.upper(), status=status).order_by('-pk')
                        else:
                            locations = Location.objects.filter(district=district.upper()).order_by('-pk')
                    else:
                        if status:
                            locations = Location.objects.filter(status=status).order_by('-pk')
                        else:
                            locations = Location.objects.all().order_by('-pk')

            ls= list()
            for loc in locations:
                dic= dict()
                dic['id']= loc.id
                dic['longitude']= loc.longitude
                dic['latitude']= loc.latitude
                ls.append(dic)
            return Response(ls)
