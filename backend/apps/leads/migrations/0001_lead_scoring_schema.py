import uuid

from django.db import migrations, models


SQL = """
CREATE TABLE IF NOT EXISTS public.lead_opportunity (
    lead_id uuid PRIMARY KEY,
    company_name text NOT NULL,
    contact_name text,
    job_title text,
    email text,
    phone_number text,
    website text,
    last_modified_date timestamptz NOT NULL,
    industry text,
    company_size text,
    annual_revenue text,
    country text,
    city text,
    lead_source text,
    lead_score integer,
    total_visits integer,
    time_on_website_sec integer,
    avg_page_views double precision,
    last_activity text,
    last_notable_activity text,
    interaction_history text,
    engagement_score double precision,
    time_per_visit double precision,
    log_visits double precision,
    log_time double precision,
    log_pageviews double precision,
    visits_x_time double precision,
    high_engagement boolean,
    text_length integer,
    word_count integer,
    unique_words integer,
    avg_word_length double precision,
    positive_word_count integer,
    negative_word_count integer,
    sentiment_ratio double precision,
    lead_score_probability double precision,
    lead_score_predicted integer,
    lead_temperature varchar(12),
    model_version varchar(100),
    scored_at timestamptz,
    imported_at timestamptz,
    is_commercial_created boolean NOT NULL DEFAULT false
);

ALTER TABLE public.lead_opportunity
    ADD COLUMN IF NOT EXISTS lead_id uuid,
    ADD COLUMN IF NOT EXISTS company_name text,
    ADD COLUMN IF NOT EXISTS contact_name text,
    ADD COLUMN IF NOT EXISTS job_title text,
    ADD COLUMN IF NOT EXISTS email text,
    ADD COLUMN IF NOT EXISTS phone_number text,
    ADD COLUMN IF NOT EXISTS website text,
    ADD COLUMN IF NOT EXISTS last_modified_date timestamptz,
    ADD COLUMN IF NOT EXISTS industry text,
    ADD COLUMN IF NOT EXISTS company_size text,
    ADD COLUMN IF NOT EXISTS annual_revenue text,
    ADD COLUMN IF NOT EXISTS country text,
    ADD COLUMN IF NOT EXISTS city text,
    ADD COLUMN IF NOT EXISTS lead_source text,
    ADD COLUMN IF NOT EXISTS lead_score integer,
    ADD COLUMN IF NOT EXISTS total_visits integer,
    ADD COLUMN IF NOT EXISTS time_on_website_sec integer,
    ADD COLUMN IF NOT EXISTS avg_page_views double precision,
    ADD COLUMN IF NOT EXISTS last_activity text,
    ADD COLUMN IF NOT EXISTS last_notable_activity text,
    ADD COLUMN IF NOT EXISTS interaction_history text,
    ADD COLUMN IF NOT EXISTS engagement_score double precision,
    ADD COLUMN IF NOT EXISTS time_per_visit double precision,
    ADD COLUMN IF NOT EXISTS log_visits double precision,
    ADD COLUMN IF NOT EXISTS log_time double precision,
    ADD COLUMN IF NOT EXISTS log_pageviews double precision,
    ADD COLUMN IF NOT EXISTS visits_x_time double precision,
    ADD COLUMN IF NOT EXISTS high_engagement boolean,
    ADD COLUMN IF NOT EXISTS text_length integer,
    ADD COLUMN IF NOT EXISTS word_count integer,
    ADD COLUMN IF NOT EXISTS unique_words integer,
    ADD COLUMN IF NOT EXISTS avg_word_length double precision,
    ADD COLUMN IF NOT EXISTS positive_word_count integer,
    ADD COLUMN IF NOT EXISTS negative_word_count integer,
    ADD COLUMN IF NOT EXISTS sentiment_ratio double precision,
    ADD COLUMN IF NOT EXISTS lead_score_probability double precision,
    ADD COLUMN IF NOT EXISTS lead_score_predicted integer,
    ADD COLUMN IF NOT EXISTS lead_temperature varchar(12),
    ADD COLUMN IF NOT EXISTS model_version varchar(100),
    ADD COLUMN IF NOT EXISTS scored_at timestamptz,
    ADD COLUMN IF NOT EXISTS imported_at timestamptz,
    ADD COLUMN IF NOT EXISTS is_commercial_created boolean NOT NULL DEFAULT false;

CREATE INDEX IF NOT EXISTS ix_lead_opportunity_lead_temperature
    ON public.lead_opportunity (lead_temperature);
CREATE INDEX IF NOT EXISTS ix_lead_opportunity_lead_score_predicted
    ON public.lead_opportunity (lead_score_predicted);
CREATE INDEX IF NOT EXISTS ix_lead_opportunity_scored_at
    ON public.lead_opportunity (scored_at);

CREATE TABLE IF NOT EXISTS public.performance_model (
    id bigserial PRIMARY KEY,
    model_name varchar(100) NOT NULL,
    model_version varchar(100) NOT NULL,
    best_model varchar(50) NOT NULL,
    stack_name varchar(255) NOT NULL,
    accuracy double precision NOT NULL,
    precision double precision NOT NULL,
    recall double precision NOT NULL,
    f1_score double precision NOT NULL,
    roc_auc double precision NOT NULL,
    threshold double precision NOT NULL,
    training_dataset_size integer NOT NULL,
    feature_count integer NOT NULL,
    last_training_date timestamptz NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_performance_model_last_training_date
    ON public.performance_model (last_training_date DESC);
"""


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(SQL, reverse_sql=migrations.RunSQL.noop),
            ],
            state_operations=[
                migrations.CreateModel(
                    name="LeadOpportunity",
                    fields=[
                        ("lead_id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                        ("company_name", models.TextField()),
                        ("contact_name", models.TextField(blank=True, null=True)),
                        ("job_title", models.TextField(blank=True, null=True)),
                        ("email", models.TextField(blank=True, null=True)),
                        ("phone_number", models.TextField(blank=True, null=True)),
                        ("website", models.TextField(blank=True, null=True)),
                        ("last_modified_date", models.DateTimeField()),
                        ("industry", models.TextField(blank=True, null=True)),
                        ("company_size", models.TextField(blank=True, null=True)),
                        ("annual_revenue", models.TextField(blank=True, null=True)),
                        ("country", models.TextField(blank=True, null=True)),
                        ("city", models.TextField(blank=True, null=True)),
                        ("lead_source", models.TextField(blank=True, null=True)),
                        ("lead_score", models.IntegerField(blank=True, null=True)),
                        ("total_visits", models.IntegerField(blank=True, null=True)),
                        ("time_on_website_sec", models.IntegerField(blank=True, null=True)),
                        ("avg_page_views", models.FloatField(blank=True, null=True)),
                        ("last_activity", models.TextField(blank=True, null=True)),
                        ("last_notable_activity", models.TextField(blank=True, null=True)),
                        ("interaction_history", models.TextField(blank=True, null=True)),
                        ("engagement_score", models.FloatField(blank=True, null=True)),
                        ("time_per_visit", models.FloatField(blank=True, null=True)),
                        ("log_visits", models.FloatField(blank=True, null=True)),
                        ("log_time", models.FloatField(blank=True, null=True)),
                        ("log_pageviews", models.FloatField(blank=True, null=True)),
                        ("visits_x_time", models.FloatField(blank=True, null=True)),
                        ("high_engagement", models.BooleanField(blank=True, null=True)),
                        ("text_length", models.IntegerField(blank=True, null=True)),
                        ("word_count", models.IntegerField(blank=True, null=True)),
                        ("unique_words", models.IntegerField(blank=True, null=True)),
                        ("avg_word_length", models.FloatField(blank=True, null=True)),
                        ("positive_word_count", models.IntegerField(blank=True, null=True)),
                        ("negative_word_count", models.IntegerField(blank=True, null=True)),
                        ("sentiment_ratio", models.FloatField(blank=True, null=True)),
                        ("lead_score_probability", models.FloatField(blank=True, null=True)),
                        ("lead_score_predicted", models.IntegerField(blank=True, null=True)),
                        ("lead_temperature", models.CharField(blank=True, max_length=12, null=True)),
                        ("model_version", models.CharField(blank=True, max_length=100, null=True)),
                        ("scored_at", models.DateTimeField(blank=True, null=True)),
                        ("imported_at", models.DateTimeField(blank=True, null=True)),
                    ],
                    options={
                        "verbose_name": "Lead opportunity",
                        "verbose_name_plural": "Lead opportunities",
                        "db_table": "lead_opportunity",
                        "ordering": ("-last_modified_date", "company_name"),
                        "managed": False,
                    },
                ),
                migrations.CreateModel(
                    name="LeadScoringPerformance",
                    fields=[
                        ("id", models.BigAutoField(primary_key=True, serialize=False)),
                        ("model_name", models.CharField(max_length=100)),
                        ("model_version", models.CharField(max_length=100)),
                        ("best_model", models.CharField(max_length=50)),
                        ("stack_name", models.CharField(max_length=255)),
                        ("accuracy", models.FloatField()),
                        ("precision", models.FloatField()),
                        ("recall", models.FloatField()),
                        ("f1_score", models.FloatField()),
                        ("roc_auc", models.FloatField()),
                        ("threshold", models.FloatField()),
                        ("training_dataset_size", models.IntegerField()),
                        ("feature_count", models.IntegerField()),
                        ("last_training_date", models.DateTimeField()),
                    ],
                    options={
                        "verbose_name": "Lead scoring performance",
                        "verbose_name_plural": "Lead scoring performance",
                        "db_table": "performance_model",
                        "ordering": ("-last_training_date", "-id"),
                        "managed": False,
                    },
                ),
            ],
        ),
    ]
