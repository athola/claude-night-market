"""Tests for destructive-command-guard bundled rule.

Verifies the rule file exists, loads correctly, and matches
only destructive commands targeting production-looking paths.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from hookify.core.config_loader import ConfigLoader
from hookify.core.rule_engine import RuleEngine

RULE_FILE = (
    Path(__file__).parent.parent
    / "skills"
    / "rule-catalog"
    / "rules"
    / "security"
    / "destructive-command-guard.md"
)


class TestDestructiveCommandGuardRuleFile:
    """Verify the rule file exists and has correct metadata."""

    def test_rule_file_exists(self) -> None:
        assert RULE_FILE.exists(), f"Rule file not found: {RULE_FILE}"

    def test_rule_loads_without_error(self) -> None:
        loader = ConfigLoader(include_bundled=True)
        rule = loader.load_rule(RULE_FILE, source="bundled")
        assert rule.name == "destructive-command-guard"

    def test_rule_is_enabled_by_default(self) -> None:
        loader = ConfigLoader(include_bundled=True)
        rule = loader.load_rule(RULE_FILE, source="bundled")
        assert rule.enabled is True

    def test_rule_event_is_bash(self) -> None:
        loader = ConfigLoader(include_bundled=True)
        rule = loader.load_rule(RULE_FILE, source="bundled")
        assert rule.event == "bash"

    def test_rule_action_is_warn(self) -> None:
        loader = ConfigLoader(include_bundled=True)
        rule = loader.load_rule(RULE_FILE, source="bundled")
        assert rule.action == "warn"

    def test_rule_has_nonempty_message(self) -> None:
        loader = ConfigLoader(include_bundled=True)
        rule = loader.load_rule(RULE_FILE, source="bundled")
        assert rule.message.strip()


class TestDestructiveCommandGuardMatching:
    """Verify the rule matches production-targeting destructive commands."""

    @pytest.fixture()
    def engine(self) -> RuleEngine:
        loader = ConfigLoader(include_bundled=True)
        rule = loader.load_rule(RULE_FILE, source="bundled")
        return RuleEngine([rule])

    # --- should match ---

    def test_rm_rf_on_prod_path(self, engine: RuleEngine) -> None:
        results = engine.evaluate_event(
            "bash", {"command": "rm -rf /var/app/production/data"}
        )
        assert any(r.matched for r in results)

    def test_rm_rf_on_path_containing_prod(self, engine: RuleEngine) -> None:
        results = engine.evaluate_event("bash", {"command": "rm -rf ./prod/configs"})
        assert any(r.matched for r in results)

    def test_rm_rf_on_live_path(self, engine: RuleEngine) -> None:
        results = engine.evaluate_event("bash", {"command": "rm -rf /srv/live/uploads"})
        assert any(r.matched for r in results)

    def test_git_push_force_to_prod(self, engine: RuleEngine) -> None:
        results = engine.evaluate_event(
            "bash", {"command": "git push --force origin production"}
        )
        assert any(r.matched for r in results)

    def test_kubectl_delete_in_prod_context(self, engine: RuleEngine) -> None:
        results = engine.evaluate_event(
            "bash", {"command": "kubectl delete deployment api --namespace=production"}
        )
        assert any(r.matched for r in results)

    def test_terraform_destroy_with_prod_workspace(self, engine: RuleEngine) -> None:
        results = engine.evaluate_event(
            "bash", {"command": "terraform destroy -var-file=prod.tfvars"}
        )
        assert any(r.matched for r in results)

    def test_drop_table_on_prod_db(self, engine: RuleEngine) -> None:
        results = engine.evaluate_event(
            "bash", {"command": "psql $PROD_DATABASE_URL -c 'DROP TABLE users'"}
        )
        assert any(r.matched for r in results)

    def test_delete_from_with_production_envvar(self, engine: RuleEngine) -> None:
        results = engine.evaluate_event(
            "bash",
            {"command": "mysql --host=$PRODUCTION_DB_HOST -e 'DELETE FROM sessions'"},
        )
        assert any(r.matched for r in results)

    # --- should NOT match (safe commands) ---

    def test_rm_rf_in_tmp_does_not_match(self, engine: RuleEngine) -> None:
        results = engine.evaluate_event(
            "bash", {"command": "rm -rf /tmp/build_artifacts"}
        )
        assert not any(r.matched for r in results)

    def test_rm_rf_in_dev_path_does_not_match(self, engine: RuleEngine) -> None:
        results = engine.evaluate_event("bash", {"command": "rm -rf ./dev/cache"})
        assert not any(r.matched for r in results)

    def test_regular_git_push_does_not_match(self, engine: RuleEngine) -> None:
        results = engine.evaluate_event(
            "bash", {"command": "git push origin feature/my-branch"}
        )
        assert not any(r.matched for r in results)

    def test_kubectl_get_does_not_match(self, engine: RuleEngine) -> None:
        results = engine.evaluate_event(
            "bash", {"command": "kubectl get pods -n production"}
        )
        assert not any(r.matched for r in results)

    def test_terraform_plan_does_not_match(self, engine: RuleEngine) -> None:
        results = engine.evaluate_event(
            "bash", {"command": "terraform plan -var-file=prod.tfvars"}
        )
        assert not any(r.matched for r in results)

    def test_drop_table_on_test_db_does_not_match(self, engine: RuleEngine) -> None:
        results = engine.evaluate_event(
            "bash", {"command": "psql $TEST_DATABASE_URL -c 'DROP TABLE users'"}
        )
        assert not any(r.matched for r in results)
