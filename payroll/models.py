from django.db import models
from controller.models import *
from dictionary.models import DictionaryItem
import datetime
from django.utils import timezone


# Create your models here.
class NameField(models.CharField):

    def get_prep_value(self, value):
        return str(value).lower()


# ============================================= calculation ==============================================================
class CalculationDay(models.Model):
    code = NameField(max_length=50, blank=True, null=True)
    date = models.PositiveSmallIntegerField()
    is_active = models.BooleanField(default=True)
    recorded_by = models.PositiveIntegerField(null=False)
    recorded_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return self.code

    class Meta:
        verbose_name = "Calculation Day"
        verbose_name_plural = "Calculation Days"


# ============================================= salary ==============================================================
class StaffSalary(models.Model):
    code = NameField(max_length=50, blank=True, null=True)
    staff = models.ForeignKey(Staff, on_delete=models.RESTRICT)
    amount = models.DecimalField(max_digits=1000, decimal_places=2, default=0)
    account_number = NameField(max_length=150, blank=True, null=True)
    branch_code = NameField(max_length=150, blank=True, null=True)
    customer_number = NameField(max_length=150, blank=True, null=True)
    ledger = NameField(max_length=150, blank=True, null=True)
    sub_ledger = NameField(max_length=150, blank=True, null=True)
    tin_number = NameField(max_length=150, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    recorded_by = models.PositiveIntegerField(null=False)
    recorded_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return self.code

    class Meta:
        unique_together = ("staff", "is_active")
        verbose_name = "Staff Salary"
        verbose_name_plural = "Staff Salary"


# ============================================= organization ==============================================================
class Organization(models.Model):
    code = NameField(max_length=50, blank=True, null=True)
    name = NameField(max_length=512, blank=True, null=True)
    account = NameField(max_length=512, blank=True, null=True)
    branch = NameField(max_length=150, blank=True, null=True)
    ledger = NameField(max_length=150, blank=True, null=True)
    sub_ledger = NameField(max_length=150, blank=True, null=True)
    is_formal = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    recorded_by = models.PositiveIntegerField(null=False)
    recorded_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return self.code

    class Meta:
        verbose_name = "Organization"
        verbose_name_plural = "Organization"


# ============================================= staff organization ==============================================================
class StaffOrganization(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.RESTRICT)
    organization = models.ForeignKey(Organization, on_delete=models.RESTRICT)
    amount = models.DecimalField(max_digits=1000, decimal_places=2, default=0)
    balance = models.DecimalField(max_digits=1000, decimal_places=2, default=0)
    percentage = models.FloatField(default=0)
    is_percentage = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    recorded_by = models.PositiveIntegerField(null=False)
    recorded_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return self.staff.staff_opf

    class Meta:
        verbose_name = "Organization"
        verbose_name_plural = "Organization"


# ============================================= allowance ==============================================================
class Allowance(models.Model):
    code = NameField(max_length=50, blank=True, null=True)
    name = NameField(max_length=512, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_repeated = models.BooleanField(default=False)
    recorded_by = models.PositiveIntegerField(null=False)
    recorded_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Allowance"
        verbose_name_plural = "Allowances"


# ============================================= deduction ==============================================================
class Deduction(models.Model):
    code = NameField(max_length=50, blank=True, null=True)
    name = NameField(max_length=512, blank=True, null=True)
    account = NameField(max_length=150, blank=True, null=True)
    branch = NameField(max_length=150, blank=True, null=True)
    ledger = NameField(max_length=150, blank=True, null=True)
    sub_ledger = NameField(max_length=150, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    recorded_by = models.PositiveIntegerField(null=False)
    recorded_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Deduction"
        verbose_name_plural = "Deductions"


# ============================================= allowance ==============================================================
class StaffAllowance(models.Model):
    code = NameField(max_length=50, blank=True, null=True)
    staff = models.ForeignKey(Staff, on_delete=models.RESTRICT)
    allowance = models.ForeignKey(Allowance, on_delete=models.RESTRICT)
    amount = models.DecimalField(max_digits=1000, decimal_places=2, default=0)
    is_percentage = models.BooleanField(default=False)
    percentage = models.FloatField(default=0)
    is_active = models.BooleanField(default=True)
    recorded_by = models.PositiveIntegerField(null=False)
    recorded_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return self.code

    class Meta:
        verbose_name = "Staff Allowance"
        verbose_name_plural = "Staff Allowances"


# ============================================= deduction ==============================================================
class StaffDeduction(models.Model):
    code = NameField(max_length=50, blank=True, null=True)
    staff = models.ForeignKey(Staff, on_delete=models.RESTRICT)
    deduction = models.ForeignKey(Deduction, on_delete=models.RESTRICT)
    amount = models.DecimalField(max_digits=1000, decimal_places=2, default=0)
    percentage = models.FloatField(default=0)
    balance = models.DecimalField(max_digits=1000, decimal_places=2, default=0)
    is_percentage = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    recorded_by = models.PositiveIntegerField(null=False)
    recorded_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return self.code

    class Meta:
        verbose_name = "Staff Deduction"
        verbose_name_plural = "Staff Deductions"


# ============================================= payee deduction ==============================================================
class PayeeDeduction(models.Model):
    code = NameField(max_length=50, blank=True, null=True)
    deduction = models.ForeignKey(Deduction, on_delete=models.RESTRICT)
    initia_amount = models.DecimalField(max_digits=1000, decimal_places=2, default=0)
    range_percentage = models.FloatField(default=0)
    upper_range = models.DecimalField(max_digits=1000, decimal_places=2, default=0)
    lower_range = models.DecimalField(max_digits=1000, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    recorded_by = models.PositiveIntegerField(null=False)
    recorded_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return self.code

    class Meta:
        verbose_name = "Payee Deduction"
        verbose_name_plural = "Payee Deductions"


class SecurityFundDeduction(models.Model):
    code = NameField(max_length=50, blank=True, null=True)
    deduction = models.ForeignKey(Deduction, on_delete=models.RESTRICT)
    fund = models.ForeignKey(SecurityFund, on_delete=models.RESTRICT)
    percentage = models.FloatField(default=0)
    is_active = models.BooleanField(default=True)
    recorded_by = models.PositiveIntegerField(null=False)
    recorded_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return self.code

    class Meta:
        verbose_name = "Security Deduction"
        verbose_name_plural = "Security Deductions"


class HelthDeduction(models.Model):
    code = NameField(max_length=50, blank=True, null=True)
    deduction = models.ForeignKey(Deduction, on_delete=models.RESTRICT)
    fund = models.ForeignKey(HealthFund, on_delete=models.RESTRICT, default=1)
    percentage = models.FloatField(default=0)
    is_active = models.BooleanField(default=True)
    recorded_by = models.PositiveIntegerField(null=False)
    recorded_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return self.code

    class Meta:
        verbose_name = "Helth Deduction"
        verbose_name_plural = "Helth Deductions"


# ============================================= monthly allowance ==============================================================
class MonthlyAllowance(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.RESTRICT)
    allowance = models.ForeignKey(Allowance, on_delete=models.RESTRICT)
    amount = models.DecimalField(max_digits=1000, decimal_places=2, default=0)
    date = models.DateField(default=timezone.now)
    month = models.PositiveIntegerField(default=datetime.date.today().month)
    year = models.PositiveIntegerField(default=datetime.date.today().year)
    is_active = models.BooleanField(default=True)
    month_consumed = models.PositiveIntegerField(default=0)
    year_consumed = models.PositiveIntegerField(default=0)
    recorded_by = models.PositiveIntegerField(null=False)
    recorded_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return self.staff.full_name

    class Meta:
        unique_together = ("staff", "date", "allowance")
        verbose_name = "Monthly Allowance"
        verbose_name_plural = "Monthly Allowances"


# ============================================= monthly deduction ==============================================================
class MonthlyDeduction(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.RESTRICT)
    deduction = models.ForeignKey(Deduction, on_delete=models.RESTRICT)
    organization = models.ForeignKey(
        Organization, on_delete=models.RESTRICT, null=True, blank=True
    )
    amount = models.DecimalField(max_digits=1000, decimal_places=2, default=0)
    date = models.DateField(default=timezone.now)
    month = models.PositiveIntegerField(default=datetime.date.today().month)
    year = models.PositiveIntegerField(default=datetime.date.today().year)
    month_consumed = models.PositiveIntegerField(default=0)
    year_consumed = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    recorded_by = models.PositiveIntegerField(null=False)
    recorded_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return self.staff.full_name

    class Meta:
        unique_together = ("staff", "date", "organization", "deduction")
        verbose_name = "Monthly Deduction"
        verbose_name_plural = "Monthly Deductions"


# ============================================= monthly deduction ==============================================================
class PayrollFormula(models.Model):
    code = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    formula_type = NameField(max_length=255)
    expression = models.TextField()
    variables = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        unique_together = ("code", "is_active")
        verbose_name = "Payroll Formula"
        verbose_name_plural = "Payroll Formulas"


# ============================================= monthly deduction ==============================================================


class Payroll(models.Model):
    code = NameField(max_length=50, blank=True, null=True)
    total_staff = models.PositiveIntegerField(default=0)
    month = models.PositiveIntegerField(default=datetime.date.today().month)
    year = models.PositiveIntegerField(default=datetime.date.today().year)
    formula = models.ForeignKey(PayrollFormula, on_delete=models.RESTRICT)
    is_approved = models.BooleanField(default=False)
    is_canceled = models.BooleanField(default=False)
    is_paid = models.BooleanField(default=False)
    recorded_by = models.PositiveIntegerField(null=False)
    recorded_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return self.code

    class Meta:
        unique_together = ("month", "year", "is_approved")
        verbose_name = "Payroll"
        verbose_name_plural = "Payrolls"


# ============================================= monthly deduction ==============================================================
class StaffPayroll(models.Model):
    payroll = models.ForeignKey(Payroll, on_delete=models.RESTRICT)
    staff = models.ForeignKey(Staff, on_delete=models.RESTRICT)
    basic_salary = models.DecimalField(max_digits=1000, decimal_places=2, default=0)
    total_allowance = models.DecimalField(max_digits=1000, decimal_places=2, default=0)
    total_deduction = models.DecimalField(max_digits=1000, decimal_places=2, default=0)
    payee = models.DecimalField(max_digits=1000, decimal_places=2, default=0)
    security_fund = models.DecimalField(max_digits=1000, decimal_places=2, default=0)
    helth_fund = models.DecimalField(max_digits=1000, decimal_places=2, default=0)
    net_salary = models.DecimalField(max_digits=1000, decimal_places=2, default=0)
    month = models.PositiveIntegerField(default=datetime.date.today().month)
    year = models.PositiveIntegerField(default=datetime.date.today().year)
    recorded_by = models.PositiveIntegerField(null=False)
    recorded_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return self.staff.full_name

    class Meta:
        unique_together = ("staff", "month", "year")
        verbose_name = "Staff Payroll"
        verbose_name_plural = "Staff Payrolls"


class PayrollVariable(models.Model):
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Formula variable"
        verbose_name_plural = "Formula variables"
