from backend.app.evaluation.dataset import load_dataset
from backend.app.retrieval.postgres import _normalize_duration_terms


def test_rag_025_contains_equivalent_duration_evidence():
    """Dataset sanity check: the claim uses '12 months' and E072 uses '365 days'."""
    cases = load_dataset()
    case = next(item for item in cases if item.case_id == "RAG-025")

    evidence_by_id = {
        item.id: item
        for item in case.evidence
    }

    assert "12 months" in case.claim.lower()
    assert "365 days" in evidence_by_id["E072"].content.lower()


def test_normalize_twelve_months_to_365_days():
    """_normalize_duration_terms maps '12 months' and '12 month' to '365 days'."""
    assert _normalize_duration_terms("12 months") == "365 days"
    assert _normalize_duration_terms("12 month") == "365 days"


def test_normalize_duration_ilike_matches_e072_content():
    """Normalized ILIKE pattern matches E072's equivalent duration."""
    cases = load_dataset()
    case = next(item for item in cases if item.case_id == "RAG-025")
    evidence_by_id = {item.id: item for item in case.evidence}

    normalized_query = _normalize_duration_terms(case.claim)
    e072_content = evidence_by_id["E072"].content.lower()

    assert "365 days" in normalized_query
    assert "365 days" in e072_content
    assert normalized_query.lower().find("365 days") >= 0
