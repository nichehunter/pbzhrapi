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
from gateway.serializers import *
from gateway.models import *
from kpi.models import *


#====================================================== staff====================================================
class StaffData(APIView):

    serializer_class = StaffDataSerializer

    def get(self, request, pk):
        instance = Staff.objects.get(staff_opf=pk)
        serializer = StaffDataSerializer(instance, many=False)
        return JsonResponse(serializer.data, safe=False)


class StaffCount(APIView):

    def get(self, request, data, branch, department):
        if data == "department":
                depart = Department.objects.filter(parent_department__id=department)
                if depart:
                    staff = StaffDepartment.objects.filter(department__id__in=depart, is_active=True).count()
                    return Response({'count': staff}, status=status.HTTP_200_OK)
                else:
                    staff = StaffDepartment.objects.filter(department__id=department, is_active=True).count()
                    return Response({'count': staff}, status=status.HTTP_200_OK)
        elif data == "branch":
            bra = Branch.objects.filter(parent_branch__id=branch)
            if bra:
                staff = StaffDepartment.objects.filter(branch__id__in=bra, is_active=True).count()
                return Response({'count': staff}, status=status.HTTP_200_OK)
            else:
                staff = StaffDepartment.objects.filter(branch__id=branch, is_active=True).count()
                return Response({'count': staff}, status=status.HTTP_200_OK)
            


class LeaveAssignmentCount(APIView):

    def get(self, request, pk):
        leave = LeaveAssignment.objects.filter(assigned_to__id=pk, is_active=True).count()
        return Response({'count': leave}, status=status.HTTP_200_OK)



class GenerateEmployeeData(APIView):
    def post(self, request):
        instance = Staff.objects.all()
        saved_count = 0
        senior_benefit = ["1","7","8","9","10","11","12"]
        junior_benefit = ["1","7","8"]

        for staff in instance:
            staff_dept = staff.staff_department.filter(is_active=True).first()
            supervisor = staff.staff.filter(is_active=True).first()
            gender_name = staff.gender.dictionary_item_name.lower() if staff.gender else ''
            status_name = staff.employment_status.dictionary_item_name.lower() if staff.employment_status else ''
            salary_amount = StaffSalary.objects.filter(staff=staff, is_active=True).first()

            reporting = now().strftime('%d%m%Y%H%M')
            branch_code = staff_dept.branch.branch_code if staff_dept else None
            name = staff.full_name
            gender = "1" if gender_name == "male" else "2"
            dob = staff.dob.strftime('%d%m%Y%H%M')
            identity = "7"
            identity_number = staff.zanid if staff.zanid else "pbz"
            position = staff_dept.title.dictionary_item_name if staff_dept and staff_dept.title else "officer"
            position_category = "senior management" if supervisor and supervisor.supervise_type_id in [40, 64] else "non-senior management"
            status_val = (
                "1" if status_name == "permanent"
                else "3" if status_name == "contract"
                else "4"
            )
            department = staff_dept.department.department_name if staff_dept else "commercial"
            doh = staff.doh.strftime('%d%m%Y%H%M')
            nationality = "tanzania"
            promotion = supervisor.dos.strftime('%d%m%Y%H%M') if supervisor else None
            salary = salary_amount.amount if salary_amount else 0

            existing = EmployeeData.objects.using('legacy').filter(emplayee_identity_number=identity_number).first()

            if existing:
                # Compare all fields
                all_match = (
                    existing.branch_code == branch_code and
                    existing.emplayee_name == name and
                    existing.emplayee_gender == gender and
                    existing.emplayee_date_birth == dob and
                    existing.emplayee_identity_type == identity and
                    existing.emplayee_position == position and
                    existing.emplayee_position_category == position_category and
                    existing.emplayee_status == status_val and
                    existing.emplayee_department == department and
                    existing.emplayee_appointment_date == doh and
                    existing.emplayee_nationality == nationality and
                    existing.emplayee_last_promotion_date == promotion and
                    existing.emplayee_basic_salary == salary
                )
                if all_match:
                    print(f"Staff ID {staff.id}: identical — skipped")
                    continue  # all fields match, skip

            # Save new if not exists or fields differ
            new_record = EmployeeData.objects.using('legacy').create(
                reporting_date=reporting,
                branch_code=branch_code,
                emplayee_name=name,
                emplayee_gender=gender,
                emplayee_date_birth=dob,
                emplayee_identity_type=identity,
                emplayee_identity_number=identity_number,
                emplayee_position=position,
                emplayee_position_category=position_category,
                emplayee_status=status_val,
                emplayee_department=department,
                emplayee_appointment_date=doh,
                emplayee_nationality=nationality,
                emplayee_last_promotion_date=promotion,
                emplayee_basic_salary=salary,
                emplayee_benefit = senior_benefit if position_category == "senior management" else junior_benefit
            )
            saved_count += 1
            print(f"Staff ID {staff.id}: saved (new ID: {new_record.id})")

        return Response({"message": f"Successfully processed staff records. New records: {saved_count}"}, status=status.HTTP_200_OK)


#====================================================== kpi ====================================================
class kpiSearch(django_filters.FilterSet):

    class Meta:
        model = Kpi
        fields = {
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
    serializer_class = KpiSerializerExport
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = kpiSearch
    search_fields = ['code','name', 'year']
    ordering_fields = ['id','code','name']
    ordering = ['-id']



