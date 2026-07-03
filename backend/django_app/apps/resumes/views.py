from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Resume, ResumeVersion
from .serializers import ResumeSerializer, ResumeVersionSerializer


class ResumeViewSet(viewsets.ModelViewSet):
    serializer_class = ResumeSerializer

    def get_queryset(self):
        return Resume.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'], url_path='versions/(?P<version_id>[^/.]+)/set-active')
    def set_active(self, request, pk=None, version_id=None):
        try:
            resume = self.get_object()
            version = ResumeVersion.objects.get(id=version_id, resume=resume)
            
            # Deactivate other versions
            resume.versions.update(is_active=False)
            
            # Activate this one
            version.is_active = True
            version.save()
            
            return Response(ResumeVersionSerializer(version).data)
        except ResumeVersion.DoesNotExist:
            return Response({"error": "Version not found"}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['get'])
    def compare(self, request, pk=None):
        resume = self.get_object()
        v1_id = request.query_params.get('v1')
        v2_id = request.query_params.get('v2')
        
        if not v1_id or not v2_id:
            return Response({"error": "Please provide v1 and v2 UUIDs in query parameters"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            v1 = ResumeVersion.objects.get(id=v1_id, resume=resume)
            v2 = ResumeVersion.objects.get(id=v2_id, resume=resume)
        except ResumeVersion.DoesNotExist:
            return Response({"error": "One or both resume versions not found"}, status=status.HTTP_404_NOT_FOUND)
            
        diff = self._compare_json(v1.structured_data, v2.structured_data)
        return Response({
            "v1": {
                "id": v1.id,
                "label": v1.label,
                "version_number": v1.version_number
            },
            "v2": {
                "id": v2.id,
                "label": v2.label,
                "version_number": v2.version_number
            },
            "diff": diff
        })

    def _compare_json(self, d1: dict, d2: dict) -> dict:
        comparison = {}
        all_keys = set(d1.keys()).union(set(d2.keys()))
        for key in all_keys:
            val1 = d1.get(key)
            val2 = d2.get(key)
            if val1 != val2:
                comparison[key] = {
                    "v1": val1,
                    "v2": val2,
                    "status": "changed" if (val1 and val2) else ("added" if val2 else "removed")
                }
            else:
                comparison[key] = {
                    "value": val1,
                    "status": "unchanged"
                }
        return comparison
