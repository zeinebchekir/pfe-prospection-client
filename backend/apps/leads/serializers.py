from django.utils import timezone
from rest_framework import serializers

from .models import LeadOpportunity, LeadScoringPerformance


class LeadOpportunitySerializer(serializers.ModelSerializer):
    class Meta:
        model = LeadOpportunity
        fields = [
            "lead_id",
            "company_name",
            "contact_name",
            "job_title",
            "email",
            "phone_number",
            "website",
            "last_modified_date",
            "industry",
            "company_size",
            "annual_revenue",
            "country",
            "city",
            "lead_source",
            "total_visits",
            "time_on_website_sec",
            "avg_page_views",
            "last_activity",
            "last_notable_activity",
            "interaction_history",
            "lead_score_probability",
            "lead_score_predicted",
            "lead_temperature",
            "model_version",
            "scored_at",
            "imported_at",
        ]


class LeadOpportunityWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeadOpportunity
        fields = [
            "company_name",
            "contact_name",
            "job_title",
            "email",
            "phone_number",
            "website",
            "last_modified_date",
            "industry",
            "company_size",
            "annual_revenue",
            "country",
            "city",
            "lead_source",
            "total_visits",
            "time_on_website_sec",
            "avg_page_views",
            "last_activity",
            "last_notable_activity",
            "interaction_history",
        ]
        extra_kwargs = {
            "company_name": {"required": True},
            "last_modified_date": {"required": False, "allow_null": True},
            "contact_name": {"required": False, "allow_null": True, "allow_blank": True},
            "job_title": {"required": False, "allow_null": True, "allow_blank": True},
            "email": {"required": False, "allow_null": True, "allow_blank": True},
            "phone_number": {"required": False, "allow_null": True, "allow_blank": True},
            "website": {"required": False, "allow_null": True, "allow_blank": True},
            "industry": {"required": False, "allow_null": True, "allow_blank": True},
            "company_size": {"required": False, "allow_null": True, "allow_blank": True},
            "annual_revenue": {"required": False, "allow_null": True, "allow_blank": True},
            "country": {"required": False, "allow_null": True, "allow_blank": True},
            "city": {"required": False, "allow_null": True, "allow_blank": True},
            "lead_source": {"required": False, "allow_null": True, "allow_blank": True},
            "total_visits": {"required": False, "allow_null": True},
            "time_on_website_sec": {"required": False, "allow_null": True},
            "avg_page_views": {"required": False, "allow_null": True},
            "last_activity": {"required": False, "allow_null": True, "allow_blank": True},
            "last_notable_activity": {"required": False, "allow_null": True, "allow_blank": True},
            "interaction_history": {"required": False, "allow_null": True, "allow_blank": True},
        }

    def create(self, validated_data):
        now = timezone.now()
        validated_data.setdefault("last_modified_date", now)
        validated_data.setdefault("imported_at", now)
        return LeadOpportunity.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.last_modified_date = timezone.now()
        instance.save()
        return instance


class LeadScoringPerformanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeadScoringPerformance
        fields = [
            "model_name",
            "model_version",
            "best_model",
            "stack_name",
            "accuracy",
            "precision",
            "recall",
            "f1_score",
            "roc_auc",
            "threshold",
            "training_dataset_size",
            "feature_count",
            "last_training_date",
        ]
