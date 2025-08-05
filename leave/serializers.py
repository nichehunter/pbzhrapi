from rest_framework import fields, serializers
import json
import datetime
from dictionary.models import *
from controller.models import Staff
from controller.serializers import *
from leave.models import *


#================================================ export ===============================================
class DictionaryItemSerializerExport(serializers.ModelSerializer):
    class Meta:
        model = DictionaryItem
        fields = ('id','dictionary_item_name')
        read_only_fields = ('id',)


class LeaveDaysExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveDays
        fields = ('id','days')
        read_only_fields = ('id',)


class LeaveTypeExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveType
        fields = ('id','name')
        read_only_fields = ('id',)


class LeaveDurationExportSerializer(serializers.ModelSerializer):
    duration_type = DictionaryItemSerializerExport(read_only=True)
    class Meta:
        model = LeaveDuration
        fields = ('id','duration_type','start_time','end_time','hours')
        read_only_fields = ('id',)


class LeaveApplicationExportSerializer(serializers.ModelSerializer):
    leave_type = LeaveTypeExportSerializer(read_only=True)
    status = DictionaryItemSerializerExport(read_only=True)
    class Meta:
        model = LeaveApplication
        fields = ('id','leave_type','start_date','end_date','return_date','working_days','total_days','status')
        read_only_fields = ('id',)

class LeaveCommentExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveComment
        fields = ('id','comment')
        read_only_fields = ('id',)


class LeaveStaffExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Staff
        fields = ('id','staff_opf','code','full_name')
        read_only_fields = ('id',)


class LeaveApproveExportSerializer(serializers.ModelSerializer):
    approved_by = LeaveStaffExportSerializer(read_only=True)
    class Meta:
        model = LeaveApproval
        fields = ('id','approved_by')
        read_only_fields = ('id',)

class LeaveAcceptExportSerializer(serializers.ModelSerializer):
    accepted_by = LeaveStaffExportSerializer(read_only=True)
    class Meta:
        model = LeaveAccepted
        fields = ('id','accepted_by')
        read_only_fields = ('id',)

#============================================== leave type ===================================================
class LeaveTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveType
        fields = ('__all__')
        read_only_fields = ('id',)


class LeaveTypeListSerializer(serializers.ModelSerializer):
    counting = DictionaryItemSerializerExport(read_only=True)
    leave_type_days = LeaveDaysExportSerializer(many=True)
    class Meta:
        model = LeaveType
        fields = ('__all__')
        read_only_fields = ('id',)


class LeaveTypeUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveType
        fields = ('__all__')
        read_only_fields = ('id','recorded_by')


#============================================== leave type ===================================================
class LeaveDaysSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveDays
        fields = ('__all__')
        read_only_fields = ('id',)


class LeaveDaysUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveDays
        fields = ('__all__')
        read_only_fields = ('id','recorded_by')


#============================================== leave application ===================================================
class LeaveApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveApplication
        fields = ('__all__')
        read_only_fields = ('id',)


class LeaveApplicationListSerializer(serializers.ModelSerializer):
    staff = StaffExportSerializer(read_only=True)
    leave_type = LeaveTypeExportSerializer(read_only=True)
    application_duration = LeaveDurationExportSerializer(many=True)
    status = DictionaryItemSerializerExport(read_only=True)
    leave_approve = LeaveApproveExportSerializer(many=True)
    leave_accept = LeaveAcceptExportSerializer(many=True)
    class Meta:
        model = LeaveApplication
        fields = ('__all__')
        read_only_fields = ('id',)


class LeaveApplicationUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveApplication
        fields = ('__all__')
        read_only_fields = ('id','recorded_by')


class LeaveChangeStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveApplication
        fields = ('id','status')
        read_only_fields = ('id','recorded_by')

#============================================== leave counting ===================================================
class LeaveCountingDaysSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveCountingDays
        fields = ('__all__')
        read_only_fields = ('id',)


class LeaveCountingDaysListSerializer(serializers.ModelSerializer):
    leave = LeaveApplicationExportSerializer(read_only=True)
    class Meta:
        model = LeaveCountingDays
        fields = ('__all__')
        read_only_fields = ('id',)


class LeaveCountingDaysUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveCountingDays
        fields = ('__all__')
        read_only_fields = ('id','recorded_by')


#============================================== leave duration ===================================================
class LeaveDurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveDuration
        fields = ('__all__')
        read_only_fields = ('id',)


class LeaveDurationUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveDuration
        fields = ('__all__')
        read_only_fields = ('id','recorded_by')


#============================================== leave assignment ===================================================
class LeaveAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveAssignment
        fields = ('__all__')
        read_only_fields = ('id',)


class LeaveAssignmentListSerializer(serializers.ModelSerializer):
    assigned_to = LeaveStaffExportSerializer(read_only=True)
    assigned_by = LeaveStaffExportSerializer(read_only=True)
    leave = LeaveApplicationExportSerializer(read_only=True)
    assigned_comment = LeaveCommentExportSerializer(many=True)
    class Meta:
        model = LeaveAssignment
        fields = ('__all__')
        read_only_fields = ('id',)


class LeaveAssignmentUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveAssignment
        fields = ('__all__')
        read_only_fields = ('id','recorded_by')


#============================================== leave approval ===================================================
class LeaveApprovalSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveApproval
        fields = ('__all__')
        read_only_fields = ('id',)


class LeaveApprovalUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveApproval
        fields = ('__all__')
        read_only_fields = ('id','recorded_by')


#============================================== leave comment ===================================================
class LeaveCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveComment
        fields = ('__all__')
        read_only_fields = ('id',)

class LeaveCommentListSerializer(serializers.ModelSerializer):
    commented_by = LeaveStaffExportSerializer(read_only=True)
    leave = LeaveApplicationExportSerializer(read_only=True)
    class Meta:
        model = LeaveComment
        fields = ('__all__')
        read_only_fields = ('id',)

class LeaveCommentUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveComment
        fields = ('__all__')
        read_only_fields = ('id','recorded_by')


#============================================== leave accepted ===================================================
class LeaveAcceptedSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveAccepted
        fields = ('__all__')
        read_only_fields = ('id',)


class LeaveAcceptedUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveAccepted
        fields = ('__all__')
        read_only_fields = ('id','recorded_by')


#============================================== leave rejected ===================================================
class LeaveRejectedSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveRejected
        fields = ('__all__')
        read_only_fields = ('id',)


class LeaveRejectedUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveRejected
        fields = ('__all__')
        read_only_fields = ('id','recorded_by')


#============================================== leave rejected ===================================================
class LeaveRejectedSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveRejected
        fields = ('__all__')
        read_only_fields = ('id',)


class LeaveRejectedUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveRejected
        fields = ('__all__')
        read_only_fields = ('id','recorded_by')

#============================================== leave canceled ===================================================
class LeaveCanceledSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveCanceled
        fields = ('__all__')
        read_only_fields = ('id',)


class LeaveCanceledUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveCanceled
        fields = ('__all__')
        read_only_fields = ('id','recorded_by')

#============================================== leave balance ===================================================
class LeaveBalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveBalance
        fields = ('__all__')
        read_only_fields = ('id',)


class LeaveBalanceUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveBalance
        fields = ('__all__')
        read_only_fields = ('id','recorded_by')

#============================================== Roster ===================================================
class RosterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Roster
        fields = ('__all__')
        read_only_fields = ('id',)


class RosterUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Roster
        fields = ('__all__')
        read_only_fields = ('id','recorded_by')


class RosterExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Roster
        fields = ('id','name')
        read_only_fields = ('id',)

#============================================== leave roster ===================================================
class LeaveRosterSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveRoster
        fields = ('__all__')
        read_only_fields = ('id',)


class LeaveRosterListSerializer(serializers.ModelSerializer):
    staff = LeaveStaffExportSerializer(read_only=True)
    roster = RosterExportSerializer(read_only=True)
    status = DictionaryItemSerializerExport(read_only=True)
    class Meta:
        model = LeaveRoster
        fields = ('__all__')
        read_only_fields = ('id',)


class LeaveRosterUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveRoster
        fields = ('__all__')
        read_only_fields = ('id','recorded_by')

#============================================== leave blocked ===================================================
class LeaveBlockedPeriordSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveBlockedPeriord
        fields = ('__all__')
        read_only_fields = ('id',)


class LeaveBlockedPeriordUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveBlockedPeriord
        fields = ('__all__')
        read_only_fields = ('id','recorded_by')


#============================================== public holiday ===================================================
class PublicHolidaySerializer(serializers.ModelSerializer):
    class Meta:
        model = PublicHoliday
        fields = ('__all__')
        read_only_fields = ('id',)


class PublicHolidayUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PublicHoliday
        fields = ('__all__')
        read_only_fields = ('id','recorded_by')

#============================================== working days ===================================================
class WorkingDaysSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkingDays
        fields = ('__all__')
        read_only_fields = ('id',)


class WorkingDaysListSerializer(serializers.ModelSerializer):
    type_work = DictionaryItemSerializerExport(read_only=True)
    class Meta:
        model = WorkingDays
        fields = ('__all__')
        read_only_fields = ('id',)


class WorkingDaysUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkingDays
        fields = ('__all__')
        read_only_fields = ('id','recorded_by')