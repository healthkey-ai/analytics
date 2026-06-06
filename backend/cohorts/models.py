from django.conf import settings
from django.db import models


class SavedCohort(models.Model):
    # db_constraint=False because the identity table is managed by ctomop,
    # not this app. On a fresh DB, migrate will fail if ctomop hasn't run yet
    # and the identity table doesn't exist.
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="saved_cohorts",
        db_constraint=False,
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    filters = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"], name="cohort_user_created_idx"),
        ]

    def __str__(self):
        return f"{self.name} ({self.user})"
