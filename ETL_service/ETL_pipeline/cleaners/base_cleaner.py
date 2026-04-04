"""
base_cleaner.py — Abstract base class for all cleaners.

Adapted for FastAPI: operates on plain dicts (from Pydantic .model_dump())
instead of Django ORM instances.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class CleaningReport:
    source: str
    total_input: int = 0
    total_cleaned: int = 0
    total_rejected: int = 0
    issues: list[dict] = field(default_factory=list)

    def add_issue(self, index: int, reason: str):
        self.issues.append({"index": index, "reason": reason})
        self.total_rejected += 1

    def summary(self) -> str:
        return (
            f"[{self.source}] "
            f"Input: {self.total_input} | "
            f"Cleaned: {self.total_cleaned} | "
            f"Rejected: {self.total_rejected}"
        )


class BaseCleaner(ABC):
    """
    Abstract base for all data cleaners.

    Subclasses must implement:
      - clean_entreprise(entreprise: dict) → dict | None
      - clean_lead(lead: dict) → dict | None

    Operates on plain dicts (converted from Pydantic models via .model_dump()).
    """

    source_name: str = "UNKNOWN"

    def clean(self, results: list[dict]) -> tuple[list[dict], CleaningReport]:
        """
        Main entry point.

        Args:
            results: list of {"entreprise": dict, "lead": dict | None}

        Returns:
            - cleaned_results: same structure with cleaned dicts
            - report: CleaningReport with stats and issues
        """
        report = CleaningReport(source=self.source_name, total_input=len(results))
        cleaned = []

        for i, row in enumerate(results):
            entreprise = row.get("entreprise")
            lead = row.get("lead")

            clean_ent = None
            if entreprise is not None:
                try:
                    clean_ent = self.clean_entreprise(dict(entreprise))
                except Exception as e:
                    report.add_issue(i, f"Entreprise cleaning crashed: {e}")

            if clean_ent is None:
                report.add_issue(i, "Entreprise rejected (no usable identity)")
                continue

            clean_lead = None
            if lead is not None:
                try:
                    clean_lead = self.clean_lead(dict(lead))
                except Exception as e:
                    report.add_issue(i, f"Lead cleaning crashed: {e}")

            cleaned.append({"entreprise": clean_ent, "lead": clean_lead})
            report.total_cleaned += 1

        return cleaned, report

    @abstractmethod
    def clean_entreprise(self, entreprise: dict) -> dict | None:
        """Clean and return an entreprise dict, or None to reject it."""
        ...

    @abstractmethod
    def clean_lead(self, lead: dict) -> dict | None:
        """Clean and return a lead dict, or None if not applicable."""
        ...