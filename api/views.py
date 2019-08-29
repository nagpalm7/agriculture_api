from rest_framework import status
from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import *
from .serializers import *
from .permissions import *
from datetime import date, timedelta
import os
import calendar

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
