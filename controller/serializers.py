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


class StaffExportSerializer(serializers.ModelSerializer):
    gender = DictionaryItemSerializerExport(read_only=True)
    class Meta:
        model = Staff
        fields = ('id','staff_opf','code','full_name','email','phone_number','address','gender')
        read_only_fields = ('id',)


class SupervisorExportSerializer(serializers.ModelSerializer):
    staff = StaffExportSerializer(read_only=True)
    supervise_type = DictionaryItemSerializerExport(read_only=True)
    class Meta:
        model = Supervisor
        fields = ('id','staff','code','dos','doe','supervise_type')
        read_only_fields = ('id',)

class SecurityFundExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = SecurityFund
        fields = ('id','code','name')
        read_only_fields = ('id',)

#----------------------person serializer-------------------------------------------------#

class PersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = ('__all__')
        read_only_fields = ('id',)


class PersonUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = ('__all__')
        read_only_fields = ('id','recorded_by')


#===============================staff serializer====================================================#
class StaffSerializer(serializers.ModelSerializer):
    class Meta:
        model = Staff
        fields = ('__all__')
        read_only_fields = ('id',)


class StaffListSerializer(serializers.ModelSerializer):
    gender = DictionaryItemSerializerExport(read_only=True)
    id_type = DictionaryItemSerializerExport(read_only=True)
    job_title = DictionaryItemSerializerExport(read_only=True)
    employment_status = DictionaryItemSerializerExport(read_only=True)
    class Meta:
        model = Staff
        fields = ('__all__')
        read_only_fields = ('id',)


class StaffUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Staff
        fields = ('__all__')
        read_only_fields = ('id','staff_opf','is_active','recorded_by')


class StaffStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Staff
        fields = ('id','is_active')
        read_only_fields = ('id',)


#===============================qualification serializer====================================================#
class StaffQualificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffQualification
        fields = ('__all__')
        read_only_fields = ('id',)


class StaffQualificationListSerializer(serializers.ModelSerializer):
    qualification_type = DictionaryItemSerializerExport(read_only=True)
    class Meta:
        model = StaffQualification
        fields = ('__all__')
        read_only_fields = ('id',)


class StaffQualificationRemoveSerializer(serializers.Serializer):
    qualification = serializers.IntegerField()

#===============================supervisor serializer====================================================#
class SupervisorDepartmentSerializer(serializers.ModelSerializer):
    branch = BranchExportSerializer(read_only=True)
    department = DepartmentExportSerializer(read_only=True)
    class Meta:
        model = StaffDepartment
        fields = ('id','staff','branch','department','is_active')
        read_only_fields = ('id',)


class SupervisorStaffSerializer(serializers.ModelSerializer):
    staff_department = serializers.SerializerMethodField()
    class Meta:
        model = Staff
        fields = ('id','staff_opf','code','full_name','staff_department')
        read_only_fields = ('id',)

    def get_staff_department(self, instance):
        doc = instance.staff_department.filter(is_active=True).order_by('-id')[:1]
        return SupervisorDepartmentSerializer(doc, many=True).data

class SupervisorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supervisor
        fields = ('__all__')
        read_only_fields = ('id',)


class SupervisorListSerializer(serializers.ModelSerializer):
    staff = SupervisorStaffSerializer(read_only=True)
    supervise_type = DictionaryItemSerializerExport(read_only=True)
    class Meta:
        model = Supervisor
        fields = ('__all__')
        read_only_fields = ('id',)

class SupervisorUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supervisor
        fields = ('__all__')
        read_only_fields = ('id','recorded_by')

#===============================branch serializer====================================================#
class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = ('__all__')
        read_only_fields = ('id',)


class BranchListSerializer(serializers.ModelSerializer):
    branch_location = DictionaryItemSerializerExport(read_only=True)
    parent_branch = BranchExportSerializer(read_only=True)
    bank_type = DictionaryItemSerializerExport(read_only=True)
    branch_type = DictionaryItemSerializerExport(read_only=True)
    class Meta:
        model = Branch
        fields = ('__all__')
        read_only_fields = ('id',)


class BranchUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = ('__all__')
        read_only_fields = ('id','recorded_by')

#===============================branch serializer====================================================#
class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ('__all__')
        read_only_fields = ('id',)


class DepartmentListSerializer(serializers.ModelSerializer):
    parent_department = DepartmentExportSerializer(read_only=True)
    class Meta:
        model = Department
        fields = ('__all__')
        read_only_fields = ('id',)


class DepartmentUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ('__all__')
        read_only_fields = ('id','recorded_by')

#===============================branch serializer====================================================#
class BranchManagerSerializer(serializers.ModelSerializer):
    class Meta:
        model = BranchManager
        fields = ('__all__')
        read_only_fields = ('id',)


class BranchManagerListSerializer(serializers.ModelSerializer):
    supervisor = SupervisorExportSerializer(read_only=True)
    class Meta:
        model = BranchManager
        fields = ('__all__')
        read_only_fields = ('id',)


class BranchManagerUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BranchManager
        fields = ('__all__')
        read_only_fields = ('id','recorded_by')


#===============================branch serializer====================================================#
class DepartmentHeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = DepartmentHead
        fields = ('__all__')
        read_only_fields = ('id',)


class DepartmentHeadListSerializer(serializers.ModelSerializer):
    supervisor = SupervisorExportSerializer(read_only=True)
    class Meta:
        model = DepartmentHead
        fields = ('__all__')
        read_only_fields = ('id',)


class DepartmentHeadUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DepartmentHead
        fields = ('__all__')
        read_only_fields = ('id','recorded_by')


#===============================branch serializer====================================================#
class StaffDepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffDepartment
        fields = ('__all__')
        read_only_fields = ('id',)

class StaffBranchSerializer(serializers.ModelSerializer):
    branch = BranchExportSerializer(read_only=True)
    department = DepartmentExportSerializer(read_only=True)
    staff = StaffExportSerializer(read_only=True)
    title = DictionaryItemSerializerExport(read_only=True)
    class Meta:
        model = StaffDepartment
        fields = ('id','staff','branch','department','title','is_active','recorded_at','removed_at')
        read_only_fields = ('id',)

class StaffDepartmentUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffDepartment
        fields = ('__all__')
        read_only_fields = ('id','recorded_by')


class DepartmentStaffSerializer(serializers.ModelSerializer):
    staff = StaffExportSerializer(read_only=True)
    title = DictionaryItemSerializerExport(read_only=True)
    class Meta:
        model = StaffDepartment
        fields = ('id','staff','title','is_active')
        read_only_fields = ('id',)

#===============================branch serializer====================================================#
class StaffBenefitSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffBenefit
        fields = ('__all__')
        read_only_fields = ('id',)


class StaffBenefitUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffBenefit
        fields = ('__all__')
        read_only_fields = ('id','recorded_by')

#===============================branch serializer====================================================#
class StaffBenefitDependentSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffBenefitDependent
        fields = ('__all__')
        read_only_fields = ('id',)


class StaffBenefitDependentUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffBenefitDependent
        fields = ('__all__')
        read_only_fields = ('id','recorded_by')

#===============================branch serializer====================================================#
class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ('__all__')
        read_only_fields = ('id',)


class DocumentListSerializer(serializers.ModelSerializer):
    document_type = DictionaryItemSerializerExport(read_only=True)
    class Meta:
        model = Document
        fields = ('__all__')
        read_only_fields = ('id',)


class DocumentRemoveSerializer(serializers.Serializer):
    document = serializers.IntegerField()


#===============================branch serializer====================================================#
class StaffSecurityFundSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffSecurityFund
        fields = ('__all__')
        read_only_fields = ('id',)


class StaffSecurityFundListSerializer(serializers.ModelSerializer):
    staff = StaffExportSerializer(read_only=True)
    fund = SecurityFundExportSerializer(read_only=True)
    class Meta:
        model = StaffSecurityFund
        fields = ('__all__')
        read_only_fields = ('id',)


class StaffSecurityFundUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffSecurityFund
        fields = ('__all__')
        read_only_fields = ('id','recorded_by')





