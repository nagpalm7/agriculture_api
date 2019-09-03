from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns
from api import views

urlpatterns = [
    path('api/user/', views.UserList.as_view(), name='user-list'),
    path('api/get-user/', views.GetUser.as_view(), name='get-user'),
    path('api/user/<int:pk>/', views.UserDetail.as_view(), name='user-detail'),
    path('api/upload/locations/', views.LocationList.as_view(), name='user-detail'),
]

urlpatterns = format_suffix_patterns(urlpatterns)