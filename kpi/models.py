from django.db import models
from django.core.validators import MinValueValidator
from controller.models import *
from dictionary.models import DictionaryItem
import datetime

# Create your models here.
class NameField(models.CharField):

    def get_prep_value(self, value):
        return str(value).lower()



class Kpi(models.Model):
    code = NameField(max_length=20, blank=True, null=True)
    name = NameField(max_length=50, blank=True, null=True)
    descriptions = NameField(max_length=512, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    year = models.CharField(max_length=15, blank=True, null=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="departmentkpi")
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="branchkpi")
    level = models.ForeignKey(DictionaryItem, on_delete = models.RESTRICT, null=True, blank=True)
    recorded_by = models.PositiveIntegerField(null=False)
    recorded_at = models.DateTimeField(auto_now_add = True, null=True)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Kpi"
        verbose_name_plural = "Kips"


class Section(models.Model):
    code = NameField(max_length=20, blank=True, null=True)
    name = NameField(max_length=50)
    descriptions = NameField(max_length=512, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    kpi = models.ForeignKey(Kpi, on_delete = models.RESTRICT, related_name="section")
    recorded_by = models.PositiveIntegerField(null=False)
    recorded_at = models.DateTimeField(auto_now_add = True, null=True)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Section"
        verbose_name_plural = "Sections"


class KeyResult(models.Model):
    name = models.TextField()
    weighting_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0) 
    is_active = models.BooleanField(default=True)
    section = models.ForeignKey(Section, on_delete = models.RESTRICT, related_name="result")
    kpi = models.ForeignKey(Kpi, on_delete = models.RESTRICT, related_name="kpiresult")
    recorded_by = models.PositiveIntegerField(null=False)
    recorded_at = models.DateTimeField(auto_now_add = True, null=True)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Key Result"
        verbose_name_plural = "Key Results"



class Performance(models.Model):
    performance_measure = models.TextField()
    fy_target = models.TextField()
    weighting = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    result = models.ForeignKey(KeyResult, on_delete = models.RESTRICT, related_name="performance")
    kpi = models.ForeignKey(Kpi, on_delete = models.RESTRICT, related_name="kpiperfomance")
    recorded_by = models.PositiveIntegerField(null=False)
    recorded_at = models.DateTimeField(auto_now_add = True, null=True)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Performance"
        verbose_name_plural = "Performances"


class StaffKPI(models.Model):
    staff = models.ForeignKey(Staff, on_delete = models.RESTRICT, related_name="staffkpi")
    perfomance = models.ForeignKey(Performance, on_delete = models.RESTRICT)
    kpi = models.ForeignKey(Kpi, on_delete = models.RESTRICT)
    actual = models.DecimalField(max_digits=10, decimal_places=1, default=0)
    rating = models.DecimalField(max_digits=10, decimal_places=1, default=0)
    weighting_rating = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    recorded_by = models.PositiveIntegerField(null=False)
    recorded_at = models.DateTimeField(auto_now_add = True, null=True)

    def __str__(self):
        return self.staff.full_name
    
    class Meta:
        verbose_name = "Staff KPI"
        verbose_name_plural = "Staff KPIs"


