from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.http.response import JsonResponse
import statistics
from django.utils import timezone

import json
import datetime
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
from django_filters import DateRangeFilter, DateFilter
import io, csv, pandas as pd
from rest_framework.parsers import MultiPartParser

from training.models import *
from dictionary.models import DictionaryItem
from training.serializers import *


# ====================================================== training ====================================================
class trainingFilter(django_filters.FilterSet):

    class Meta:
        model = Training
        fields = {
            "training_type__id": ["exact", "in"],
            "satatus__id": ["exact", "in"],
            "quarter": ["exact", "in"],
            "year": ["exact", "in"],
            "start_date": ["exact", "in", "gte"],
            "end_date": ["exact", "in", "lte"],
        }


class TrainingAdd(CreateAPIView):

    serializer_class = TrainingSerializer

    def generate_auto_training_code(self, prefix="TRN"):
        """Generates an automatic sequential training code e.g., TRN-2026-0001."""
        year = timezone.now().strftime("%Y")
        last_training = (
            Training.objects.filter(code__startswith=f"{prefix}-{year}-")
            .order_by("-id")
            .first()
        )

        if last_training and last_training.code:
            try:
                last_seq = int(last_training.code.split("-")[-1])
                new_seq = last_seq + 1
            except (ValueError, IndexError):
                new_seq = 1
        else:
            new_seq = 1

        return f"{prefix}-{year}-{new_seq:04d}"

    def post(self, request):
        serializer = TrainingSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(code=self.generate_auto_training_code())
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TrainingList(ListAPIView):
    queryset = Training.objects.all()
    serializer_class = TrainingListSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [
        django_filters.rest_framework.DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = trainingFilter
    search_fields = ["code", "name", "training_type__dictionary_item_name"]
    ordering_fields = ["id", "code", "name", "training_type__dictionary_item_name"]
    ordering = ["-id"]


class TrainingUpdate(CreateAPIView):

    serializer_class = TrainingUpdateSerializer

    def put(self, request, pk):
        salary = Training.objects.get(id=pk)
        serializer = TrainingUpdateSerializer(salary, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TrainingDetails(APIView):

    def get_object(self, pk):
        try:
            return Training.objects.get(pk=pk)
        except Training.DoesNotExist:
            return None

    def get(self, request, pk):
        training = self.get_object(pk)
        if not training:
            return Response(
                {"error": "Training not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = TrainingListSerializer(training, many=False)
        return JsonResponse(serializer.data, safe=False)

    def patch(self, request, pk):
        training = self.get_object(pk)
        if not training:
            return Response(
                {"error": "Training not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = TrainingSerializer(training, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()

            return Response(
                {
                    "message": "Training updated successfully.",
                    "data": serializer.data,
                },
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TrainingLatest(APIView):

    serializer_class = TrainingSerializer

    def get(self, request):
        project = Training.objects.all().latest("id")
        serializer = TrainingSerializer(project, many=False)
        return JsonResponse(serializer.data, safe=False)


# ====================================================== leave type ====================================================
class staffTrainingFilter(django_filters.FilterSet):

    class Meta:
        model = StaffTraining
        fields = {
            "staff__id": ["exact", "in"],
            "training__id": ["exact", "in"],
            "training__quarter": ["exact", "in"],
            "training__year": ["exact", "in"],
            "training__start_date": ["exact", "in", "gte"],
            "training__end_date": ["exact", "in", "lte"],
        }


class StaffTrainingAdd(CreateAPIView):

    serializer_class = StaffTrainingSerializer

    def post(self, request):
        serializer = StaffTrainingSerializer(data=request.data, many=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StaffTrainingList(ListAPIView):
    queryset = StaffTraining.objects.all()
    serializer_class = StaffTrainingListSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [
        django_filters.rest_framework.DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = staffTrainingFilter
    search_fields = ["training__code", "training__name", "staff__staff_opf"]
    ordering_fields = ["id", "training__code", "training__name", "staff__staff_opf"]
    ordering = ["-id"]


class StaffTrainingUpdate(CreateAPIView):

    serializer_class = StaffTrainingUpdateSerializer

    def put(self, request, pk):
        leave = StaffTraining.objects.get(id=pk)
        serializer = StaffTrainingUpdateSerializer(leave, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ====================================================== leave type ====================================================
class attachmentTrainingFilter(django_filters.FilterSet):

    class Meta:
        model = TrainingAttachment
        fields = {
            "training__id": ["exact", "in"],
            "training__quarter": ["exact", "in"],
            "training__year": ["exact", "in"],
            "training__start_date": ["exact", "in", "gte"],
            "training__end_date": ["exact", "in", "lte"],
        }


class TrainingAttachmentAdd(CreateAPIView):

    serializer_class = TrainingAttachmentSerializer

    def post(self, request):
        serializer = TrainingAttachmentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TrainingAttachmentList(ListAPIView):
    queryset = TrainingAttachment.objects.all()
    serializer_class = TrainingAttachmentListSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    filter_backends = [
        django_filters.rest_framework.DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = attachmentTrainingFilter
    search_fields = [
        "training__code",
        "training__name",
    ]
    ordering_fields = [
        "id",
        "training__code",
        "training__name",
    ]
    ordering = ["-id"]


class TrainingAttachmentUpdate(CreateAPIView):

    serializer_class = TrainingAttachmentUpdateSerializer

    def put(self, request, pk):
        leave = TrainingAttachment.objects.get(id=pk)
        serializer = TrainingAttachmentUpdateSerializer(leave, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
