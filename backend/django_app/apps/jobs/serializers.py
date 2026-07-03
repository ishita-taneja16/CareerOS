# pyrefly: ignore [missing-import]
from rest_framework import serializers
from .models import JobApplication, InterviewSession

class JobApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobApplication
        fields = ('id', 'user', 'company', 'role_title', 'job_description', 'ats_score', 'status', 'applied_date', 'notes', 'created_at', 'updated_at')
        read_only_fields = ('user',)

class InterviewSessionSerializer(serializers.ModelSerializer):
    job_details = JobApplicationSerializer(source='job', read_only=True)

    class Meta:
        model = InterviewSession
        fields = ('id', 'user', 'job', 'job_details', 'job_description_raw', 'feedback', 'overall_score', 'created_at', 'updated_at')
        read_only_fields = ('user',)
