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

#====================================================== kpi ====================================================
class sectionSearch(django_filters.FilterSet):

	class Meta:
		model = Section
		fields = {
			'id' : ['exact','in'],
			'code' : ['exact', 'icontains'], 
			'name' : ['exact', 'icontains'],
			'kpi__id' : ['exact'],
		}


class KPISectionList(ListAPIView):
	queryset = Section.objects.all()
	serializer_class = KPISectionSerializer
	pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
	filter_backends = [django_filters.rest_framework.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
	filterset_class = sectionSearch
	search_fields = ['code','name']
	ordering_fields = ['id','code','name']
	ordering = ['code']


#====================================================== kpi ====================================================
class resultSearch(django_filters.FilterSet):

	class Meta:
		model = KeyResult
		fields = {
			'id' : ['exact','in'],
			'name' : ['exact', 'icontains'],
			'kpi__id' : ['exact'],
			'section__id' : ['exact'],
		}


class KPIResultList(ListAPIView):
	queryset = KeyResult.objects.all()
	serializer_class = KPIResultSerializer
	pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
	filter_backends = [django_filters.rest_framework.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
	filterset_class = resultSearch
	search_fields = ['name']
	ordering_fields = ['id','name']
	ordering = ['section__code','name']


#====================================================== kpi ====================================================
class perfomanceSearch(django_filters.FilterSet):

	class Meta:
		model = Performance
		fields = {
			'id' : ['exact','in'],
			'performance_measure' : ['exact', 'icontains'],
			'kpi__id' : ['exact'],
			'result__id' : ['exact'],
		}


class KPIPerformanceList(ListAPIView):
	queryset = Performance.objects.all()
	serializer_class = KPIPerfomanceSerializer
	pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
	filter_backends = [django_filters.rest_framework.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
	filterset_class = perfomanceSearch
	search_fields = ['performance_measure']
	ordering_fields = ['id','performance_measure']
	ordering = ['result__section__code','result__name','performance_measure']



#====================================================== staff kpi ====================================================
class staffSearch(django_filters.FilterSet):

	class Meta:
		model = StaffKPI
		fields = {
			'id' : ['exact','in'],
			'kpi__id' : ['exact'],
		}


class KPIStaffList(ListAPIView):
	serializer_class = StaffKPIListSerializer
	pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
	filter_backends = [django_filters.rest_framework.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
	filterset_class = staffSearch
	search_fields = ['staff__staff_opf','staff__staff_cpf', 'staff__full_name']
	ordering_fields = ['id','staff__full_name','staff__staff_opf']
	ordering = ['staff__full_name','staff__staff_opf']

	def get_queryset(self):
		qs = StaffKPI.objects.all().distinct('staff__full_name','staff__staff_opf')
		return qs.order_by('staff__full_name','staff__staff_opf')


class StaffKPIData(APIView):
    def get(self, request, *args, **kwargs):
        kpi_id = request.query_params.get("kpi_id")
        staff_id = request.query_params.get("staff_id")

        if not kpi_id or not staff_id:
            return Response({}, status=status.HTTP_200_OK)

        # Check if there is at least one StaffKPI for this KPI and staff
        if not StaffKPI.objects.filter(kpi_id=kpi_id, staff_id=staff_id).exists():
            return Response([], status=status.HTTP_200_OK)

        # Only get the KPI if matching StaffKPI exists
        try:
            kpi_instance = Kpi.objects.get(id=kpi_id)
        except Kpi.DoesNotExist:
            return Response({}, status=status.HTTP_200_OK)

        serializer = StaffKpiSerializer(
            kpi_instance,
            context={"staff_id": staff_id, "kpi_id": kpi_instance.id}
        )

        return Response(serializer.data, status=status.HTTP_200_OK)






