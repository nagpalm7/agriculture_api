from django.db import models
from django.contrib.auth.models import User as DjangoUser
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from datetime import date
from django.core.validators import (
    FileExtensionValidator
)
from django.db.models import Q

userTypes = ( ('admin','admin'),('dda','dda'), ('ado', 'ado') )
choices_status = ( ('pending','pending'),('ongoing','ongoing'),('completed','completed') )

class User(models.Model):
    name = models.CharField(max_length = 100, blank = False, null = False, unique = False)
    typeOfUser = models.CharField(max_length=10,choices=userTypes,default='admin')
    auth_user = models.OneToOneField(DjangoUser, on_delete=models.CASCADE)
    district = models.CharField(max_length=10, blank = True, null = True, unique = False)
    dda_head = models.ForeignKey('self', on_delete = models.CASCADE, limit_choices_to={'typeOfUser': 'dda'}, blank = True, null = True,)
    
    def __str__(self):
        if self.name:
            return str(self.name + ' (' + self.typeOfUser + ')')
        else:
            return self.auth_user.username

    def save(self, *args, **kwargs):
        if self.district:
            self.district = self.district.lower()
        return super(User, self).save(*args, **kwargs)
        
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
    dda = models.ForeignKey(User, on_delete = models.CASCADE, blank = True, null = True, related_name = 'dda')        
    ado = models.ForeignKey(User, on_delete = models.CASCADE, limit_choices_to={'typeOfUser': 'ado'}, blank = True, null = True, default = None, related_name = 'ado')
    status = models.CharField(max_length = 10, choices = choices_status, default = 'pending')
    # csv_file = models.FileField(
    #     upload_to='locationCSVs/',
    #     validators=[FileExtensionValidator(['csv'])],
    # )

    def __str__(self):
        return self.district + ' ' + self.state