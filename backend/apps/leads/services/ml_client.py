import json
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from django.conf import settings


class LeadScoringServiceError(Exception):
    """Raised when the IA/ML scoring service cannot fulfill a request."""


def rescore_opportunity(lead_id):
    return _post_json(f"/lead-scoring/rescore/{lead_id}", timeout=180)


def train_opportunity_model():
    return _post_json("/lead-scoring/train", timeout=900)


def get_opportunity_model_performance():
    return _get_json("/lead-scoring/performance/latest", timeout=60)


def _post_json(path, payload=None, timeout=60):
    return _request_json("POST", path, payload=payload or {}, timeout=timeout)


def _get_json(path, timeout=60):
    return _request_json("GET", path, timeout=timeout)


def _request_json(method, path, payload=None, timeout=60):
    base_url = settings.LEAD_SCORING_SERVICE_URL.rstrip("/") + "/"
    request = Request(
        urljoin(base_url, path.lstrip("/")),
        data=None if payload is None else json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method=method,
    )

    try:
        with urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
    except HTTPError as exc:
        detail = _extract_error_detail(exc)
        raise LeadScoringServiceError(detail) from exc
    except URLError as exc:
        raise LeadScoringServiceError(
            "Le service de scoring IA/ML est indisponible. Verifie le conteneur `ia-ml`."
        ) from exc

    return json.loads(body) if body else {}


def _extract_error_detail(error):
    try:
        payload = json.loads(error.read().decode("utf-8"))
    except Exception:
        return "Le service de scoring IA/ML a repondu avec une erreur."

    if isinstance(payload, dict):
        return payload.get("detail") or payload.get("message") or str(payload)

    return str(payload)
