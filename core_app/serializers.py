from core_app.models import Student, User
from rest_framework import serializers


class StudentSerializer(serializers.HyperlinkedModelSerializer):

    account = serializers.PrimaryKeyRelatedField(
        write_only=True, queryset=User.objects.all())

    class Meta:
        model = Student
        fields = ['url', 'name', 'account', 'id']
