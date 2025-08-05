from rest_framework import fields, serializers
import json
import datetime
from training.models import *
from controller.models import Staff
from dictionary.models import DictionaryItem


#================================================ export ===============================================
class DictionaryItemSerializerExport(serializers.ModelSerializer):
    class Meta:
        model = DictionaryItem
        fields = ('id','dictionary_item_name')
        read_only_fields = ('id',)

class StaffExportSerializer(serializers.ModelSerializer):
    gender = DictionaryItemSerializerExport(read_only=True)
    class Meta:
        model = Staff
        fields = ('id','staff_opf','code','full_name','phone_number','address','gender')
        read_only_fields = ('id',)


class TrainingExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Training
        fields = ('id','name')
        read_only_fields = ('id',)

#================================================ export ===============================================
class TrainingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Training
        fields = ('__all__')
        read_only_fields = ('id',)


class TrainingListSerializer(serializers.ModelSerializer):
    training_type = DictionaryItemSerializerExport(read_only=True)
    satatus = DictionaryItemSerializerExport(read_only=True)
    class Meta:
        model = Training
        fields = ('__all__')
        read_only_fields = ('id',)


class TrainingUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Training
        fields = ('__all__')
        read_only_fields = ('id','recorded_by')


#================================================ export ===============================================
class StaffTrainingSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffTraining
        fields = ('__all__')
        read_only_fields = ('id',)


class StaffTrainingListSerializer(serializers.ModelSerializer):
    training = TrainingListSerializer(read_only=True)
    staff = StaffExportSerializer(read_only=True)
    class Meta:
        model = StaffTraining
        fields = ('__all__')
        read_only_fields = ('id',)


class StaffTrainingUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffTraining
        fields = ('__all__')
        read_only_fields = ('id','recorded_by')


#================================================ export ===============================================
class TrainingAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainingAttachment
        fields = ('__all__')
        read_only_fields = ('id',)


class TrainingAttachmentListSerializer(serializers.ModelSerializer):
    training = TrainingListSerializer(read_only=True)
    class Meta:
        model = TrainingAttachment
        fields = ('__all__')
        read_only_fields = ('id',)


class TrainingAttachmentUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainingAttachment
        fields = ('__all__')
        read_only_fields = ('id','recorded_by')