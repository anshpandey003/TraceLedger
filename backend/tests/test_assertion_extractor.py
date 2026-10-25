from backend.app.services.assertion_extractor import AssertionExtractor


def test_extracts_maximum_assertion():
    assertions = AssertionExtractor().extract(
        "The maximum refund amount is ₹25,000."
    )

    assert len(assertions) == 1
    assert assertions[0].assertion_type == "maximum"
    assert assertions[0].fact.value == 25000.0


def test_extracts_minimum_assertion():
    assertions = AssertionExtractor().extract(
        "The minimum refund amount is ₹500."
    )

    assert len(assertions) == 1
    assert assertions[0].assertion_type == "minimum"
    assert assertions[0].fact.value == 500.0


def test_extracts_limit_assertion():
    assertions = AssertionExtractor().extract(
        "The refund limit is ₹25,000."
    )

    assert len(assertions) == 1
    assert assertions[0].assertion_type == "limit"
    assert assertions[0].fact.value == 25000.0


def test_extracts_max_refund_parameter():
    assertions = AssertionExtractor().extract(
        "The max_refund_amount parameter is set to 25000."
    )

    assert len(assertions) == 1
    assert assertions[0].assertion_type == "maximum"
    assert assertions[0].fact.value == 25000.0


def test_ignores_unqualified_number():
    assertions = AssertionExtractor().extract(
        "The documentation contains 12 examples."
    )

    assert assertions == []