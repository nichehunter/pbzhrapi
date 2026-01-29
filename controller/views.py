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
from controller.serializers import *


#====================================================== person view ====================================================
class PersonAdd(CreateAPIView):

    serializer_class = PersonSerializer

    def post(self, request):
        serializer = PersonSerializer(data=request.data, many=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PersonList(ListAPIView):
    queryset = Person.objects.all()
    serializer_class = PersonSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['code','full_name']
    ordering_fields = ['id','code','full_name']
    ordering = ['-id']


class PersonUpdate(CreateAPIView):

    serializer_class = PersonUpdateSerializer

    def put(self, request, pk):
        person = Person.objects.get(id=pk)
        serializer = PersonUpdateSerializer(person, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#====================================================== staff view ====================================================
class staffSearch(django_filters.FilterSet):

    class Meta:
        model = Staff
        fields = {'staff_opf' : ['exact', 'in'], 'is_active' : ['exact']}

class staffBranchSearch(django_filters.FilterSet):

    class Meta:
        model = StaffDepartment
        fields = {'staff__id' : ['exact', 'in'],'staff__staff_opf' : ['exact', 'in'], 'is_active' : ['exact']}

class StaffAdd(CreateAPIView):

    serializer_class = StaffSerializer

    def post(self, request):
        serializer = StaffSerializer(data=request.data, many=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StaffList(ListAPIView):
    queryset = Staff.objects.all()
    serializer_class = StaffListSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = staffSearch
    search_fields = ['staff_opf','full_name']
    ordering_fields = ['id','staff_opf','full_name']
    ordering = ['staff_opf']


class StaffUpdate(CreateAPIView):

    serializer_class = StaffUpdateSerializer

    def put(self, request, pk):
        staff = Staff.objects.get(id=pk)
        serializer = StaffUpdateSerializer(staff, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StaffDetails(APIView):

    serializer_class = StaffListSerializer

    def get(self, request, pk):
        project = Staff.objects.get(id=pk)
        serializer = StaffListSerializer(project, many=False)
        return JsonResponse(serializer.data, safe=False)


class StaffBranchDetails(ListAPIView):
    queryset = StaffDepartment.objects.all()
    serializer_class = StaffBranchSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = staffBranchSearch
    search_fields = ['branch__branch_code','department__department_name','branch__branch_name','department__department_name']
    ordering_fields = ['id']
    ordering = ['-id']


class StaffUpdateStatus(CreateAPIView):

    serializer_class = StaffStatusSerializer

    def put(self, request, pk):
        staff = Staff.objects.get(id=pk)
        serializer = StaffStatusSerializer(staff, data=request.data)
        if serializer.is_valid():
            dataStatus = serializer.validated_data
            last_record = StaffDepartment.objects.filter(staff=staff).order_by('-id').first()
            if last_record:
                last_record.is_active = dataStatus["is_active"]
                last_record.save()
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#====================================================== qualification view ====================================================
class qualificationSearch(django_filters.FilterSet):

    class Meta:
        model = StaffQualification
        fields = {'staff__id' : ['exact', 'in']}


class StaffQualificationAdd(CreateAPIView):

    serializer_class = StaffQualificationSerializer

    def post(self, request):
        serializer = StaffQualificationSerializer(data=request.data, many=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StaffQualificationList(ListAPIView):
    queryset = StaffQualification.objects.all()
    serializer_class = StaffQualificationListSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = qualificationSearch
    search_fields = ['code','name','ended_year']
    ordering_fields = ['id','code','name','ended_year']
    ordering = ['-id']


class StaffQualificationRemove(APIView):

    serializer_class = StaffQualificationRemoveSerializer

    def post(self, request):
        serializer = StaffQualificationRemoveSerializer(data=request.data)
        if serializer.is_valid():
            dataId = serializer.validated_data
            StaffQualification.objects.filter(id=dataId['qualification']).delete()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#====================================================== supervisor view ====================================================
class supervisorSearch(django_filters.FilterSet):

    class Meta:
        model = Supervisor
        fields = {
            'staff__id' : ['exact', 'in'],
            'is_active' : ['exact']
        }


class SupervisorAdd(CreateAPIView):

    serializer_class = SupervisorSerializer

    def post(self, request):
        serializer = SupervisorSerializer(data=request.data, many=True)
        if serializer.is_valid():
            for x in serializer.validated_data:
                staff = x.get('staff')
                superv = Supervisor.objects.filter(is_active=True, staff__id = staff.id)
                branch = BranchManager.objects.filter(supervisor__staff__id=staff.id, is_active=True)
                depart = DepartmentHead.objects.filter(supervisor__staff__id=staff.id, is_active=True)
                if superv:
                    superv.update(is_active=False, doe=datetime.date.today())
                if branch:
                    branch.update(is_active=False, removed_at=datetime.date.today())
                if depart:
                    depart.update(is_active=False, removed_at=datetime.date.today())
            
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SupervisorList(ListAPIView):
    queryset = Supervisor.objects.all()
    serializer_class = SupervisorListSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = supervisorSearch
    search_fields = ['staff__staff_opf','staff__full_name']
    ordering_fields = ['id','staff__staff_opf','staff__full_name']
    ordering = ['-id']


class SupervisorUpdate(CreateAPIView):

    serializer_class = SupervisorUpdateSerializer

    def put(self, request, pk):
        staff = Supervisor.objects.get(id=pk)
        serializer = SupervisorUpdateSerializer(staff, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#====================================================== branch view ====================================================
class branchSearch(django_filters.FilterSet):

    class Meta:
        model = Branch
        fields = {'branch_type__id' : ['exact', 'in'],'branch_code' : ['exact', 'in'],'parent_branch__id' : ['exact', 'in']}


class BranchAdd(CreateAPIView):

    serializer_class = BranchSerializer

    def post(self, request):
        serializer = BranchSerializer(data=request.data, many=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BranchList(ListAPIView):
    queryset = Branch.objects.all()
    serializer_class = BranchListSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = branchSearch
    search_fields = ['branch_code','branch_name']
    ordering_fields = ['id','branch_code','branch_name']
    ordering = ['id']


class BranchUpdate(CreateAPIView):

    serializer_class = BranchUpdateSerializer

    def put(self, request, pk):
        branch = Branch.objects.get(id=pk)
        serializer = BranchUpdateSerializer(branch, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class BranchDetails(APIView):

    serializer_class = BranchListSerializer

    def get(self, request, pk):
        project = Branch.objects.get(id=pk)
        serializer = BranchListSerializer(project, many=False)
        return JsonResponse(serializer.data, safe=False)


#====================================================== branch view ====================================================
class departmentSearch(django_filters.FilterSet):

    class Meta:
        model = Department
        fields = {'department_code' : ['exact', 'in'], 'parent_department__id' : ['exact', 'in']}


class DepartmentAdd(CreateAPIView):

    serializer_class = DepartmentSerializer

    def post(self, request):
        serializer = DepartmentSerializer(data=request.data, many=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DepartmentAllList(ListAPIView):
    queryset = Department.objects.all()
    serializer_class = DepartmentListSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = departmentSearch
    search_fields = ['department_code','department_name']
    ordering_fields = ['id','department_code','department_name']
    ordering = ['department_name']


class DepartmentList(ListAPIView):
    queryset = Department.objects.filter(parent_department__isnull=True)
    serializer_class = DepartmentListSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = departmentSearch
    search_fields = ['department_code','department_name']
    ordering_fields = ['id','department_code','department_name']
    ordering = ['department_name']


class SubDepartmentList(ListAPIView):
    queryset = Department.objects.filter(parent_department__isnull=False)
    serializer_class = DepartmentListSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = departmentSearch
    search_fields = ['department_code','department_name']
    ordering_fields = ['id','department_code','department_name']
    ordering = ['department_name']


class DepartmentUpdate(CreateAPIView):

    serializer_class = DepartmentUpdateSerializer

    def put(self, request, pk):
        department = Department.objects.get(id=pk)
        serializer = DepartmentUpdateSerializer(department, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DepartmentDetails(APIView):

    serializer_class = DepartmentListSerializer

    def get(self, request, pk):
        project = Department.objects.get(id=pk)
        serializer = DepartmentListSerializer(project, many=False)
        return JsonResponse(serializer.data, safe=False)


#====================================================== branch view ====================================================
class branchManagerSearch(django_filters.FilterSet):

    class Meta:
        model = BranchManager
        fields = {'branch__id' : ['exact', 'in'],'is_active' : ['exact'],}


class BranchManagerAdd(CreateAPIView):

    serializer_class = BranchManagerSerializer

    def post(self, request):
        serializer = BranchManagerSerializer(data=request.data, many=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BranchManagerList(ListAPIView):
    queryset = BranchManager.objects.all()
    serializer_class = BranchManagerListSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = branchManagerSearch
    search_fields = ['supervisor__staff__staff_opf','branch__branch_name']
    ordering_fields = ['id','supervisor__staff__staff_opf','branch__branch_name']
    ordering = ['-id']


class BranchManagerUpdate(CreateAPIView):

    serializer_class = BranchManagerUpdateSerializer

    def put(self, request, pk):
        branch = BranchManager.objects.get(id=pk)
        serializer = BranchManagerUpdateSerializer(branch, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#====================================================== branch view ====================================================
class departHeadSearch(django_filters.FilterSet):

    class Meta:
        model = DepartmentHead
        fields = {'department__id' : ['exact', 'in'],'is_active' : ['exact'],}

class DepartmentHeadAdd(CreateAPIView):

    serializer_class = DepartmentHeadSerializer

    def post(self, request):
        serializer = DepartmentHeadSerializer(data=request.data, many=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DepartmentHeadList(ListAPIView):
    queryset = DepartmentHead.objects.all()
    serializer_class = DepartmentHeadListSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = departHeadSearch
    search_fields = ['supervisor__staff__staff_opf','department__department_name']
    ordering_fields = ['id','supervisor__staff__staff_opf','department__department_name']
    ordering = ['-id']


class DepartmentHeadUpdate(CreateAPIView):

    serializer_class = DepartmentHeadUpdateSerializer

    def put(self, request, pk):
        department = DepartmentHead.objects.get(id=pk)
        serializer = DepartmentHeadUpdateSerializer(department, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#====================================================== staff department view ====================================================
class staffDepartmentSearch(django_filters.FilterSet):
    department__id__not = django_filters.NumberFilter(field_name='department__id', exclude=True)
    branch__id__not = django_filters.NumberFilter(field_name='branch__id', exclude=True)
    class Meta:
        model = StaffDepartment
        fields = {'department__id' : ['exact', 'in'], 'branch__id' : ['exact', 'in'], 'staff__id' : ['exact', 'in'],'is_active': ['exact']}


class StaffDepartmentAdd(CreateAPIView):

    serializer_class = StaffDepartmentSerializer

    def post(self, request):
        serializer = StaffDepartmentSerializer(data=request.data, many=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StaffDepartmentChange(CreateAPIView):

    serializer_class = StaffDepartmentSerializer

    def post(self, request):
        serializer = StaffDepartmentSerializer(data=request.data)
        if serializer.is_valid():
            staff = serializer.validated_data.get('staff')
            depart = StaffDepartment.objects.filter(is_active=True, staff__id = staff.id)
            depart.update(is_active=False, removed_at=datetime.date.today())
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StaffDepartmentList(ListAPIView):
    queryset = StaffDepartment.objects.all()
    serializer_class = StaffDepartmentSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['staff__staff_opf','department__department_name','branch__branch_name']
    ordering_fields = ['id','staff__staff_opf','department__department_name','branch__branch_name']
    ordering = ['id']


class DepartmentStaffList(ListAPIView):
    queryset = StaffDepartment.objects.filter(is_active=True)
    serializer_class = DepartmentStaffSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = staffDepartmentSearch
    search_fields = ['staff__staff_opf','department__department_name','branch__branch_name']
    ordering_fields = ['id','staff__staff_opf','department__department_name','branch__branch_name']
    ordering = ['id']


class StaffDepartmentFilter(ListAPIView):
    queryset = StaffDepartment.objects.filter(is_active=True)
    serializer_class = DepartmentStaffSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = staffDepartmentSearch
    search_fields = ['staff__staff_opf','department__department_name','branch__branch_name']
    ordering_fields = ['id','staff__staff_opf','department__department_name','branch__branch_name']
    ordering = ['id']



class StaffDepartmentUpdate(CreateAPIView):

    serializer_class = StaffDepartmentUpdateSerializer

    def put(self, request, pk):
        department = StaffDepartment.objects.get(id=pk)
        serializer = StaffDepartmentUpdateSerializer(department, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#====================================================== staff department view ====================================================
class StaffBenefitAdd(CreateAPIView):

    serializer_class = StaffBenefitSerializer

    def post(self, request):
        serializer = StaffBenefitSerializer(data=request.data, many=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StaffBenefitList(ListAPIView):
    queryset = StaffBenefit.objects.all()
    serializer_class = StaffBenefitSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['staff__staff_opf','benefit_provider','benefit_type__dictionary_item_name']
    ordering_fields = ['id','staff__staff_opf','benefit_provider','benefit_type__dictionary_item_name']
    ordering = ['-id']


class StaffBenefitUpdate(CreateAPIView):

    serializer_class = StaffBenefitUpdateSerializer

    def put(self, request, pk):
        staff = StaffBenefit.objects.get(id=pk)
        serializer = StaffBenefitUpdateSerializer(staff, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#====================================================== staff department view ====================================================
class StaffBenefitDependentAdd(CreateAPIView):

    serializer_class = StaffBenefitDependentSerializer

    def post(self, request):
        serializer = StaffBenefitDependentSerializer(data=request.data, many=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StaffBenefitDependentList(ListAPIView):
    queryset = StaffBenefitDependent.objects.all()
    serializer_class = StaffBenefitDependentSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['benefit__staff__staff_opf','benefit__benefit_provider','benefit__benefit_type__dictionary_item_name']
    ordering_fields = ['id','benefit__staff__staff_opf','benefit__benefit_provider','benefit__benefit_type__dictionary_item_name']
    ordering = ['-id']


class StaffBenefitDependentUpdate(CreateAPIView):

    serializer_class = StaffBenefitDependentUpdateSerializer

    def put(self, request, pk):
        staff = StaffBenefitDependent.objects.get(id=pk)
        serializer = StaffBenefitDependentUpdateSerializer(staff, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#====================================================== person view ====================================================
class documentSearch(django_filters.FilterSet):

    class Meta:
        model = Document
        fields = {'staff__id' : ['exact', 'in']}


class DocumentAdd(CreateAPIView):

    serializer_class = DocumentSerializer

    def post(self, request):
        serializer = DocumentSerializer(data=request.data, many=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DocumentList(ListAPIView):
    queryset = Document.objects.all()
    serializer_class = DocumentListSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = documentSearch
    search_fields = ['staff__staff_opf','document_name']
    ordering_fields = ['id','staff__staff_opf','document_name']
    ordering = ['-id']


class DocumentRemove(APIView):

    serializer_class = DocumentRemoveSerializer

    def post(self, request):
        serializer = DocumentRemoveSerializer(data=request.data)
        if serializer.is_valid():
            dataId = serializer.validated_data
            Document.objects.filter(id=dataId['document']).delete()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#====================================================== pension view ====================================================
class pensionSearch(django_filters.FilterSet):

    class Meta:
        model = StaffSecurityFund
        fields = {'fund__id' : ['exact', 'in'],'staff__id' : ['exact', 'in'],'fund__code': ['exact', 'in'],'fund__name': ['exact', 'in']}


class StaffSecurityFundAdd(CreateAPIView):

    serializer_class = StaffSecurityFundSerializer

    def post(self, request):
        serializer = StaffSecurityFundSerializer(data=request.data, many=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StaffSecurityFundList(ListAPIView):
    queryset = StaffSecurityFund.objects.all()
    serializer_class = StaffSecurityFundListSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = pensionSearch
    search_fields = ['staff__staff_opf','staff__full_name','fund__code','fund__name']
    ordering_fields = ['id','staff__staff_opf','staff__full_name','fund__code','fund__name']
    ordering = ['-id']


class StaffSecurityFundUpdate(CreateAPIView):

    serializer_class = StaffSecurityFundUpdateSerializer

    def put(self, request, pk):
        pensin = StaffSecurityFund.objects.get(id=pk)
        serializer = StaffSecurityFundUpdateSerializer(pensin, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)