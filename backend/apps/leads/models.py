import uuid

from django.db import models


class LeadOpportunity(models.Model):
    lead_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company_name = models.TextField()
    contact_name = models.TextField(blank=True, null=True)
    job_title = models.TextField(blank=True, null=True)
    email = models.TextField(blank=True, null=True)
    phone_number = models.TextField(blank=True, null=True)
    website = models.TextField(blank=True, null=True)
    last_modified_date = models.DateTimeField()
    industry = models.TextField(blank=True, null=True)
    company_size = models.TextField(blank=True, null=True)
    annual_revenue = models.TextField(blank=True, null=True)
    country = models.TextField(blank=True, null=True)
    city = models.TextField(blank=True, null=True)
    lead_source = models.TextField(blank=True, null=True)
    total_visits = models.IntegerField(blank=True, null=True)
    time_on_website_sec = models.IntegerField(blank=True, null=True)
    avg_page_views = models.FloatField(blank=True, null=True)
    last_activity = models.TextField(blank=True, null=True)
    last_notable_activity = models.TextField(blank=True, null=True)
    interaction_history = models.TextField(blank=True, null=True)
    imported_at = models.DateTimeField(blank=True, null=True)
    is_commercial_created = models.BooleanField(default=False)

    class Meta:
        managed = False
        db_table = "lead_opportunity"
        ordering = ("-last_modified_date", "company_name")
        verbose_name = "Lead opportunity"
        verbose_name_plural = "Lead opportunities"

    def __str__(self):
        return f"{self.company_name} ({self.lead_id})"
