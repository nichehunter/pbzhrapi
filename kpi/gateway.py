from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.http.response import JsonResponse
import statistics

import json
import datetime
from decimal import Decimal
from django.db import transaction
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
from gateway.service import *


# ===================================================================================
# KPI Add Functions
# ===================================================================================
class StaffKPIPeriodFilter(django_filters.FilterSet):

    class Meta:
        model = StaffKPIPeriod
        fields = {
            "id": ["exact", "in"],
            "window__id": ["exact", "in"],
            "staff__id": ["exact", "in"],
            "station_id": ["exact", "in"],
            "station_supervisor__id": ["exact", "in"],
            "status": ["exact"],
        }


class StaffKPIPeriodList(ListAPIView):
    queryset = StaffKPIPeriod.objects.all()
    serializer_class = StaffKPIPeriodListSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [
        django_filters.rest_framework.DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = StaffKPIPeriodFilter
    search_fields = [
        "^status",
        "^staff__staff_opf",
        "^staff__full_name",
        "^station_name",
    ]
    ordering_fields = [
        "id",
        "staff__staff_opf",
        "staff__full_name",
        "status",
    ]
    ordering = ["-id"]


# ===================================================================================
# KPI Add Functions
# ===================================================================================
class SupervisorKPIPeriodsListView(APIView):
    """Returns all KPI periods assigned to a supervisor where window status is open.

    Query Parameters:
      - search: Matches against staff full name, staff OPF/PF number, or period status.
      - supervisor_id: ID of the supervisor staff member.
    """

    def get(self, request, supervisor):
        supervisor_id = supervisor
        search_query = request.query_params.get("search", "").strip()

        if not supervisor_id:
            return Response(
                {"error": "The 'supervisor' path parameter is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        queryset = (
            StaffKPIPeriod.objects.filter(
                station_supervisor_id=supervisor_id,
                window__status="open",
            )
            .select_related("staff", "window")
            .order_by("-submitted_at", "-recorded_at")
        )

        if search_query:
            search_filter = (
                Q(staff__full_name__istartswith=search_query)
                | Q(staff__staff_opf__istartswith=search_query)
                | Q(status__icontains=search_query)
            )

            if " " in search_query:
                name_parts = search_query.split()
                search_filter |= Q(staff__full_name__icontains=" ".join(name_parts))

            queryset = queryset.filter(search_filter)

        periods_data = []
        for period in queryset:
            staff_opf = getattr(period.staff, "staff_opf", None) or "N/A"

            submission_date = (
                timezone.localtime(period.submitted_at).strftime("%Y-%m-%d %H:%M")
                if period.submitted_at
                else None
            )

            periods_data.append(
                {
                    "id": period.id,
                    "staff_opf": staff_opf,
                    "staff_name": str(period.staff),
                    "submission_date": submission_date,
                    "window_code": period.window.code,
                    "status": period.status,
                }
            )

        return Response(
            {
                "count": len(periods_data),
                "results": periods_data,
            },
            status=status.HTTP_200_OK,
        )


# ===================================================================================
# KPI Add Functions
# ===================================================================================
class StaffKPIFormStructureView(APIView):
    """Returns KPI Form structure for a staff period.

    Query Parameters:
      - mode: 'all' (default) returns the full structure with pre-filled saved draft values.
              'saved_only' (or only_saved=true) returns strictly saved items filtered to
              active sections/key results/measures.
    """

    def resolve_staff_kpi_scopes(self, kpi_period):
        """Returns a list of valid scope strings for a staff member."""
        station = (kpi_period.station or "").lower()

        # 1. Head Office Department Hierarchy Traversal
        if station == "department":
            scopes = []
            current_dept_id = kpi_period.station_id

            while current_dept_id:
                try:
                    dept = Department.objects.select_related("parent_department").get(
                        pk=current_dept_id
                    )

                    if dept.department_name and dept.department_name not in scopes:
                        scopes.append(dept.department_name)

                    if dept.parent_department:
                        current_dept_id = dept.parent_department.id
                    else:
                        break
                except (Department.DoesNotExist, ValueError, TypeError):
                    break

            if not scopes and kpi_period.station_name:
                scopes.append(kpi_period.station_name)

            return scopes if scopes else ["ALL"]

        # 2. Branch Type Handling ("Islamic Bank" -> "islamic")
        elif station == "branch":
            raw_type = kpi_period.station_type or "conventional"
            first_word = raw_type.strip().split()[0].lower()
            return [first_word]

        # 3. Fallback
        return [kpi_period.station_name] if kpi_period.station_name else ["ALL"]

    def get(self, request, pk):
        try:
            kpi_period = StaffKPIPeriod.objects.select_related("staff", "window").get(
                pk=pk
            )
        except StaffKPIPeriod.DoesNotExist:
            return Response(
                {"error": "Staff KPI Period not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Determine mode from query parameters: ?mode=saved_only or ?only_saved=true
        mode = request.query_params.get("mode", "all").lower()
        only_saved = (
            mode == "saved_only"
            or request.query_params.get("only_saved", "").lower() == "true"
        )

        # Get target scopes for this staff member
        target_scopes = self.resolve_staff_kpi_scopes(kpi_period)

        # Fetch existing saved KPI items
        existing_items = StaffKPIItem.objects.filter(kpi_period=kpi_period)
        existing_items_map = {
            item.performance_measure_id: item for item in existing_items
        }

        # Filter measures if only_saved mode is activated
        measures_queryset = KPIPerformanceMeasure.objects.filter(is_active=True)
        if only_saved:
            measures_queryset = measures_queryset.filter(
                id__in=existing_items_map.keys()
            )

        # Match Key Results where department matches target scopes or "ALL"
        scope_filter = Q(department__in=target_scopes) | Q(department__iexact="ALL")

        key_results_prefetch = Prefetch(
            "key_results",
            queryset=KPIKeyResult.objects.filter(
                scope_filter, is_active=True
            ).prefetch_related(Prefetch("measures", queryset=measures_queryset)),
        )

        # Prefetch active section weights to prevent N+1 queries
        weights_prefetch = Prefetch(
            "weights",
            queryset=KPISectionWeight.objects.filter(is_active=True),
            to_attr="active_weights",
        )

        # Fetch active KPI sections with preloaded weights and key results
        sections = (
            KPISection.objects.filter(is_active=True)
            .prefetch_related(key_results_prefetch, weights_prefetch)
            .order_by("id")
        )

        sections_data = []

        for section in sections:
            # Extract section weight from prefetched active weights
            active_weight_obj = (
                section.active_weights[0] if section.active_weights else None
            )
            section_weight = (
                str(active_weight_obj.weight) if active_weight_obj else "0.00"
            )

            key_results_data = []

            for kr in section.key_results.all():
                measures_data = []

                for measure in kr.measures.all():
                    saved_item = existing_items_map.get(measure.id)

                    # In only_saved mode, skip measures that haven't been saved yet
                    if only_saved and not saved_item:
                        continue

                    measures_data.append(
                        {
                            "id": measure.id,
                            "description": measure.description,
                            "unit_of_measure": measure.unit_of_measure,
                            "saved_item": (
                                {
                                    "item_id": saved_item.id,
                                    "target_value": str(saved_item.target_value),
                                    "actual_value": str(saved_item.actual_value),
                                    "weighting": str(saved_item.weighting),
                                    "rating": str(saved_item.rating),
                                    "weighting_rating": str(
                                        saved_item.weighting_rating
                                    ),
                                }
                                if saved_item
                                else None
                            ),
                        }
                    )

                # Only include key result if it has visible measures
                if measures_data:
                    key_results_data.append(
                        {
                            "id": kr.id,
                            "title": kr.title,
                            "description": kr.description,
                            "scope": kr.department,
                            "measures": measures_data,
                        }
                    )

            # Only include section if it has matching key results
            if key_results_data:
                sections_data.append(
                    {
                        "id": section.id,
                        "code": section.code,
                        "title": section.title,
                        "description": section.description,
                        "weight": section_weight,  # <-- Added Section Weight here
                        "key_results": key_results_data,
                    }
                )

        response_payload = {
            "period": {
                "id": kpi_period.id,
                "window_code": kpi_period.window.code,
                "window_title": kpi_period.window.title,
                "window_status": kpi_period.window.status,
                "status": kpi_period.status,
                "total_score": str(kpi_period.total_score),
                "staff_name": str(kpi_period.staff),
                "staff_opf": str(kpi_period.staff.staff_opf),
                "station_type": kpi_period.station_type,
                "station_name": kpi_period.station_name,
                "resolved_scopes": target_scopes,
                "mode": "saved_only" if only_saved else "all",
            },
            "sections": sections_data,
        }

        return Response(response_payload, status=status.HTTP_200_OK)


# ===================================================================================
# KPI Add Functions
# ===================================================================================
class CreateStaffKPIItemsView(APIView):
    """Bulk creates, updates, or cleans up StaffKPIItem records without destroying PKs."""

    def post(self, request, pk):
        try:
            kpi_period = StaffKPIPeriod.objects.get(pk=pk)
        except StaffKPIPeriod.DoesNotExist:
            return Response(
                {"error": "Staff KPI Period not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if kpi_period.status not in ["draft", "rejected", "submitted"]:
            return Response(
                {
                    "error": (
                        "Cannot modify KPIs for a period that is approved, or locked."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        items_data = request.data.get("items", [])
        is_submit = request.data.get("submit", False)

        if not isinstance(items_data, list) or not items_data:
            return Response(
                {"error": "An 'items' list payload is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            # 1. Map existing database items by performance_measure_id
            existing_items = StaffKPIItem.objects.filter(kpi_period=kpi_period)
            existing_items_map = {
                item.performance_measure_id: item for item in existing_items
            }

            items_to_create = []
            items_to_update = []
            processed_measure_ids = set()
            total_weighted_score = Decimal("0.00")

            for item_data in items_data:
                measure_id = item_data["performance_measure_id"]
                processed_measure_ids.add(measure_id)

                weighting = Decimal(str(item_data.get("weighting", 0)))
                rating = Decimal(str(item_data.get("rating", 0)))
                weighting_rating = Decimal(str(item_data.get("weighting_rating", 0)))
                target_val = item_data.get("target_value", "0.00")
                actual_val = Decimal(str(item_data.get("actual_value", 0)))

                total_weighted_score += weighting_rating

                if measure_id in existing_items_map:
                    # 2. UPDATE existing instance if present
                    item = existing_items_map[measure_id]
                    item.section_id = item_data["section_id"]
                    item.key_result_id = item_data["key_result_id"]
                    item.target_value = target_val
                    item.actual_value = actual_val
                    item.weighting = weighting
                    item.rating = rating
                    item.weighting_rating = weighting_rating

                    items_to_update.append(item)
                else:
                    # 3. CREATE new instance if missing
                    items_to_create.append(
                        StaffKPIItem(
                            kpi_period=kpi_period,
                            section_id=item_data["section_id"],
                            key_result_id=item_data["key_result_id"],
                            performance_measure_id=measure_id,
                            target_value=target_val,
                            actual_value=actual_val,
                            weighting=weighting,
                            rating=rating,
                            weighting_rating=weighting_rating,
                        )
                    )

            # 4. Perform bulk DB operations
            if items_to_create:
                StaffKPIItem.objects.bulk_create(items_to_create)

            if items_to_update:
                StaffKPIItem.objects.bulk_update(
                    items_to_update,
                    fields=[
                        "section_id",
                        "key_result_id",
                        "target_value",
                        "actual_value",
                        "weighting",
                        "rating",
                        "weighting_rating",
                    ],
                )

            # 5. Delete only items removed from the form payload by the user
            items_to_remove = set(existing_items_map.keys()) - processed_measure_ids
            if items_to_remove:
                StaffKPIItem.objects.filter(
                    kpi_period=kpi_period,
                    performance_measure_id__in=items_to_remove,
                ).delete()

            # 6. Update period aggregate score and status
            kpi_period.total_score = total_weighted_score
            if is_submit:
                kpi_period.status = "submitted"
            kpi_period.save()

        return Response(
            {
                "message": (
                    "KPIs submitted successfully."
                    if is_submit
                    else "KPI draft saved successfully."
                ),
                "total_score": str(total_weighted_score),
                "status": kpi_period.status,
            },
            status=status.HTTP_200_OK,
        )


# ===================================================================================
# KPI Add Functions
# ===================================================================================
class SubmitStaffKPIView(APIView):
    """API endpoint for a staff member to formally submit their KPI evaluation for supervisor approval."""

    def post(self, request, pk):
        try:
            kpi_period = StaffKPIPeriod.objects.select_related(
                "staff", "station_supervisor", "window"
            ).get(pk=pk)
        except StaffKPIPeriod.DoesNotExist:
            return Response(
                {"error": "Staff KPI Period not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if kpi_period.status not in ["draft", "rejected"]:
            return Response(
                {
                    "error": f"Cannot submit KPI period currently in '{kpi_period.get_status_display()}' status."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        default_comment = (
            f"KPI submission submitted for approval by {kpi_period.staff.full_name} "
            f"({getattr(kpi_period.staff, 'staff_opf', 'N/A')})."
        )
        final_comment = default_comment.strip()

        with transaction.atomic():
            now = timezone.now()
            kpi_period.status = "submitted"
            kpi_period.submitted_at = now
            kpi_period.save(update_fields=["status", "submitted_at"])

            StaffKPISubmissionLog.objects.create(
                kpi_period=kpi_period,
                action="submitted",
                actor=kpi_period.staff,
                comments=final_comment,
            )

            supervisor = kpi_period.station_supervisor
            email_sent = False

            if supervisor and getattr(supervisor, "email", None):
                staff_opf = getattr(kpi_period.staff, "staff_opf", "N/A")

                local_submission_time = timezone.localtime(now).strftime(
                    "%Y-%m-%d %H:%M"
                )

                try:
                    html_message = generate_kpi_submission_html_email(
                        supervisor_name=getattr(
                            supervisor, "full_name", str(supervisor)
                        ),
                        staff_name=str(kpi_period.staff),
                        staff_pf=staff_opf,
                        window_title=kpi_period.window.title,
                        submission_date=local_submission_time,
                        comments=final_comment,
                    )

                    # Dispatch payload using HTML content
                    email_sent = send_email(
                        email=supervisor.email,
                        subject=f"KPI Submission for Approval: {kpi_period.staff} ({staff_opf})",
                        message=html_message,
                    )

                except Exception as e:
                    print(
                        f"Failed to send email to supervisor {supervisor.email}: {str(e)}"
                    )

        return Response(
            {
                "message": "KPI submitted successfully for supervisor approval.",
                "period_id": kpi_period.id,
                "status": kpi_period.status,
                "submitted_at": (
                    kpi_period.submitted_at.isoformat()
                    if kpi_period.submitted_at
                    else None
                ),
                "email_notification_sent": email_sent,
            },
            status=status.HTTP_200_OK,
        )


# ===================================================================================
# KPI Add Functions
# ===================================================================================
class ApproveStaffKPIPeriodView(APIView):
    """API Endpoint for supervisors to approve a submitted Staff KPI Period.

    Payload Requirements:
      - kpi_period_id (int)
      - supervisor_id (int)
      - comments (str) [Mandatory]
    """

    def post(self, request):
        kpi_period_id = request.data.get("kpi_period_id")
        supervisor_id = request.data.get("supervisor_id")
        comments = request.data.get("comments", "").strip()

        # 1. Input Validations
        if not kpi_period_id or not supervisor_id:
            return Response(
                {"error": "Both 'kpi_period_id' and 'supervisor_id' are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not comments:
            return Response(
                {"error": "Approval comments/remarks are mandatory."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 2. Retrieve resources
        kpi_period = get_object_or_404(StaffKPIPeriod, id=kpi_period_id)
        supervisor = get_object_or_404(Staff, id=supervisor_id)

        # 3. Status Validation
        if kpi_period.status != "submitted":
            return Response(
                {
                    "error": f"Cannot approve KPI period with current status '{kpi_period.status}'. It must be 'submitted'."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        now = timezone.now()
        local_approval_date = timezone.localtime(now).strftime("%Y-%m-%d %H:%M")

        # Extract names & PF numbers safely
        supervisor_full_name = getattr(supervisor, "full_name", str(supervisor))
        staff_full_name = getattr(kpi_period.staff, "full_name", str(kpi_period.staff))
        staff_pf = (
            getattr(kpi_period.staff, "pf_number", None)
            or getattr(kpi_period.staff, "staff_opf", None)
            or "N/A"
        )

        # 4. Atomic Database Transaction
        with transaction.atomic():
            # Update StaffKPIPeriod status & approval details
            kpi_period.status = "approved"
            kpi_period.approver_name = supervisor_full_name
            kpi_period.approved_by = supervisor.id
            kpi_period.approved_at = now
            kpi_period.save()

            # Record action in StaffKPISubmissionLog
            StaffKPISubmissionLog.objects.create(
                kpi_period=kpi_period,
                action="approved",
                actor=supervisor,
                comments=comments,
            )

        # 5. Dispatch Email to HR
        hr_email = config("HR_EMAIL")

        html_message = generate_hr_kpi_approval_html_email(
            supervisor_name=supervisor_full_name,
            staff_name=staff_full_name,
            staff_pf=staff_pf,
            window_title=kpi_period.window.title,
            approval_date=local_approval_date,
            comments=comments,
            total_score=str(kpi_period.total_score),
        )

        email_sent = send_email(
            email=hr_email,
            subject=f"KPI Approved: {staff_full_name} ({staff_pf}) - {kpi_period.window.title}",
            message=html_message,
        )

        return Response(
            {
                "message": "KPI Period approved successfully.",
                "kpi_period_id": kpi_period.id,
                "status": kpi_period.status,
                "approved_at": timezone.localtime(kpi_period.approved_at).isoformat(),
                "email_sent_to_hr": email_sent,
            },
            status=status.HTTP_200_OK,
        )


# ===================================================================================
# KPI Add Functions
# ===================================================================================
class RejectStaffKPIPeriodView(APIView):
    """API Endpoint for supervisors to reject/return a Staff KPI Period for corrections.

    Payload Requirements:
      - kpi_period_id (int)
      - supervisor_id (int)
      - comments (str) [Mandatory]
    """

    def post(self, request):
        kpi_period_id = request.data.get("kpi_period_id")
        supervisor_id = request.data.get("supervisor_id")
        comments = request.data.get("comments", "").strip()

        if not kpi_period_id or not supervisor_id:
            return Response(
                {"error": "Both 'kpi_period_id' and 'supervisor_id' are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not comments:
            return Response(
                {
                    "error": "Feedback/rejection comments are required to explain what needs correction."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        kpi_period = get_object_or_404(StaffKPIPeriod, id=kpi_period_id)
        supervisor = get_object_or_404(Staff, id=supervisor_id)

        if kpi_period.status != "submitted":
            return Response(
                {
                    "error": f"Cannot return KPI period with status '{kpi_period.status}'. It must be in 'submitted' status."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        now = timezone.now()
        local_rejection_date = timezone.localtime(now).strftime("%Y-%m-%d %H:%M")

        supervisor_full_name = getattr(supervisor, "full_name", str(supervisor))
        staff_full_name = getattr(kpi_period.staff, "full_name", str(kpi_period.staff))
        staff_email = getattr(kpi_period.staff, "email", None)

        with transaction.atomic():
            kpi_period.status = "rejected"
            kpi_period.save()

            StaffKPISubmissionLog.objects.create(
                kpi_period=kpi_period,
                action="rejected",
                actor=supervisor,
                comments=comments,
            )

        email_sent = False
        if staff_email:
            html_message = generate_staff_kpi_rejection_html_email(
                staff_name=staff_full_name,
                supervisor_name=supervisor_full_name,
                window_title=kpi_period.window.title,
                rejection_date=local_rejection_date,
                comments=comments,
            )

            email_sent = send_email(
                email=staff_email,
                subject=f"KPI Appraisal Returned for Corrections: {kpi_period.window.title}",
                message=html_message,
            )

        return Response(
            {
                "message": "KPI Period returned to staff for corrections successfully.",
                "kpi_period_id": kpi_period.id,
                "status": kpi_period.status,
                "email_sent_to_staff": email_sent,
            },
            status=status.HTTP_200_OK,
        )
