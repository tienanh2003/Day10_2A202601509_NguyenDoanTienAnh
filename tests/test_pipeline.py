import unittest
from datetime import datetime, UTC, timedelta
import pandas as pd

from core.config import load_settings
from ingestion.crossref import parse_crossref_payload
from ingestion.cleaning import build_clean_dataframe
from evaluation.testset import build_test_set
from observability.quality import run_data_quality_checks, build_freshness_report


class TestDataPipeline(unittest.TestCase):
    def setUp(self):
        self.settings = load_settings()
        self.run_date = datetime.now(UTC)

    def test_parse_crossref_payload(self):
        mock_payload = {
            "message": {
                "items": [
                    {
                        "DOI": "10.1000/test.doi",
                        "title": ["<jats:p>Sample Title for Testing</jats:p>"],
                        "abstract": "<jats:p>This is a <b>test</b> summary with HTML tags that should be stripped cleanly during parsing.</jats:p>",
                        "author": [{"given": "Jane", "family": "Doe"}, {"given": "John", "family": "Smith"}],
                        "subject": ["Computer Science", "Artificial Intelligence"],
                        "published": {"date-parts": [[2025, 3, 15]]},
                        "URL": "https://doi.org/10.1000/test.doi",
                        "link": [{"URL": "https://arxiv.org/pdf/2503.12345.pdf", "content-type": "application/pdf"}],
                    }
                ]
            }
        }
        records = parse_crossref_payload(mock_payload)
        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertEqual(record.paper_id, "10.1000/test.doi")
        self.assertIn("Sample Title for Testing", record.title)
        self.assertNotIn("<jats:p>", record.summary)
        self.assertNotIn("<b>", record.summary)
        self.assertEqual(record.published, "2025-03-15")
        self.assertEqual(len(record.authors), 2)

    def test_build_clean_dataframe(self):
        mock_payloads = [
            {
                "DOI": "10.1000/paper.1",
                "title": ["Paper One"],
                "abstract": "This is a sufficiently long summary for paper one that exceeds the minimum required character length threshold of 100 characters for validation.",
                "author": [{"given": "Alice", "family": "Bob"}],
                "subject": ["AI"],
                "published": {"date-parts": [[2025, 1, 10]]},
                "URL": "https://doi.org/10.1000/paper.1",
            },
            {
                "DOI": "10.1000/paper.2",
                "title": ["Too Short Paper"],
                "abstract": "Short abstract",  # < 100 chars, should be filtered out
                "author": [{"given": "Charlie", "family": "David"}],
                "subject": ["CS"],
                "published": {"date-parts": [[2025, 2, 20]]},
                "URL": "https://doi.org/10.1000/paper.2",
            },
        ]
        records = parse_crossref_payload({"message": {"items": mock_payloads}})
        df_clean = build_clean_dataframe(records, self.run_date)
        self.assertEqual(len(df_clean), 1)
        self.assertEqual(df_clean.iloc[0]["paper_id"], "10.1000/paper.1")
        self.assertIn("Title: Paper One", df_clean.iloc[0]["text_for_embedding"])

    def test_testset_generation(self):
        mock_payloads = [
            {
                "DOI": f"10.1000/paper.{i}",
                "title": [f"Paper {i} Title"],
                "abstract": f"This is the comprehensive summary for paper number {i} containing extensive details to ensure it passes character length filters easily.",
                "author": [{"given": f"Author{i}", "family": "Test"}],
                "subject": ["CategoryA"],
                "published": {"date-parts": [[2024, 5, i + 1]]},
                "URL": f"https://doi.org/10.1000/paper.{i}",
            }
            for i in range(5)
        ]
        records = parse_crossref_payload({"message": {"items": mock_payloads}})
        df_clean = build_clean_dataframe(records, self.run_date)
        
        test_path = self.settings.paths.eval_testset.parent / "test_set_unit.json"
        test_set = build_test_set(df_clean, test_path)
        self.assertGreater(len(test_set), 0)
        self.assertIn("question", test_set[0])
        self.assertIn("ground_truth", test_set[0])
        self.assertIn("ground_truth_doc_ids", test_set[0])

    def test_quality_and_freshness(self):
        fresh_date = (self.run_date - timedelta(days=10)).strftime("%Y-%m-%d")
        pub_year, pub_month, pub_day = map(int, fresh_date.split("-"))
        mock_payload = {
            "message": {
                "items": [
                    {
                        "DOI": "10.1000/fresh.1",
                        "title": ["Fresh Paper"],
                        "abstract": "A valid long summary that easily satisfies the minimum 100 character length requirements and demonstrates clean data quality checks in unit tests.",
                        "author": [{"given": "Jane", "family": "Doe"}],
                        "subject": ["Tech"],
                        "published": {"date-parts": [[pub_year, pub_month, pub_day]]},
                        "URL": "https://doi.org/10.1000/fresh.1",
                    }
                ]
            }
        }
        records = parse_crossref_payload(mock_payload)
        df_clean = build_clean_dataframe(records, self.run_date)
        quality = run_data_quality_checks(df_clean, self.settings, "unit_test_quality")
        freshness = build_freshness_report(df_clean, self.settings, self.settings.paths.quality_dir / "unit_test_freshness.json")
        
        self.assertTrue(quality["all_passed"])
        self.assertTrue(freshness["is_fresh"])


if __name__ == "__main__":
    unittest.main()
