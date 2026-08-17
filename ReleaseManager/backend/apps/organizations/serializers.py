from rest_framework import serializers
from .models import BusinessLine, Group


class BusinessLineSerializer(serializers.ModelSerializer):
    leader_name = serializers.CharField(source='leader.display_name', read_only=True, allow_null=True)

    class Meta:
        model = BusinessLine
        fields = '__all__'


class GroupSerializer(serializers.ModelSerializer):
    business_line_name = serializers.CharField(source='business_line.name', read_only=True)
    leader_name = serializers.CharField(source='leader.display_name', read_only=True, allow_null=True)
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = '__all__'

    def get_member_count(self, obj):
        return obj.memberships.count()


class OrgTreeNodeSerializer(serializers.Serializer):
    """组织树节点"""
    id = serializers.IntegerField()
    type = serializers.CharField()  # 'business_line' | 'group' | 'user'
    name = serializers.CharField()
    code = serializers.CharField(required=False)
    leader_id = serializers.IntegerField(required=False, allow_null=True)
    leader_name = serializers.CharField(required=False, allow_null=True)
    membership_type = serializers.CharField(required=False)
    children = serializers.ListField(child=serializers.DictField(), default=[])