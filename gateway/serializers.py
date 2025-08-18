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


#================================================ export ===============================================
class StaffDepartmentSerializer(serializers.ModelSerializer):
    branch = BranchExportSerializer(read_only=True)
    department = DepartmentExportSerializer(read_only=True)
    title = DictionaryItemSerializerExport(read_only=True)
    position = DictionaryItemSerializerExport(read_only=True)
    class Meta:
        model = StaffDepartment
        fields = ['branch', 'department', 'title', 'position', 'is_active']



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

#================================================ kpi ===============================================
class StaffKPISerializerRegister(serializers.ModelSerializer):
    class Meta:
        model = StaffKPI
        fields = ('__all__')
        read_only_fields = ('id',)

class KpiSerializerExport(serializers.ModelSerializer):
    class Meta:
        model = Kpi
        fields = ('__all__')
        read_only_fields = ('id',)

class PerformanceSerializerExport(serializers.ModelSerializer):
    class Meta:
        model = Performance
        fields = ('__all__')
        read_only_fields = ('id',)

class KeyResultSerializerExport(serializers.ModelSerializer):
    performance = serializers.SerializerMethodField()

    class Meta:
        model = KeyResult
        fields = ('__all__')
        read_only_fields = ('id',)

    def get_performance(self, obj):
        performances = obj.performance.all().order_by('id')
        return PerformanceSerializerExport(performances, many=True).data

class SectionSerializerExport(serializers.ModelSerializer):
    result = serializers.SerializerMethodField()

    class Meta:
        model = Section
        fields = ('__all__')
        read_only_fields = ('id',)

    def get_result(self, obj):
        key_results = obj.result.all().order_by('id')
        return KeyResultSerializerExport(key_results, many=True).data


class KpiListSerializerExport(serializers.ModelSerializer):
    section = serializers.SerializerMethodField()

    class Meta:
        model = Kpi
        fields = ('__all__')
        read_only_fields = ('id',)

    def get_section(self, obj):
        # Manually fetch and order Section objects
        sections = obj.section.all().order_by('id')
        return SectionSerializerExport(sections, many=True).data

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


class StaffKpiListSerializerExport(serializers.ModelSerializer):
    section = SectionSerializer(many=True, read_only=True)

    class Meta:
        model = Kpi
        fields = [
            "id", "code", "name", "descriptions", "is_active", "year",
            "recorded_by", "recorded_at", "department", "branch", "level",
            "section"
        ]




