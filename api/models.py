from django.db import models
from django.contrib.auth.models import User as DjangoUser
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from datetime import date
from django.core.validators import (
    FileExtensionValidator
)

userTypes = ( ('admin','admin'),('dda','dda'), ('ado', 'ado') )
choices_status = ( ('pending','pending'),('ongoing','ongoing'),('completed','completed') )

class User(models.Model):
    name = models.CharField(max_length = 100, blank = False, null = False, unique = False)
    typeOfUser = models.CharField(max_length=10,choices=userTypes,default='admin')
    auth_user = models.OneToOneField(DjangoUser, on_delete=models.CASCADE)
    district = models.CharField(max_length=10, blank = True, null = True, unique = False)
    def __str__(self):
        if self.name:
            return str(self.name)
        else:
            return self.auth_user.username
    class Meta:
        ordering = ["name"]

class Location(models.Model):
    state = models.CharField(max_length = 50, blank = False, null = False, unique = False)
    district = models.CharField(max_length = 50, blank = False, null = False, unique = False)
    block_name = models.CharField(max_length = 50, blank = False, null = False, unique = False)
    village_name = models.CharField(max_length = 100, blank = False, null = False, unique = False)
    longitude = models.CharField(max_length = 100, blank = False, null = False, unique = False)
    latitude = models.CharField(max_length = 100, blank = False, null = False, unique = False)
    acq_date = models.DateField(default = timezone.now)
    acq_time = models.TimeField(default = timezone.now)
    dda = models.ForeignKey(User, on_delete = models.CASCADE, blank = True, null = True, related_name = 'ddo')        
    ado = models.ForeignKey(User, on_delete = models.CASCADE, blank = True, null = True, default = None, related_name = 'ado')
    status = models.CharField(max_length = 10, choices = choices_status, default = 'pending')
    # csv_file = models.FileField(
    #     upload_to='locationCSVs/',
    #     validators=[FileExtensionValidator(['csv'])],
    # )