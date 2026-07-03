from rest_framework import serializers
from .models import Resume, ResumeVersion

class ResumeVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResumeVersion
        fields = ('id', 'resume', 'version_number', 'label', 'raw_text', 'structured_data', 'is_active', 'created_at', 'updated_at')
        read_only_fields = ('version_number',)

class ResumeSerializer(serializers.ModelSerializer):
    versions = ResumeVersionSerializer(many=True, read_only=True)
    active_version = serializers.SerializerMethodField()

    class Meta:
        model = Resume
        fields = ('id', 'user', 'title', 'versions', 'active_version', 'created_at', 'updated_at')
        read_only_fields = ('user',)

    def get_active_version(self, obj):
        active = obj.versions.filter(is_active=True).first()
        if active:
            return ResumeVersionSerializer(active).data
        return None
