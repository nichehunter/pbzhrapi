from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.http.response import JsonResponse
from django.utils import timezone
from django.db import transaction
from django.db.models.functions import Coalesce
from collections import defaultdict
import statistics
import re

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


# class StaffSalaryAdd(CreateAPIView):
#     serializer_class = SalarySerializer

#     def post(self, request):
#         serializer = SalarySerializer(data=request.data, many=True)
#         if serializer.is_valid():
#             try:
#                 with transaction.atomic():  # start atomic transaction
#                     for x in serializer.validated_data:
#                         staff = x.get("staff")
#                         salary = StaffSalary.objects.filter(
#                             is_active=True, staff__id=staff.id
#                         )
#                         if salary.exists():
#                             salary.update(is_active=False)
#                     serializer.save()
#                 return Response(serializer.data, status=status.HTTP_201_CREATED)
#             except Exception as e:
#                 return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StaffSalaryAdd(APIView):
    def post(self, request):
        data = request.data
        staff_id = data.get("staff")
        amount = data.get("amount")
        recorded_by = data.get("recorded_by")

        if not staff_id or not amount:
            return Response(
                {"error": "staff and amount are mandatory fields."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        previous_salary = (
            StaffSalary.objects.filter(staff_id=staff_id)
            .order_by("-recorded_at")
            .first()
        )

        required_fields = [
            "account_number",
            "branch_code",
            "customer_number",
            "ledger",
            "sub_ledger",
            "tin_number",
        ]

        new_salary_data = {
            "staff_id": staff_id,
            "amount": amount,
            "recorded_by": recorded_by,
            "is_active": True,
        }

        missing_fields = []
        for field in required_fields:
            val = data.get(field)

            if val:
                new_salary_data[field] = val
            elif previous_salary:
                new_salary_data[field] = getattr(previous_salary, field)
            else:
                missing_fields.append(field)

        if missing_fields:
            return Response(
                {
                    "error": "This staff has no previous salary record. Full information is required.",
                    "missing_fields": missing_fields,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            with transaction.atomic():
                StaffSalary.objects.filter(staff_id=staff_id, is_active=True).update(
                    is_active=False
                )
                new_record = StaffSalary.objects.create(**new_salary_data)

            return Response(
                {"message": "Staff salary updated successfully", "id": new_record.id},
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


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
        "^code",
        "^staff__full_name",
        "^staff__staff_opf",
        "^customer_number",
        "^account_number",
        "^tin_number",
    ]
    ordering_fields = ["id", "code", "staff__full_name", "staff__staff_opf"]
    ordering = ["staff__staff_opf"]


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


class ChangeStaffSalaryStatus(APIView):
    """
    Toggles the is_active status for a list of StaffSalary IDs.
    If True, becomes False. If False, becomes True.
    """

    def post(self, request):
        salary_ids = request.data.get("ids", [])

        if not salary_ids:
            return Response(
                {"error": "Please provide a list of IDs in the 'ids' field."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # We use a bulk update with a conditional toggle logic
        # This updates every record in the list in one SQL command
        updated_count = StaffSalary.objects.filter(id__in=salary_ids).update(
            is_active=Case(
                When(is_active=True, then=Value(False)),
                When(is_active=False, then=Value(True)),
                output_field=BooleanField(),
            )
        )

        return Response(
            {
                "message": f"Successfully toggled {updated_count} records.",
                "updated_count": updated_count,
            },
            status=status.HTTP_200_OK,
        )


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
        "^organization__code",
        "^organization__name",
        "^organization__account",
        "^staff__staff_opf",
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


class ChangeStaffOrganizationStatusView(APIView):
    """
    Toggles the is_active status for a list of StaffOrganization IDs.
    If True, becomes False. If False, becomes True.
    """

    def post(self, request):
        organization_ids = request.data.get("ids", [])

        if not organization_ids:
            return Response(
                {"error": "Please provide a list of IDs in the 'ids' field."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # We use a bulk update with a conditional toggle logic
        # This updates every record in the list in one SQL command
        updated_count = StaffOrganization.objects.filter(
            id__in=organization_ids
        ).update(
            is_active=Case(
                When(is_active=True, then=Value(False)),
                When(is_active=False, then=Value(True)),
                output_field=BooleanField(),
            )
        )

        return Response(
            {
                "message": f"Successfully toggled {updated_count} records.",
                "updated_count": updated_count,
            },
            status=status.HTTP_200_OK,
        )


class StaffOrganizationTotal(APIView):
    """
    Returns the total sum of 'amount' for active records filtered by organization.
    """

    def get(self, request, org_id):

        if not org_id:
            return Response(
                {"error": "org_id parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = StaffOrganization.objects.filter(
            organization_id=org_id, is_active=True
        ).aggregate(total_amount=Sum("amount"))

        total = result.get("total_amount") or 0

        return Response(
            {"organization_id": org_id, "total_active_amount": total},
            status=status.HTTP_200_OK,
        )


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


class ChangeStaffAllowanceStatusView(APIView):
    """
    Toggles the is_active status for a list of StaffAllowance IDs.
    If True, becomes False. If False, becomes True.
    """

    def post(self, request):
        allowance_ids = request.data.get("ids", [])

        if not allowance_ids:
            return Response(
                {"error": "Please provide a list of IDs in the 'ids' field."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # We use a bulk update with a conditional toggle logic
        # This updates every record in the list in one SQL command
        updated_count = StaffAllowance.objects.filter(id__in=allowance_ids).update(
            is_active=Case(
                When(is_active=True, then=Value(False)),
                When(is_active=False, then=Value(True)),
                output_field=BooleanField(),
            )
        )

        return Response(
            {
                "message": f"Successfully toggled {updated_count} records.",
                "updated_count": updated_count,
            },
            status=status.HTTP_200_OK,
        )


class StaffAllowanceTotal(APIView):
    """
    Returns the total sum of 'amount' for active records filtered by allowance.
    """

    def get(self, request, alw_id):

        if not alw_id:
            return Response(
                {"error": "alw_id parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = StaffAllowance.objects.filter(
            allowance_id=alw_id, is_active=True
        ).aggregate(total_amount=Sum("amount"))

        total = result.get("total_amount") or 0

        return Response(
            {"allowance_id": alw_id, "total_active_amount": total},
            status=status.HTTP_200_OK,
        )


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


class ChangeStaffDeductionStatusView(APIView):
    """
    Toggles the is_active status for a list of StaffDeduction IDs.
    If True, becomes False. If False, becomes True.
    """

    def post(self, request):
        deduction_ids = request.data.get("ids", [])

        if not deduction_ids:
            return Response(
                {"error": "Please provide a list of IDs in the 'ids' field."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # We use a bulk update with a conditional toggle logic
        # This updates every record in the list in one SQL command
        updated_count = StaffDeduction.objects.filter(id__in=deduction_ids).update(
            is_active=Case(
                When(is_active=True, then=Value(False)),
                When(is_active=False, then=Value(True)),
                output_field=BooleanField(),
            )
        )

        return Response(
            {
                "message": f"Successfully toggled {updated_count} records.",
                "updated_count": updated_count,
            },
            status=status.HTTP_200_OK,
        )


class StaffDeductionTotal(APIView):
    """
    Returns the total sum of 'amount' for active records filtered by deduction.
    """

    def get(self, request, ded_id):

        if not ded_id:
            return Response(
                {"error": "ded_id parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = StaffDeduction.objects.filter(
            deduction_id=ded_id, is_active=True
        ).aggregate(total_amount=Sum("amount"))

        total = result.get("total_amount") or 0

        return Response(
            {"deduction_id": ded_id, "total_active_amount": total},
            status=status.HTTP_200_OK,
        )


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


class ProcessPayroll(APIView):
    @transaction.atomic
    def post(self, request):
        data = request.data
        staff_list = data.get("staff_payrolls", [])
        month = datetime.date.today().month
        year = datetime.date.today().year
        recorded_by = data.get("recorded_by")

        # 1. Create Payroll Header
        payroll_header = Payroll.objects.create(
            code=f"pbz{month:02}{(year % 100):02}",
            total_staff=len(staff_list),
            month=month,
            year=year,
            formula_id=data.get("formula_id"),
            recorded_by=recorded_by,
        )

        staff_ids = [item.get("staff") for item in staff_list]

        # 2. SMART LOOKUP: Check if data was frozen (month/year matches)
        # If not, fallback to any active records
        def get_active_records(model_class):
            # Base fields common to all
            fields = ["staff_id", "id", "amount", "date"]

            # Check for Allowance vs Deduction specific ID
            if hasattr(model_class, "allowance_id"):
                fields.append("allowance_id")
            else:
                fields.append("deduction_id")

            # Check if organization_id exists (for Organization-specific deductions)
            if hasattr(model_class, "organization_id"):
                fields.append("organization_id")

            # Try to find frozen records first
            frozen = model_class.objects.filter(
                staff_id__in=staff_ids,
                is_active=True,
                month_consumed=month,
                year_consumed=year,
            )

            if frozen.exists():
                return frozen.values(*fields)

            # Fallback: Take all active records
            return model_class.objects.filter(
                staff_id__in=staff_ids, is_active=True
            ).values(*fields)

        # def get_active_records(model_class):
        #     # Try to find frozen records first
        #     frozen = model_class.objects.filter(
        #         staff_id__in=staff_ids,
        #         is_active=True,
        #         month_consumed=month,
        #         year_consumed=year,
        #     )
        #     if frozen.exists():
        #         return frozen.values(
        #             "staff_id",
        #             "id",
        #             "amount",
        #             (
        #                 "allowance_id"
        #                 if hasattr(model_class, "allowance_id")
        #                 else "deduction_id"
        #             ),
        #         )

        #     # Fallback: Take all active records
        #     return model_class.objects.filter(
        #         staff_id__in=staff_ids, is_active=True
        #     ).values(
        #         "staff_id",
        #         "id",
        #         "amount",
        #         (
        #             "allowance_id"
        #             if hasattr(model_class, "allowance_id")
        #             else "deduction_id"
        #         ),
        #     )

        active_allowances = get_active_records(MonthlyAllowance)
        active_deductions = get_active_records(MonthlyDeduction)

        # Map for lookup
        allowance_lookup = defaultdict(list)
        for a in active_allowances:
            allowance_lookup[a["staff_id"]].append(a)

        deduction_lookup = defaultdict(list)
        for d in active_deductions:
            deduction_lookup[d["staff_id"]].append(d)

        # 3. Preparation
        staff_payroll_objects = []
        itemized_allowances = []
        itemized_deductions = []

        # Track IDs to deactivate later
        allowance_ids_to_close = [a["id"] for a in active_allowances]
        deduction_ids_to_close = [d["id"] for d in active_deductions]

        branch_mapping = dict(
            StaffDepartment.objects.filter(
                staff_id__in=staff_ids, is_active=True
            ).values_list("staff_id", "id")
        )

        for item in staff_list:
            sid = item.get("staff")

            # --- Main StaffPayroll Entry ---
            staff_payroll_objects.append(
                StaffPayroll(
                    payroll=payroll_header,
                    staff_id=sid,
                    branch_id=branch_mapping.get(sid),
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

            # --- Map Allowances ---
            for alw in allowance_lookup.get(sid, []):
                itemized_allowances.append(
                    StaffPayrollAllowance(
                        staff_id=sid,
                        payroll=payroll_header,
                        allowance_id=alw["allowance_id"],
                        date=ded.get("date"),
                        amount=alw["amount"],
                        recorded_by=recorded_by,
                    )
                )

            # --- Map Deductions ---
            for ded in deduction_lookup.get(sid, []):
                itemized_deductions.append(
                    StaffPayrollDeduction(
                        staff_id=sid,
                        payroll=payroll_header,
                        deduction_id=ded["deduction_id"],
                        organization_id=ded.get("organization_id"),  # May be None
                        date=ded.get("date"),
                        amount=ded["amount"],
                        recorded_by=recorded_by,
                    )
                )

            # --- System Items (Payee/Pension/Health) ---
            self._add_system_deductions(
                sid, item, payroll_header, recorded_by, itemized_deductions, data
            )

        # 4. Bulk Create
        StaffPayroll.objects.bulk_create(staff_payroll_objects)
        StaffPayrollAllowance.objects.bulk_create(itemized_allowances)
        StaffPayrollDeduction.objects.bulk_create(itemized_deductions)

        # 5. Final Step: Close exactly the records we used
        MonthlyAllowance.objects.filter(id__in=allowance_ids_to_close).update(
            month_consumed=month, year_consumed=year, is_active=False
        )
        MonthlyDeduction.objects.filter(id__in=deduction_ids_to_close).update(
            month_consumed=month, year_consumed=year, is_active=False
        )

        return Response({"message": "Payroll processed successfully"}, status=201)

    def _add_system_deductions(self, sid, item, header, user_id, ded_list, data):
        mapping = [
            (data.get("payee_id"), item.get("payee")),
            (data.get("security_id"), item.get("security_fund")),
            (data.get("health_id"), item.get("helth_fund")),
        ]
        for d_id, amt in mapping:
            if d_id and amt and amt > 0:
                ded_list.append(
                    StaffPayrollDeduction(
                        staff_id=sid,
                        payroll=header,
                        deduction_id=d_id,
                        date=datetime.date.today(),
                        amount=amt,
                        recorded_by=user_id,
                    )
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
            # 1. SETUP PREFETCHES
            # We fetch active salaries and departments to validate presence
            salary_prefetch = Prefetch(
                "staffsalary_set",
                queryset=StaffSalary.objects.filter(is_active=True),
                to_attr="active_salaries",
            )

            dept_prefetch = Prefetch(
                "staff_department",
                queryset=StaffDepartment.objects.filter(is_active=True),
                to_attr="active_department",
            )

            # Check if frozen records exist for the current month
            cut_off_active = MonthlyAllowance.objects.filter(
                month_consumed=month, year_consumed=year, is_active=True
            ).exists()

            allowance_filter = Q(
                month_consumed=month, year_consumed=year, is_active=True
            ) | Q(is_active=True)
            allowance_prefetch = Prefetch(
                "monthlyallowance_set",
                queryset=MonthlyAllowance.objects.filter(allowance_filter),
                to_attr="all_allowances",
            )

            deduction_filter = Q(
                month_consumed=month, year_consumed=year, is_active=True
            ) | Q(is_active=True)
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
                Staff.objects.filter(is_active=True)
                .prefetch_related(
                    salary_prefetch,
                    dept_prefetch,
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

            # 3. CACHE GLOBAL DATA
            payroll_variables = list(PayrollVariable.objects.all())
            payroll_formulas = list(
                PayrollFormula.objects.filter(is_active=True).order_by("id")
            )
            paye_ranges = list(PayeeDeduction.objects.filter(is_active=True))
            health_funds_map = {
                hf.fund_id: hf for hf in HelthDeduction.objects.filter(is_active=True)
            }
            security_funds_map = {
                sf.fund_id: sf
                for sf in SecurityFundDeduction.objects.filter(is_active=True)
            }

            payroll_data = []

            # 4. PROCESS DATA IN MEMORY
            for staff in staff_qs:
                # --- VALIDATION ---
                # Ensure Active Department exists
                if not staff.active_department:
                    return Response(
                        {
                            "error": f"Staff with OPF {staff.staff_opf} ({staff.full_name.upper()}) does not have an active department record."
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                # Ensure Active Salary exists
                if not staff.active_salaries:
                    return Response(
                        {
                            "error": f"Staff with OPF {staff.staff_opf} ({staff.full_name.upper()}) does not have an active salary record."
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                # Fetch IDs from the prefetched attributes
                dept_id = staff.active_department[0].id
                basic_salary = (
                    staff.active_salaries[0].amount if staff.active_salaries else 0
                )

                # Context Setup
                variable_values = {
                    v.name: decimal.Decimal("0.00") for v in payroll_variables
                }
                payroll_result = {
                    f.code: decimal.Decimal("0.00") for f in payroll_formulas
                }

                variable_values["basic_salary"] = basic_salary
                payroll_result["basic_salary"] = basic_salary

                # --- Calculate Allowances (Handle Freeze logic) ---
                if cut_off_active:
                    curr_allowances = [
                        a.amount
                        for a in staff.all_allowances
                        if a.month_consumed == month
                    ]
                else:
                    curr_allowances = [
                        a.amount for a in staff.all_allowances if a.is_active
                    ]

                allowance_total = sum(curr_allowances)
                variable_values["allowance"] = allowance_total
                payroll_result["allowance"] = allowance_total

                # --- Calculate Deductions (Handle Freeze logic) ---
                if cut_off_active:
                    curr_deductions = [
                        d.amount
                        for d in staff.all_deductions
                        if d.month_consumed == month
                    ]
                else:
                    curr_deductions = [
                        d.amount for d in staff.all_deductions if d.is_active
                    ]

                deduction_total = sum(curr_deductions)
                variable_values["deduction"] = deduction_total
                payroll_result["deduction"] = deduction_total

                # --- Health & Pension Percentages ---
                staff_health = (
                    staff.active_health_funds[0] if staff.active_health_funds else None
                )
                h_perc = (
                    health_funds_map[staff_health.fund_id].percentage
                    if staff_health and staff_health.fund_id in health_funds_map
                    else 0
                )
                variable_values["helth_percentage"] = h_perc

                staff_fund = staff.active_funds[0] if staff.active_funds else None
                p_perc = (
                    security_funds_map[staff_fund.fund_id].percentage
                    if staff_fund and staff_fund.fund_id in security_funds_map
                    else 0
                )
                variable_values["pension_percentage"] = p_perc

                # --- Initial Formula Evaluation ---
                for formula in payroll_formulas:
                    res = self.evaluate_formula(formula.expression, variable_values)
                    payroll_result[formula.code] = res
                    variable_values[formula.code] = res

                # --- Tax (PAYE) Calculation ---
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

                # --- Final Formula Evaluation (Including Tax) ---
                for formula in payroll_formulas:
                    res = self.evaluate_formula(formula.expression, variable_values)
                    payroll_result[formula.code] = res
                    variable_values[formula.code] = res

                # payroll_result.update(
                #     {
                #         "payee_id": data.get("payee_id"),
                #         "security_id": data.get("security_id"),
                #         "health_id": data.get("health_id"),
                #     }
                # )

                # 5. CONSTRUCT FINAL OBJECT
                payroll_data.append(
                    {
                        "staff_data": {
                            "id": staff.id,
                            "full_name": staff.full_name,
                            "staff_opf": staff.staff_opf,
                            "code": staff.code,
                            "staff_department": dept_id,  # Appended StaffDepartment PK
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
            return decimal.Decimal(str(round(result, 2)))
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


class StaffPayrollData(APIView):
    def get(self, request):
        staff_id = request.query_params.get("staff_id")
        payroll_id = request.query_params.get("payroll_id")

        if not staff_id or not payroll_id:
            return Response(
                {"error": "Both staff_id and payroll_id are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # 1. Fetch the main payroll summary
            payroll_entry = StaffPayroll.objects.select_related("staff", "payroll").get(
                staff_id=staff_id, payroll_id=payroll_id
            )

            # 2. Fetch TIN and Customer Number from StaffSalary (Active record)
            salary_info = (
                StaffSalary.objects.filter(staff_id=staff_id, is_active=True)
                .values("tin_number", "customer_number")
                .first()
            )

            pension_info = (
                StaffSecurityFund.objects.filter(staff_id=staff_id, is_active=True)
                .values("account")
                .first()
            )

            # 3. Fetch Itemized Allowances
            allowances = StaffPayrollAllowance.objects.filter(
                staff_id=staff_id, payroll_id=payroll_id
            ).select_related("allowance")

            # 4. Fetch Itemized Deductions
            deductions = (
                StaffPayrollDeduction.objects.filter(
                    staff_id=staff_id, payroll_id=payroll_id
                )
                .exclude(deduction__id__in=[2, 3, 6])
                .select_related("deduction", "organization")
            )

            allowance_list = [
                {
                    "name": self._clean_name(item.allowance.name, "allowance"),
                    "amount": item.amount,
                }
                for item in allowances
            ]
            total_allowance_itemized = sum(item["amount"] for item in allowance_list)

            statutory_items = [
                {"name": "Tax Contribution", "amount": payroll_entry.payee},
                {"name": "Pension Contribution", "amount": payroll_entry.security_fund},
                {"name": "ZHSF Contribution", "amount": payroll_entry.helth_fund},
            ]

            # Calculate Total for convenience
            total_statutory = sum(item["amount"] for item in statutory_items)

            # 4. Process Other Deductions and Calculate Total
            other_deductions_list = [
                {
                    "name": (
                        item.organization.name
                        if item.organization
                        else self._clean_name(item.deduction.name, "deduction")
                    ),
                    "amount": item.amount,
                }
                for item in deductions
            ]
            total_other_deductions = sum(
                item["amount"] for item in other_deductions_list
            )

            # 5. Construct response
            data = {
                "staff_info": {
                    "opf": payroll_entry.staff.staff_opf,
                    "code": payroll_entry.staff.code,
                    "full_name": payroll_entry.staff.full_name,
                    "branch_name": (
                        payroll_entry.branch.branch.branch_name
                        if payroll_entry.branch
                        else "N/A"
                    ),
                    "payroll_code": payroll_entry.payroll.code,
                    "period": payroll_entry.month,
                    "year": payroll_entry.year,
                    "tin_number": (
                        salary_info.get("tin_number") if salary_info else "N/A"
                    ),
                    "customer_number": (
                        salary_info.get("customer_number") if salary_info else "N/A"
                    ),
                    "pension_account": (
                        pension_info.get("account") if pension_info else "N/A"
                    ),
                },
                "salary_summary": {
                    "basic_salary": payroll_entry.basic_salary,
                    "gross_salary": payroll_entry.basic_salary
                    + payroll_entry.total_allowance,
                    "net_salary": payroll_entry.net_salary,
                },
                "statutory_deductions": {
                    "items": statutory_items,
                    "total_amount": total_statutory,
                },
                "allowances": {
                    "items": allowance_list,
                    "total_amount": total_allowance_itemized,
                },
                "deductions": {
                    "items": other_deductions_list,
                    "total_amount": total_other_deductions,
                },
            }

            return Response(data, status=status.HTTP_200_OK)

        except StaffPayroll.DoesNotExist:
            return Response(
                {"error": "Payroll record not found."}, status=status.HTTP_404_NOT_FOUND
            )

    def _clean_name(self, name, suffix_type):
        """Removes the word 'deduction' or 'allowance' from the end of the string"""
        if not name:
            return ""
        # Regex to case-insensitively find the word at the end of the string
        pattern = rf"\s*{suffix_type}\s*$"
        return re.sub(pattern, "", name, flags=re.IGNORECASE).strip()


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

        supervisor_prefetch = Prefetch(
            "staff__staff",
            queryset=Supervisor.objects.filter(is_active=True).only(
                "staff_id", "supervise_type_id"
            ),
            to_attr="active_supervisor",
        )

        queryset = (
            StaffPayroll.objects.filter(payroll_id=payroll_id)
            .select_related(
                "staff",
                "branch",
                "branch__branch",
                "branch__department",
                "branch__position",
            )
            .prefetch_related(salary_prefetch, supervisor_prefetch)
            .order_by("staff__staff_opf")
        )

        export_data = []
        for record in queryset:
            staff = record.staff
            dept_info = record.branch

            salary = staff.active_salary[0] if staff.active_salary else None
            supervisor = (
                staff.active_supervisor[0]
                if getattr(staff, "active_supervisor", None)
                else None
            )

            export_data.append(
                {
                    "staff_opf": staff.staff_opf,
                    "full_name": staff.full_name,
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

        # 1. Fetch Payroll Data with Fallbacks
        # If branch logic is returning empty, Coalesce ensures the record isn't dropped.
        payrolls = (
            StaffPayroll.objects.filter(payroll_id=payroll_id)
            .select_related("branch__branch__parent_branch", "staff__staff")
            .annotate(
                g_id=Coalesce(
                    "branch__branch__parent_branch_id", "branch__branch_id", Value(0)
                ),
                g_name=Coalesce(
                    "branch__branch__parent_branch__branch_name",
                    "branch__branch__branch_name",
                    Value("Unknown/Unassigned Branch"),
                ),
                g_code=Coalesce(
                    "branch__branch__parent_branch__branch_code",
                    "branch__branch__branch_code",
                    Value("000"),
                ),
                is_snr=Case(
                    When(
                        staff__staff__supervise_type_id__in=senior_ids,
                        then=True,
                    ),
                    default=False,
                    output_field=BooleanField(),
                ),
            )
            .values(
                "staff_id",
                "basic_salary",
                "g_id",
                "g_name",
                "g_code",
                "is_snr",
            )
        )

        if not payrolls.exists():
            return Response(
                {"message": "No records found for this payroll ID", "results": []}
            )

        # 2. Fetch Historical Allowances
        staff_ids = [p["staff_id"] for p in payrolls]
        allowances = StaffPayrollAllowance.objects.filter(
            staff_id__in=staff_ids,
            payroll_id=payroll_id,
        ).values("staff_id", "allowance_id", "amount")

        allowance_map = defaultdict(lambda: {"housing": 0, "others": 0})
        for acc in allowances:
            sid = acc["staff_id"]
            if acc["allowance_id"] == 10:  # Assuming 10 is Housing
                allowance_map[sid]["housing"] += acc["amount"]
            else:
                allowance_map[sid]["others"] += acc["amount"]

        # 3. Grouping Logic
        final_groups = defaultdict(
            lambda: {
                "Regular": {"count": 0, "salary": 0, "housing": 0, "allowance": 0},
                "Senior": {"count": 0, "salary": 0, "housing": 0, "allowance": 0},
            }
        )
        branch_info = {}
        processed_staff = set()

        for p in payrolls:
            sid = p["staff_id"]
            # Avoid duplication if a staff member has multiple branch assignments
            if sid in processed_staff:
                continue
            processed_staff.add(sid)

            bid = p["g_id"]
            branch_info[bid] = {"name": p["g_name"], "code": p["g_code"]}
            group_key = "Senior" if p["is_snr"] else "Regular"

            final_groups[bid][group_key]["count"] += 1
            final_groups[bid][group_key]["salary"] += p["basic_salary"]
            final_groups[bid][group_key]["housing"] += allowance_map[sid]["housing"]
            final_groups[bid][group_key]["allowance"] += allowance_map[sid]["others"]

        # 4. Generate Structured Results
        results = []
        # Sort by branch name for a clean report
        sorted_bids = sorted(branch_info.keys(), key=lambda x: branch_info[x]["name"])

        for bid in sorted_bids:
            info = branch_info[bid]
            reg = final_groups[bid]["Regular"]
            snr = final_groups[bid]["Senior"]
            total_branch_staff = reg["count"] + snr["count"]

            # REGULAR STAFF SECTION
            if reg["count"] > 0:
                results.append(
                    self._make_row(
                        info,
                        "Regular Staff",
                        "Basic Salary",
                        "6643",
                        reg["salary"],
                        total_branch_staff,
                    )
                )
                results.append(
                    self._make_row(
                        info,
                        "Regular Staff",
                        "Housing",
                        "6650",
                        reg["housing"],
                        total_branch_staff,
                    )
                )
                results.append(
                    self._make_row(
                        info,
                        "Regular Staff",
                        "Other Allowance",
                        "6644",
                        reg["allowance"],
                        total_branch_staff,
                    )
                )

            # SENIOR MANAGEMENT SECTION
            if snr["count"] > 0:
                results.append(
                    self._make_row(
                        info,
                        "Senior Management",
                        "Basic Salary",
                        "6640",
                        snr["salary"],
                        total_branch_staff,
                    )
                )
                # Seniors combine housing and others into one ledger
                results.append(
                    self._make_row(
                        info,
                        "Senior Management",
                        "Total Allowance",
                        "6641",
                        snr["housing"] + snr["allowance"],
                        total_branch_staff,
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
        """Helper to format the ledger rows consistently"""
        return {
            "branch_code": branch_info["code"],
            "branch_name": branch_info["name"],
            "total_staff": staff_count,
            "customer": "0",
            "ledger": ledger,
            "sub_ledger": "0",
            "group": group_name,
            "type": amount_type,
            "amount": float(round(amount, 2)),
        }


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
            StaffPayrollDeduction.objects.filter(payroll_id=payroll_id)
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

        # 1. SDL Calculation (Use 'or 0' to prevent None errors)
        sdl_raw = (
            queryset.aggregate(
                total=Sum(
                    (F("basic_salary") + F("total_allowance")) * Value(0.04),
                    output_field=DecimalField(),
                )
            )["total"]
            or 0
        )

        # 2. ZHSF Calculation (Ensure Value is Decimal for precision)
        zhsf_raw = (
            queryset.aggregate(
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
            or 0
        )

        # 3. Pension Calculation (Aligned with Deduction Logic)
        pension_query = (
            queryset.filter(staff__staffsecurityfund__is_active=True)
            .values(
                fund_id=F("staff__staffsecurityfund__fund_id"),
                name=F("staff__staffsecurityfund__fund__name"),
            )
            .annotate(
                raw_amount=Sum(
                    Case(
                        When(
                            fund_id=1,
                            then=F("basic_salary") * Value(0.14),
                        ),
                        default=F("basic_salary") * Value(0.13),
                        output_field=DecimalField(),
                    )
                )
            )
        )

        results = {
            "sdl": {
                "branch_code": "201",
                "customer": "0",
                "ledger": "6648",
                "sub_ledger": "0",
                "amount": round_decimal(sdl_raw),
            },
            "zhsf": {
                "branch_code": "201",
                "customer": "0",
                "ledger": "6651",
                "sub_ledger": "0",
                "amount": round_decimal(zhsf_raw),
            },
            "pension_contributions": [
                {
                    "fund_name": item["name"],
                    "fund_id": item["fund_id"],  # Added for debugging
                    "branch_code": "201",
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

        # Base queryset for this specific payroll
        queryset = StaffPayroll.objects.filter(payroll_id=payroll_id)

        # 1. Salary Calculation (Total Net Salary)
        salary_raw = (
            queryset.aggregate(total=Sum(F("net_salary"), output_field=DecimalField()))[
                "total"
            ]
            or 0
        )

        # 2. Payee Calculation (Total Payee + Additional 4% component)
        payee_raw = (
            queryset.aggregate(
                total=Sum(
                    ((F("basic_salary") + F("total_allowance")) * Value(0.04))
                    + F("payee"),
                    output_field=DecimalField(),
                )
            )["total"]
            or 0
        )

        # 3. ZHSF Calculation (7% of Basic for staff with active health fund)
        zhsf_raw = (
            queryset.aggregate(
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
            or 0
        )

        # 4. Pension Calculation & Staff Counts
        # We group by the specific fund details to provide a breakdown
        pension_query = (
            queryset.filter(staff__staffsecurityfund__is_active=True)
            .values(
                fund_id=F("staff__staffsecurityfund__fund_id"),
                name=F("staff__staffsecurityfund__fund__name"),
                branch_code=F("staff__staffsecurityfund__fund__branch"),
                customer=F("staff__staffsecurityfund__fund__account"),
                ledger=F("staff__staffsecurityfund__fund__ledger"),
                sub_ledger=F("staff__staffsecurityfund__fund__sub_ledger"),
            )
            .annotate(
                staff_count=Count("id"),  # Counts how many staff fall into this fund
                raw_amount=Sum(
                    Case(
                        When(
                            fund_id=1,  # Fund 1 uses 21%
                            then=F("basic_salary") * Value(0.21),
                        ),
                        default=F("basic_salary") * Value(0.20),  # Others use 20%
                        output_field=DecimalField(),
                    )
                ),
            )
        )

        # Construct final response
        results = {
            "salary": {
                "label": "Net Salary Payment",
                "branch_code": "201",
                "customer": "0",
                "ledger": "5834",
                "sub_ledger": "0",
                "amount": round_decimal(salary_raw),
            },
            "payee": {
                "label": "Total PAYE (Inc. 4% Employer)",
                "branch_code": "201",
                "customer": "0",
                "ledger": "5731",
                "sub_ledger": "0",
                "amount": round_decimal(payee_raw),
            },
            "zhsf": {
                "label": "Zanzibar Health Service Fund (7%)",
                "branch_code": "201",
                "customer": "0",
                "ledger": "5834",
                "sub_ledger": "0",
                "amount": round_decimal(zhsf_raw),
            },
            "pension_contributions": [
                {
                    "fund_name": item["name"],
                    "staff_count": item["staff_count"],  # Number of staff in this fund
                    "is_fund_1": item["fund_id"]
                    == 1,  # Helper to identify the 21% group
                    "branch_code": item["branch_code"],
                    "customer": item["customer"],
                    "ledger": item["ledger"],
                    "sub_ledger": item["sub_ledger"],
                    "amount": round_decimal(item["raw_amount"]),
                }
                for item in pension_query
            ],
        }

        return Response(results)
