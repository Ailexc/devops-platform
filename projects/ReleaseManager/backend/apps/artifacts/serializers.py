from rest_framework import serializers
from .models import ArtifactRepository, Artifact, ArtifactPromotion


class ArtifactRepositorySerializer(serializers.ModelSerializer):
    artifact_count = serializers.SerializerMethodField()

    class Meta:
        model = ArtifactRepository
        fields = '__all__'

    def get_artifact_count(self, obj):
        return obj.artifact_set.count() if hasattr(obj, 'artifact_set') else 0


class ArtifactListSerializer(serializers.ModelSerializer):
    """列表用：精简字段"""
    application_name = serializers.CharField(source='application.name', read_only=True)
    application_code = serializers.CharField(source='application.code', read_only=True)
    repository_name = serializers.CharField(source='repository.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.display_name', read_only=True)
    promotion_count = serializers.SerializerMethodField()

    class Meta:
        model = Artifact
        fields = [
            'id', 'application', 'application_name', 'application_code',
            'version', 'artifact_type', 'repository_name',
            'storage_path', 'image_tag', 'current_env',
            'branch', 'commit_id', 'build_duration',
            'file_size', 'status', 'created_at', 'created_by_name',
            'promotion_count',
        ]

    def get_promotion_count(self, obj):
        return obj.promotions.count() if hasattr(obj, 'promotions') else 0


class ArtifactDetailSerializer(serializers.ModelSerializer):
    """详情用：完整字段"""
    application_name = serializers.CharField(source='application.name', read_only=True)
    application_code = serializers.CharField(source='application.code', read_only=True)
    repository_name = serializers.CharField(source='repository.name', read_only=True)
    repository_url = serializers.CharField(source='repository.url', read_only=True)
    created_by_name = serializers.CharField(source='created_by.display_name', read_only=True)
    promotions = serializers.SerializerMethodField()

    class Meta:
        model = Artifact
        fields = '__all__'

    def get_promotions(self, obj):
        qs = obj.promotions.select_related('from_env', 'to_env', 'promoted_by').order_by('created_at')
        return ArtifactPromotionSerializer(qs, many=True).data


class ArtifactPromotionSerializer(serializers.ModelSerializer):
    from_env_name = serializers.CharField(source='from_env.name', read_only=True)
    to_env_name = serializers.CharField(source='to_env.name', read_only=True)
    promoted_by_name = serializers.CharField(source='promoted_by.display_name', read_only=True)

    class Meta:
        model = ArtifactPromotion
        fields = '__all__'