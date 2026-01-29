from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.http.response import JsonResponse
from django.utils import timezone
from django.db import transaction
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
from django_filters import DateRangeFilter, DateFilter
import io, csv, pandas as pd
from rest_framework.parsers import MultiPartParser

from payroll.models import *
from dictionary.models import DictionaryItem
from controller.models import SecurityFund, StaffSecurityFund
from payroll.serializers import *


# ====================================================== calculation ====================================================
class dayFilter(django_filters.FilterSet):

    class Meta:
        model = CalculationDay
        fields = {
            "id": ["exact", "in"],
            "code": ["exact", "in"],
            "date": ["exact"],
            "is_active": ["exact"],
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
    filter_backends = [
        django_filters.rest_framework.DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = dayFilter
    search_fields = [
        "code",
    ]
    ordering_fields = ["id", "code"]
    ordering = ["-id"]


# ====================================================== payroll ====================================================
class staffSalaryFilter(django_filters.FilterSet):

    class Meta:
        model = StaffSalary
        fields = {
            "staff__id": ["exact", "in"],
            "account_number": ["exact", "in"],
            "tin_number": ["exact", "in"],
            "is_active": ["exact"],
        }


class StaffSalaryAdd(CreateAPIView):
    serializer_class = SalarySerializer

    def post(self, request):
        serializer = SalarySerializer(data=request.data, many=True)
        if serializer.is_valid():
            try:
                with transaction.atomic():  # start atomic transaction
                    for x in serializer.validated_data:
                        staff = x.get("staff")
                        salary = StaffSalary.objects.filter(
                            is_active=True, staff__id=staff.id
                        )
                        if salary.exists():
                            salary.update(is_active=False)
                    serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StaffSalaryList(ListAPIView):
    queryset = StaffSalary.objects.all()
    serializer_class = SalaryListSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [
        django_filters.rest_framework.DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = staffSalaryFilter
    search_fields = [
        "code",
        "staff__full_name",
        "staff__staff_opf",
        "account_number",
        "tin_number",
    ]
    ordering_fields = ["id", "code", "staff__full_name", "staff__staff_opf"]
    ordering = ["-id"]


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


# ====================================================== organization ====================================================
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
    search_fields = ["code", "name", "account"]
    ordering_fields = ["id", "code", "name", "account"]
    ordering = ["-id"]


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


# ====================================================== staff organization ====================================================
class staffOrganizationSearch(django_filters.FilterSet):

    class Meta:
        model = StaffOrganization
        fields = {
            "organization__id": ["exact", "in"],
            "staff__id": ["exact", "in"],
            "is_active": ["exact"],
        }


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
    filter_backends = [
        django_filters.rest_framework.DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = staffOrganizationSearch
    search_fields = [
        "organization__code",
        "organization__name",
        "organization__account",
        "staff__staff_opf",
    ]
    ordering_fields = [
        "id",
        "organization__code",
        "organization__name",
        "organization__account",
        "staff__staff_opf",
    ]
    ordering = ["-id"]


class StaffOrganizationUpdate(CreateAPIView):

    serializer_class = StaffOrganizationUpdateSerializer

    def put(self, request, pk):
        salary = StaffOrganization.objects.get(id=pk)
        serializer = StaffOrganizationUpdateSerializer(salary, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ====================================================== allowance ====================================================
class allowanceSearch(django_filters.FilterSet):

    class Meta:
        model = Allowance
        fields = {
            "code": ["exact", "in"],
            "name": ["exact", "in"],
            "is_active": ["exact"],
            "is_repeated": ["exact"],
        }


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
    filter_backends = [
        django_filters.rest_framework.DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = allowanceSearch
    search_fields = ["code", "name"]
    ordering_fields = ["id", "code", "name"]
    ordering = ["-id"]


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


# ====================================================== deduction ====================================================
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
    search_fields = ["code", "name"]
    ordering_fields = ["id", "code", "name"]
    ordering = ["-id"]


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


# ====================================================== allowance ====================================================
class staffAllowanceSearch(django_filters.FilterSet):

    class Meta:
        model = StaffAllowance
        fields = {
            "allowance__id": ["exact", "in"],
            "staff__id": ["exact", "in"],
            "is_active": ["exact"],
        }


class StaffAllowanceAdd(CreateAPIView):
    serializer_class = StaffAllowanceSerializer

    def post(self, request):
        serializer = StaffAllowanceSerializer(data=request.data, many=True)
        if serializer.is_valid():
            try:
                with transaction.atomic():  # start atomic transaction
                    for x in serializer.validated_data:
                        staff = x.get("staff")
                        StaffAllowance.objects.filter(
                            is_active=True, staff__id=staff.id
                        ).update(is_active=False)
                    serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StaffAllowanceList(ListAPIView):
    queryset = StaffAllowance.objects.all()
    serializer_class = StaffAllowanceListSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [
        django_filters.rest_framework.DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = staffAllowanceSearch
    search_fields = ["allowance__code", "allowance__name", "staff__staff_opf"]
    ordering_fields = ["id", "allowance__code", "allowance__name", "staff__staff_opf"]
    ordering = ["-id"]


class StaffAllowanceUpdate(CreateAPIView):

    serializer_class = StaffAllowanceUpdateSerializer

    def put(self, request, pk):
        salary = StaffAllowance.objects.get(id=pk)
        serializer = StaffAllowanceUpdateSerializer(salary, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ====================================================== deduction ====================================================
class staffDeductionSearch(django_filters.FilterSet):

    class Meta:
        model = StaffDeduction
        fields = {
            "deduction__id": ["exact", "in"],
            "staff__id": ["exact", "in"],
            "is_active": ["exact"],
        }


class StaffDeductionAdd(CreateAPIView):
    serializer_class = StaffDeductionSerializer

    def post(self, request):
        serializer = StaffDeductionSerializer(data=request.data, many=True)
        if serializer.is_valid():
            try:
                with transaction.atomic():  # atomic transaction
                    for x in serializer.validated_data:
                        staff = x.get("staff")
                        StaffDeduction.objects.filter(
                            is_active=True, staff__id=staff.id
                        ).update(is_active=False)
                    serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StaffDeductionList(ListAPIView):
    queryset = StaffDeduction.objects.all()
    serializer_class = StaffDeductionListSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [
        django_filters.rest_framework.DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = staffDeductionSearch
    search_fields = ["deduction__code", "deduction__name", "staff__staff_opf"]
    ordering_fields = ["id", "deduction__code", "deduction__name", "staff__staff_opf"]
    ordering = ["-id"]


class StaffDeductionUpdate(CreateAPIView):

    serializer_class = StaffDeductionUpdateSerializer

    def put(self, request, pk):
        salary = StaffDeduction.objects.get(id=pk)
        serializer = StaffDeductionUpdateSerializer(salary, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ====================================================== deduction ====================================================
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
    search_fields = ["range_percentage", "upper_range", "lower_range"]
    ordering_fields = ["id", "range_percentage", "upper_range", "lower_range"]
    ordering = ["id"]


class PayeeDeductionUpdate(CreateAPIView):

    serializer_class = PayeeDeductionUpdateSerializer

    def put(self, request, pk):
        salary = PayeeDeduction.objects.get(id=pk)
        serializer = PayeeDeductionUpdateSerializer(salary, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ====================================================== deduction ====================================================
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
    search_fields = ["code", "name"]
    ordering_fields = ["id", "code", "name"]
    ordering = ["id"]


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


# ====================================================== allowance ====================================================
class monthAllowanceSearch(django_filters.FilterSet):

    class Meta:
        model = MonthlyAllowance
        fields = {
            "staff__id": ["exact", "in"],
            "month": ["exact", "in"],
            "month_consumed": ["exact", "in"],
            "date": ["range"],
            "year": ["exact", "in"],
            "is_active": ["exact"],
        }


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
    filter_backends = [
        django_filters.rest_framework.DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = monthAllowanceSearch
    search_fields = ["allowance__code", "allowance__name", "staff__staff_opf"]
    ordering_fields = [
        "id",
        "allowance__code",
        "allowance__name",
        "staff__staff_opf",
        "date",
    ]
    ordering = ["-id"]


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
                status=status.HTTP_400_BAD_REQUEST,
            )

        deleted_count, _ = MonthlyAllowance.objects.filter(
            id__in=ids, is_active=True
        ).delete()

        return Response(
            {"detail": f"{deleted_count} record(s) deleted."},
            status=status.HTTP_204_NO_CONTENT,
        )


# ====================================================== deduction ====================================================
class monthDeductionSearch(django_filters.FilterSet):

    class Meta:
        model = MonthlyDeduction
        fields = {
            "staff__id": ["exact", "in"],
            "staff__staff_opf": ["exact", "icontains"],
            "month": ["exact", "in"],
            "month_consumed": ["exact", "in"],
            "date": ["range"],
            "year": ["exact", "in"],
            "is_active": ["exact"],
        }


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
    filter_backends = [
        django_filters.rest_framework.DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = monthDeductionSearch
    search_fields = ["deduction__code", "deduction__name", "staff__staff_opf"]
    ordering_fields = [
        "id",
        "deduction__code",
        "deduction__name",
        "staff__staff_opf",
        "date",
    ]
    ordering = ["-id"]


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
                status=status.HTTP_400_BAD_REQUEST,
            )

        deleted_count, _ = MonthlyDeduction.objects.filter(
            id__in=ids, is_active=True
        ).delete()

        return Response(
            {"detail": f"{deleted_count} record(s) deleted."},
            status=status.HTTP_204_NO_CONTENT,
        )


# ====================================================== deduction ====================================================
class payrollSearch(django_filters.FilterSet):

    class Meta:
        model = Payroll
        fields = {
            "month": ["exact", "in"],
            "year": ["exact", "in"],
            "is_canceled": ["exact"],
        }


class PayrollAdd(CreateAPIView):

    serializer_class = PayrollSerializer

    def post(self, request):
        serializer = PayrollSerializer(data=request.data)
        if serializer.is_valid():
            MonthlyAllowance.objects.filter(
                is_active=True,
                month_consumed=0,
                month=datetime.date.today().month,
                year=datetime.date.today().year,
            ).update(month_consumed=datetime.date.today().month, is_active=False)
            MonthlyDeduction.objects.filter(
                is_active=True,
                month_consumed=0,
                month=datetime.date.today().month,
                year=datetime.date.today().year,
            ).update(month_consumed=datetime.date.today().month, is_active=False)

            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PayrollList(ListAPIView):
    queryset = Payroll.objects.all()
    serializer_class = PayrollSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [
        django_filters.rest_framework.DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = payrollSearch
    search_fields = ["code", "month", "year"]
    ordering_fields = ["id", "code", "month", "year"]
    ordering = ["-id"]


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
        MonthlyAllowance.objects.filter(
            is_active=True,
            month_consumed=0,
            month=datetime.date.today().month,
            year=datetime.date.today().year,
        ).update(month_consumed=datetime.date.today().month, is_active=False)
        MonthlyDeduction.objects.filter(
            is_active=True,
            month_consumed=0,
            month=datetime.date.today().month,
            year=datetime.date.today().year,
        ).update(month_consumed=datetime.date.today().month, is_active=False)
        return Response("done", status=status.HTTP_200_OK)


# class GeneratePayroll(APIView):
#     def get(self, request):
#         with transaction.atomic():
#             param_list = request.query_params.get("staff_ids", "")
#             # id_list = ast.literal_eval(param_list)
#             id_list = [int(id) for id in param_list.split(",") if id.isdigit()]
#             if id_list:
#                 # print(id_list)
#                 staff_ids = Staff.objects.filter(
#                     is_active=True, id__in=id_list, staffsalary__is_active=True
#                 ).values("id", "full_name", "staff_opf", "code")
#             else:
#                 staff_ids = Staff.objects.filter(
#                     is_active=True, staffsalary__is_active=True
#                 ).values("id", "full_name", "staff_opf", "code")

#             payroll_data = []
#             variable_values = {}
#             for staff_id in staff_ids:
#                 staff = Staff.objects.get(id=staff_id["id"])
#                 staff_salaries = StaffSalary.objects.filter(staff=staff, is_active=True)
#                 staff_allowances = MonthlyAllowance.objects.filter(
#                     staff=staff,
#                     month_consumed=datetime.date.today().month,
#                     year=datetime.date.today().year,
#                 )
#                 staff_deductions = MonthlyDeduction.objects.filter(
#                     staff=staff,
#                     month_consumed=datetime.date.today().month,
#                     year=datetime.date.today().year,
#                 )
#                 staff_allowances1 = MonthlyAllowance.objects.filter(
#                     staff=staff, is_active=True
#                 )
#                 staff_deductions1 = MonthlyDeduction.objects.filter(
#                     staff=staff, is_active=True
#                 )
#                 staff_funds = StaffSecurityFund.objects.filter(
#                     staff=staff, is_active=True
#                 )
#                 staff_helths = HelthDeduction.objects.filter(is_active=True)
#                 paye_ranges = PayeeDeduction.objects.filter(is_active=True)
#                 helth_fund = PayeeDeduction.objects.filter(is_active=True)

#                 payrollData = {}

#                 variables = PayrollVariable.objects.all()
#                 formula = PayrollFormula.objects.filter(is_active=True).order_by("id")
#                 for vr in variables:
#                     variable_values[vr.name] = 0
#                 for fr in formula:
#                     payrollData[fr.code] = 0
#                 for fr in formula:
#                     if staff_salaries:
#                         staff_salary = StaffSalary.objects.get(
#                             staff=staff, is_active=True
#                         )
#                         variable_values["basic_salary"] = float(staff_salary.amount)
#                         payrollData["basic_salary"] = float(staff_salary.amount)
#                     else:
#                         variable_values["basic_salary"] = float(0)
#                         payrollData["basic_salary"] = float(0)

#                     if staff_allowances:
#                         variable_values["allowance"] = float(
#                             sum(allowance.amount for allowance in staff_allowances)
#                         )
#                         payrollData["allowance"] = float(
#                             sum(allowance.amount for allowance in staff_allowances)
#                         )
#                     else:
#                         variable_values["allowance"] = float(
#                             sum(allowance.amount for allowance in staff_allowances1)
#                         )
#                         payrollData["allowance"] = float(
#                             sum(allowance.amount for allowance in staff_allowances1)
#                         )

#                     if staff_deductions:
#                         variable_values["deduction"] = float(
#                             sum(deduction.amount for deduction in staff_deductions)
#                         )
#                         payrollData["deduction"] = float(
#                             sum(deduction.amount for deduction in staff_deductions)
#                         )
#                     else:
#                         variable_values["deduction"] = float(
#                             sum(deduction.amount for deduction in staff_deductions1)
#                         )
#                         payrollData["deduction"] = float(
#                             sum(deduction.amount for deduction in staff_deductions1)
#                         )

#                     if staff_helths:
#                         helth = HelthDeduction.objects.get(is_active=True)
#                         variable_values["helth_percentage"] = float(helth.percentage)

#                     if staff_funds:
#                         staff_fund = StaffSecurityFund.objects.get(
#                             staff=staff, is_active=True
#                         )
#                         fund = SecurityFundDeduction.objects.get(
#                             is_active=True, fund=staff_fund.fund
#                         )
#                         variable_values["pension_percentage"] = float(fund.percentage)
#                     else:
#                         variable_values["pension_percentage"] = float(0)
#                     payrollData[fr.code] = 0

#                     payrollData[fr.code] = self.evaluate_formula(
#                         fr.expression, variable_values
#                     )

#                     if fr.code in payrollData:
#                         gross = payrollData["gross_salary"]
#                         security = payrollData["security_fund"]
#                         helth = payrollData["helth_fund"]
#                         paye_range = self.find_applicable_paye_range(
#                             (gross - (security - helth)), paye_ranges
#                         )
#                         variable_values["payee_lower_range"] = float(
#                             paye_range["lower_range"]
#                         )
#                         variable_values["payee_percentage"] = float(
#                             paye_range["range_percentage"]
#                         )
#                         variable_values["payee_initial_amount"] = float(
#                             paye_range["initia_amount"]
#                         )
#                         payrollData[fr.code] = self.evaluate_formula(
#                             fr.expression, variable_values
#                         )

#                 payroll_data.append({"staff_data": staff_id, "payroll": payrollData})

#             return Response({"payrollData": payroll_data})

#     def find_applicable_paye_range(self, remaining_amount, paye_ranges):
#         """
#         Find the applicable PAYE range based on the remaining amount.
#         """
#         for paye_range in paye_ranges:
#             # print(paye_range)
#             if paye_range.lower_range <= remaining_amount < paye_range.upper_range:
#                 return {
#                     "lower_range": paye_range.lower_range,
#                     "initia_amount": paye_range.initia_amount,
#                     "range_percentage": round(
#                         decimal.Decimal(paye_range.range_percentage), 2
#                     ),
#                 }

#         return None

#     def evaluate_formula(self, expression, variables):
#         """
#         Evaluate a formula expression using Python's eval.
#         """
#         return round((eval(expression, variables)), 2)


class GeneratePayroll(APIView):
    def get(self, request):
        today = datetime.date.today()
        month = today.month
        year = today.year

        param_list = request.query_params.get("staff_ids", "")
        id_list = [int(i) for i in param_list.split(",") if i.isdigit()]

        with transaction.atomic():
            # 1. SETUP PREFETCHES (Prevents N+1 Query Slowness)
            salary_prefetch = Prefetch(
                "staffsalary_set",
                queryset=StaffSalary.objects.filter(is_active=True, amount__gt=0),
                to_attr="active_salaries",
            )
            allowance_prefetch = Prefetch(
                "monthlyallowance_set",
                queryset=MonthlyAllowance.objects.filter(is_active=True),
                to_attr="all_allowances",
            )
            deduction_prefetch = Prefetch(
                "monthlydeduction_set",
                queryset=MonthlyDeduction.objects.filter(is_active=True),
                to_attr="all_deductions",
            )
            fund_prefetch = Prefetch(
                "staffsecurityfund_set",
                queryset=StaffSecurityFund.objects.filter(is_active=True),
                to_attr="active_funds",
            )

            # 2. OPTIMIZED QUERY
            staff_qs = (
                Staff.objects.filter(
                    is_active=True,
                    staffsalary__is_active=True,
                    staffsalary__amount__gt=0,
                )
                .prefetch_related(
                    salary_prefetch,
                    allowance_prefetch,
                    deduction_prefetch,
                    fund_prefetch,
                )
                .distinct()
                .order_by("staff_opf")
            )

            if id_list:
                staff_qs = staff_qs.filter(id__in=id_list)

            # 3. CACHE GLOBAL DATA (Fetched once, used for all staff)
            payroll_variables = list(PayrollVariable.objects.all())
            payroll_formulas = list(
                PayrollFormula.objects.filter(is_active=True).order_by("id")
            )
            paye_ranges = list(PayeeDeduction.objects.filter(is_active=True))
            helth_deduction = HelthDeduction.objects.filter(is_active=True).first()
            security_funds = {
                sf.fund_id: sf
                for sf in SecurityFundDeduction.objects.filter(is_active=True)
            }

            payroll_data = []

            # 4. PROCESS DATA IN MEMORY
            for staff in staff_qs:
                # Basic container for math context
                variable_values = {
                    v.name: decimal.Decimal("0.00") for v in payroll_variables
                }
                # Final results dictionary that goes to Frontend
                payroll_result = {
                    f.code: decimal.Decimal("0.00") for f in payroll_formulas
                }

                # --- Salary ---
                salary = staff.active_salaries[0] if staff.active_salaries else None
                basic_salary = salary.amount if salary else decimal.Decimal("0.00")
                variable_values["basic_salary"] = basic_salary
                payroll_result["basic_salary"] = basic_salary  # <-- ADDED FOR OUTPUT

                # --- Allowances ---
                curr_allowances = [
                    a.amount
                    for a in staff.all_allowances
                    if a.month_consumed == month and a.year == year
                ]
                if not curr_allowances:
                    curr_allowances = [
                        a.amount for a in staff.all_allowances if a.is_active
                    ]

                allowance_total = sum(curr_allowances)
                variable_values["allowance"] = allowance_total
                payroll_result["allowance"] = allowance_total  # <-- ADDED FOR OUTPUT

                # --- Deductions ---
                curr_deductions = [
                    d.amount
                    for d in staff.all_deductions
                    if d.month_consumed == month and d.year == year
                ]
                if not curr_deductions:
                    curr_deductions = [
                        d.amount for d in staff.all_deductions if d.is_active
                    ]

                deduction_total = sum(curr_deductions)
                variable_values["deduction"] = deduction_total
                payroll_result["deduction"] = deduction_total  # <-- ADDED FOR OUTPUT

                # --- Health & Pension ---
                h_perc = helth_deduction.percentage if helth_deduction else 0
                variable_values["helth_percentage"] = h_perc
                payroll_result["helth_percentage"] = h_perc  # <-- ADDED FOR OUTPUT

                staff_fund = staff.active_funds[0] if staff.active_funds else None
                if staff_fund and staff_fund.fund_id in security_funds:
                    p_perc = security_funds[staff_fund.fund_id].percentage
                else:
                    p_perc = 0

                variable_values["pension_percentage"] = p_perc
                payroll_result["pension_percentage"] = p_perc  # <-- ADDED FOR OUTPUT

                # --- Formula Calculation: Pass 1 ---
                for formula in payroll_formulas:
                    res = self.evaluate_formula(formula.expression, variable_values)
                    payroll_result[formula.code] = res
                    variable_values[formula.code] = res

                # --- PAYE Logic ---
                gross = payroll_result.get("gross_salary", 0)
                security = payroll_result.get("security_fund", 0)
                helth = payroll_result.get("helth_fund", 0)

                taxable = gross - (security + helth)
                paye_range = self.find_applicable_paye_range(taxable, paye_ranges)

                if paye_range:
                    variable_values.update(
                        {
                            "payee_lower_range": paye_range["lower_range"],
                            "payee_percentage": paye_range["range_percentage"],
                            "payee_initial_amount": paye_range["initia_amount"],
                        }
                    )

                    # --- Formula Calculation: Pass 2 (Re-calculate with PAYE) ---
                    for formula in payroll_formulas:
                        res = self.evaluate_formula(formula.expression, variable_values)
                        payroll_result[formula.code] = res
                        variable_values[formula.code] = res

                # 5. CONSTRUCT FINAL OBJECT
                payroll_data.append(
                    {
                        "staff_data": {
                            "id": staff.id,
                            "full_name": staff.full_name,
                            "staff_opf": staff.staff_opf,
                            "code": staff.code,
                        },
                        "payroll": payroll_result,
                    }
                )

        return Response({"payrollData": payroll_data})

    def find_applicable_paye_range(self, remaining_amount, paye_ranges):
        for paye_range in paye_ranges:
            if paye_range.lower_range <= remaining_amount < paye_range.upper_range:
                return {
                    "lower_range": paye_range.lower_range,
                    "initia_amount": paye_range.initia_amount,
                    "range_percentage": round(paye_range.range_percentage, 2),
                }
        return None

    def evaluate_formula(self, expression, variables):
        try:
            # We convert to float for the math, then back to Decimal for precision
            context = {k: float(v) for k, v in variables.items()}
            # Disabling builtins for basic security
            result = eval(expression, {"__builtins__": None}, context)
            return round(decimal.Decimal(str(result)), 2)
        except Exception:
            return decimal.Decimal("0.00")


# ====================================================== deduction ====================================================
class staffPayrollSearch(django_filters.FilterSet):

    class Meta:
        model = StaffPayroll
        fields = {
            "payroll__id": ["exact", "in"],
            "staff__id": ["exact", "in"],
            "year": ["exact", "in"],
            "month": ["exact", "in"],
        }


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
    filter_backends = [
        django_filters.rest_framework.DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = staffPayrollSearch
    search_fields = [
        "payroll__code",
        "payroll__month",
        "staff__staff_opf",
        "staff__full_name",
    ]
    ordering_fields = [
        "id",
        "payroll__code",
        "payroll__month",
        "staff__staff_opf",
        "staff__full_name",
    ]
    ordering = ["-id"]


class StaffPayrollUpdate(CreateAPIView):

    serializer_class = StaffPayrollUpdateSerializer

    def put(self, request, pk):
        salary = StaffPayroll.objects.get(id=pk)
        serializer = StaffPayrollUpdateSerializer(salary, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ====================================================== deduction ====================================================
class PayrollFormulaAdd(CreateAPIView):

    serializer_class = PayrollFormulaSerializer

    def post(self, request):
        serializer = PayrollFormulaSerializer(data=request.data)
        if serializer.is_valid():
            code = serializer.validated_data.get("code")
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
    search_fields = ["code", "name"]
    ordering_fields = ["id", "code", "name"]
    ordering = ["-id"]


# ====================================================== deduction ====================================================
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
    search_fields = ["code", "name"]
    ordering_fields = ["id", "code", "name"]
    ordering = ["code"]
