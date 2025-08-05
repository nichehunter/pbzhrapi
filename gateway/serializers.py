from rest_framework import fields, serializers
import json
import datetime
from controller.models import *
from dictionary.models import DictionaryItem


#================================================ export ===============================================
class DictionaryItemSerializerExport(serializers.ModelSerializer):
    class Meta:
        model = DictionaryItem
        fields = ('id','dictionary_item_name')
        read_only_fields = ('id',)


class BranchExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = ('id','branch_code','branch_name')
        read_only_fields = ('id',)

class DepartmentExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ('id','department_code','department_name')
        read_only_fields = ('id',)


#================================================ export ===============================================
class StaffDepartmentSerializer(serializers.ModelSerializer):
    branch = BranchExportSerializer(read_only=True)
    department = DepartmentExportSerializer(read_only=True)
    title = DictionaryItemSerializerExport(read_only=True)
    class Meta:
        model = StaffDepartment
        fields = ['branch', 'department', 'title', 'is_active']



#===============================staff serializer====================================================#
class StaffDataSerializer(serializers.ModelSerializer):
    active_departments = serializers.SerializerMethodField()
    gender = DictionaryItemSerializerExport(read_only=True)
    job_title = DictionaryItemSerializerExport(read_only=True)
    employment_status = DictionaryItemSerializerExport(read_only=True)
    class Meta:
        model = Staff
        fields = ('__all__')
        read_only_fields = ('id',)

    def get_active_departments(self, obj):
        active_departments = obj.staff_department.filter(is_active=True)
        return StaffDepartmentSerializer(active_departments, many=True).data