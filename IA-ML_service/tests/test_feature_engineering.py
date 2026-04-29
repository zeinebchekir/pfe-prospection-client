import sys
import unittest
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.lead_scoring.feature_engineering import (  # noqa: E402
    MISSING_CATEGORY_VALUE,
    MISSING_TEXT_VALUE,
    TARGET_COLUMN,
    TEXT_COLUMN,
    build_preprocessing_state,
    clean_text,
    normalize_dataframe,
    transform_dataframe,
)


class FeatureEngineeringTests(unittest.TestCase):
    def test_clean_text_normalizes_noise_and_leak_words(self):
        cleaned = clean_text("  Intéressé par le devis, réunion demain !!!  ")
        self.assertEqual(cleaned, "interesse par le reunion demain")

    def test_normalize_dataframe_adds_expected_columns(self):
        frame = normalize_dataframe([{"Lead ID": "1", "Lead Source": "Web"}])
        self.assertIn("lead_id", frame.columns)
        self.assertIn(TEXT_COLUMN, frame.columns)
        self.assertIn(TARGET_COLUMN, frame.columns)
        self.assertIn("total_visits", frame.columns)

    def test_transform_dataframe_normalizes_categories_and_counts_tokens(self):
        source = pd.DataFrame(
            [
                {
                    "lead_id": "1",
                    TARGET_COLUMN: 1,
                    "total_visits": 4,
                    "time_on_website_sec": 80,
                    "avg_page_views": 3,
                    "industry": " SaaS ",
                    "company_size": "50-100",
                    "annual_revenue": "High",
                    "country": "France",
                    "city": "Paris",
                    "lead_source": "Web",
                    "last_activity": "Email Opened",
                    "last_notable_activity": "Email Replied",
                    "job_title": "CTO",
                    TEXT_COLUMN: "Interesse par demo reunion projet",
                },
                {
                    "lead_id": "2",
                    TARGET_COLUMN: 0,
                    "total_visits": 2,
                    "time_on_website_sec": 20,
                    "avg_page_views": 1,
                    "industry": "Manufacturing",
                    "company_size": "1-10",
                    "annual_revenue": "Low",
                    "country": "Tunisia",
                    "city": "Tunis",
                    "lead_source": "Referral",
                    "last_activity": "No Activity",
                    "last_notable_activity": "No Activity",
                    "job_title": "CEO",
                    TEXT_COLUMN: "Pas disponible, reporte",
                },
            ]
        )

        state = build_preprocessing_state(source)
        transformed = transform_dataframe(
            [
                {
                    "lead_id": "3",
                    "total_visits": -5,
                    "time_on_website_sec": -10,
                    "avg_page_views": None,
                    "industry": " SaaS ",
                    "company_size": None,
                    "annual_revenue": "  ",
                    "country": " FRANCE ",
                    "city": "Paris",
                    "lead_source": "Web",
                    "last_activity": "Email Opened",
                    "last_notable_activity": "Email Replied",
                    "job_title": "CTO",
                    TEXT_COLUMN: "Intéressé réunion projet, pas indisponible",
                }
            ],
            state,
        )

        row = transformed.transformed_source.iloc[0]
        self.assertGreaterEqual(row["total_visits"], 0)
        self.assertGreaterEqual(row["time_on_website_sec"], 0)
        self.assertEqual(row["industry"], "saas")
        self.assertEqual(row["company_size"], MISSING_CATEGORY_VALUE)
        self.assertEqual(row["annual_revenue"], MISSING_CATEGORY_VALUE)
        self.assertEqual(row["country"], "france")
        self.assertEqual(row["positive_word_count"], 3)
        self.assertEqual(row["negative_word_count"], 2)

    def test_transform_dataframe_uses_missing_text_fallback(self):
        source = pd.DataFrame(
            [
                {
                    "lead_id": "1",
                    TARGET_COLUMN: 1,
                    "total_visits": 1,
                    "time_on_website_sec": 10,
                    "avg_page_views": 2,
                    "industry": "SaaS",
                    "company_size": "1-10",
                    "annual_revenue": "High",
                    "country": "France",
                    "city": "Paris",
                    "lead_source": "Web",
                    "last_activity": "Email Opened",
                    "last_notable_activity": "Email Replied",
                    "job_title": "CTO",
                    TEXT_COLUMN: "Projet interessant",
                }
            ]
        )

        state = build_preprocessing_state(source)
        transformed = transform_dataframe([{"lead_id": "2", TEXT_COLUMN: None}], state)
        self.assertEqual(transformed.transformed_source.iloc[0][TEXT_COLUMN], MISSING_TEXT_VALUE)


if __name__ == "__main__":
    unittest.main()
