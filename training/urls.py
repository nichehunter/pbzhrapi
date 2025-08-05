from django.urls import path
from django.conf.urls.static import static
from django.conf import settings
from training.views import *

#-----------------------------------urls---------------------------------------------

urlpatterns = [
	path('training', TrainingAdd.as_view()),
	path('training/update/<int:pk>', TrainingUpdate.as_view()),
	path('training/list', TrainingList.as_view()),
	path('training/details/<int:pk>', TrainingDetails.as_view()),
	path('training/latest', TrainingLatest.as_view()),
	path('staff-training/list', StaffTrainingList.as_view()),
	path('staff-training', StaffTrainingAdd.as_view()),
	path('staff-training/update/<int:pk>', StaffTrainingUpdate.as_view()),
	path('training-attachment', TrainingAttachmentAdd.as_view()),
	path('training-attachment/update/<int:pk>', TrainingAttachmentUpdate.as_view()),
	path('training-attachment/list', TrainingAttachmentList.as_view()),
]+static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)