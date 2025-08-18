from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.http.response import JsonResponse
import statistics

import json
import datetime
from django.utils.timezone import now
from rest_framework import pagination
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import *
from rest_framework.generics import *
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import *
from django.db.models import *
from datetime import date, timedelta
from rest_framework.settings import api_settings
from rest_framework import filters
import django_filters.rest_framework
from django_filters import DateRangeFilter,DateFilter
import io, csv, pandas as pd
from rest_framework.parsers import MultiPartParser

from controller.models import *
from controller.serializers import *
from leave.models import *
from dictionary.models import DictionaryItem
from payroll.models import StaffSalary
from leave.serializers import *
from kpi.serializers import *
from gateway.models import *
from kpi.models import *


#====================================================== kpi ====================================================
class kpiSearch(django_filters.FilterSet):

    class Meta:
        model = Kpi
        fields = {
        	'id' : ['exact','in'],
            'code' : ['exact', 'icontains'], 
            'name' : ['exact', 'icontains'], 
            'year' : ['exact'],
            'department__id' : ['exact'],
            'branch__id' : ['exact'],
            'level__id' : ['exact'],
            'is_active' : ['exact']
        }


class KPIList(ListAPIView):
    queryset = Kpi.objects.all()
    serializer_class = KPIListSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = kpiSearch
    search_fields = ['code','name', 'year']
    ordering_fields = ['id','code','name']
    ordering = ['-id']

#====================================================== staff kpi ====================================================
class staffSearch(django_filters.FilterSet):

    class Meta:
        model = StaffKPI
        fields = {
        	'id' : ['exact','in'],
            'kpi__id' : ['exact'],
        }



class KPIStaffList(ListAPIView):
    queryset = StaffKPI.objects.all()
    serializer_class = StaffKPISerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = staffSearch
    search_fields = ['staff__staff_opf','staff__staff_cpf', 'staff__full_name']
    ordering_fields = ['id','staff__full_name','staff__staff_opf']
    ordering = ['staff__full_name']


