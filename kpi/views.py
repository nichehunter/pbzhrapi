from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.http.response import JsonResponse
from django.db import transaction

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
from django_filters import DateRangeFilter, DateFilter
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


# ====================================================== kpi ====================================================
class kpiSearch(django_filters.FilterSet):

    class Meta:
        model = Kpi
        fields = {
            "id": ["exact", "in"],
            "code": ["exact", "icontains"],
            "name": ["exact", "icontains"],
            "year": ["exact"],
            "department__id": ["exact"],
            "branch__id": ["exact"],
            "level__id": ["exact"],
            "is_active": ["exact"],
        }


class KPIList(ListAPIView):
    queryset = Kpi.objects.all()
    serializer_class = KPIListSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [
        django_filters.rest_framework.DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = kpiSearch
    search_fields = ["code", "name", "year"]
    ordering_fields = ["id", "code", "name"]
    ordering = ["-id"]


# ====================================================== kpi ====================================================
class sectionSearch(django_filters.FilterSet):

    class Meta:
        model = Section
        fields = {
            "id": ["exact", "in"],
            "code": ["exact", "icontains"],
            "name": ["exact", "icontains"],
            "kpi__id": ["exact"],
        }


class KPISectionList(ListAPIView):
    queryset = Section.objects.all()
    serializer_class = KPISectionSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [
        django_filters.rest_framework.DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = sectionSearch
    search_fields = ["code", "name"]
    ordering_fields = ["id", "code", "name"]
    ordering = ["code"]


# ====================================================== kpi ====================================================
class resultSearch(django_filters.FilterSet):

    class Meta:
        model = KeyResult
        fields = {
            "id": ["exact", "in"],
            "name": ["exact", "icontains"],
            "kpi__id": ["exact"],
            "section__id": ["exact"],
        }


class KPIResultList(ListAPIView):
    queryset = KeyResult.objects.all()
    serializer_class = KPIResultSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [
        django_filters.rest_framework.DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = resultSearch
    search_fields = ["name"]
    ordering_fields = ["id", "name"]
    ordering = ["section__code", "name"]


# ====================================================== kpi ====================================================
class perfomanceSearch(django_filters.FilterSet):

    class Meta:
        model = Performance
        fields = {
            "id": ["exact", "in"],
            "performance_measure": ["exact", "icontains"],
            "kpi__id": ["exact"],
            "result__id": ["exact"],
        }


class KPIPerformanceList(ListAPIView):
    queryset = Performance.objects.all()
    serializer_class = KPIPerfomanceSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [
        django_filters.rest_framework.DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = perfomanceSearch
    search_fields = ["performance_measure"]
    ordering_fields = ["id", "performance_measure"]
    ordering = ["result__section__code", "result__name", "performance_measure"]


# ====================================================== staff kpi ====================================================
class staffSearch(django_filters.FilterSet):

    class Meta:
        model = StaffKPI
        fields = {
            "id": ["exact", "in"],
            "kpi__id": ["exact"],
        }


class KPIStaffList(ListAPIView):
    serializer_class = StaffKPIListSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [
        django_filters.rest_framework.DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = staffSearch
    search_fields = ["staff__staff_opf", "staff__staff_cpf", "staff__full_name"]
    ordering_fields = ["id", "staff__full_name", "staff__staff_opf"]
    ordering = ["staff__full_name", "staff__staff_opf"]

    def get_queryset(self):
        qs = StaffKPI.objects.all().distinct("staff__full_name", "staff__staff_opf")
        return qs.order_by("staff__full_name", "staff__staff_opf")


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
            kpi_instance, context={"staff_id": staff_id, "kpi_id": kpi_instance.id}
        )

        return Response(serializer.data, status=status.HTTP_200_OK)


# ===================================================================================
# KPI Section Views
# ===================================================================================
class SectionFilter(django_filters.FilterSet):

    class Meta:
        model = KPISection
        fields = {
            "id": ["exact", "in"],
            "code": ["exact", "icontains"],
            "title": ["exact", "icontains"],
            "is_active": ["exact"],
        }


class KPISectionAdd(CreateAPIView):
    serializer_class = KPISectionSerializer

    def post(self, request):
        data = request.data

        is_bulk = isinstance(data, list)
        serializer = self.get_serializer(data=data, many=is_bulk)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class KPISectionList(ListAPIView):
    queryset = KPISection.objects.all()
    serializer_class = KPISectionSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [
        django_filters.rest_framework.DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = SectionFilter
    search_fields = ["^code", "^title"]
    ordering_fields = ["id", "code", "title"]
    ordering = ["-id"]


class KPISectionAllList(APIView):

    def get(self, request):
        sections = KPISection.objects.filter(is_active=True).values("id", "title")
        return Response({"results": list(sections)}, status=status.HTTP_200_OK)


# ===================================================================================
# KPI Key Result views
# ===================================================================================
class KeyResultFilter(django_filters.FilterSet):

    class Meta:
        model = KPIKeyResult
        fields = {
            "id": ["exact", "in"],
            "title": ["exact", "icontains"],
            "section__id": ["exact"],
        }


class KeyResultAdd(CreateAPIView):
    serializer_class = KPIKeyResultSerializer

    def post(self, request):
        data = request.data

        is_bulk = isinstance(data, list)
        serializer = self.get_serializer(data=data, many=is_bulk)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class KeyResultList(ListAPIView):
    queryset = KPIKeyResult.objects.all()
    serializer_class = KPIKeyResultListSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [
        django_filters.rest_framework.DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = KeyResultFilter
    search_fields = ["^title"]
    ordering_fields = ["id", "title"]
    ordering = ["-id"]


class KPIKeyResultAllList(APIView):

    def get(self, request):
        key_results = KPIKeyResult.objects.filter(is_active=True).values("id", "title")
        return Response({"results": list(key_results)}, status=status.HTTP_200_OK)


# ===================================================================================
# KPI KPI Performance Measure views
# ===================================================================================
class KPIPerformanceMeasureFilter(django_filters.FilterSet):

    class Meta:
        model = KPIPerformanceMeasure
        fields = {
            "id": ["exact", "in"],
            "description": ["exact", "icontains"],
            "key_result__id": ["exact"],
        }


class KPIPerformanceMeasureAdd(CreateAPIView):
    serializer_class = KPIPerformanceMeasureSerializer

    def post(self, request):
        data = request.data

        is_bulk = isinstance(data, list)
        serializer = self.get_serializer(data=data, many=is_bulk)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class KPIPerformanceMeasureList(ListAPIView):
    queryset = KPIPerformanceMeasure.objects.all()
    serializer_class = KPIPerformanceMeasureListSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [
        django_filters.rest_framework.DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = KPIPerformanceMeasureFilter
    search_fields = ["^description"]
    ordering_fields = [
        "id",
        "key_result__section__code",
        "key_result__title",
        "description",
    ]
    ordering = ["-id"]


# ===================================================================================
# KPI Window views
# ===================================================================================
class HRKPIWindowFilter(django_filters.FilterSet):

    class Meta:
        model = HRKPIWindow
        fields = {
            "id": ["exact", "in"],
            "code": ["exact", "icontains"],
            "title": ["exact", "icontains"],
            "status": ["exact"],
        }


class HRKPIWindowAdd(CreateAPIView):
    serializer_class = HRKPIWindowSerializer

    def generate_window_code(self):
        now = datetime.datetime.now()
        month_map = {
            1: "jan",
            2: "feb",
            3: "mar",
            4: "apr",
            5: "may",
            6: "jun",
            7: "jul",
            8: "aug",
            9: "sept",
            10: "oct",
            11: "nov",
            12: "dec",
        }

        month_str = month_map[now.month]
        day_str = now.strftime("%d")
        year_str = now.strftime("%y")

        return f"{month_str}{day_str}{year_str}"

    def post(self, request):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            generated_code = self.generate_window_code()

            with transaction.atomic():
                window = serializer.save(code=generated_code)

                active_staff_deps = (
                    StaffDepartment.objects.filter(
                        is_active=True,
                        staff__is_active=True,
                        staff__is_exit=False,
                    )
                    .select_related(
                        "staff",
                        "branch",
                        "branch__branch_type",
                        "department",
                    )
                    .order_by("staff_id", "-recorded_at")
                )

                latest_staff_assignments = {}
                for sd in active_staff_deps:
                    if sd.staff_id not in latest_staff_assignments:
                        latest_staff_assignments[sd.staff_id] = sd

                active_dept_heads = {
                    dh.department_id: getattr(dh.supervisor, "staff", None)
                    for dh in DepartmentHead.objects.filter(is_active=True)
                    .select_related("supervisor__staff")
                    .order_by("-recorded_at")
                }

                active_branch_mgrs = {
                    bm.branch_id: getattr(bm.supervisor, "staff", None)
                    for bm in BranchManager.objects.filter(is_active=True)
                    .select_related("supervisor__staff")
                    .order_by("-recorded_at")
                }

                kpi_periods_to_create = []

                for staff_id, sd in latest_staff_assignments.items():
                    branch = sd.branch
                    department = sd.department

                    if branch and branch.id == 1:
                        station = "department"
                        station_type = None
                        station_id = str(department.id) if department else None
                        station_name = (
                            department.department_name if department else None
                        )
                        station_supervisor = (
                            active_dept_heads.get(department.id) if department else None
                        )

                    else:
                        station = "branch"
                        station_type = (
                            branch.bank_type.dictionary_item_name
                            if branch and branch.bank_type
                            else None
                        )
                        station_id = str(branch.id) if branch else None
                        station_name = branch.branch_name if branch else None
                        station_supervisor = (
                            active_branch_mgrs.get(branch.id) if branch else None
                        )

                    kpi_periods_to_create.append(
                        StaffKPIPeriod(
                            window=window,
                            staff=sd.staff,
                            station=station,
                            station_type=station_type,
                            station_id=station_id,
                            station_name=station_name,
                            station_supervisor=station_supervisor,
                            status="draft",
                        )
                    )

                StaffKPIPeriod.objects.bulk_create(
                    kpi_periods_to_create,
                    ignore_conflicts=True,
                )

            return Response(
                {
                    "message": f"HR KPI Window created successfully and initiated KPI periods for {len(kpi_periods_to_create)} staff members.",
                    "data": serializer.data,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class HRKPIWindowList(ListAPIView):
    queryset = HRKPIWindow.objects.all()
    serializer_class = HRKPIWindowSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [
        django_filters.rest_framework.DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = HRKPIWindowFilter
    search_fields = ["^title"]
    ordering_fields = [
        "id",
        "code",
        "title",
        "status",
    ]
    ordering = ["-id"]


class HRKPIWindowDetailView(APIView):
    def get_object(self, pk):
        try:
            return HRKPIWindow.objects.get(pk=pk)
        except HRKPIWindow.DoesNotExist:
            return None

    def get(self, request, pk):
        window = self.get_object(pk)
        if not window:
            return Response(
                {"error": "HR KPI Window not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Fetch status counts in a single aggregated DB query
        status_counts = (
            StaffKPIPeriod.objects.filter(window_id=pk)
            .values("status")
            .annotate(count=Count("id"))
        )

        # Map query results into a dictionary
        status_map = {item["status"]: item["count"] for item in status_counts}

        # Construct the fixed key response format
        status_breakdown = {
            "draft": status_map.get("draft", 0),
            "submitted": status_map.get("submitted", 0),
            "approved": status_map.get("approved", 0),
            "rejected": status_map.get("rejected", 0),
            "archived": status_map.get("archived", 0),
        }

        # Sum total staff from status counts
        total_staff = sum(status_breakdown.values())

        serializer = HRKPIWindowSerializer(window)
        data = serializer.data
        data["total_staff"] = total_staff
        data["status_breakdown"] = status_breakdown

        return Response(data, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        window = self.get_object(pk)
        if not window:
            return Response(
                {"error": "HR KPI Window not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Partial update for flexible field updates (e.g., status, title, dates)
        serializer = HRKPIWindowSerializer(window, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()

            # Include the updated total staff count in the response
            total_staff = StaffKPIPeriod.objects.filter(window_id=pk).count()
            data = serializer.data
            data["total_staff"] = total_staff

            return Response(
                {
                    "message": "HR KPI Window updated successfully.",
                    "data": data,
                },
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ===================================================================================
# KPI Window views
# ===================================================================================
class StaffKPIPeriodFilter(django_filters.FilterSet):

    class Meta:
        model = StaffKPIPeriod
        fields = {
            "id": ["exact", "in"],
            "window__id": ["exact", "in"],
            "status": ["exact"],
        }


class KPIPeriodList(ListAPIView):
    queryset = StaffKPIPeriod.objects.all()
    serializer_class = KPIPeriodListSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [
        django_filters.rest_framework.DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = StaffKPIPeriodFilter
    search_fields = [
        "^staff__staff_opf",
        "^staff__full_name",
        "^status",
        "^station_name",
        "^station_supervisor__full_name",
        "^station_supervisor__staff_opf",
    ]
    ordering_fields = [
        "id",
        "staff__staff_opf",
        "staff__full_name",
        "status",
    ]
    ordering = ["-id"]
