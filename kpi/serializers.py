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


class KPISectionExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Section
        fields = ('id','code')
        read_only_fields = ('id',)

class KPIResultExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = KeyResult
        fields = ('id','name')
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


class StaffKPIListSerializer(serializers.ModelSerializer):
    staff = StaffExportSerializer(read_only=True)
    class Meta:
        model = StaffKPI
        fields = ('__all__')
        read_only_fields = ('id',)

#================================================ kpi ===============================================
class KPISectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Section
        fields = ('__all__')
        read_only_fields = ('id',)


#================================================ kpi ===============================================
class KPIResultSerializer(serializers.ModelSerializer):
    section = KPISectionExportSerializer(read_only=True)
    class Meta:
        model = KeyResult
        fields = ('__all__')
        read_only_fields = ('id',)


#================================================ kpi ===============================================
class KPIPerfomanceSerializer(serializers.ModelSerializer):
    result = KPIResultExportSerializer(read_only=True)
    class Meta:
        model = Performance
        fields = ('__all__')
        read_only_fields = ('id',)


#================================================ kpi done ===============================================
class PerformanceSerializer(serializers.ModelSerializer):
    actual = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()
    weighting_rating = serializers.SerializerMethodField()

    class Meta:
        model = Performance
        fields = [
            "id", "performance_measure", "fy_target", "weighting",
            "is_active", "recorded_by", "recorded_at", "result",
            "actual", "rating", "weighting_rating"
        ]

    def get_actual(self, obj):
        staff_id = self.context.get("staff_id")
        kpi_id = self.context.get("kpi_id")
        try:
            staff_kpi = StaffKPI.objects.get(staff=staff_id, perfomance=obj, kpi=kpi_id)
            return staff_kpi.actual
        except StaffKPI.DoesNotExist:
            return None  # or 0

    def get_rating(self, obj):
        staff_id = self.context.get("staff_id")
        kpi_id = self.context.get("kpi_id")
        try:
            staff_kpi = StaffKPI.objects.get(staff=staff_id, perfomance=obj, kpi=kpi_id)
            return staff_kpi.rating
        except StaffKPI.DoesNotExist:
            return None  # or 0

    def get_weighting_rating(self, obj):
        staff_id = self.context.get("staff_id")
        kpi_id = self.context.get("kpi_id")
        try:
            staff_kpi = StaffKPI.objects.get(staff=staff_id, perfomance=obj, kpi=kpi_id)
            return staff_kpi.weighting_rating
        except StaffKPI.DoesNotExist:
            return None  # or 0



class KeyResultSerializer(serializers.ModelSerializer):
    performance = PerformanceSerializer(many=True, read_only=True)

    class Meta:
        model = KeyResult
        fields = [
            "id", "name", "weighting_percentage", "is_active",
            "recorded_by", "recorded_at", "section", "performance"
        ]


class SectionSerializer(serializers.ModelSerializer):
    result = KeyResultSerializer(many=True, read_only=True)

    class Meta:
        model = Section
        fields = [
            "id", "code", "name", "descriptions", "is_active",
            "recorded_by", "recorded_at", "kpi", "result"
        ]


class StaffKpiSerializer(serializers.ModelSerializer):
    section = SectionSerializer(many=True, read_only=True)

    class Meta:
        model = Kpi
        fields = [
            "id", "code", "name", "descriptions", "is_active", "year",
            "recorded_by", "recorded_at", "department", "branch", "level",
            "section"
        ]
