from django.db import models
from django.core.validators import MinValueValidator
from controller.models import *
from dictionary.models import DictionaryItem
import datetime

# Create your models here.
class NameField(models.CharField):

    def get_prep_value(self, value):
        return str(value).lower()


class LeaveType(models.Model):
    code = NameField(max_length=15, blank=True, null=True)
    name = NameField(max_length=50)
    descriptions = NameField(max_length=512, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    counting = models.ForeignKey(DictionaryItem, on_delete = models.RESTRICT)
    recorded_by = models.PositiveIntegerField(null=False)
    recorded_at = models.DateTimeField(auto_now_add = True, null=True)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Leave Type"
        verbose_name_plural = "Leave Types"


class LeaveDays(models.Model):
    leave_type = models.ForeignKey(LeaveType, on_delete = models.RESTRICT, related_name="leave_type_days")
    days = models.PositiveIntegerField(null=False)
    recorded_by = models.PositiveIntegerField(null=False)
    recorded_at = models.DateTimeField(auto_now_add = True, null=True)

    def __str__(self):
        return self.leave_type.name
    
    class Meta:
        verbose_name = "Leave Days"
        verbose_name_plural = "Leave Days"


class Roster(models.Model):
    name = NameField(max_length=50, blank=True, null=True)
    number = models.PositiveIntegerField(null=False)
    recorded_by = models.PositiveIntegerField(null=False)
    recorded_at = models.DateTimeField(auto_now_add = True, null=True)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Roster"
        verbose_name_plural = "Rosters"



class LeaveApplication(models.Model):
    code = NameField(max_length=15, blank=True, null=True)
    staff = models.ForeignKey(Staff, on_delete = models.RESTRICT)
    leave_type = models.ForeignKey(LeaveType, on_delete = models.RESTRICT)
    start_date = models.DateField()
    end_date = models.DateField()
    return_date = models.DateField(null=True, blank=True)
    working_days = models.DecimalField(max_digits=1000, decimal_places=2, default=0)
    total_days = models.DecimalField(max_digits=1000, decimal_places=2, default=0)
    reason = NameField(max_length=512, blank=True, null=True)
    status = models.ForeignKey(DictionaryItem, on_delete = models.RESTRICT)
    is_active = models.BooleanField(default=True)
    year = models.PositiveIntegerField(default=datetime.date.today().year)
    recorded_by = models.PositiveIntegerField(null=False)
    recorded_at = models.DateTimeField(auto_now_add = True, null=True)

    def __str__(self):
        return self.code
    
    class Meta:
        unique_together = ('staff','leave_type','is_active')
        verbose_name = "Leave Application"
        verbose_name_plural = "Leave Applications"


class LeaveDuration(models.Model):
    leave = models.ForeignKey(LeaveApplication, on_delete = models.RESTRICT, related_name="application_duration")
    duration_type = models.ForeignKey(DictionaryItem, on_delete = models.RESTRICT)
    start_time = models.TimeField(null=True)
    end_time = models.TimeField(null=True)
    hours = models.DecimalField(max_digits=1000, decimal_places=2, default=0)
    recorded_by = models.PositiveIntegerField(null=False)
    recorded_at = models.DateTimeField(auto_now_add = True, null=True)

    def __str__(self):
        return self.leave.code
    
    class Meta:
        verbose_name = "Leave Duration"
        verbose_name_plural = "Leave Durations"


class LeaveAssignment(models.Model):
    leave = models.ForeignKey(LeaveApplication, on_delete = models.RESTRICT)
    assigned_by = models.ForeignKey(Staff, on_delete = models.RESTRICT, related_name="assigned_by", null=True)
    assigned_to = models.ForeignKey(Staff, on_delete = models.RESTRICT)
    is_active = models.BooleanField(default=True)
    recorded_by = models.PositiveIntegerField(null=False)
    recorded_at = models.DateTimeField(auto_now_add = True, null=True)

    def __str__(self):
        return self.leave.code
    
    class Meta:
        verbose_name = "Leave Assignment"
        verbose_name_plural = "Leave Assignments"


class LeaveApproval(models.Model):
    leave = models.ForeignKey(LeaveApplication, on_delete = models.RESTRICT, related_name="leave_approve")
    approved_by = models.ForeignKey(Staff, on_delete = models.RESTRICT)
    recorded_by = models.PositiveIntegerField(null=False)
    recorded_at = models.DateTimeField(auto_now_add = True, null=True)

    def __str__(self):
        return self.leave.code
    
    class Meta:
        verbose_name = "Leave Approval"
        verbose_name_plural = "Leave Approval"


class LeaveAccepted(models.Model):
    leave = models.ForeignKey(LeaveApplication, on_delete = models.RESTRICT, related_name="leave_accept")
    accepted_by = models.ForeignKey(Staff, on_delete = models.RESTRICT)
    roster = models.ForeignKey(Roster, on_delete = models.RESTRICT)
    status = models.ForeignKey(DictionaryItem, on_delete = models.RESTRICT)
    recorded_by = models.PositiveIntegerField(null=False)
    recorded_at = models.DateTimeField(auto_now_add = True, null=True)

    def __str__(self):
        return self.leave.code
    
    class Meta:
        verbose_name = "Leave Accepted"
        verbose_name_plural = "Leave Accepted"


class LeaveRejected(models.Model):
    leave = models.ForeignKey(LeaveApplication, on_delete = models.RESTRICT)
    rejected_by = models.ForeignKey(Staff, on_delete = models.RESTRICT)
    reason = NameField(max_length=512, blank=True, null=True)
    recorded_by = models.PositiveIntegerField(null=False)
    recorded_at = models.DateTimeField(auto_now_add = True, null=True)

    def __str__(self):
        return self.leave.code
    
    class Meta:
        verbose_name = "Leave Rejected"
        verbose_name_plural = "Leave Rejected"


class LeaveCanceled(models.Model):
    leave = models.ForeignKey(LeaveAccepted, on_delete = models.RESTRICT)
    canceled_by = models.ForeignKey(Staff, on_delete = models.RESTRICT)
    reason = NameField(max_length=512, blank=True, null=True)
    utilised_days = models.PositiveIntegerField(null=False)
    recorded_by = models.PositiveIntegerField(null=False)
    recorded_at = models.DateTimeField(auto_now_add = True, null=True)

    def __str__(self):
        return self.leave.code
    
    class Meta:
        verbose_name = "Leave Cnaceled"
        verbose_name_plural = "Leave Cnaceled"


class LeaveComment(models.Model):
    leave = models.ForeignKey(LeaveApplication, on_delete = models.RESTRICT)
    assignment = models.ForeignKey(LeaveAssignment, on_delete = models.RESTRICT, null=True, related_name="assigned_comment")
    approve = models.ForeignKey(LeaveApproval, on_delete = models.RESTRICT, null=True, related_name="approve_comment")
    reject = models.ForeignKey(LeaveRejected, on_delete = models.RESTRICT, null=True, related_name="reject_comment")
    cancel = models.ForeignKey(LeaveCanceled, on_delete = models.RESTRICT, null=True, related_name="cancel_comment")
    accept = models.ForeignKey(LeaveAccepted, on_delete = models.RESTRICT, null=True, related_name="accept_comment")
    commented_by = models.ForeignKey(Staff, on_delete = models.RESTRICT)
    comment = NameField(max_length=512, blank=True, null=True)
    recorded_by = models.PositiveIntegerField(null=False)
    recorded_at = models.DateTimeField(auto_now_add = True, null=True)

    def __str__(self):
        return self.leave.code
    
    class Meta:
        verbose_name = "Leave Comment"
        verbose_name_plural = "Leave Comments"



class LeaveBalance(models.Model):
    staff = models.ForeignKey(Staff, on_delete = models.RESTRICT)
    leave_type = models.ForeignKey(LeaveType, on_delete = models.RESTRICT, null=True)
    entitlement = models.IntegerField(validators=[MinValueValidator(-1000)], null=True) 
    utilised = models.IntegerField(validators=[MinValueValidator(-1000)], null=True) 
    balance = models.IntegerField(validators=[MinValueValidator(-1000)], null=True) 
    year = models.PositiveIntegerField(default=datetime.date.today().year)
    is_used = models.BooleanField(default=False)
    is_expired = models.BooleanField(default=False)
    recorded_by = models.PositiveIntegerField(null=False)
    recorded_at = models.DateTimeField(auto_now_add = True, null=True)

    def __str__(self):
        return self.staff.full_name
    
    class Meta:
        verbose_name = "Leave Balance"
        verbose_name_plural = "Leave Balance"


class LeaveRoster(models.Model):
    staff = models.ForeignKey(Staff, on_delete = models.RESTRICT)
    roster = models.ForeignKey(Roster, on_delete = models.RESTRICT)
    start_date = models.DateField()
    end_date = models.DateField()
    year = models.PositiveIntegerField(default=datetime.date.today().year)
    status = models.ForeignKey(DictionaryItem, on_delete = models.RESTRICT)
    recorded_by = models.PositiveIntegerField(null=False)
    recorded_at = models.DateTimeField(auto_now_add = True, null=True)

    def __str__(self):
        return self.staff.full_name
    
    class Meta:
        verbose_name = "Leave Roster"
        verbose_name_plural = "Leave Rosters"


class LeaveCountingDays(models.Model):
    leave = models.ForeignKey(LeaveApplication, on_delete = models.RESTRICT)
    date = models.DateField()
    year = models.PositiveIntegerField(default=datetime.date.today().year)
    is_counted = models.BooleanField(default=False)
    is_canceled = models.BooleanField(default=False)
    recorded_by = models.PositiveIntegerField(null=False)
    recorded_at = models.DateTimeField(auto_now_add = True, null=True)

    def __str__(self):
        return self.leave.code
    
    class Meta:
        verbose_name = "Leave Counting Days"
        verbose_name_plural = "Leave Counting Days"


class LeaveBlockedPeriord(models.Model):
    start_date = models.DateField()
    end_date = models.DateField()
    reason = NameField(max_length=512, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_finish = models.BooleanField(default=False)
    recorded_by = models.PositiveIntegerField(null=False)
    recorded_at = models.DateTimeField(auto_now_add = True, null=True)

    def __str__(self):
        return self.reason
    
    class Meta:
        verbose_name = "Leave Blocked"
        verbose_name_plural = "Leave Blocked"


class PublicHoliday(models.Model):
    name = NameField(max_length=50, blank=True, null=True)
    date = models.DateField()
    description = NameField(max_length=512, blank=True, null=True)
    is_annual_repeated = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    recorded_by = models.PositiveIntegerField(null=False)
    recorded_at = models.DateTimeField(auto_now_add = True, null=True)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Public Holiday"
        verbose_name_plural = "Public Holiday"


class WorkingDays(models.Model):
    name = NameField(max_length=50, blank=True, null=True)
    type_work = models.ForeignKey(DictionaryItem, on_delete = models.RESTRICT)
    is_active = models.BooleanField(default=True)
    recorded_by = models.PositiveIntegerField(null=False)
    recorded_at = models.DateTimeField(auto_now_add = True, null=True)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Working Day"
        verbose_name_plural = "Working Days"