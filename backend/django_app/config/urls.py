from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/users/', include('apps.users.urls')),
    path('api/v1/resumes/', include('apps.resumes.urls')),
    path('api/v1/jobs/', include('apps.jobs.urls')),
]
