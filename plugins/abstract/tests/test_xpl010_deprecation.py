"""Guards that the retired XPL010 rule stays retired and unreferenced."""

import warnings

import abstract
from abstract import estimate_tokens as package_shim
from abstract.tokens import estimate_tokens


def test_estimate_tokens_emits_deprecation_warning():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        estimate_tokens("hello world")
    assert any(issubclass(w.category, DeprecationWarning) for w in caught)


def test_star_import_does_not_offer_the_deprecated_name():
    """``from abstract import *`` and autocomplete steer to the new name."""
    assert "estimate_tokens" not in abstract.__all__
    assert "estimate_text_tokens" in abstract.__all__


def test_the_deprecated_name_still_imports_from_the_package():
    """Dropping it from ``__all__`` does not break an explicit import."""
    assert package_shim is estimate_tokens
