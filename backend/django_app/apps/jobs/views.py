# pyrefly: ignore [missing-import]
from rest_framework import viewsets
# pyrefly: ignore [missing-import]
from rest_framework.decorators import action
# pyrefly: ignore [missing-import]
from rest_framework.response import Response
# pyrefly: ignore [missing-import]
from django.db.models import Avg, Count
from .models import JobApplication, InterviewSession
from .serializers import JobApplicationSerializer, InterviewSessionSerializer


class JobApplicationViewSet(viewsets.ModelViewSet):
    serializer_class = JobApplicationSerializer

    def get_queryset(self):
        return JobApplication.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        queryset = self.get_queryset()
        counts = queryset.values('status').annotate(total=Count('id'))
        avg_ats = queryset.aggregate(avg_ats=Avg('ats_score'))['avg_ats'] or 0.0

        stats_dict = {
            "total": queryset.count(),
            "saved": 0,
            "applied": 0,
            "interviewing": 0,
            "offered": 0,
            "rejected": 0,
            "average_ats_score": round(avg_ats, 2)
        }
        for item in counts:
            status_name = item['status']
            if status_name in stats_dict:
                stats_dict[status_name] = item['total']

        return Response(stats_dict)


class InterviewSessionViewSet(viewsets.ModelViewSet):
    serializer_class = InterviewSessionSerializer

    def get_queryset(self):
        return InterviewSession.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
