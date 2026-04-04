"""
app.py — FastAPI application replacing Django's CleanersConfig.

Endpoints:
  POST /clean/boamp      — cleans a batch of BOAMP records
  POST /clean/datagouv   — cleans a batch of dataGouv records
  GET  /health           — liveness check
"""

from fastapi import FastAPI, HTTPException
from .schemas import RawRecord, CleanResponse, CleanedRecord, CleaningReportOutput, IssueDetail
from .boamp_cleaner import BoampCleaner
from .dataGouv_cleaner import DataGouvCleaner

app = FastAPI(
    title="Cleaners API",
    description="Data cleaning service for BOAMP and dataGouv procurement/company records.",
    version="1.0.0",
)

_boamp_cleaner = BoampCleaner()
_datagouv_cleaner = DataGouvCleaner()


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def _serialize_report(report) -> CleaningReportOutput:
    return CleaningReportOutput(
        source=report.source,
        total_input=report.total_input,
        total_cleaned=report.total_cleaned,
        total_rejected=report.total_rejected,
        issues=[IssueDetail(**i) for i in report.issues],
        summary=report.summary(),
    )


def _run_cleaner(cleaner, records: list[RawRecord]) -> CleanResponse:
    raw = [r.model_dump() for r in records]
    cleaned, report = cleaner.clean(raw)

    results = []
    for row in cleaned:
        results.append(
            CleanedRecord(
                entreprise=row["entreprise"],
                lead=row["lead"],
            )
        )

    return CleanResponse(results=results, report=_serialize_report(report))


# ─────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────

@app.get("/health", tags=["Meta"])
def health():
    """Liveness check."""
    return {"status": "ok"}


@app.post("/clean/boamp", response_model=CleanResponse, tags=["Cleaners"])
def clean_boamp(records: list[RawRecord]):
    """
    Clean a batch of BOAMP records.

    Each record must have an `entreprise` object and optionally a `lead` object.
    Returns cleaned records alongside a detailed cleaning report.
    """
    if not records:
        raise HTTPException(status_code=422, detail="Payload must not be empty.")
    return _run_cleaner(_boamp_cleaner, records)


@app.post("/clean/datagouv", response_model=CleanResponse, tags=["Cleaners"])
def clean_datagouv(records: list[RawRecord]):
    """
    Clean a batch of dataGouv records.

    dataGouv records enrich the Entreprise table only — leads are always null.
    Returns cleaned records alongside a detailed cleaning report.
    """
    if not records:
        raise HTTPException(status_code=422, detail="Payload must not be empty.")
    return _run_cleaner(_datagouv_cleaner, records)