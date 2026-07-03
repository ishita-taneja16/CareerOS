# pyrefly: ignore [missing-import]
from django.urls import path, include
# pyrefly: ignore [missing-import]
from rest_framework.routers import DefaultRouter
from .views import JobApplicationViewSet, InterviewSessionViewSet

router = DefaultRouter()
router.register(r'applications', JobApplicationViewSet, basename='jobapplication')
router.register(r'interviews', InterviewSessionViewSet, basename='interviewsession')

urlpatterns = [
    path('', include(router.urls)),
]
