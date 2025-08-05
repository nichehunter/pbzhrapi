from rest_framework import fields, serializers
import json
import datetime
from dictionary.models import *

#----------------------create serializer-------------------------------------------------#

class DictionarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Dictionary
        fields = ('__all__')
        read_only_fields = ('id',)


class DictionaryUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dictionary
        fields = ('__all__')
        read_only_fields = ('id','recorded_by')


class DictionaryItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = DictionaryItem
        fields = ('__all__')
        read_only_fields = ('id',)


class DictionaryItemListSerializer(serializers.ModelSerializer):
    dictionary = DictionarySerializer(read_only=True)
    class Meta:
        model = DictionaryItem
        fields = ('__all__')
        read_only_fields = ('id',)


class DictionaryItemPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = DictionaryItem
        fields = ('__all__')
        read_only_fields = ('id',)


class DictionaryItemUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DictionaryItem
        fields = ('__all__')
        read_only_fields = ('id','recorded_by')

class DictionarySerializerExport(serializers.ModelSerializer):
    class Meta:
        model = Dictionary
        fields = ('id','dictionary_name')
        read_only_fields = ('id',)


class DictionaryItemSerializerExport(serializers.ModelSerializer):
    class Meta:
        model = DictionaryItem
        fields = ('id','dictionary_item_name')
        read_only_fields = ('id',)


