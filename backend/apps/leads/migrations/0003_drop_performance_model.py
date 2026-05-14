from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("leads", "0002_commercial_created_flag"),
    ]

    operations = [
        migrations.RunSQL(
            "DROP TABLE IF EXISTS public.performance_model;",
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
