from django.urls import path
from django.conf.urls.static import static
from django.conf import settings
from report.views import *

#-----------------------------------urls---------------------------------------------

urlpatterns = [
	path('count', PBZCount.as_view()),
	path('staff-center', StaffCenter.as_view()),
	path('staff-title', StaffTitle.as_view()),
]+static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)