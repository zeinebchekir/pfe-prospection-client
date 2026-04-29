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
    lead_score = models.IntegerField(blank=True, null=True)
    total_visits = models.IntegerField(blank=True, null=True)
    time_on_website_sec = models.IntegerField(blank=True, null=True)
    avg_page_views = models.FloatField(blank=True, null=True)
    last_activity = models.TextField(blank=True, null=True)
    last_notable_activity = models.TextField(blank=True, null=True)
    interaction_history = models.TextField(blank=True, null=True)
    engagement_score = models.FloatField(blank=True, null=True)
    time_per_visit = models.FloatField(blank=True, null=True)
    log_visits = models.FloatField(blank=True, null=True)
    log_time = models.FloatField(blank=True, null=True)
    log_pageviews = models.FloatField(blank=True, null=True)
    visits_x_time = models.FloatField(blank=True, null=True)
    high_engagement = models.BooleanField(blank=True, null=True)
    text_length = models.IntegerField(blank=True, null=True)
    word_count = models.IntegerField(blank=True, null=True)
    unique_words = models.IntegerField(blank=True, null=True)
    avg_word_length = models.FloatField(blank=True, null=True)
    positive_word_count = models.IntegerField(blank=True, null=True)
    negative_word_count = models.IntegerField(blank=True, null=True)
    sentiment_ratio = models.FloatField(blank=True, null=True)
    lead_score_probability = models.FloatField(blank=True, null=True)
    lead_score_predicted = models.IntegerField(blank=True, null=True)
    lead_temperature = models.CharField(max_length=12, blank=True, null=True)
    model_version = models.CharField(max_length=100, blank=True, null=True)
    scored_at = models.DateTimeField(blank=True, null=True)
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


class LeadScoringPerformance(models.Model):
    id = models.BigAutoField(primary_key=True)
    model_name = models.CharField(max_length=100)
    model_version = models.CharField(max_length=100)
    best_model = models.CharField(max_length=50)
    stack_name = models.CharField(max_length=255)
    accuracy = models.FloatField()
    precision = models.FloatField()
    recall = models.FloatField()
    f1_score = models.FloatField()
    roc_auc = models.FloatField()
    threshold = models.FloatField()
    training_dataset_size = models.IntegerField()
    feature_count = models.IntegerField()
    last_training_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "performance_model"
        ordering = ("-last_training_date", "-id")
        verbose_name = "Lead scoring performance"
        verbose_name_plural = "Lead scoring performance"
