from rest_framework import fields, serializers
import json
import datetime
from controller.models import *
from dictionary.models import DictionaryItem
from kpi.models import *


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


class StaffExportSerializer(serializers.ModelSerializer):
    gender = DictionaryItemSerializerExport(read_only=True)
    class Meta:
        model = Staff
        fields = ('id','staff_opf','staff_cpf','full_name','gender','phone_number')
        read_only_fields = ('id',)



#================================================ kpi ===============================================
class KPISerializer(serializers.ModelSerializer):
    class Meta:
        model = Kpi
        fields = ('__all__')
        read_only_fields = ('id',)


class KPIListSerializer(serializers.ModelSerializer):
    department = DepartmentExportSerializer(read_only=True)
    branch = BranchExportSerializer(read_only=True)
    level = DictionaryItemSerializerExport(read_only=True)
    class Meta:
        model = Kpi
        fields = ('__all__')
        read_only_fields = ('id',)


class StaffKPISerializer(serializers.ModelSerializer):
    staff = StaffExportSerializer(read_only=True)
    class Meta:
        model = StaffKPI
        fields = ('__all__')
        read_only_fields = ('id',)