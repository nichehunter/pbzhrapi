from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.http.response import JsonResponse
import statistics

import json
import datetime
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
from dictionary.models import *



# ============================ dashboard ====================================
class PBZCount(APIView):
	def get(self, request):
		staff = Staff.objects.filter(is_active=True).count()
		branch = Branch.objects.filter(is_active=True).count()
		unit = Department.objects.filter(is_active=True).count()
		data = {'staff': staff, 'branch': branch,'unit': unit}
		return JsonResponse(data)


class StaffCenter(APIView):
	def get(self, request):
		bra = Branch.objects.filter(is_active=True, branch_type=4)
		ctr = Branch.objects.filter(is_active=True, branch_type=6)
		bre = Branch.objects.filter(is_active=True, branch_type=7)
		col = Branch.objects.filter(is_active=True, branch_type=61)
		staff = Staff.objects.filter(is_active=True)
		head = StaffDepartment.objects.filter(is_active=True, branch=1, staff__in=staff).count()
		branch = StaffDepartment.objects.filter(is_active=True, branch__in = bra, staff__in=staff).count()
		center = StaffDepartment.objects.filter(is_active=True, branch__in = ctr, staff__in=staff).count()
		bureue = StaffDepartment.objects.filter(is_active=True, branch__in = bre, staff__in=staff).count()
		collection = StaffDepartment.objects.filter(is_active=True, branch__in = col, staff__in=staff).count()
		data = {'labels': ['Head Office','Branch','Service Center','Bureue de change','Collection Point'], 'results': [head, branch, center, bureue, collection]}
		return JsonResponse(data)


class StaffTitle(APIView):
	def get(self, request):
		drc = DictionaryItem.objects.filter(dictionary_item_parent=23)
		mgr = DictionaryItem.objects.filter(dictionary_item_parent=22)
		snr = DictionaryItem.objects.filter(dictionary_item_parent=21)
		ofc = DictionaryItem.objects.filter(dictionary_item_parent=20)
		staff = Staff.objects.filter(is_active=True)
		director = StaffDepartment.objects.filter(is_active=True, title__in=drc, staff__in=staff).count()
		manager = StaffDepartment.objects.filter(is_active=True, title__in=mgr, staff__in=staff).count()
		senior = StaffDepartment.objects.filter(is_active=True, title__in=snr, staff__in=staff).count()
		officer = StaffDepartment.objects.filter(is_active=True, title__in=ofc, staff__in=staff).count()
		data = {'labels': ['Head & Directors','Managers','Seniors & Incharge','Officers & Others'], 'results': [director, manager, senior, officer]}
		return JsonResponse(data)