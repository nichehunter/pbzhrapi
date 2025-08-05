from django.db import models
import datetime
from django.contrib.postgres.fields import ArrayField

# Create your models here.
class NameField(models.CharField):

    def get_prep_value(self, value):
        return str(value).lower()


class EmployeeData(models.Model):
    reporting_date = NameField(max_length=50,blank=True, null=True)
    branch_code = NameField(max_length=50, blank=True, null=True)
    emplayee_name = NameField(max_length=150, blank=True, null=True)
    emplayee_gender = NameField(max_length=10, blank=True, null=True)
    emplayee_date_birth = NameField(max_length=50,blank=True, null=True)
    emplayee_identity_type = NameField(max_length=50, blank=True, null=True)
    emplayee_identity_number = NameField(max_length=50, blank=True, null=True)
    emplayee_position = NameField(max_length=150, blank=True, null=True)
    emplayee_position_category = NameField(max_length=50, blank=True, null=True)
    emplayee_status = NameField(max_length=50, blank=True, null=True)
    emplayee_department = NameField(max_length=50, blank=True, null=True)
    emplayee_appointment_date = NameField(max_length=50,blank=True, null=True)
    emplayee_nationality = NameField(max_length=50, blank=True, null=True)
    emplayee_last_promotion_date = NameField(max_length=50,blank=True, null=True)
    emplayee_basic_salary = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    emplayee_benefit = ArrayField(models.CharField(max_length=150, blank=True),blank=True,null=True,default=list)


    def __str__(self):
        return self.emplayee_name
    
    class Meta:
        verbose_name = "Employee Data"
        verbose_name_plural = "Employee Data"