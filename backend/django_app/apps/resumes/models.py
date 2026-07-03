from django.db import models
from django.conf import settings
from apps.core.models import BaseModel

class Resume(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="resumes"
    )
    title = models.CharField(max_length=255, default="My Resume")

    def __str__(self):
        return f"{self.title} ({self.user.email})"

class ResumeVersion(BaseModel):
    resume = models.ForeignKey(
        Resume,
        on_delete=models.CASCADE,
        related_name="versions"
    )
    version_number = models.IntegerField()
    label = models.CharField(max_length=255, default="Version")
    raw_text = models.TextField(blank=True, default="")
    structured_data = models.JSONField(blank=True, default=dict)
    is_active = models.BooleanField(default=False)

    class Meta:
        ordering = ["-version_number"]

    def __str__(self):
        return f"{self.resume.title} - v{self.version_number} ({self.label})"
