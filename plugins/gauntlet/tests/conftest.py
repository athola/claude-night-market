from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest


@pytest.fixture()
def tmp_gauntlet_dir(tmp_path: Path) -> Path:
    """Create a .gauntlet/ directory with standard subdirectories."""
    gauntlet_dir = tmp_path / ".gauntlet"
    for subdir in ("annotations", "progress", "state"):
        (gauntlet_dir / subdir).mkdir(parents=True)
    return gauntlet_dir


@pytest.fixture()
def sample_knowledge_base(tmp_gauntlet_dir: Path) -> Path:
    """Create a knowledge.json with 3 entries."""
    entries = [
        {
            "id": "ke-001",
            "category": "business_logic",
            "module": "billing",
            "concept": "Pro-rata calculation",
            "detail": (
                "When a subscription upgrades mid-cycle, the charge is "
                "pro-rated based on remaining days in the billing period."
            ),
            "related_files": ["src/billing/proration.py"],
            "difficulty": 2,
            "tags": ["billing", "subscription"],
            "extracted_at": "2026-01-01T00:00:00",
            "source": "code",
            "consumers": ["billing_service"],
        },
        {
            "id": "ke-002",
            "category": "architecture",
            "module": "core",
            "concept": "Event sourcing",
            "detail": (
                "All state changes are persisted as an ordered sequence of "
                "events. The current state is derived by replaying events."
            ),
            "related_files": ["src/core/event_store.py"],
            "difficulty": 3,
            "tags": ["architecture", "events"],
            "extracted_at": "2026-01-01T00:00:00",
            "source": "code",
            "consumers": [],
        },
        {
            "id": "ke-003",
            "category": "data_flow",
            "module": "auth",
            "concept": "Token refresh flow",
            "detail": (
                "Access tokens expire after 15 minutes. Refresh tokens are "
                "used to obtain new access tokens without re-authentication."
            ),
            "related_files": ["src/auth/tokens.py"],
            "difficulty": 2,
            "tags": ["auth", "tokens"],
            "extracted_at": "2026-01-01T00:00:00",
            "source": "code",
            "consumers": ["auth_middleware"],
        },
    ]
    kb_path = tmp_gauntlet_dir / "knowledge.json"
    kb_path.write_text(json.dumps(entries, indent=2))
    return kb_path


@pytest.fixture()
def sample_annotation(tmp_gauntlet_dir: Path) -> Path:
    """Create a YAML annotation file for auth-token-expiry."""
    content = textwrap.dedent(
        """\
        id: ann-auth-token-expiry
        category: business_logic
        module: auth
        concept: Token expiry rationale
        detail: >
          The 15-minute access token expiry was chosen after a security audit
          in Q3 2024. The previous value of 60 minutes was flagged as too long
          for high-value accounts. Refresh tokens have a 30-day expiry and are
          rotated on each use.
        related_files:
          - src/auth/tokens.py
          - src/auth/middleware.py
        tags:
          - auth
          - security
          - tokens
        source: annotation
        """
    )
    ann_path = tmp_gauntlet_dir / "annotations" / "auth-token-expiry.yaml"
    ann_path.write_text(content)
    return ann_path


@pytest.fixture()
def sample_python_file(tmp_path: Path) -> Path:
    """Create a Python file with a calculate_discount function."""
    content = textwrap.dedent(
        """\
        from __future__ import annotations


        def calculate_discount(price: float, customer_tier: str) -> float:
            \"\"\"Calculate the discount for a given price and customer tier.

            Business rules:
            - Gold customers receive a 20% discount on all orders.
            - Silver customers receive a 10% discount on orders over $100.
            - Standard customers receive no discount.
            - Discounts cannot be stacked with promotional codes.

            Args:
                price: The original price before discount.
                customer_tier: One of 'gold', 'silver', or 'standard'.

            Returns:
                The discounted price.
            \"\"\"
            if customer_tier == "gold":
                return price * 0.80
            if customer_tier == "silver" and price > 100:
                return price * 0.90
            return price
        """
    )
    py_path = tmp_path / "discounts.py"
    py_path.write_text(content)
    return py_path
