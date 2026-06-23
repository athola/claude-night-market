import warnings

from abstract.tokens import estimate_tokens


def test_estimate_tokens_emits_deprecation_warning():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        estimate_tokens("hello world")
    assert any(issubclass(w.category, DeprecationWarning) for w in caught)
