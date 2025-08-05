from rest_framework import fields, serializers
import json
import datetime
from payroll.models import *
from controller.models import Staff, SecurityFund
from dictionary.models import DictionaryItem


#================================================ export ===============================================
class DictionaryItemSerializerExport(serializers.ModelSerializer):
    class Meta:
        model = DictionaryItem
        fields = ('id','dictionary_item_name')
        read_only_fields = ('id',)

class StaffExportSerializer(serializers.ModelSerializer):
    gender = DictionaryItemSerializerExport(read_only=True)
    class Meta:
        model = Staff
        fields = ('id','staff_opf','code','full_name','phone_number','address','gender')
        read_only_fields = ('id',)


class AllowanceExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Allowance
        fields = ('id','name','is_active')
        read_only_fields = ('id',)

class DeductionExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Deduction
        fields = ('id','name','is_active')
        read_only_fields = ('id',)

class OrganizationExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ('id','name','account')
        read_only_fields = ('id',)

#================================================ salary ===============================================
class SalarySerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffSalary
        fields = ('__all__')
        read_only_fields = ('id',)


class SalaryListSerializer(serializers.ModelSerializer):
    staff = StaffExportSerializer(read_only=True)
    class Meta:
        model = StaffSalary
        fields = ('__all__')
        read_only_fields = ('id',)


class SalaryUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffSalary
        fields = ('__all__')
        read_only_fields = ('id','recorded_by')


#================================================ allowance ===============================================
class AllowanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Allowance
        fields = ('__all__')
        read_only_fields = ('id',)


class AllowanceUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Allowance
        fields = ('__all__')
        read_only_fields = ('id','recorded_by')


#================================================ deduction ===============================================
class DeductionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Deduction
        fields = ('__all__')
        read_only_fields = ('id',)


class DeductionUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Deduction
        fields = ('__all__')
        read_only_fields = ('id','recorded_by')


#================================================ staff allowance ===============================================
class StaffAllowanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffAllowance
        fields = ('__all__')
        read_only_fields = ('id',)


class StaffAllowanceListSerializer(serializers.ModelSerializer):
    staff = StaffExportSerializer(read_only=True)
    allowance = AllowanceExportSerializer(read_only=True)
    class Meta:
        model = StaffAllowance
        fields = ('__all__')
        read_only_fields = ('id',)


class StaffAllowanceUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffAllowance
        fields = ('__all__')
        read_only_fields = ('id','recorded_by')


#================================================ staff deduction ===============================================
class StaffDeductionSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffDeduction
        fields = ('__all__')
        read_only_fields = ('id',)


class StaffDeductionListSerializer(serializers.ModelSerializer):
    staff = StaffExportSerializer(read_only=True)
    deduction = DeductionExportSerializer(read_only=True)
    class Meta:
        model = StaffDeduction
        fields = ('__all__')
        read_only_fields = ('id',)


class StaffDeductionUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffDeduction
        fields = ('__all__')
        read_only_fields = ('id','recorded_by')


#================================================ staff deduction ===============================================
class PayeeDeductionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayeeDeduction
        fields = ('__all__')
        read_only_fields = ('id',)


class PayeeDeductionListSerializer(serializers.ModelSerializer):
    deduction = DeductionExportSerializer(read_only=True)
    class Meta:
        model = PayeeDeduction
        fields = ('__all__')
        read_only_fields = ('id',)


class PayeeDeductionUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayeeDeduction
        fields = ('__all__')
        read_only_fields = ('id','recorded_by')


#================================================ staff deduction ===============================================
class SecurityFundSerializer(serializers.ModelSerializer):
    class Meta:
        model = SecurityFund
        fields = ('__all__')
        read_only_fields = ('id',)


class SecurityFundUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SecurityFund
        fields = ('__all__')
        read_only_fields = ('id','recorded_by')

#================================================ monthly allowance ===============================================
class MonthlyAllowanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = MonthlyAllowance
        fields = ('__all__')
        read_only_fields = ('id',)


class MonthlyAllowanceListSerializer(serializers.ModelSerializer):
    staff = StaffExportSerializer(read_only=True)
    allowance = AllowanceExportSerializer(read_only=True)
    class Meta:
        model = MonthlyAllowance
        fields = ('__all__')
        read_only_fields = ('id',)


class MonthlyAllowanceUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MonthlyAllowance
        fields = ('__all__')
        read_only_fields = ('id','recorded_by')


#================================================ monthly deduction ===============================================
class MonthlyDeductionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MonthlyDeduction
        fields = ('__all__')
        read_only_fields = ('id',)


class MonthlyDeductionListSerializer(serializers.ModelSerializer):
    staff = StaffExportSerializer(read_only=True)
    deduction = DeductionExportSerializer(read_only=True)
    organization = OrganizationExportSerializer(read_only=True)
    class Meta:
        model = MonthlyDeduction
        fields = ('__all__')
        read_only_fields = ('id',)


class MonthlyDeductionUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MonthlyDeduction
        fields = ('__all__')
        read_only_fields = ('id','recorded_by')



#================================================ payroll ===============================================
class PayrollSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payroll
        fields = ('__all__')
        read_only_fields = ('id',)


class PayrollUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payroll
        fields = ('__all__')
        read_only_fields = ('id','recorded_by')


#================================================ payroll ===============================================
class StaffPayrollSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffPayroll
        fields = ('__all__')
        read_only_fields = ('id',)


class StaffPayrollListSerializer(serializers.ModelSerializer):
    staff = StaffExportSerializer(read_only=True)
    payroll = PayrollSerializer(read_only=True)
    class Meta:
        model = StaffPayroll
        fields = ('__all__')
        read_only_fields = ('id',)


class StaffPayrollUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffPayroll
        fields = ('__all__')
        read_only_fields = ('id','recorded_by')

#================================================ allowance ===============================================
class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ('__all__')
        read_only_fields = ('id',)


class OrganizationUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ('__all__')
        read_only_fields = ('id','recorded_by')


#================================================ allowance ===============================================
class StaffOrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffOrganization
        fields = ('__all__')
        read_only_fields = ('id',)


class StaffOrganizationListSerializer(serializers.ModelSerializer):
    staff = StaffExportSerializer(read_only=True)
    organization = OrganizationExportSerializer(read_only=True)
    class Meta:
        model = StaffOrganization
        fields = ('__all__')
        read_only_fields = ('id',)



class StaffOrganizationUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffOrganization
        fields = ('__all__')
        read_only_fields = ('id','recorded_by')


#================================================ formula ===============================================
class PayrollFormulaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayrollFormula
        fields = ('__all__')
        read_only_fields = ('id',)


class PayrollVariableSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayrollVariable
        fields = ('__all__')
        read_only_fields = ('id',)


