from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.http.response import JsonResponse
from django.utils import timezone
import statistics

import json, decimal, ast
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

from payroll.models import *
from dictionary.models import DictionaryItem
from controller.models import SecurityFund,StaffSecurityFund
from payroll.serializers import *


#====================================================== calculation ====================================================
class dayFilter(django_filters.FilterSet):

    class Meta:
        model = CalculationDay
        fields = {
            'id': ['exact', 'in'],
            'code': ['exact', 'in'],
            'date': ['exact'],
            'is_active': ['exact']
        }

class CalculationDayAdd(CreateAPIView):

    serializer_class = CalculationSerializer

    def generate_calculation_code(self):
        count = CalculationDay.objects.count() + 1
        return f"{count:06d}"

    def post(self, request):
        serializer = CalculationSerializer(data=request.data)
        if serializer.is_valid():
            day = CalculationDay.objects.filter(is_active=True)
            if day:
                day.update(is_active=False)
            serializer.save(code=self.generate_calculation_code())
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CalculationDayList(ListAPIView):
    queryset = CalculationDay.objects.all()
    serializer_class = CalculationSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend,filters.SearchFilter,filters.OrderingFilter]
    filterset_class = dayFilter
    search_fields = ['code',]
    ordering_fields = ['id','code']
    ordering = ['-id']


#====================================================== payroll ====================================================
class staffSalaryFilter(django_filters.FilterSet):

    class Meta:
        model = StaffSalary
        fields = {'staff__id': ['exact', 'in'],'account_number': ['exact', 'in'],'tin_number': ['exact', 'in'],'is_active': ['exact']}


class StaffSalaryAdd(CreateAPIView):

    serializer_class = SalarySerializer

    def post(self, request):
        serializer = SalarySerializer(data=request.data, many=True)
        if serializer.is_valid():
            for x in serializer.validated_data:
                staff = x.get('staff')
                salary = StaffSalary.objects.filter(is_active=True, staff__id = staff.id)
                if salary:
                    salary.update(is_active=False)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StaffSalaryList(ListAPIView):
    queryset = StaffSalary.objects.all()
    serializer_class = SalaryListSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend,filters.SearchFilter,filters.OrderingFilter]
    filterset_class = staffSalaryFilter
    search_fields = ['code','staff__full_name','staff__staff_opf','account_number','tin_number']
    ordering_fields = ['id','code','staff__full_name','staff__staff_opf']
    ordering = ['-id']


class StaffSalaryUpdate(CreateAPIView):

    serializer_class = SalaryUpdateSerializer

    def get(self, request, pk):
        salary = StaffSalary.objects.get(id=pk)
        serializer = SalaryUpdateSerializer(salary, many=False)
        return Response(serializer.data, status=status.HTTP_200_OK)


    def put(self, request, pk):
        salary = StaffSalary.objects.get(id=pk)
        serializer = SalaryUpdateSerializer(salary, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#====================================================== organization ====================================================
class OrganizationAdd(CreateAPIView):

    serializer_class = OrganizationSerializer

    def post(self, request):
        serializer = OrganizationSerializer(data=request.data, many=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrganizationList(ListAPIView):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['code','name','account']
    ordering_fields = ['id','code','name','account']
    ordering = ['-id']


class OrganizationUpdate(CreateAPIView):

    serializer_class = OrganizationUpdateSerializer

    def put(self, request, pk):
        salary = Organization.objects.get(id=pk)
        serializer = OrganizationUpdateSerializer(salary, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrganizationDetail(APIView):

    serializer_class = OrganizationSerializer

    def get(self, request, pk):
        organization = Organization.objects.get(id=pk)
        serializer = OrganizationSerializer(organization, many=False)
        return JsonResponse(serializer.data, safe=False)

#====================================================== staff organization ====================================================
class staffOrganizationSearch(django_filters.FilterSet):

    class Meta:
        model = StaffOrganization
        fields = {'organization__id' : ['exact', 'in'], 'staff__id': ['exact', 'in'],'is_active': ['exact']}


class StaffOrganizationAdd(CreateAPIView):

    serializer_class = StaffOrganizationSerializer

    def post(self, request):
        serializer = StaffOrganizationSerializer(data=request.data, many=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StaffOrganizationList(ListAPIView):
    queryset = StaffOrganization.objects.all()
    serializer_class = StaffOrganizationListSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend,filters.SearchFilter,filters.OrderingFilter]
    filterset_class = staffOrganizationSearch
    search_fields = ['organization__code','organization__name','organization__account','staff__staff_opf']
    ordering_fields = ['id','organization__code','organization__name','organization__account','staff__staff_opf']
    ordering = ['-id']


class StaffOrganizationUpdate(CreateAPIView):

    serializer_class = StaffOrganizationUpdateSerializer

    def put(self, request, pk):
        salary = StaffOrganization.objects.get(id=pk)
        serializer = StaffOrganizationUpdateSerializer(salary, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#====================================================== allowance ====================================================
class allowanceSearch(django_filters.FilterSet):

    class Meta:
        model = Allowance
        fields = {'code' : ['exact', 'in'], 'name': ['exact', 'in'],'is_active': ['exact'],'is_repeated': ['exact']}


class AllowanceAdd(CreateAPIView):

    serializer_class = AllowanceSerializer

    def post(self, request):
        serializer = AllowanceSerializer(data=request.data, many=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AllowanceList(ListAPIView):
    queryset = Allowance.objects.all()
    serializer_class = AllowanceSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend,filters.SearchFilter,filters.OrderingFilter]
    filterset_class = allowanceSearch
    search_fields = ['code','name']
    ordering_fields = ['id','code','name']
    ordering = ['-id']


class AllowanceUpdate(CreateAPIView):

    serializer_class = AllowanceUpdateSerializer

    def put(self, request, pk):
        salary = Allowance.objects.get(id=pk)
        serializer = AllowanceUpdateSerializer(salary, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AllowanceDetail(APIView):

    serializer_class = AllowanceSerializer

    def get(self, request, pk):
        data = Allowance.objects.get(id=pk)
        serializer = AllowanceSerializer(data, many=False)
        return JsonResponse(serializer.data, safe=False)

#====================================================== deduction ====================================================
class DeductionAdd(CreateAPIView):

    serializer_class = DeductionSerializer

    def post(self, request):
        serializer = DeductionSerializer(data=request.data, many=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeductionList(ListAPIView):
    queryset = Deduction.objects.all()
    serializer_class = DeductionSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['code','name']
    ordering_fields = ['id','code','name']
    ordering = ['-id']


class DeductionUpdate(CreateAPIView):

    serializer_class = DeductionUpdateSerializer

    def put(self, request, pk):
        salary = Deduction.objects.get(id=pk)
        serializer = DeductionUpdateSerializer(salary, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeductionDetail(APIView):

    serializer_class = DeductionSerializer

    def get(self, request, pk):
        data = Deduction.objects.get(id=pk)
        serializer = DeductionSerializer(data, many=False)
        return JsonResponse(serializer.data, safe=False)

#====================================================== allowance ====================================================
class staffAllowanceSearch(django_filters.FilterSet):

    class Meta:
        model = StaffAllowance
        fields = {'allowance__id' : ['exact', 'in'], 'staff__id': ['exact', 'in'],'is_active': ['exact']}


class StaffAllowanceAdd(CreateAPIView):

    serializer_class = StaffAllowanceSerializer

    def post(self, request):
        serializer = StaffAllowanceSerializer(data=request.data, many=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StaffAllowanceList(ListAPIView):
    queryset = StaffAllowance.objects.all()
    serializer_class = StaffAllowanceListSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend,filters.SearchFilter,filters.OrderingFilter]
    filterset_class = staffAllowanceSearch
    search_fields = ['allowance__code','allowance__name','staff__staff_opf']
    ordering_fields = ['id','allowance__code','allowance__name','staff__staff_opf']
    ordering = ['-id']


class StaffAllowanceUpdate(CreateAPIView):

    serializer_class = StaffAllowanceUpdateSerializer

    def put(self, request, pk):
        salary = StaffAllowance.objects.get(id=pk)
        serializer = StaffAllowanceUpdateSerializer(salary, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#====================================================== deduction ====================================================
class staffDeductionSearch(django_filters.FilterSet):

    class Meta:
        model = StaffDeduction
        fields = {'deduction__id' : ['exact', 'in'], 'staff__id': ['exact', 'in'],'is_active': ['exact']}


class StaffDeductionAdd(CreateAPIView):

    serializer_class = StaffDeductionSerializer

    def post(self, request):
        serializer = StaffDeductionSerializer(data=request.data, many=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StaffDeductionList(ListAPIView):
    queryset = StaffDeduction.objects.all()
    serializer_class = StaffDeductionListSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend,filters.SearchFilter,filters.OrderingFilter]
    filterset_class = staffDeductionSearch
    search_fields = ['deduction__code','deduction__name','staff__staff_opf']
    ordering_fields = ['id','deduction__code','deduction__name','staff__staff_opf']
    ordering = ['-id']


class StaffDeductionUpdate(CreateAPIView):

    serializer_class = StaffDeductionUpdateSerializer

    def put(self, request, pk):
        salary = StaffDeduction.objects.get(id=pk)
        serializer = StaffDeductionUpdateSerializer(salary, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#====================================================== deduction ====================================================
class PayeeDeductionAdd(CreateAPIView):

    serializer_class = PayeeDeductionSerializer

    def post(self, request):
        serializer = PayeeDeductionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PayeeDeductionList(ListAPIView):
    queryset = PayeeDeduction.objects.all()
    serializer_class = PayeeDeductionListSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['range_percentage','upper_range','lower_range']
    ordering_fields = ['id','range_percentage','upper_range','lower_range']
    ordering = ['id']


class PayeeDeductionUpdate(CreateAPIView):

    serializer_class = PayeeDeductionUpdateSerializer

    def put(self, request, pk):
        salary = PayeeDeduction.objects.get(id=pk)
        serializer = PayeeDeductionUpdateSerializer(salary, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#====================================================== deduction ====================================================
class SecurityFundAdd(CreateAPIView):

    serializer_class = SecurityFundSerializer

    def post(self, request):
        serializer = SecurityFundSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SecurityFundList(ListAPIView):
    queryset = SecurityFund.objects.all()
    serializer_class = SecurityFundSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['code','name']
    ordering_fields = ['id','code','name']
    ordering = ['id']


class SecurityFundUpdate(CreateAPIView):

    serializer_class = SecurityFundUpdateSerializer

    def put(self, request, pk):
        salary = SecurityFund.objects.get(id=pk)
        serializer = SecurityFundUpdateSerializer(salary, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SecurityFundDetail(APIView):

    serializer_class = SecurityFundSerializer

    def get(self, request, pk):
        data = SecurityFund.objects.get(id=pk)
        serializer = SecurityFundSerializer(data, many=False)
        return JsonResponse(serializer.data, safe=False)

#====================================================== allowance ====================================================
class monthAllowanceSearch(django_filters.FilterSet):

    class Meta:
        model = MonthlyAllowance
        fields = {'staff__id' : ['exact', 'in'],'month': ['exact', 'in'], 'month_consumed': ['exact', 'in'], 'date': ['range'],'year': ['exact', 'in'],'is_active': ['exact']}


class MonthlyAllowanceAdd(CreateAPIView):

    serializer_class = MonthlyAllowanceSerializer

    def post(self, request):
        serializer = MonthlyAllowanceSerializer(data=request.data, many=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MonthlyAllowanceList(ListAPIView):
    queryset = MonthlyAllowance.objects.all()
    serializer_class = MonthlyAllowanceListSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend,filters.SearchFilter,filters.OrderingFilter]
    filterset_class = monthAllowanceSearch
    search_fields = ['allowance__code','allowance__name','staff__staff_opf']
    ordering_fields = ['id','allowance__code','allowance__name','staff__staff_opf','date']
    ordering = ['-id']


class MonthlyAllowanceUpdate(CreateAPIView):

    serializer_class = MonthlyAllowanceUpdateSerializer

    def put(self, request, pk):
        salary = MonthlyAllowance.objects.get(id=pk)
        serializer = MonthlyAllowanceUpdateSerializer(salary, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MonthlyAllowanceDelete(APIView):
    def delete(self, request, *args, **kwargs):
        ids = request.data.get("ids", [])

        if not isinstance(ids, list) or not ids:
            return Response(
                {"detail": "A non-empty list of IDs is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        deleted_count, _ = MonthlyAllowance.objects.filter(id__in=ids, is_active=True).delete()

        return Response(
            {"detail": f"{deleted_count} record(s) deleted."},
            status=status.HTTP_204_NO_CONTENT
        )

#====================================================== deduction ====================================================
class monthDeductionSearch(django_filters.FilterSet):

    class Meta:
        model = MonthlyDeduction
        fields = {'staff__id' : ['exact', 'in'],'month': ['exact', 'in'], 'month_consumed': ['exact', 'in'], 'date': ['range'],'year': ['exact', 'in'],'is_active': ['exact']}

class MonthlyDeductionAdd(CreateAPIView):

    serializer_class = MonthlyDeductionSerializer

    def post(self, request):
        serializer = MonthlyDeductionSerializer(data=request.data, many=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MonthlyDeductionList(ListAPIView):
    queryset = MonthlyDeduction.objects.all()
    serializer_class = MonthlyDeductionListSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend,filters.SearchFilter,filters.OrderingFilter]
    filterset_class = monthDeductionSearch
    search_fields = ['deduction__code','deduction__name','staff__staff_opf']
    ordering_fields = ['id','deduction__code','deduction__name','staff__staff_opf','date']
    ordering = ['-id']


class MonthlyDeductionUpdate(CreateAPIView):

    serializer_class = MonthlyDeductionUpdateSerializer

    def put(self, request, pk):
        salary = MonthlyDeduction.objects.get(id=pk)
        serializer = MonthlyDeductionUpdateSerializer(salary, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class MonthlyDeductionDelete(APIView):
    def delete(self, request, *args, **kwargs):
        ids = request.data.get("ids", [])

        if not isinstance(ids, list) or not ids:
            return Response(
                {"detail": "A non-empty list of IDs is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        deleted_count, _ = MonthlyDeduction.objects.filter(id__in=ids, is_active=True).delete()

        return Response(
            {"detail": f"{deleted_count} record(s) deleted."},
            status=status.HTTP_204_NO_CONTENT
        )


#====================================================== deduction ====================================================
class payrollSearch(django_filters.FilterSet):

    class Meta:
        model = Payroll
        fields = {'month': ['exact', 'in'], 'year': ['exact', 'in'],'is_canceled': ['exact']}

class PayrollAdd(CreateAPIView):

    serializer_class = PayrollSerializer

    def post(self, request):
        serializer = PayrollSerializer(data=request.data)
        if serializer.is_valid():
            MonthlyAllowance.objects.filter(is_active=True,month_consumed=0, month=datetime.date.today().month, year=datetime.date.today().year).update(month_consumed=datetime.date.today().month, is_active=False)
            MonthlyDeduction.objects.filter(is_active=True,month_consumed=0, month=datetime.date.today().month, year=datetime.date.today().year).update(month_consumed=datetime.date.today().month, is_active=False)
            
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PayrollList(ListAPIView):
    queryset = Payroll.objects.all()
    serializer_class = PayrollSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend,filters.SearchFilter,filters.OrderingFilter]
    filterset_class = payrollSearch
    search_fields = ['code','month','year']
    ordering_fields = ['id','code','month','year']
    ordering = ['-id']


class PayrollUpdate(CreateAPIView):

    serializer_class = PayrollUpdateSerializer

    def put(self, request, pk):
        salary = Payroll.objects.get(id=pk)
        serializer = PayrollUpdateSerializer(salary, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PayrollDetail(APIView):

    serializer_class = PayrollSerializer

    def get(self, request, pk):
        data = Payroll.objects.get(id=pk)
        serializer = PayrollSerializer(data, many=False)
        return JsonResponse(serializer.data, safe=False)


class PayrollFreeze(APIView):

    def post(self, request):
        MonthlyAllowance.objects.filter(is_active=True,month_consumed=0, month=datetime.date.today().month, year=datetime.date.today().year).update(month_consumed=datetime.date.today().month, is_active=False)
        MonthlyDeduction.objects.filter(is_active=True,month_consumed=0, month=datetime.date.today().month, year=datetime.date.today().year).update(month_consumed=datetime.date.today().month, is_active=False)
        return Response("done", status=status.HTTP_200_OK)


class GeneratePayroll(APIView):
    def get(self, request):
        param_list = request.query_params.get('staff_ids', '')
        # id_list = ast.literal_eval(param_list)
        id_list = [int(id) for id in param_list.split(',') if id.isdigit()]
        if id_list:
            # print(id_list)
            staff_ids = Staff.objects.filter(is_active=True, id__in=id_list).values('id','full_name','staff_opf','code')
        else:
            staff_ids = Staff.objects.filter(is_active=True).values('id','full_name','staff_opf','code')
        
        payroll_data = []
        variable_values = {}
        for staff_id in staff_ids:
            staff = Staff.objects.get(id=staff_id['id'])
            staff_salaries = StaffSalary.objects.filter(staff=staff, is_active=True)
            staff_allowances = MonthlyAllowance.objects.filter(staff=staff, month_consumed=datetime.date.today().month, year=datetime.date.today().year)
            staff_deductions = MonthlyDeduction.objects.filter(staff=staff, month_consumed=datetime.date.today().month, year=datetime.date.today().year)
            staff_allowances1 = MonthlyAllowance.objects.filter(staff=staff, is_active=True)
            staff_deductions1 = MonthlyDeduction.objects.filter(staff=staff, is_active=True)
            staff_funds = StaffSecurityFund.objects.filter(staff=staff, is_active=True)
            staff_helths = HelthDeduction.objects.filter(is_active=True)
            paye_ranges = PayeeDeduction.objects.filter(is_active=True)
            helth_fund = PayeeDeduction.objects.filter(is_active=True)

            payrollData = {}

            variables = PayrollVariable.objects.all()
            formula = PayrollFormula.objects.filter(is_active=True).order_by('id')
            for vr in variables:
                variable_values[vr.name]=0
            for fr in formula:
                payrollData[fr.code] = 0
            for fr in formula:
                if staff_salaries:
                    staff_salary = StaffSalary.objects.get(staff=staff, is_active=True)
                    variable_values['basic_salary'] = float(staff_salary.amount)
                    payrollData['basic_salary'] = float(staff_salary.amount)
                else:
                    variable_values['basic_salary'] = float(0)
                    payrollData['basic_salary'] = float(0)
                
                if staff_allowances:
                    variable_values['allowance'] = float(sum(allowance.amount for allowance in staff_allowances))
                    payrollData['allowance'] = float(sum(allowance.amount for allowance in staff_allowances))
                else:
                    variable_values['allowance'] = float(sum(allowance.amount for allowance in staff_allowances1))
                    payrollData['allowance'] = float(sum(allowance.amount for allowance in staff_allowances1))

                if staff_deductions:
                    variable_values['deduction'] = float(sum(deduction.amount for deduction in staff_deductions))
                    payrollData['deduction'] = float(sum(deduction.amount for deduction in staff_deductions))
                else:
                    variable_values['deduction'] = float(sum(deduction.amount for deduction in staff_deductions1))
                    payrollData['deduction'] = float(sum(deduction.amount for deduction in staff_deductions1))

                if staff_helths:
                    helth = HelthDeduction.objects.get(is_active=True)
                    variable_values['helth_percentage'] = float(helth.percentage)
                
                if staff_funds:
                    staff_fund = StaffSecurityFund.objects.get(staff=staff, is_active=True)
                    fund = SecurityFundDeduction.objects.get(is_active=True, fund=staff_fund.fund)
                    variable_values['pension_percentage'] = float(fund.percentage)
                else:
                    variable_values['pension_percentage'] = float(0)
                payrollData[fr.code] = 0

                payrollData[fr.code] =  self.evaluate_formula(fr.expression, variable_values)


                if fr.code in payrollData:
                    gross = payrollData['gross_salary']
                    security = payrollData['security_fund']
                    helth = payrollData['helth_fund']
                    paye_range = self.find_applicable_paye_range((gross - (security - helth)), paye_ranges)
                    variable_values['payee_lower_range'] = float(paye_range['lower_range'])
                    variable_values['payee_percentage'] = float(paye_range['range_percentage'])
                    variable_values['payee_initial_amount'] = float(paye_range['initia_amount'])
                    payrollData[fr.code] =  self.evaluate_formula(fr.expression, variable_values)

            payroll_data.append({'staff_data': staff_id, 'payroll':payrollData})

        return Response({'payrollData': payroll_data})


    def find_applicable_paye_range(self, remaining_amount, paye_ranges):
        """
        Find the applicable PAYE range based on the remaining amount.
        """
        for paye_range in paye_ranges:
            # print(paye_range)
            if paye_range.lower_range <= remaining_amount < paye_range.upper_range:
                return {"lower_range":paye_range.lower_range, "initia_amount": paye_range.initia_amount, "range_percentage": round(decimal.Decimal(paye_range.range_percentage),2)}

        return None

    def evaluate_formula(self, expression, variables):
        """
        Evaluate a formula expression using Python's eval.
        """
        return round((eval(expression, variables)),2)

#====================================================== deduction ====================================================
class staffPayrollSearch(django_filters.FilterSet):

    class Meta:
        model = StaffPayroll
        fields = {'payroll__id' : ['exact', 'in'], 'staff__id': ['exact', 'in'],'year': ['exact','in'],'month': ['exact','in']}

class StaffPayrollAdd(CreateAPIView):

    serializer_class = StaffPayrollSerializer

    def post(self, request):
        serializer = StaffPayrollSerializer(data=request.data, many=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StaffPayrollList(ListAPIView):
    queryset = StaffPayroll.objects.all()
    serializer_class = StaffPayrollListSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend,filters.SearchFilter,filters.OrderingFilter]
    filterset_class = staffPayrollSearch
    search_fields = ['payroll__code','payroll__month','staff__staff_opf','staff__full_name']
    ordering_fields = ['id','payroll__code','payroll__month','staff__staff_opf','staff__full_name']
    ordering = ['-id']


class StaffPayrollUpdate(CreateAPIView):

    serializer_class = StaffPayrollUpdateSerializer

    def put(self, request, pk):
        salary = StaffPayroll.objects.get(id=pk)
        serializer = StaffPayrollUpdateSerializer(salary, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#====================================================== deduction ====================================================
class PayrollFormulaAdd(CreateAPIView):

    serializer_class = PayrollFormulaSerializer

    def post(self, request):
        serializer = PayrollFormulaSerializer(data=request.data)
        if serializer.is_valid():
            code = serializer.validated_data.get('code')
            formula = PayrollFormula.objects.filter(code=code, is_active=True)
            if formula:
                formula.update(is_active=False)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PayrollFormulaList(ListAPIView):
    queryset = PayrollFormula.objects.all()
    serializer_class = PayrollFormulaSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['code','name']
    ordering_fields = ['id','code','name']
    ordering = ['-id']


#====================================================== deduction ====================================================
class PayrollVariableAdd(CreateAPIView):

    serializer_class = PayrollVariableSerializer

    def post(self, request):
        serializer = PayrollVariableSerializer(data=request.data, many=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PayrollVariableList(ListAPIView):
    queryset = PayrollVariable.objects.all()
    serializer_class = PayrollVariableSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['code','name']
    ordering_fields = ['id','code','name']
    ordering = ['code']