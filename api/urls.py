from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns
from api import views

urlpatterns = [
    # Url for base user / auth user
    path('api/user/', views.UserList.as_view(), name='user-list'),
    path('api/user/dda/', views.DDAList.as_view(), name='user-list-dda'),
    path('api/get-user/', views.GetUser.as_view(), name='get-user'),
    path('api/user/<int:pk>/', views.UserDetail.as_view(), name='user-detail'),
    # Url for districts
    path('api/district/', views.DistrictList.as_view(), name='district-list'),
    path('api/district/<int:pk>/', views.DistrictDetail.as_view(), name='district-detail'),
    # Url for districts
    path('api/village/', views.VillageList.as_view(), name='village-view'),
    path('api/village/<int:pk>/', views.VillageDetail.as_view(), name='village-detail'),
    path('api/villages-list/', views.VillageViewSet.as_view({'get': 'list'}), name='village-list'),
    # Url for admin, ado and dda list paginated
    path('api/users-list/admin/', views.AdminViewSet.as_view({'get': 'list'}), name='admin-list'),
    path('api/users-list/dda/', views.DdaViewSet.as_view({'get': 'list'}), name='dda-list'),
    path('api/users-list/ado/', views.AdosViewSet.as_view({'get': 'list'}), name='ado-list'),
    # vllages district wise
    path('api/villages-list/district/<int:pk>/', views.VillagesDistrictWiseViewSet.as_view({'get': 'list'}), name='village-district-list'),

    path('api/upload/locations/', views.LocationList.as_view(), name='upload-locations'),
    path('api/location/<int:pk>/', views.LocationDetail.as_view(), name='location-detail'),
    path('api/locations/<str:status>', views.LocationViewSet.as_view({'get': 'list'}), name='admin-location-list'),
    path('api/locations/ado/<str:status>', views.LocationViewSetAdo.as_view({'get': 'list'}), name='ado-location-list'),
    path('api/locations/dda/<str:status>', views.LocationViewSetDda.as_view({'get': 'list'}), name='dda-location-list'),
    path('api/admin/ado/<int:pk>/<str:status>', views.LocationViewSetAdoForAdmin.as_view({'get': 'list'}), name='admin-ado-location-list'),
    path('api/admin/dda/<int:pk>/<str:status>', views.LocationViewSetDdaForAdmin.as_view({'get': 'list'}), name='admin-dda-location-list'),
    path('api/location/district/<int:pk>/<str:status>', views.LocationDistrictWiseViewSet.as_view({'get': 'list'}), name='location-district-location-list'),
    # List of ados under a specific dda logged in
    path('api/ado/', views.AdoViewSet.as_view({'get': 'list'}), name='ado-list'),
    # Ado report and image views
    path('api/report-ado/<int:pk>/', views.AdoReportDetail.as_view(), name='ado-report-detail'),
    path('api/report-ado/add/', views.AddAdoReport.as_view(), name='add-ado-report'),
    path('api/upload/images/', views.ImageView.as_view(), name='upload-images'),
    # Bulk add village
    path('api/upload/villages/', views.BulkAddVillage.as_view(), name='upload-villages'),
    # Bulk add village
    path('api/upload/districts/', views.BulkAddDistrict.as_view(), name='upload-districts'),
    # Bulk add ado
    path('api/upload/ado/', views.BulkAddAdo.as_view(), name='upload-ado'),
    # Bulk add ado
    path('api/upload/dda/', views.BulkAddDda.as_view(), name='upload-dda'),
    # Trigger sms
    path('api/trigger/sms/<str:status>', views.TriggerSMS.as_view(), name='trigger-sms'),
    path('api/ado-export-pdf/',views.ExportAdoPdf),
    path('api/generate-passwords-ado/',views.GeneratePasswordsForAdo.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)