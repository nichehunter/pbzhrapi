from django.db import models
import datetime
from dictionary.models import *

# Create your models here.
class NameField(models.CharField):

    def get_prep_value(self, value):
        return str(value).lower()


class Person(models.Model):
    code = NameField(max_length=5, blank=True, null=True)
    full_name = NameField(max_length=150, blank=True, null=True)
    dob = models.DateField(null=False)
    gender = models.ForeignKey(DictionaryItem, on_delete = models.RESTRICT, related_name="gender")
    address = NameField(max_length=50, blank=True, null=True)
    phone_number = NameField(max_length=50, blank=True, null=True)
    email = models.EmailField(null=True, blank=True)
    zanid = models.CharField(max_length=150, blank=True, null=True)
    nida = models.CharField(max_length=150, blank=True, null=True)
    recorded_by = models.PositiveIntegerField(null=False)
    recorded_at = models.DateTimeField(auto_now_add = True, null=True)

    def __str__(self):
        return self.full_name
    
    class Meta:
        verbose_name = "Person"
        verbose_name_plural = "People"


class Staff(Person):
    staff_opf = models.PositiveIntegerField(unique=True)
    staff_cpf = models.CharField(max_length=50, blank=True, null=True)
    next_keen = NameField(max_length=150, blank=True, null=True)
    keen_number = NameField(max_length=50, blank=True, null=True)
    personal_email = models.EmailField(null=True, blank=True)
    employment_status = models.ForeignKey(DictionaryItem, on_delete = models.RESTRICT, related_name="status", null=True)
    doh = models.DateField(null=True)
    job_title = models.ForeignKey(DictionaryItem, on_delete = models.RESTRICT, related_name="title", null=True)
    is_active = models.BooleanField(default=True)



class StaffQualification(models.Model):
    name = NameField(max_length=150, blank=True, null=True)
    ended_year = models.PositiveIntegerField(null=False)
    staff = models.ForeignKey(Staff, on_delete = models.RESTRICT)
    qualification_type = models.ForeignKey(DictionaryItem, on_delete = models.RESTRICT, related_name="type")
    qualification_doc = models.CharField(max_length=10000000, blank=True, null=True)
    recorded_by = models.PositiveIntegerField(null=False)
    recorded_at = models.DateTimeField(auto_now_add = True, null=True)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Qualification"
        verbose_name_plural = "Qualifications"


class Supervisor(models.Model):
    code = NameField(max_length=15, blank=True, null=True)
    staff = models.ForeignKey(Staff, on_delete = models.RESTRICT, related_name="staff")
    dos = models.DateField(null=False)
    supervise_type = models.ForeignKey(DictionaryItem, on_delete = models.RESTRICT, related_name="super_type")
    is_active = models.BooleanField(default=True)
    doe = models.DateField(null=True)
    recorded_by = models.PositiveIntegerField(null=False)
    recorded_at = models.DateTimeField(auto_now_add = True, null=True)

    def __str__(self):
        return self.staff.full_name
    
    class Meta:
        verbose_name = "Supervisor"
        verbose_name_plural = "Supervisors"

    

class Branch(models.Model):
    branch_code = NameField(max_length=15, blank=True, null=True)
    branch_name = NameField(max_length=150, blank=True, null=True)
    bank_type = models.ForeignKey(DictionaryItem, on_delete = models.RESTRICT, related_name="bank_type", null=True)
    branch_type = models.ForeignKey(DictionaryItem, on_delete = models.RESTRICT, related_name="branch_type")
    branch_location = models.ForeignKey(DictionaryItem, on_delete = models.RESTRICT, related_name="branch_location")
    parent_branch = models.ForeignKey('self', blank=True, null=True, related_name='parent', on_delete = models.RESTRICT)
    is_active = models.BooleanField(default=True)
    recorded_by = models.PositiveIntegerField(null=False)
    recorded_at = models.DateTimeField(auto_now_add = True, null=True)

    def __str__(self):
        return self.branch_name
    
    class Meta:
        verbose_name = "Branch"
        verbose_name_plural = "Branches"


class Department(models.Model):
    department_code = NameField(max_length=15, blank=True, null=True)
    department_name = NameField(max_length=150, blank=True, null=True)
    parent_department = models.ForeignKey('self', blank=True, null=True, related_name='parent', on_delete = models.RESTRICT)
    is_active = models.BooleanField(default=True)
    recorded_by = models.PositiveIntegerField(null=False)
    recorded_at = models.DateTimeField(auto_now_add = True, null=True)

    def __str__(self):
        return self.department_name
    
    class Meta:
        verbose_name = "Department"
        verbose_name_plural = "Departmentes"


class BranchManager(models.Model):
    branch = models.ForeignKey(Branch, on_delete = models.RESTRICT)
    supervisor = models.ForeignKey(Supervisor, on_delete = models.RESTRICT)
    is_active = models.BooleanField(default=True)
    removed_at = models.DateField(null=True)
    recorded_by = models.PositiveIntegerField(null=False)
    recorded_at = models.DateTimeField(auto_now_add = True, null=True)

    def __str__(self):
        return self.branch.branch_name
    
    class Meta:
        verbose_name = "Branch Manager"
        verbose_name_plural = "Branch Managers"


class DepartmentHead(models.Model):
    department = models.ForeignKey(Department, on_delete = models.RESTRICT)
    supervisor = models.ForeignKey(Supervisor, on_delete = models.RESTRICT)
    is_active = models.BooleanField(default=True)
    removed_at = models.DateField(null=True)
    recorded_by = models.PositiveIntegerField(null=False)
    recorded_at = models.DateTimeField(auto_now_add = True, null=True)

    def __str__(self):
        return self.department.department_name
    
    class Meta:
        verbose_name = "Department Head"
        verbose_name_plural = "Department Head"


class StaffDepartment(models.Model):
    branch = models.ForeignKey(Branch, on_delete = models.RESTRICT)
    department = models.ForeignKey(Department, on_delete = models.RESTRICT)
    staff = models.ForeignKey(Staff, on_delete = models.RESTRICT, related_name="staff_department")
    title = models.ForeignKey(DictionaryItem, on_delete = models.RESTRICT, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    removed_at = models.DateField(null=True)
    recorded_by = models.PositiveIntegerField(null=False)
    recorded_at = models.DateTimeField(auto_now_add = True, null=True)

    def __str__(self):
        return self.staff.full_name
    
    class Meta:
        verbose_name = "Staff Department"
        verbose_name_plural = "Staff Department"



class StaffBenefit(models.Model):
    staff = models.ForeignKey(Staff, on_delete = models.RESTRICT)
    benefit_type = models.ForeignKey(DictionaryItem, on_delete = models.RESTRICT, related_name="benefit_type")
    benefit_provider = NameField(max_length=150, blank=True, null=True)
    no_dependent = models.PositiveIntegerField(default=50)
    is_active = models.BooleanField(default=True)
    remaks = NameField(max_length=512, blank=True, null=True)
    recorded_by = models.PositiveIntegerField(null=False)
    recorded_at = models.DateTimeField(auto_now_add = True, null=True)

    def __str__(self):
        return self.staff.name
    
    class Meta:
        verbose_name = "Staff Benefit"
        verbose_name_plural = "Staff Benefits"


class StaffBenefitDependent(models.Model):
    benefit = models.ForeignKey(StaffBenefit, on_delete = models.RESTRICT)
    benefit_dependent = models.ForeignKey(Person, on_delete = models.RESTRICT, related_name="benefit_dependent")
    is_active = models.BooleanField(default=True)
    remaks = NameField(max_length=512, blank=True, null=True)
    recorded_by = models.PositiveIntegerField(null=False)
    recorded_at = models.DateTimeField(auto_now_add = True, null=True)

    def __str__(self):
        return self.benefit.staff.name
    
    class Meta:
        verbose_name = "Staff Benefit Dependent"
        verbose_name_plural = "Staff Benefit Dependents"


class SecurityFund(models.Model):
    code = NameField(max_length=50, blank=True, null=True)
    name = NameField(max_length=150, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    recorded_by = models.PositiveIntegerField(null=False)
    recorded_at = models.DateTimeField(auto_now_add = True, null=True)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Security Fund"
        verbose_name_plural = "Security Fund"


class StaffSecurityFund(models.Model):
    staff = models.ForeignKey(Staff, on_delete = models.RESTRICT)
    fund = models.ForeignKey(SecurityFund, on_delete = models.RESTRICT)
    account = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    recorded_by = models.PositiveIntegerField(null=False)
    recorded_at = models.DateTimeField(auto_now_add = True, null=True)

    def __str__(self):
        return self.staff.name
    
    class Meta:
        verbose_name = "Staff Security Fund"
        verbose_name_plural = "Staff Security Funds"


class Document(models.Model):
    staff = models.ForeignKey(Staff, on_delete = models.RESTRICT)
    document_type = models.ForeignKey(DictionaryItem, on_delete = models.RESTRICT, related_name="document_type")
    document_name = NameField(max_length=150, blank=True, null=True)
    document_file = models.CharField(max_length=10000000, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    remaks = NameField(max_length=512, blank=True, null=True)
    recorded_by = models.PositiveIntegerField(null=False)
    recorded_at = models.DateTimeField(auto_now_add = True, null=True)

    def __str__(self):
        return self.document_name
    
    class Meta:
        verbose_name = "Document"
        verbose_name_plural = "Documents"




