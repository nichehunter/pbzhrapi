from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.http.response import JsonResponse
import statistics

import json
from rest_framework import pagination
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import *
from rest_framework.generics import *
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import *
from django.db.models import *
from datetime import date, timedelta
from rest_framework.settings import api_settings
from rest_framework import filters
import django_filters.rest_framework
from django_filters import DateRangeFilter,DateFilter
import io, csv, pandas as pd
from rest_framework.parsers import MultiPartParser

from dictionary.models import *
from dictionary.serializers import *

# Create your views here.

#-----------------------------------------------------dictionary view ---------------------------------------------------------

class DictionaryAdd(CreateAPIView):

    serializer_class = DictionarySerializer

    def post(self, request):
        serializer = DictionarySerializer(data=request.data, many=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DictionaryList(ListAPIView):
    queryset = Dictionary.objects.all()
    serializer_class = DictionarySerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['dictionary_code','dictionary_name']
    ordering_fields = ['id','dictionary_code','dictionary_name']
    ordering = ['-id']



class DictionaryUpdate(CreateAPIView):

    serializer_class = DictionaryUpdateSerializer

    def put(self, request, pk):
        dictio = Dictionary.objects.get(id=pk)
        serializer = DictionaryUpdateSerializer(dictio, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



#------------------------------------------------- dictionary item --------------------------------------------------------------------------
class itemFilter(django_filters.FilterSet):

    class Meta:
        model = DictionaryItem
        fields = {'dictionary_item_name' : ['exact', 'in']}


class DictionaryItemCheck(ListAPIView):
    queryset = DictionaryItem.objects.all()
    serializer_class = DictionaryItemSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend,filters.SearchFilter,filters.OrderingFilter]
    filterset_class = itemFilter
    search_fields = ['dictionary_item_code','dictionary_item_name']
    ordering_fields = ['id','dictionary_item_code','dictionary_item_name','dictionary']
    ordering = ['-id']


class DictionaryItemList(ListAPIView):
    queryset = DictionaryItem.objects.all()
    serializer_class = DictionaryItemListSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['dictionary_item_code','dictionary_item_name','dictionary__dictionary_name']
    ordering_fields = ['id','dictionary_item_code','dictionary_item_name','dictionary']
    ordering = ['-id']


class parentFilter(django_filters.FilterSet):

    class Meta:
        model = DictionaryItem
        fields = ['dictionary__id',]

class FilterDictionaryItemParent(ListAPIView):
    queryset = DictionaryItem.objects.all().order_by('-id')
    serializer_class = DictionaryItemSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend,filters.SearchFilter,filters.OrderingFilter]
    filterset_class = parentFilter
    search_fields = ['dictionary_item_code','dictionary_item_name']
    ordering_fields = ['id','dictionary_item_code','dictionary_item_name','dictionary']
    ordering = ['dictionary_item_name']


class parentItemFilter(django_filters.FilterSet):

    class Meta:
        model = DictionaryItem
        fields = ['dictionary_item_parent',]


class FilterDictionaryItemParentData(ListAPIView):
    queryset = DictionaryItem.objects.all().order_by('-id')
    serializer_class = DictionaryItemSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend,filters.SearchFilter,filters.OrderingFilter]
    filterset_class = parentItemFilter
    search_fields = ['dictionary_item_code','dictionary_item_name']
    ordering_fields = ['id','dictionary_item_code','dictionary_item_name','dictionary']
    ordering = ['dictionary_item_name']


class DictionaryItemAdd(CreateAPIView):

    serializer_class = DictionaryItemPostSerializer

    def post(self, request):
        serializer = DictionaryItemPostSerializer(data=request.data, many=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class DictionaryItemUpdate(CreateAPIView):

    serializer_class = DictionaryItemUpdateSerializer

    def put(self, request, pk):
        dictio = DictionaryItem.objects.get(id=pk)
        serializer = DictionaryItemUpdateSerializer(dictio, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)