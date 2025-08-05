from django.db import models

# Create your models here.
from django.db import models
from controller.models import *
from dictionary.models import DictionaryItem
import datetime
import pandas as pd

# Create your models here.
class NameField(models.CharField):

    def get_prep_value(self, value):
        return str(value).lower()

#============================================= salary ==============================================================
class Training(models.Model):
    code = NameField(max_length=50, blank=True, null=True)
    name = NameField(max_length=512, blank=True, null=True)
    training_type = models.ForeignKey(DictionaryItem, on_delete = models.RESTRICT)
    description = NameField(max_length=512, blank=True, null=True)
    start_date = models.DateField()
    end_date = models.DateField()
    location = NameField(max_length=512, blank=True, null=True)
    satatus = models.ForeignKey(DictionaryItem, on_delete = models.RESTRICT, related_name="training_status")
    quarter = models.PositiveIntegerField(default=pd.Timestamp(datetime.date.today()).quarter)
    year = models.PositiveIntegerField(default=datetime.date.today().year)
    recorded_by = models.PositiveIntegerField(null=False)
    recorded_at = models.DateTimeField(auto_now_add = True, null=True)

    def __str__(self):
        return self.code
    
    class Meta:
        verbose_name = "Training"
        verbose_name_plural = "Trainings"


#============================================= salary ==============================================================
class StaffTraining(models.Model):
    staff = models.ForeignKey(Staff, on_delete = models.RESTRICT)
    training = models.ForeignKey(Training, on_delete = models.RESTRICT)
    is_active = models.BooleanField(default=True)
    recorded_by = models.PositiveIntegerField(null=False)
    recorded_at = models.DateTimeField(auto_now_add = True, null=True)

    def __str__(self):
        return self.training.code
    
    class Meta:
        verbose_name = "Staff Training"
        verbose_name_plural = "Staff Trainings"


#============================================= salary ==============================================================
class TrainingAttachment(models.Model):
    training = models.ForeignKey(Training, on_delete = models.RESTRICT)
    training_attachment = models.ForeignKey(DictionaryItem, on_delete = models.RESTRICT)
    file = models.FileField(null=True, blank=True)
    recorded_by = models.PositiveIntegerField(null=False)
    recorded_at = models.DateTimeField(auto_now_add = True, null=True)

    def __str__(self):
        return self.training.code
    
    class Meta:
        verbose_name = "Training Attachment"
        verbose_name_plural = "Training Attachments"