from django.urls import path
from django.conf.urls.static import static
from django.conf import settings
from kpi.views import *

#-----------------------------------urls---------------------------------------------

urlpatterns = [
	path('kpi/list', KPIList.as_view()),
	path('kpi-section/list', KPISectionList.as_view()),
	path('kpi-result/list', KPIResultList.as_view()),
	path('kpi-perfomance/list', KPIPerformanceList.as_view()),
	path('kpi-staff', StaffKPIData.as_view()),
	path('kpi-staff/list', KPIStaffList.as_view()),
]+static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)