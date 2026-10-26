from backend.app.services.fact_normalizer import FactNormalizer


def test_normalizes_inr_currency_with_commas():
    text = "The maximum refund amount is \u20b925,000."
    facts = FactNormalizer().extract_numeric_facts(text)

    assert len(facts) == 1
    assert facts[0].value == 25000.0
    assert facts[0].unit == "INR"
    assert facts[0].raw_text == "\u20b925,000"


def test_normalizes_inr_currency_code_before_number():
    facts = FactNormalizer().extract_numeric_facts(
        "The maximum refund amount is INR 25,000."
    )

    assert len(facts) == 1
    assert facts[0].value == 25000.0
    assert facts[0].unit == "INR"


def test_normalizes_inr_currency_code_after_number():
    facts = FactNormalizer().extract_numeric_facts(
        "The maximum refund amount is 25,000 INR."
    )

    assert len(facts) == 1
    assert facts[0].value == 25000.0
    assert facts[0].unit == "INR"


def test_normalizes_usd_currency_with_commas():
    facts = FactNormalizer().extract_numeric_facts(
        "The maximum refund amount is $25,000."
    )

    assert len(facts) == 1
    assert facts[0].value == 25000.0
    assert facts[0].unit == "USD"


def test_normalizes_eur_currency_with_commas():
    text = "The maximum refund amount is \u20ac25,000."
    facts = FactNormalizer().extract_numeric_facts(text)

    assert len(facts) == 1
    assert facts[0].value == 25000.0
    assert facts[0].unit == "EUR"


def test_normalizes_gbp_currency_with_commas():
    text = "The maximum refund amount is \u00a325,000."
    facts = FactNormalizer().extract_numeric_facts(text)

    assert len(facts) == 1
    assert facts[0].value == 25000.0
    assert facts[0].unit == "GBP"


def test_normalizes_plain_number():
    facts = FactNormalizer().extract_numeric_facts(
        "The maximum refund amount is 25000."
    )

    assert len(facts) == 1
    assert facts[0].value == 25000.0
    assert facts[0].unit is None


def test_normalizes_percentage():
    facts = FactNormalizer().extract_numeric_facts(
        "The service fee is 10%."
    )

    assert len(facts) == 1
    assert facts[0].value == 10.0
    assert facts[0].unit == "percent"


def test_normalizes_storage_units():
    facts = FactNormalizer().extract_numeric_facts(
        "The upload limit is 25 GB."
    )

    assert len(facts) == 1
    assert facts[0].value == 25.0
    assert facts[0].unit == "gb"


def test_extracts_multiple_numeric_facts():
    text = "Refunds range from \u20b910,000 to \u20b925,000."
    facts = FactNormalizer().extract_numeric_facts(text)

    assert len(facts) == 2
    assert facts[0].value == 10000.0
    assert facts[0].unit == "INR"
    assert facts[1].value == 25000.0
    assert facts[1].unit == "INR"


def test_preserves_raw_text():
    facts = FactNormalizer().extract_numeric_facts(
        "The threshold is $5,000."
    )

    assert len(facts) == 1
    assert facts[0].raw_text == "$5,000"
    assert facts[0].unit == "USD"
