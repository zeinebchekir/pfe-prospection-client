from django.db import migrations, models


SQL = """
ALTER TABLE public.lead_opportunity
    ADD COLUMN IF NOT EXISTS is_commercial_created boolean NOT NULL DEFAULT false;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("leads", "0001_lead_scoring_schema"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(SQL, reverse_sql=migrations.RunSQL.noop),
            ],
            state_operations=[
                migrations.AddField(
                    model_name="leadopportunity",
                    name="is_commercial_created",
                    field=models.BooleanField(default=False),
                ),
            ],
        ),
    ]
