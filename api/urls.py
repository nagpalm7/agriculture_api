from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns
from api import views

urlpatterns = [
    path('api/user/', views.UserList.as_view(), name='user-list'),
    path('api/get-user/', views.GetUser.as_view(), name='get-user'),
    path('api/user/<int:pk>/', views.UserDetail.as_view(), name='user-detail'),
    path('api/upload/locations/', views.LocationList.as_view(), name='user-detail'),
    path('api/location/<int:pk>/', views.LocationDetail.as_view(), name='location-detail'),
    path('api/locations/<str:status>', views.LocationViewSet.as_view({'get': 'list'}), name='admin-location-list'),
    path('api/locations/ado/<str:status>', views.LocationViewSetAdo.as_view({'get': 'list'}), name='ado-location-list'),
    path('api/locations/dda/<str:status>', views.LocationViewSetDda.as_view({'get': 'list'}), name='dda-location-list'),
    path('api/ado/', views.AdoViewSet.as_view({'get': 'list'}), name='ado-list'),
]

urlpatterns = format_suffix_patterns(urlpatterns)