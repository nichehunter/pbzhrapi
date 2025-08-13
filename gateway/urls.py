from django.urls import path
from django.conf.urls.static import static
from django.conf import settings
from dictionary.views import *
from controller.views import *
from leave.views import *
from gateway.views import *
from payroll.views import *

#-----------------------------------urls---------------------------------------------

urlpatterns = [
	path('dictionary/item/parent', FilterDictionaryItemParent.as_view()),
	path('staff/update/<int:pk>', StaffUpdate.as_view()),
	path('staff/details/<int:pk>', StaffDetails.as_view()),
	path('staff/data/<int:pk>', StaffData.as_view()),
	path('staff/list', StaffList.as_view()),
	path('staff/branch/details', StaffBranchDetails.as_view()),
	path('staff-qualification/list', StaffQualificationList.as_view()),
	path('staff-qualification', StaffQualificationAdd.as_view()),
	path('supervisor/list', SupervisorList.as_view()),
	path('supervisor/staff/list', DepartmentStaffList.as_view()),
	path('document/list', DocumentList.as_view()),
	path('document', DocumentAdd.as_view()),
	path('department/all/list', DepartmentAllList.as_view()),
	path('department-head/list', DepartmentHeadList.as_view()),
	path('branch/list', BranchList.as_view()),
	path('branch-manager/list', BranchManagerList.as_view()),
	path('roster/list', RosterList.as_view()),
	path('leave-roster', LeaveRosterAdd.as_view()),
	path('leave-roster/list', LeaveRosterList.as_view()),
	path('leave-application', LeaveApplicationAdd.as_view()),
	path('leave-application/list', LeaveApplicationList.as_view()),
	path('leave-application/update/<int:pk>', LeaveApplicationUpdate.as_view()),
	path('leave-application/details/<int:pk>', LeaveApplicationDetail.as_view()),
	path('leave-duration', LeaveDurationAdd.as_view()),
	path('leave-duration/list', LeaveDurationList.as_view()),
	path('leave-assignment', LeaveAssignmentAdd.as_view()),
	path('leave-status/<int:pk>', LeaveApplicationChangeStatus.as_view()),
	path('leave-assignment/list', LeaveAssignmentList.as_view()),
	path('leave-foward', LeaveFowardAdd.as_view()),
	path('leave-comment', LeaveCommentAdd.as_view()),
	path('leave-approval', LeaveApprovalAdd.as_view()),
	path('leave-rejected', LeaveRejectedAdd.as_view()),
	path('leave-type/list', LeaveTypeList.as_view()),
	path('leave-duration/list', LeaveDurationList.as_view()),
	path('leave-balance/list', LeaveBalanceList.as_view()),
	path('holiday/list', PublicHolidayList.as_view()),


	path('supervisor/staff/count/<str:data>/<int:branch>/<int:department>', StaffCount.as_view()),
	path('supervisor/assignment/count/<int:pk>', LeaveAssignmentCount.as_view()),

	path('salary/list', StaffSalaryList.as_view()),
	path('allowance/list', StaffAllowanceList.as_view()),
	path('monthly-allowance/list', MonthlyAllowanceList.as_view()),
	path('deduction/list', StaffDeductionList.as_view()),
	path('monthly-deduction/list', MonthlyDeductionList.as_view()),
	path('organization/list', StaffOrganizationList.as_view()),
	path('payroll/list', StaffPayrollList.as_view()),
	path('staff-payroll/list', StaffPayrollList.as_view()),

	path('bot-employee', GenerateEmployeeData.as_view()),

	path('kpi/list', KPIList.as_view()),

]+static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)



