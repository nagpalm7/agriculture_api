from django.db import models
from django.contrib.auth.models import User as DjangoUser
from django.contrib.auth.models import AbstractUser, UserManager
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from datetime import date
from django.core.validators import (
    FileExtensionValidator
)
from django.db.models import Q

userTypes = ( ('admin','admin'),('dda','dda'), ('ado', 'ado') )
actions = ( ('chalaan','Challan'),('FIR','FIR') )
choices_status = ( ('pending','pending'),('ongoing','ongoing'),('completed','completed') )

# --------------------- MODELS ----------------------
class CustomUserManager(UserManager):
    def create_user(self, username, email, password=None):
        """
        Creates and saves a User.
        """
        user = self.model(
            username=username,
            email=email
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password):
        """
        Creates and saves a superuser.
        """
        user = self.create_user(
            username=username,
            email=email,
            password=password,
        )
        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

class User(AbstractUser):
    TYPE_CHOICES = (
        ('customer', 'Customer Care'),
        ('ado', 'ADO Officer'),
        ('dda', 'DDA Officer'),
        ('admin', 'Super Admin')
    )

    objects = CustomUserManager()
    type_of_user = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        blank=False,
        null=False,
    )

# SuperAdmin - 1 for each institution
class Admin(models.Model):
    name = models.CharField(max_length=200, blank=False, null=True)
    auth_user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
    )
    def __str__(self):
        return str(self.name)

class District(models.Model):
    district = models.CharField(max_length = 500, blank = True, null = True, unique = False)
    district_code = models.CharField(max_length=200, blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.district:
            self.district = self.district.upper()
        return super(District, self).save(*args, **kwargs)

    def __str__(self):
        return self.district

class Village(models.Model):
    village = models.CharField(max_length = 500, blank = True, null = True, unique = False)
    village_code = models.CharField(max_length=200, blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.village:
            self.village = self.village.upper()
        return super(Village, self).save(*args, **kwargs)

    def __str__(self):
        return self.village

class Dda(models.Model):
    name = models.CharField(max_length=200, blank=True, null=True)
    district = models.ForeignKey(District, on_delete = models.CASCADE, blank = False, null = False, related_name='dda_district')
    number = models.CharField(max_length=15, blank=True, null=True)
    email = models.CharField(max_length=100, blank=True, null=True)
    auth_user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return str(self.name + ' (' + self.district.district + ')')

class Ado(models.Model):
    name = models.CharField(max_length=200, blank=True, null=True)
    number = models.CharField(max_length=15, blank=True, null=True)
    email = models.CharField(max_length=100, blank=True, null=True)
    village = models.ManyToManyField(Village, related_name='ado_village', blank=True)
    dda = models.ForeignKey(Dda, on_delete = models.CASCADE, blank = True, null = True, related_name='ado_dda')
    auth_user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return str(self.name)

class Location(models.Model):
    state = models.CharField(max_length = 50, blank = False, null = False, unique = False)
    district = models.CharField(max_length = 50, blank = False, null = False, unique = False)
    block_name = models.CharField(max_length = 50, blank = True, null = True, unique = False)
    village_name = models.CharField(max_length = 100, blank = True, null = True, unique = False)
    longitude = models.CharField(max_length = 100, blank = False, null = False, unique = False)
    latitude = models.CharField(max_length = 100, blank = False, null = False, unique = False)
    acq_date = models.DateField(default = timezone.now)
    acq_time = models.TimeField(default = timezone.now)
    dda = models.ForeignKey(Dda, on_delete = models.CASCADE, blank = True, null = True, default = None, related_name = 'location_dda')        
    ado = models.ForeignKey(Ado, on_delete = models.CASCADE, blank = True, null = True, default = None, related_name = 'location_ado')
    status = models.CharField(max_length = 10, choices = choices_status, default = 'pending')
    # csv_file = models.FileField(
    #     upload_to='locationCSVs/',
    #     validators=[FileExtensionValidator(['csv'])],
    # )

    def save(self, *args, **kwargs):
        if self.village_name:
            self.village_name = self.village_name.upper()
        if self.district:
            self.district = self.district.upper()
        return super(Location, self).save(*args, **kwargs)

    def __str__(self):
        return self.district + ' ' + self.state
 
class AdoReport(models.Model):
    village_code = models.CharField(max_length = 50, blank = True, null = True, unique = False)
    village = models.ForeignKey(Village, on_delete = models.CASCADE, blank = True, null = True, default = None, related_name = 'location_village')
    farmer_code = models.CharField(max_length = 50, blank = True, null = True, unique = False)
    farmer_name = models.CharField(max_length = 50, blank = True, null = True, unique = False)
    father_name = models.CharField(max_length = 50, blank = True, null = True, unique = False)
    longitude = models.CharField(max_length = 100, blank = True, null = True, unique = False)
    latitude = models.CharField(max_length = 100, blank = True, null = True, unique = False)
    kila_num = models.CharField(max_length = 50, blank = True, null = True, unique = False)
    murrabba_num = models.CharField(max_length = 50, blank = True, null = True, unique = False)
    incident_reason = models.CharField(max_length = 500, blank = True, null = True, unique = False)        
    remarks = models.CharField(max_length = 500, blank = True, null = True, unique = False)
    amount = models.CharField(max_length = 500, blank = True, null = True, unique = False)
    ownership = models.CharField(max_length = 50, blank = True, null = True, unique = False)
    action = models.CharField(max_length = 50, choices = actions, blank = True, null = True, unique = False, default='FIR')
    location = models.ForeignKey(Location, on_delete = models.CASCADE)

    def __str__(self):
        return self.location.village_name

class Image(models.Model):
    report = models.ForeignKey(AdoReport, on_delete = models.CASCADE)
    image = models.ImageField(upload_to='images/')