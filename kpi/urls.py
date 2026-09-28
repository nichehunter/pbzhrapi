from django.urls import path
from django.conf.urls.static import static
from django.conf import settings
from kpi.views import *
from kpi.gateway import *

# -----------------------------------urls---------------------------------------------

urlpatterns = [
    path("kpi/list", KPIList.as_view()),
    path("kpi-section/list", KPISectionList.as_view()),
    path("kpi-result/list", KPIResultList.as_view()),
    path("kpi-perfomance/list", KPIPerformanceList.as_view()),
    path("kpi-staff", StaffKPIData.as_view()),
    path("kpi-staff/list", KPIStaffList.as_view()),
    path("section/create", KPISectionAdd.as_view()),
    path("section/list", KPISectionList.as_view()),
    path("section/all", KPISectionAllList.as_view()),
    path("result/create", KeyResultAdd.as_view()),
    path("result/list", KeyResultList.as_view()),
    path("result/all", KPIKeyResultAllList.as_view()),
    path("performance/create", KPIPerformanceMeasureAdd.as_view()),
    path("performance/list", KPIPerformanceMeasureList.as_view()),
    path("window/create", HRKPIWindowAdd.as_view()),
    path("window/list", HRKPIWindowList.as_view()),
    path("window/detail/<int:pk>", HRKPIWindowDetailView.as_view()),
    path("period/list", KPIPeriodList.as_view()),
    path("period/item/<int:pk>", StaffKPIFormStructureView.as_view()),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
