from django.db import models
import datetime

# Create your models here.
class NameField(models.CharField):

    def get_prep_value(self, value):
        return str(value).lower()


class Dictionary(models.Model):
    dictionary_code = NameField(max_length=15, blank=True, null=True)
    dictionary_name = NameField(max_length=512, blank=True, null=True)
    recorded_by = models.PositiveIntegerField(null=False)
    recorded_at = models.DateTimeField(auto_now_add = True, null=True)

    def __str__(self):
        return self.dictionary_name
    
    class Meta:
        verbose_name = "Dictionary"
        verbose_name_plural = "Dictionaries"


class DictionaryItem(models.Model):
    dictionary_item_code = NameField(max_length=15, blank=True, null=True)
    dictionary_item_name = NameField(max_length=512, blank=True, null=True)
    dictionary_item_parent = models.IntegerField(blank=True, null=True)
    dictionary = models.ForeignKey(Dictionary, on_delete = models.RESTRICT,)
    recorded_by = models.PositiveIntegerField(null=False)
    recorded_at = models.DateTimeField(auto_now_add = True, null=True)

    def __str__(self):
        return self.dictionary_item_name
    
    class Meta:
        verbose_name = "Dictionary Item"
        verbose_name_plural = "Dictionary Items"
