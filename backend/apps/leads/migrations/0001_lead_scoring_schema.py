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
    total_visits integer,
    time_on_website_sec integer,
    avg_page_views double precision,
    last_activity text,
    last_notable_activity text,
    interaction_history text,
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
    ADD COLUMN IF NOT EXISTS total_visits integer,
    ADD COLUMN IF NOT EXISTS time_on_website_sec integer,
    ADD COLUMN IF NOT EXISTS avg_page_views double precision,
    ADD COLUMN IF NOT EXISTS last_activity text,
    ADD COLUMN IF NOT EXISTS last_notable_activity text,
    ADD COLUMN IF NOT EXISTS interaction_history text,
    ADD COLUMN IF NOT EXISTS imported_at timestamptz,
    ADD COLUMN IF NOT EXISTS is_commercial_created boolean NOT NULL DEFAULT false;

"""


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
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
                        ("total_visits", models.IntegerField(blank=True, null=True)),
                        ("time_on_website_sec", models.IntegerField(blank=True, null=True)),
                        ("avg_page_views", models.FloatField(blank=True, null=True)),
                        ("last_activity", models.TextField(blank=True, null=True)),
                        ("last_notable_activity", models.TextField(blank=True, null=True)),
                        ("interaction_history", models.TextField(blank=True, null=True)),
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
            ],
        ),
    ]
