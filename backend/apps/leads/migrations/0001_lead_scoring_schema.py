from django.db import migrations


SQL = """
ALTER TABLE public.lead_opportunity
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
    ADD COLUMN IF NOT EXISTS scored_at timestamptz;

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
        migrations.RunSQL(SQL, reverse_sql=migrations.RunSQL.noop),
    ]
