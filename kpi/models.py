from django.db import models
from django.core.validators import MinValueValidator
from controller.models import *
from dictionary.models import DictionaryItem
import datetime
from django.core.exceptions import ValidationError
from django.utils import timezone


# Create your models here.
class NameField(models.CharField):

    def get_prep_value(self, value):
        return str(value).lower()


class Kpi(models.Model):
    code = NameField(max_length=20, blank=True, null=True)
    name = NameField(max_length=50, blank=True, null=True)
    descriptions = NameField(max_length=512, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    year = models.CharField(max_length=15, blank=True, null=True)
    department = models.ForeignKey(
        Department, on_delete=models.CASCADE, related_name="departmentkpi"
    )
    branch = models.ForeignKey(
        Branch, on_delete=models.CASCADE, related_name="branchkpi"
    )
    level = models.ForeignKey(
        DictionaryItem, on_delete=models.RESTRICT, null=True, blank=True
    )
    recorded_by = models.PositiveIntegerField(null=False)
    recorded_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Kpi"
        verbose_name_plural = "Kips"


class Section(models.Model):
    code = NameField(max_length=20, blank=True, null=True)
    name = NameField(max_length=50)
    descriptions = NameField(max_length=512, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    kpi = models.ForeignKey(Kpi, on_delete=models.RESTRICT, related_name="section")
    recorded_by = models.PositiveIntegerField(null=False)
    recorded_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Section"
        verbose_name_plural = "Sections"


class KeyResult(models.Model):
    name = models.TextField()
    weighting_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=0
    )
    is_active = models.BooleanField(default=True)
    section = models.ForeignKey(
        Section, on_delete=models.RESTRICT, related_name="result"
    )
    kpi = models.ForeignKey(Kpi, on_delete=models.RESTRICT, related_name="kpiresult")
    recorded_by = models.PositiveIntegerField(null=False)
    recorded_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Key Result"
        verbose_name_plural = "Key Results"


class Performance(models.Model):
    performance_measure = models.TextField()
    fy_target = models.TextField()
    weighting = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    result = models.ForeignKey(
        KeyResult, on_delete=models.RESTRICT, related_name="performance"
    )
    kpi = models.ForeignKey(
        Kpi, on_delete=models.RESTRICT, related_name="kpiperfomance"
    )
    recorded_by = models.PositiveIntegerField(null=False)
    recorded_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Performance"
        verbose_name_plural = "Performances"


class StaffKPI(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.RESTRICT, related_name="staffkpi")
    perfomance = models.ForeignKey(Performance, on_delete=models.RESTRICT)
    kpi = models.ForeignKey(Kpi, on_delete=models.RESTRICT)
    actual = models.DecimalField(max_digits=10, decimal_places=1, default=0)
    rating = models.DecimalField(max_digits=10, decimal_places=1, default=0)
    weighting_rating = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    recorded_by = models.PositiveIntegerField(null=False)
    recorded_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return self.staff.full_name

    class Meta:
        verbose_name = "Staff KPI"
        verbose_name_plural = "Staff KPIs"


# ===================================================================================
# KPI Section, Key Result, and Performance Measure Models
# ===================================================================================
class KPISection(models.Model):
    code = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    recorded_by = models.PositiveIntegerField(null=False)
    recorded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class KPISectionWeight(models.Model):
    section = models.ForeignKey(
        KPISection, on_delete=models.CASCADE, related_name="weights"
    )
    weight = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    recorded_by = models.PositiveIntegerField(null=False)
    recorded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Weight for {self.section.title}"


class KPIKeyResult(models.Model):
    section = models.ForeignKey(
        KPISection, on_delete=models.CASCADE, related_name="key_results"
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    department = models.CharField(max_length=150, null=False)
    is_active = models.BooleanField(default=True)
    recorded_by = models.PositiveIntegerField(null=False)
    recorded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.section.title} -> {self.title}"


class KPIPerformanceMeasure(models.Model):
    key_result = models.ForeignKey(
        KPIKeyResult, on_delete=models.CASCADE, related_name="measures"
    )
    description = models.TextField()
    unit_of_measure = models.CharField(max_length=50, default="Percentage")
    is_active = models.BooleanField(default=True)
    recorded_by = models.PositiveIntegerField(null=False)
    recorded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.description


# --- STAFF EXECUTION TABLES ---


class HRKPIWindow(models.Model):
    STATUS_CHOICES = (
        ("open", "Open for Submission"),
        ("closed", "Closed"),
        ("processing", "Under Evaluation"),
        ("completed", "Completed/Archived"),
    )
    code = models.CharField(max_length=50, unique=True, blank=True, null=True)
    title = models.CharField(max_length=255)  # e.g., "2026 Mid-Year KPI Evaluation"
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="open")
    recorded_by = models.PositiveIntegerField(null=False)
    recorded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.status})"


class StaffKPIPeriod(models.Model):
    STATUS_CHOICES = (
        ("draft", "Draft"),
        ("submitted", "Submitted to Manager"),
        ("approved", "Approved by Manager"),
        ("rejected", "Returned for Corrections"),
        ("archived", "Archived"),
    )
    window = models.ForeignKey(
        HRKPIWindow, on_delete=models.CASCADE, related_name="staff_periods"
    )
    staff = models.ForeignKey(
        Staff, on_delete=models.RESTRICT, related_name="staff_kpi_periods"
    )
    total_score = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Cached sum of weighted ratings",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    submitted_at = models.DateTimeField(null=True, blank=True)
    station = models.CharField(max_length=20, null=True, blank=True)
    station_type = models.CharField(max_length=20, null=True, blank=True)
    station_id = models.CharField(max_length=50, null=True, blank=True)
    station_name = models.CharField(max_length=100, null=True, blank=True)
    station_supervisor = models.ForeignKey(
        Staff,
        on_delete=models.RESTRICT,
        related_name="staff_kpi_supervisor",
        null=True,
        blank=True,
    )
    approver_name = models.CharField(max_length=50, null=True, blank=True)
    approved_by = models.PositiveIntegerField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("window", "staff")

    def __str__(self):
        return f"{self.staff} - {self.window.title}"


class StaffKPIItem(models.Model):
    kpi_period = models.ForeignKey(
        StaffKPIPeriod, on_delete=models.CASCADE, related_name="kpi_items"
    )
    section = models.ForeignKey(KPISection, on_delete=models.PROTECT)
    key_result = models.ForeignKey(KPIKeyResult, on_delete=models.PROTECT)
    performance_measure = models.ForeignKey(
        KPIPerformanceMeasure, on_delete=models.PROTECT
    )
    target_value = models.CharField(max_length=150, default="0.00")
    actual_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    weighting = models.DecimalField(
        max_digits=5, decimal_places=2, help_text="Percentage e.g. 20.00 for 20%"
    )
    rating = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    weighting_rating = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.kpi_period.window.title} -> {self.section.title} -> {self.key_result.title} -> {self.performance_measure.description}"


class StaffKPISubmissionLog(models.Model):
    ACTION_CHOICES = (
        ("submitted", "Submitted to Supervisor"),
        ("approved", "Approved by Supervisor"),
        ("rejected", "Returned for Corrections"),
    )

    kpi_period = models.ForeignKey(
        StaffKPIPeriod, on_delete=models.CASCADE, related_name="submission_logs"
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    actor = models.ForeignKey(
        Staff,
        on_delete=models.RESTRICT,
        related_name="kpi_actions_taken",
        help_text="Staff or Supervisor who performed this action",
    )
    comments = models.TextField(
        blank=True,
        null=True,
        help_text="Reason for rejection, feedback, or approval notes",
    )
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-recorded_at"]
        verbose_name = "Staff KPI Submission Log"
        verbose_name_plural = "Staff KPI Submission Logs"

    def __str__(self):
        return f"{self.kpi_period.staff.full_name} - {self.action} on {self.recorded_at.strftime('%Y-%m-%d %H:%M')}"
