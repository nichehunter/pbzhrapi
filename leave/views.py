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

from leave.models import *
from dictionary.models import DictionaryItem
from leave.serializers import *


#====================================================== leave type ====================================================
class LeaveTypeAdd(CreateAPIView):

    serializer_class = LeaveTypeSerializer

    def post(self, request):
        serializer = LeaveTypeSerializer(data=request.data, many=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LeaveTypeList(ListAPIView):
    queryset = LeaveType.objects.all()
    serializer_class = LeaveTypeListSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['code','name']
    ordering_fields = ['id','code','name']
    ordering = ['-id']


class LeaveTypeUpdate(CreateAPIView):

    serializer_class = LeaveTypeUpdateSerializer

    def put(self, request, pk):
        leave = LeaveType.objects.get(id=pk)
        serializer = LeaveTypeUpdateSerializer(leave, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#====================================================== leave type ====================================================
class LeaveDaysAdd(CreateAPIView):

    serializer_class = LeaveDaysSerializer

    def post(self, request):
        serializer = LeaveDaysSerializer(data=request.data, many=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LeaveDaysList(ListAPIView):
    queryset = LeaveDays.objects.all()
    serializer_class = LeaveDaysSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['leave_type__name','days']
    ordering_fields = ['id','leave_type__name','days']
    ordering = ['-id']


class LeaveDaysUpdate(CreateAPIView):

    serializer_class = LeaveDaysUpdateSerializer

    def put(self, request, pk):
        leave = LeaveDays.objects.get(id=pk)
        serializer = LeaveDaysUpdateSerializer(leave, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#====================================================== leave type ====================================================
class leaveApplicationFilter(django_filters.FilterSet):

    class Meta:
        model = LeaveApplication
        fields = {'year' : ['exact', 'in'], 'staff__id': ['exact', 'in'], 'leave_type__id': ['exact', 'in'], 'status__id': ['exact', 'in'], 'is_active': ['exact']}

class LeaveApplicationAdd(CreateAPIView):

    serializer_class = LeaveApplicationSerializer

    def post(self, request):
        serializer = LeaveApplicationSerializer(data=request.data, many=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LeaveApplicationList(ListAPIView):
    queryset = LeaveApplication.objects.all()
    serializer_class = LeaveApplicationListSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend,filters.SearchFilter,filters.OrderingFilter]
    filterset_class = leaveApplicationFilter
    search_fields = ['code','staff__full_name','staff__staff_opf','leave_type__name']
    ordering_fields = ['id','code','staff__full_name','staff__staff_opf','leave_type__name']
    ordering = ['-id']


class LeaveApplicationUpdate(CreateAPIView):

    serializer_class = LeaveApplicationUpdateSerializer

    def put(self, request, pk):
        leave = LeaveApplication.objects.get(id=pk)
        serializer = LeaveApplicationUpdateSerializer(leave, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LeaveApplicationChangeStatus(CreateAPIView):

    serializer_class = LeaveChangeStatusSerializer

    def put(self, request, pk):
        leave = LeaveApplication.objects.get(id=pk)
        serializer = LeaveChangeStatusSerializer(leave, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class LeaveApplicationDetail(APIView):

    serializer_class = LeaveApplicationListSerializer

    def get(self, request, pk):
        leave = LeaveApplication.objects.get(id=pk)
        serializer = LeaveApplicationListSerializer(leave, many=False)
        return JsonResponse(serializer.data, safe=False)


#====================================================== leave counting ====================================================
class leaveCountingFilter(django_filters.FilterSet):

    class Meta:
        model = LeaveCountingDays
        fields = {'year' : ['exact', 'in'], 'leave__id': ['exact', 'in'],'is_counted': ['exact']}


class LeaveCountingDaysAdd(CreateAPIView):

    serializer_class = LeaveCountingDaysSerializer

    def post(self, request):
        serializer = LeaveCountingDaysSerializer(data=request.data, many=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LeaveCountingDaysList(ListAPIView):
    queryset = LeaveCountingDays.objects.all()
    serializer_class = LeaveCountingDaysListSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend,filters.SearchFilter,filters.OrderingFilter]
    filterset_class = leaveCountingFilter
    search_fields = ['date','year']
    ordering_fields = ['id','date','year']
    ordering = ['-id']


class LeaveCountingDaysUpdate(CreateAPIView):

    serializer_class = LeaveCountingDaysUpdateSerializer

    def put(self, request, pk):
        leave = LeaveCountingDays.objects.get(id=pk)
        serializer = LeaveCountingDaysUpdateSerializer(leave, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#====================================================== leave type ====================================================
class LeaveDurationAdd(CreateAPIView):

    serializer_class = LeaveDurationSerializer

    def post(self, request):
        serializer = LeaveDurationSerializer(data=request.data, many=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LeaveDurationList(ListAPIView):
    queryset = LeaveDuration.objects.all()
    serializer_class = LeaveDurationSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['leave__code','leave__staff__full_name','leave__staff__staff_opf','leave__leave_type__name']
    ordering_fields = ['id','leave__code','leave__staff__full_name','leave__staff__staff_opf','leave__leave_type__name']
    ordering = ['-id']


class LeaveDurationUpdate(CreateAPIView):

    serializer_class = LeaveDurationUpdateSerializer

    def put(self, request, pk):
        leave = LeaveDuration.objects.get(id=pk)
        serializer = LeaveDurationUpdateSerializer(leave, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#====================================================== leave type ====================================================
class leaveAssignmentSearch(django_filters.FilterSet):

    class Meta:
        model = LeaveAssignment
        fields = {'assigned_to__id': ['exact', 'in'], 'is_active': ['exact'], 'leave__id': ['exact','in'],'leave__status__id': ['exact','in']}


class LeaveAssignmentAdd(CreateAPIView):

    serializer_class = LeaveAssignmentSerializer

    def post(self, request):
        serializer = LeaveAssignmentSerializer(data=request.data, many=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LeaveFowardAdd(CreateAPIView):

    serializer_class = LeaveAssignmentSerializer

    def post(self, request):
        serializer = LeaveAssignmentSerializer(data=request.data)
        if serializer.is_valid():
            leave = serializer.validated_data.get('leave')
            app = LeaveApplication.objects.filter(is_active=True, id = leave.id)
            ass = LeaveAssignment.objects.filter(is_active=True, leave__id = leave.id)
            ass.update(is_active=False)
            app.update(status=DictionaryItem.objects.get(id=62))
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LeaveAssignmentList(ListAPIView):
    queryset = LeaveAssignment.objects.all()
    serializer_class = LeaveAssignmentListSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend,filters.SearchFilter,filters.OrderingFilter]
    filterset_class = leaveAssignmentSearch
    search_fields = ['leave__code','assigned_to__full_name','assigned_to__staff_opf','leave__leave_type__name']
    ordering_fields = ['id','leave__code','assigned_to__full_name','assigned_to__staff_opf','leave__leave_type__name']
    ordering = ['-id']


class LeaveAssignmentUpdate(CreateAPIView):

    serializer_class = LeaveAssignmentUpdateSerializer

    def put(self, request, pk):
        leave = LeaveAssignment.objects.get(id=pk)
        serializer = LeaveAssignmentUpdateSerializer(leave, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#====================================================== leave type ====================================================
class LeaveApprovalAdd(CreateAPIView):

    serializer_class = LeaveApprovalSerializer

    def post(self, request):
        serializer = LeaveApprovalSerializer(data=request.data)
        if serializer.is_valid():
            leave = serializer.validated_data.get('leave')
            app = LeaveApplication.objects.filter(is_active=True, id = leave.id)
            ass = LeaveAssignment.objects.filter(is_active=True, leave__id = leave.id)
            ass.update(is_active=False)
            app.update(status=DictionaryItem.objects.get(id=47))
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LeaveApprovalList(ListAPIView):
    queryset = LeaveApproval.objects.all()
    serializer_class = LeaveApprovalSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['leave__code','approved_by__full_name','approved_by__staff_opf','leave__leave_type__name']
    ordering_fields = ['id','leave__code','approved_by__full_name','approved_by__staff_opf','leave__leave_type__name']
    ordering = ['-id']


class LeaveApprovalUpdate(CreateAPIView):

    serializer_class = LeaveApprovalUpdateSerializer

    def put(self, request, pk):
        leave = LeaveApproval.objects.get(id=pk)
        serializer = LeaveApprovalUpdateSerializer(leave, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#====================================================== leave type ====================================================
class leaveCommentSearch(django_filters.FilterSet):

    class Meta:
        model = LeaveComment
        fields = {'commented_by__id': ['exact', 'in'], 'leave__id': ['exact','in']}

class LeaveCommentAdd(CreateAPIView):

    serializer_class = LeaveCommentSerializer

    def post(self, request):
        serializer = LeaveCommentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LeaveCommentList(ListAPIView):
    queryset = LeaveComment.objects.all()
    serializer_class = LeaveCommentListSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend,filters.SearchFilter,filters.OrderingFilter]
    filterset_class = leaveCommentSearch
    search_fields = ['leave__code','commented_by__full_name','commented_by__staff_opf','leave__leave_type__name']
    ordering_fields = ['id','leave__code','commented_by__full_name','commented_by__staff_opf','leave__leave_type__name']
    ordering = ['-id']


class LeaveCommentUpdate(CreateAPIView):

    serializer_class = LeaveCommentUpdateSerializer

    def put(self, request, pk):
        leave = LeaveComment.objects.get(id=pk)
        serializer = LeaveCommentUpdateSerializer(leave, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#====================================================== leave type ====================================================
class LeaveAcceptedAdd(CreateAPIView):

    serializer_class = LeaveAcceptedSerializer

    def post(self, request):
        serializer = LeaveAcceptedSerializer(data=request.data)
        if serializer.is_valid():
            leave = serializer.validated_data.get('leave')
            app = LeaveApplication.objects.filter(is_active=True, id = leave.id)
            ass = LeaveAssignment.objects.filter(is_active=True, leave__id = leave.id)
            ass.update(is_active=False)
            app.update(status=DictionaryItem.objects.get(id=48))
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LeaveAcceptedList(ListAPIView):
    queryset = LeaveAccepted.objects.all()
    serializer_class = LeaveAcceptedSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['leave__code','accepted_by__full_name','accepted_by__staff_opf','leave__leave_type__name']
    ordering_fields = ['id','leave__code','accepted_by__full_name','accepted_by__staff_opf','leave__leave_type__name']
    ordering = ['-id']


class LeaveAcceptedUpdate(CreateAPIView):

    serializer_class = LeaveAcceptedUpdateSerializer

    def put(self, request, pk):
        leave = LeaveAccepted.objects.get(id=pk)
        serializer = LeaveAcceptedUpdateSerializer(leave, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#====================================================== leave type ====================================================
class LeaveRejectedAdd(CreateAPIView):

    serializer_class = LeaveRejectedSerializer

    def post(self, request):
        serializer = LeaveRejectedSerializer(data=request.data)
        if serializer.is_valid():
            leave = serializer.validated_data.get('leave')
            app = LeaveApplication.objects.filter(is_active=True, id = leave.id)
            ass = LeaveAssignment.objects.filter(is_active=True, leave__id = leave.id)
            ass.update(is_active=False)
            app.update(status=DictionaryItem.objects.get(id=49))
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LeaveRejectedList(ListAPIView):
    queryset = LeaveRejected.objects.all()
    serializer_class = LeaveRejectedSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['leave__code','rejected_by__full_name','rejected_by__staff_opf','leave__leave_type__name']
    ordering_fields = ['id','leave__code','rejected_by__full_name','rejected_by__staff_opf','leave__leave_type__name']
    ordering = ['-id']


class LeaveRejectedUpdate(CreateAPIView):

    serializer_class = LeaveRejectedUpdateSerializer

    def put(self, request, pk):
        leave = LeaveRejected.objects.get(id=pk)
        serializer = LeaveRejectedUpdateSerializer(leave, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#====================================================== leave type ====================================================
class LeaveCanceledAdd(CreateAPIView):

    serializer_class = LeaveCanceledSerializer

    def post(self, request):
        serializer = LeaveCanceledSerializer(data=request.data, many=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LeaveCanceledList(ListAPIView):
    queryset = LeaveCanceled.objects.all()
    serializer_class = LeaveCanceledSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['leave__code','canceled_by__full_name','canceled_by__staff_opf','leave__leave_type__name']
    ordering_fields = ['id','leave__code','canceled_by__full_name','canceled_by__staff_opf','leave__leave_type__name']
    ordering = ['-id']


class LeaveCanceledUpdate(CreateAPIView):

    serializer_class = LeaveCanceledUpdateSerializer

    def put(self, request, pk):
        leave = LeaveCanceled.objects.get(id=pk)
        serializer = LeaveCanceledUpdateSerializer(leave, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#====================================================== leave type ====================================================
class leaveBalanceSearch(django_filters.FilterSet):

    class Meta:
        model = LeaveBalance
        fields = {'year' : ['exact'],'staff__id': ['exact', 'in'], 'leave_type__id': ['exact', 'in'], 'is_used': ['exact'], 'is_expired': ['exact']}

class LeaveBalanceAdd(CreateAPIView):

    serializer_class = LeaveBalanceSerializer

    def post(self, request):
        serializer = LeaveBalanceSerializer(data=request.data, many=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LeaveBalanceList(ListAPIView):
    queryset = LeaveBalance.objects.all()
    serializer_class = LeaveBalanceSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend,filters.SearchFilter,filters.OrderingFilter]
    filterset_class = leaveBalanceSearch
    search_fields = ['balance','staff__full_name','staff__staff_opf']
    ordering_fields = ['id','balance','staff__full_name','staff__staff_opf']
    ordering = ['-id']


class LeaveBalanceUpdate(CreateAPIView):

    serializer_class = LeaveBalanceUpdateSerializer

    def put(self, request, pk):
        leave = LeaveBalance.objects.get(id=pk)
        serializer = LeaveBalanceUpdateSerializer(leave, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#====================================================== leave type ====================================================
class LeaveDaysAdd(CreateAPIView):

    serializer_class = LeaveDaysSerializer

    def post(self, request):
        serializer = LeaveDaysSerializer(data=request.data, many=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LeaveDaysList(ListAPIView):
    queryset = LeaveDays.objects.all()
    serializer_class = LeaveDaysSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['code','name']
    ordering_fields = ['id','code','name']
    ordering = ['-id']


class LeaveDaysUpdate(CreateAPIView):

    serializer_class = LeaveDaysUpdateSerializer

    def put(self, request, pk):
        leave = LeaveDays.objects.get(id=pk)
        serializer = LeaveDaysUpdateSerializer(leave, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#====================================================== leave type ====================================================
class rosterFilter(django_filters.FilterSet):

    class Meta:
        model = Roster
        fields = {'name' : ['exact', 'in'], 'number': ['exact', 'in']}

        
class RosterAdd(CreateAPIView):

    serializer_class = RosterSerializer

    def post(self, request):
        serializer = RosterSerializer(data=request.data, many=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RosterList(ListAPIView):
    queryset = Roster.objects.all()
    serializer_class = RosterSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend,filters.SearchFilter,filters.OrderingFilter]
    filterset_class = rosterFilter
    search_fields = ['number','name']
    ordering_fields = ['id','number','name']
    ordering = ['id']


class RosterUpdate(CreateAPIView):

    serializer_class = RosterUpdateSerializer

    def put(self, request, pk):
        leave = Roster.objects.get(id=pk)
        serializer = RosterUpdateSerializer(leave, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#====================================================== leave type ====================================================
class leaveRosterFilter(django_filters.FilterSet):

    class Meta:
        model = LeaveRoster
        fields = {'year' : ['exact', 'in'], 'staff__id': ['exact', 'in']}


class LeaveRosterAdd(CreateAPIView):

    serializer_class = LeaveRosterSerializer

    def post(self, request):
        serializer = LeaveRosterSerializer(data=request.data, many=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LeaveRosterList(ListAPIView):
    queryset = LeaveRoster.objects.all()
    serializer_class = LeaveRosterListSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend,filters.SearchFilter,filters.OrderingFilter]
    filterset_class = leaveRosterFilter
    search_fields = ['roaster__name','staff__full_name','staff__staff_opf','year']
    ordering_fields = ['id','roaster__name','staff__full_name','staff__staff_opf','year']
    ordering = ['-id']


class LeaveRosterUpdate(CreateAPIView):

    serializer_class = LeaveRosterUpdateSerializer

    def put(self, request, pk):
        leave = LeaveRoster.objects.get(id=pk)
        serializer = LeaveRosterUpdateSerializer(leave, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#====================================================== leave type ====================================================
class LeaveBlockedPeriordAdd(CreateAPIView):

    serializer_class = LeaveBlockedPeriordSerializer

    def post(self, request):
        serializer = LeaveBlockedPeriordSerializer(data=request.data, many=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LeaveBlockedPeriordList(ListAPIView):
    queryset = LeaveBlockedPeriord.objects.all()
    serializer_class = LeaveBlockedPeriordSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['start_date','end_date']
    ordering_fields = ['id','start_date','end_date']
    ordering = ['-id']


class LeaveBlockedPeriordUpdate(CreateAPIView):

    serializer_class = LeaveBlockedPeriordUpdateSerializer

    def put(self, request, pk):
        leave = LeaveBlockedPeriord.objects.get(id=pk)
        serializer = LeaveBlockedPeriordUpdateSerializer(leave, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#====================================================== leave type ====================================================
class holidaySearch(django_filters.FilterSet):

    class Meta:
        model = PublicHoliday
        fields = {'is_active' : ['exact'],}

class PublicHolidayAdd(CreateAPIView):

    serializer_class = PublicHolidaySerializer

    def post(self, request):
        serializer = PublicHolidaySerializer(data=request.data, many=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PublicHolidayList(ListAPIView):
    queryset = PublicHoliday.objects.all()
    serializer_class = PublicHolidaySerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend,filters.SearchFilter,filters.OrderingFilter]
    filterset_class = holidaySearch
    search_fields = ['date','name']
    ordering_fields = ['id','date','name']
    ordering = ['-id']


class PublicHolidayUpdate(CreateAPIView):

    serializer_class = PublicHolidayUpdateSerializer

    def put(self, request, pk):
        leave = PublicHoliday.objects.get(id=pk)
        serializer = PublicHolidayUpdateSerializer(leave, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#====================================================== leave type ====================================================
class WorkingDaysAdd(CreateAPIView):

    serializer_class = WorkingDaysSerializer

    def post(self, request):
        serializer = WorkingDaysSerializer(data=request.data, many=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class WorkingDaysList(ListAPIView):
    queryset = WorkingDays.objects.all()
    serializer_class = WorkingDaysListSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name','type_work__dictionary_item_name']
    ordering_fields = ['id','name','type_work__dictionary_item_name']
    ordering = ['id']


class WorkingDaysUpdate(CreateAPIView):

    serializer_class = WorkingDaysUpdateSerializer

    def put(self, request, pk):
        leave = WorkingDays.objects.get(id=pk)
        serializer = WorkingDaysUpdateSerializer(leave, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)