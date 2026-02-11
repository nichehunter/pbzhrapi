from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.http.response import JsonResponse
from django.utils import timezone
from django.db import transaction
from django.db.models.functions import Coalesce
from collections import defaultdict
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
from payroll.services import *
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
            "customer_number": ["exact", "in"],
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
        "customer_number",
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


# class ProcessPayroll(APIView):
#     @transaction.atomic
#     def post(self, request):
#         data = request.data
#         staff_list = data.get("staff_payrolls", [])
#         month = datetime.date.today().month
#         year = datetime.date.today().year
#         recorded_by = data.get("recorded_by")

#         # 1. Create the Main Payroll Header
#         payroll_header = Payroll.objects.create(
#             code=f"PBZ{month:02}{(year % 100):02}",
#             total_staff=len(staff_list),
#             month=month,
#             year=year,
#             formula_id=data.get("formula_id"),
#             recorded_by=recorded_by,
#         )

#         # 2. Process each staff member sent from Frontend
#         for item in staff_list:
#             # Prepare data for serializer
#             item.update({"month": month, "year": year, "recorded_by": recorded_by})

#             serializer = StaffPayrollAddSerializer(data=item)
#             if serializer.is_valid():
#                 serializer.save(payroll=payroll_header, recorded_by=recorded_by)

#                 staff_id = item.get("staff")
#                 MonthlyAllowance.objects.filter(
#                     staff_id=staff_id,
#                     is_active=True,
#                     month_consumed=0,
#                 ).update(month_consumed=datetime.date.today().month, is_active=False)

#                 MonthlyDeduction.objects.filter(
#                     staff_id=staff_id,
#                     is_active=True,
#                     month_consumed=0,
#                 ).update(month_consumed=datetime.date.today().month, is_active=False)
#             else:
#                 # If one staff record is wrong, rollback everything
#                 transaction.set_rollback(True)
#                 return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#         return Response(
#             {"message": "Payroll and status updates completed successfully"},
#             status=status.HTTP_201_CREATED,
#         )


class ProcessPayroll(APIView):
    @transaction.atomic
    def post(self, request):
        data = request.data
        staff_list = data.get("staff_payrolls", [])
        month = datetime.date.today().month
        year = datetime.date.today().year
        recorded_by = data.get("recorded_by")

        cut_off_active = MonthlyAllowance.objects.filter(
            month_consumed=month, is_active=True
        ).exists()

        # Create Header
        payroll_header = Payroll.objects.create(
            code=f"pbz{month:02}{(year % 100):02}",
            total_staff=len(staff_list),
            month=month,
            year=year,
            formula_id=data.get("formula_id"),
            recorded_by=recorded_by,
        )

        staff_payroll_objects = []
        staff_ids = []

        # 1. Validate and Prepare Objects in Memory
        for item in staff_list:
            staff_id = item.get("staff")
            staff_ids.append(staff_id)

            # Map frontend data to Model fields
            staff_payroll_objects.append(
                StaffPayroll(
                    payroll=payroll_header,
                    staff_id=staff_id,
                    basic_salary=item.get("basic_salary"),
                    total_allowance=item.get("total_allowance"),
                    total_deduction=item.get("total_deduction"),
                    payee=item.get("payee"),
                    security_fund=item.get("security_fund", 0),
                    helth_fund=item.get("helth_fund", 0),
                    net_salary=item.get("net_salary"),
                    month=month,
                    year=year,
                    recorded_by=recorded_by,
                )
            )

        # 2. Bulk Create all Staff Payroll records in ONE query
        StaffPayroll.objects.bulk_create(staff_payroll_objects)

        # 3. Bulk Update Allowances/Deductions in ONE query each
        if cut_off_active:
            MonthlyAllowance.objects.filter(
                month_consumed=month,
                is_active=True,
                year_consumed=year,
            ).update(is_active=False)

            MonthlyDeduction.objects.filter(
                month_consumed=month,
                is_active=True,
                year_consumed=year,
            ).update(is_active=False)
        else:
            MonthlyAllowance.objects.filter(
                is_active=True, month_consumed=0, year_consumed=0
            ).update(
                month_consumed=month,
                is_active=False,
                year_consumed=year,
            )

            MonthlyDeduction.objects.filter(
                is_active=True, month_consumed=0, year_consumed=0
            ).update(
                month_consumed=month,
                is_active=False,
                year_consumed=year,
            )

        return Response(
            {"message": "Payroll processed in bulk successfully"},
            status=status.HTTP_201_CREATED,
        )


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
            year_consumed=0,
        ).update(
            month_consumed=datetime.date.today().month,
            year_consumed=datetime.date.today().year,
        )
        MonthlyDeduction.objects.filter(
            is_active=True,
            month_consumed=0,
            year_consumed=0,
        ).update(
            month_consumed=datetime.date.today().month,
            year_consumed=datetime.date.today().year,
        )
        return Response("done", status=status.HTTP_200_OK)


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
                queryset=StaffSalary.objects.filter(is_active=True),
                to_attr="active_salaries",
            )

            cut_off_active = MonthlyAllowance.objects.filter(
                month_consumed=month, is_active=True
            ).exists()

            allowance_filter = Q(month_consumed=month, is_active=True) | Q(
                is_active=True
            )

            allowance_prefetch = Prefetch(
                "monthlyallowance_set",
                queryset=MonthlyAllowance.objects.filter(allowance_filter),
                to_attr="all_allowances",
            )

            deduction_filter = Q(month_consumed=month, is_active=True) | Q(
                is_active=True
            )

            deduction_prefetch = Prefetch(
                "monthlydeduction_set",
                queryset=MonthlyDeduction.objects.filter(deduction_filter),
                to_attr="all_deductions",
            )
            fund_prefetch = Prefetch(
                "staffsecurityfund_set",
                queryset=StaffSecurityFund.objects.filter(is_active=True),
                to_attr="active_funds",
            )
            health_prefetch = Prefetch(
                "staffhealthfund_set",
                queryset=StaffHealthFund.objects.filter(is_active=True),
                to_attr="active_health_funds",
            )

            # 2. OPTIMIZED QUERY
            staff_qs = (
                Staff.objects.filter(is_active=True, staffsalary__is_active=True)
                .prefetch_related(
                    salary_prefetch,
                    allowance_prefetch,
                    deduction_prefetch,
                    fund_prefetch,
                    health_prefetch,
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
            # helth_deduction = HelthDeduction.objects.filter(is_active=True).first()
            health_funds = {
                hf.fund_id: hf for hf in HelthDeduction.objects.filter(is_active=True)
            }
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
                payroll_result["basic_salary"] = basic_salary

                # --- Allowances ---
                raw_allowances = staff.all_allowances
                if cut_off_active:
                    curr_allowances = [
                        a.amount for a in raw_allowances if a.month_consumed == month
                    ]
                else:
                    curr_allowances = [a.amount for a in raw_allowances if a.is_active]

                allowance_total = round_decimal(sum(curr_allowances))
                variable_values["allowance"] = allowance_total
                payroll_result["allowance"] = allowance_total

                # --- Deductions ---
                raw_deductions = staff.all_deductions
                if cut_off_active:
                    curr_deductions = [
                        d.amount for d in raw_deductions if d.month_consumed == month
                    ]
                else:
                    curr_deductions = [d.amount for d in raw_deductions if d.is_active]

                deduction_total = round_decimal(sum(curr_deductions))
                variable_values["deduction"] = deduction_total
                payroll_result["deduction"] = deduction_total

                # --- Health & Pension ---
                staff_health = (
                    staff.active_health_funds[0] if staff.active_health_funds else None
                )
                if staff_health and staff_health.fund_id in health_funds:
                    h_perc = health_funds[staff_health.fund_id].percentage
                else:
                    h_perc = 0

                variable_values["helth_percentage"] = h_perc
                payroll_result["helth_percentage"] = h_perc

                staff_fund = staff.active_funds[0] if staff.active_funds else None
                if staff_fund and staff_fund.fund_id in security_funds:
                    p_perc = security_funds[staff_fund.fund_id].percentage
                else:
                    p_perc = 0

                variable_values["pension_percentage"] = p_perc
                payroll_result["pension_percentage"] = p_perc

                for formula in payroll_formulas:
                    res = self.evaluate_formula(formula.expression, variable_values)
                    payroll_result[formula.code] = res
                    variable_values[formula.code] = res

                gross = payroll_result.get("gross_salary", 0)
                security = payroll_result.get("security_fund", 0)
                helth = payroll_result.get("helth_fund", 0)

                taxable = gross - (security + helth)

                if staff.staff_category == "primary":
                    paye_range = self.find_applicable_paye_range(taxable, paye_ranges)

                    if paye_range:
                        variable_values.update(
                            {
                                "payee_lower_range": paye_range["lower_range"],
                                "payee_percentage": paye_range["range_percentage"],
                                "payee_initial_amount": paye_range["initia_amount"],
                            }
                        )
                else:
                    variable_values.update(
                        {
                            "payee_lower_range": 0,
                            "payee_percentage": 0.3,
                            "payee_initial_amount": 0,
                        }
                    )

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
            context = {k: float(v) for k, v in variables.items()}
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


class PayrollSummary(APIView):
    def get(self, request):
        payroll_id = request.query_params.get("payroll_id")

        if not payroll_id:
            return Response({"error": "payroll_id is mandatory"}, status=400)

        salary_prefetch = Prefetch(
            "staff__staffsalary_set",
            queryset=StaffSalary.objects.filter(is_active=True).only(
                "staff_id", "branch_code", "customer_number", "ledger", "sub_ledger"
            ),
            to_attr="active_salary",
        )

        dept_prefetch = Prefetch(
            "staff__staff_department",
            queryset=StaffDepartment.objects.filter(is_active=True).only(
                "staff_id", "branch_id", "department_id", "position_id"
            ),
            to_attr="active_dept",
        )

        queryset = (
            StaffPayroll.objects.filter(payroll_id=payroll_id)
            .select_related("staff")
            .prefetch_related(salary_prefetch, dept_prefetch)
        )

        export_data = []
        for record in queryset:
            salary = (
                record.staff.active_salary[0] if record.staff.active_salary else None
            )
            dept_info = (
                record.staff.active_dept[0] if record.staff.active_dept else None
            )

            supervisor = record.staff.staff.filter(is_active=True).first()

            export_data.append(
                {
                    "staff_opf": record.staff.staff_opf,
                    "full_name": record.staff.full_name,
                    "net_salary": record.net_salary,
                    "branch_code": salary.branch_code if salary else None,
                    "customer_number": salary.customer_number if salary else None,
                    "ledger": salary.ledger if salary else None,
                    "sub_ledger": salary.sub_ledger if salary else None,
                    "branch_id": dept_info.branch_id if dept_info else None,
                    "department_id": dept_info.department_id if dept_info else None,
                    "position_id": dept_info.position_id if dept_info else None,
                    "supervise_type_id": (
                        supervisor.supervise_type_id if supervisor else None
                    ),
                }
            )

        return Response({"results": export_data})


class PayrollAllowanceSummary(APIView):
    def get(self, request):
        payroll_id = request.query_params.get("payroll_id")
        if not payroll_id:
            return Response({"error": "payroll_id is mandatory"}, status=400)

        try:
            payroll_record = Payroll.objects.get(id=payroll_id)
            p_month, p_year = payroll_record.month, payroll_record.year
        except Payroll.DoesNotExist:
            return Response({"error": "Payroll not found"}, status=404)

        senior_ids = [40, 321, 322]

        payrolls = (
            StaffPayroll.objects.filter(
                payroll_id=payroll_id, staff__staff_department__is_active=True
            )
            .annotate(
                g_id=Coalesce(
                    "staff__staff_department__branch__parent_branch_id",
                    "staff__staff_department__branch_id",
                ),
                g_name=Coalesce(
                    "staff__staff_department__branch__parent_branch__branch_name",
                    "staff__staff_department__branch__branch_name",
                ),
                g_code=Coalesce(
                    "staff__staff_department__branch__parent_branch__branch_code",
                    "staff__staff_department__branch__branch_code",
                ),
                is_snr=Case(
                    When(
                        staff__staff__supervise_type_id__in=senior_ids,
                        staff__staff__is_active=True,
                        then=True,
                    ),
                    default=False,
                    output_field=BooleanField(),
                ),
            )
            .values("staff_id", "net_salary", "g_id", "g_name", "g_code", "is_snr")
        )

        allowances = MonthlyAllowance.objects.filter(
            month_consumed=p_month,
            year_consumed=p_year,
            is_active=False,
        ).values("staff_id", "allowance_id", "amount")

        allowance_map = defaultdict(lambda: {"housing": 0, "others": 0})
        for acc in allowances:
            sid = acc["staff_id"]
            if acc["allowance_id"] == 10:
                allowance_map[sid]["housing"] += acc["amount"]
            else:
                allowance_map[sid]["others"] += acc["amount"]

        final_groups = defaultdict(
            lambda: {
                "Regular": {"count": 0, "salary": 0, "housing": 0, "allowance": 0},
                "Senior": {"count": 0, "salary": 0, "housing": 0, "allowance": 0},
            }
        )
        branch_info = {}

        for p in payrolls:
            bid = p["g_id"]
            branch_info[bid] = {"name": p["g_name"], "code": p["g_code"]}
            group_key = "Senior" if p["is_snr"] else "Regular"
            sid = p["staff_id"]

            final_groups[bid][group_key]["count"] += 1
            final_groups[bid][group_key]["salary"] += p["net_salary"]
            final_groups[bid][group_key]["housing"] += allowance_map[sid]["housing"]
            final_groups[bid][group_key]["allowance"] += allowance_map[sid]["others"]

        results = []
        sorted_branches = sorted(
            branch_info.keys(), key=lambda x: branch_info[x]["name"]
        )

        for bid in sorted_branches:
            info = branch_info[bid]
            reg = final_groups[bid]["Regular"]
            snr = final_groups[bid]["Senior"]

            # Pre-calculate the total staff count for this branch group (Regular + Senior)
            branch_total_staff = reg["count"] + snr["count"]

            # --- REGULAR STAFF ROWS ---
            if reg["count"] > 0:
                results.append(
                    self._make_row(
                        info,
                        "Regular Staff",
                        "Salary",
                        "6643",
                        reg["salary"],
                        branch_total_staff,
                    )
                )
                results.append(
                    self._make_row(
                        info,
                        "Regular Staff",
                        "Housing",
                        "6650",
                        reg["housing"],
                        branch_total_staff,
                    )
                )
                results.append(
                    self._make_row(
                        info,
                        "Regular Staff",
                        "Allowance",
                        "6644",
                        reg["allowance"],
                        branch_total_staff,
                    )
                )

            # --- SENIOR MANAGEMENT ROWS ---
            if snr["count"] > 0:
                results.append(
                    self._make_row(
                        info,
                        "Senior Management",
                        "Salary",
                        "6640",
                        snr["salary"],
                        branch_total_staff,
                    )
                )
                snr_total_allowance = snr["allowance"] + snr["housing"]
                results.append(
                    self._make_row(
                        info,
                        "Senior Management",
                        "Allowance",
                        "6641",
                        snr_total_allowance,
                        branch_total_staff,
                    )
                )

        return Response(
            {
                "payroll_code": payroll_record.code,
                "period": f"{p_month}/{p_year}",
                "results": results,
            }
        )

    def _make_row(
        self, branch_info, group_name, amount_type, ledger, amount, staff_count
    ):
        return {
            "branch_code": branch_info["code"],
            "branch_name": branch_info["name"],
            "total_staff": staff_count,  # New field added here
            "customer": "0",
            "ledger": ledger,
            "sub_ledger": "0",
            "group": group_name,
            "type": amount_type,
            "amount": round_decimal(amount),
        }

    # def _make_row(self, branch_info, group_name, amount_type, ledger, amount):
    #     return {
    #         "branch_code": branch_info["code"],
    #         "branch_name": branch_info["name"],
    #         "customer": "0",
    #         "Currency": "1",
    #         "ledger": ledger,
    #         "sub_ledger": "0",
    #         "group": group_name,
    #         "type": amount_type,
    #         "amount": round_decimal(amount),
    #     }


class PayrollDeductionSummary(APIView):
    def get(self, request):
        payroll_id = request.query_params.get("payroll_id")
        if not payroll_id:
            return Response({"error": "payroll_id is mandatory"}, status=400)

        # 1. Fetch Payroll context
        try:
            payroll_record = Payroll.objects.get(id=payroll_id)
            p_month, p_year = payroll_record.month, payroll_record.year
        except Payroll.DoesNotExist:
            return Response({"error": "Payroll not found"}, status=404)

        # 2. Query MonthlyDeductions for this payroll period
        summary = (
            MonthlyDeduction.objects.filter(
                month_consumed=p_month, year_consumed=p_year
            )
            .exclude(deduction_id__in=[2, 3, 6])
            .values(
                "deduction_id",
                "deduction__name",
                "deduction__branch",
                "deduction__account",
                "deduction__ledger",
                "deduction__sub_ledger",
                "organization__name",
                "organization__branch",
                "organization__account",
                "organization__ledger",
                "organization__sub_ledger",
            )
            .annotate(
                total_amount=Sum("amount"),
                # Logic for the 'name' field
                computed_name=Case(
                    When(deduction_id=1, then=F("organization__name")),
                    default=F("deduction__name"),
                    output_field=CharField(),
                ),
                # Logic for the 'account' field
                computed_barnch=Case(
                    When(deduction_id=1, then=F("organization__branch")),
                    default=F("deduction__branch"),
                    output_field=CharField(),
                ),
                computed_account=Case(
                    When(deduction_id=1, then=F("organization__account")),
                    default=F("deduction__account"),
                    output_field=CharField(),
                ),
                computed_ledger=Case(
                    When(deduction_id=1, then=F("organization__ledger")),
                    default=F("deduction__ledger"),
                    output_field=CharField(),
                ),
                computed_sub_ledger=Case(
                    When(deduction_id=1, then=F("organization__sub_ledger")),
                    default=F("deduction__sub_ledger"),
                    output_field=CharField(),
                ),
            )
            .order_by("computed_name")
        )

        # 3. Format response
        results = []
        for item in summary:
            results.append(
                {
                    "deduction_id": item["deduction_id"],
                    "name": item["computed_name"],
                    "branch": item["computed_barnch"],
                    "account": item["computed_account"],
                    "ledger": item["computed_ledger"],
                    "sub_ledger": item["computed_sub_ledger"],
                    "amount": round_decimal(item["total_amount"]),
                }
            )

        return Response(
            {
                "payroll_code": payroll_record.code,
                "period": f"{p_month}/{p_year}",
                "results": results,
            }
        )


class PayrollContributionAllowanceSummary(APIView):
    def get(self, request):
        payroll_id = request.query_params.get("payroll_id")
        if not payroll_id:
            return Response({"error": "payroll_id is mandatory"}, status=400)

        queryset = StaffPayroll.objects.filter(payroll_id=payroll_id)

        # 1. SDL Calculation (4% of Gross)
        sdl_raw = queryset.aggregate(
            total=Sum(
                (F("basic_salary") + F("total_allowance")) * Value(0.04),
                output_field=DecimalField(),
            )
        )["total"]

        # 2. ZHSF Calculation (3.5% of Basic if active in Health Fund)
        zhsf_raw = queryset.aggregate(
            total=Sum(
                Case(
                    When(
                        staff__staffhealthfund__is_active=True,
                        then=F("basic_salary") * Value(0.035),
                    ),
                    default=Value(0),
                    output_field=DecimalField(),
                )
            )
        )["total"]

        # 3. Pension Calculation (14% if fund=1, else 13%)
        pension_query = (
            queryset.values(name=F("staff__staffsecurityfund__fund__name"))
            .filter(staff__staffsecurityfund__is_active=True)
            .annotate(
                raw_amount=Sum(
                    Case(
                        When(
                            staff__staffsecurityfund__fund_id=1,
                            then=F("basic_salary") * Value(0.14),
                        ),
                        default=F("basic_salary") * Value(0.13),
                        output_field=DecimalField(),
                    )
                )
            )
        )

        # Apply your round_decimal service to the results
        results = {
            "sdl": {
                "branch": "201",
                "customer": "0",
                "ledger": "6648",
                "sub_ledger": "0",
                "amount": round_decimal(sdl_raw),
            },
            "zhsf": {
                "branch": "201",
                "customer": "0",
                "ledger": "6651",
                "sub_ledger": "0",
                "amount": round_decimal(zhsf_raw),
            },
            "pension_contributions": [
                {
                    "fund_name": item["name"],
                    "branch": "201",
                    "customer": "0",
                    "ledger": "6647",
                    "sub_ledger": "0",
                    "amount": round_decimal(item["raw_amount"]),
                }
                for item in pension_query
            ],
        }

        return Response(results)


class PayrollContributionDeductionSummary(APIView):
    def get(self, request):
        payroll_id = request.query_params.get("payroll_id")
        if not payroll_id:
            return Response({"error": "payroll_id is mandatory"}, status=400)

        queryset = StaffPayroll.objects.filter(payroll_id=payroll_id)

        salary_raw = queryset.aggregate(
            total=Sum(
                F("net_salary"),
                output_field=DecimalField(),
            )
        )["total"]

        payee_raw = queryset.aggregate(
            total=Sum(
                ((F("basic_salary") + F("total_allowance")) * Value(0.04)) + F("payee"),
                output_field=DecimalField(),
            )
        )["total"]

        # 2. ZHSF Calculation (3.5% of Basic if active in Health Fund)
        zhsf_raw = queryset.aggregate(
            total=Sum(
                Case(
                    When(
                        staff__staffhealthfund__is_active=True,
                        then=F("basic_salary") * Value(0.07),
                    ),
                    default=Value(0),
                    output_field=DecimalField(),
                )
            )
        )["total"]

        # 3. Pension Calculation (14% if fund=1, else 13%)
        pension_query = (
            queryset.values(
                name=F("staff__staffsecurityfund__fund__name"),
                branch=F("staff__staffsecurityfund__fund__branch"),
                customer=F("staff__staffsecurityfund__fund__account"),
                ledger=F("staff__staffsecurityfund__fund__ledger"),
                sub_ledger=F("staff__staffsecurityfund__fund__sub_ledger"),
            )
            .filter(staff__staffsecurityfund__is_active=True)
            .annotate(
                raw_amount=Sum(
                    Case(
                        When(
                            staff__staffsecurityfund__fund_id=1,
                            then=F("basic_salary") * Value(0.21),
                        ),
                        default=F("basic_salary") * Value(0.20),
                        output_field=DecimalField(),
                    )
                )
            )
        )

        # Apply your round_decimal service to the results
        results = {
            "salary": {
                "branch": "201",
                "customer": "0",
                "ledger": "5834",
                "sub_ledger": "0",
                "amount": round_decimal(salary_raw),
            },
            "payee": {
                "branch": "201",
                "customer": "0",
                "ledger": "5731",
                "sub_ledger": "0",
                "amount": round_decimal(payee_raw),
            },
            "zhsf": {
                "branch": "201",
                "customer": "0",
                "ledger": "5834",
                "sub_ledger": "0",
                "amount": round_decimal(zhsf_raw),
            },
            "pension_contributions": [
                {
                    "fund_name": item["name"],
                    "branch": item["branch"],
                    "customer": item["customer"],
                    "ledger": item["ledger"],
                    "sub_ledger": item["sub_ledger"],
                    "amount": round_decimal(item["raw_amount"]),
                }
                for item in pension_query
            ],
        }

        return Response(results)
