from rest_framework import serializers
from .models import AuditLog

class AuditLogSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.display_name', read_only=True)
    class Meta:
        model = AuditLog
        fields = '__all__'