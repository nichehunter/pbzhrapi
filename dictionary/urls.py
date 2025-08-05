from django.urls import path
from django.conf.urls.static import static
from django.conf import settings
from dictionary.views import *

#-----------------------------------urls---------------------------------------------

urlpatterns = [
	path('dictionary', DictionaryAdd.as_view()),
	path('dictionary/update/<int:pk>', DictionaryUpdate.as_view()),
	path('dictionary/filter', DictionaryList.as_view()),
	path('dictionary/item/filter', DictionaryItemList.as_view()),
	path('dictionary/item', DictionaryItemAdd.as_view()),
	path('dictionary/item/check', DictionaryItemCheck.as_view()),
	path('dictionary/item/update/<int:pk>', DictionaryItemUpdate.as_view()),
	path('dictionary/item/parent', FilterDictionaryItemParent.as_view()),
	path('dictionary/item/parent/data', FilterDictionaryItemParentData.as_view()),
]+static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)