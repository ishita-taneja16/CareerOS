from django.db import models
from django.conf import settings
from apps.core.models import BaseModel

class JobApplication(BaseModel):
    STATUS_CHOICES = [
        ("saved", "Saved"),
        ("applied", "Applied"),
        ("interviewing", "Interviewing"),
        ("offered", "Offered"),
        ("rejected", "Rejected"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="job_applications"
    )
    company = models.CharField(max_length=255)
    role_title = models.CharField(max_length=255)
    job_description = models.TextField(blank=True, default="")
    ats_score = models.FloatField(null=True, blank=True)
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default="saved"
    )
    applied_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, default="")

    def __str__(self):
        return f"{self.role_title} at {self.company} ({self.user.email})"

class InterviewSession(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="interview_sessions"
    )
    job = models.ForeignKey(
        JobApplication,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="interviews"
    )
    job_description_raw = models.TextField(blank=True, default="")
    feedback = models.JSONField(blank=True, default=dict)
    overall_score = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"Interview for {self.job.role_title if self.job else 'Custom Job'} ({self.user.email})"
