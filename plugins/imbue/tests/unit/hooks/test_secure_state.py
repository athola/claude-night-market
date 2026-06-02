# ruff: noqa: D101,D102,D103,D205,D212,E501
"""Tests for the shared secure-state primitives in vow_utils.

Feature: Per-user, symlink-safe state files for hooks

As the imbue verification spine
I want hook state files kept in a private per-user dir and opened with
O_NOFOLLOW
So that an attacker on a shared host cannot plant a symlink at a
predictable /tmp path and redirect a hook's truncating write onto a
victim file (CWE-59).

These primitives are consumed by guard_scope_ramp, vow_bounded_reads,
and vow_bounded_reads_reset so the symlink defense lives in one place.
"""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

import pytest


@pytest.fixture
def vu():
    """Import the vow_utils shared module via importlib."""
    shared = Path(__file__).resolve().parents[3] / "hooks" / "shared"
    module_path = shared / "vow_utils.py"
    spec = importlib.util.spec_from_file_location("vow_utils", module_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["vow_utils"] = mod
    spec.loader.exec_module(mod)
    return mod


class TestSecureStateDir:
    @pytest.mark.unit
    def test_override_is_honored(self, vu, tmp_path, monkeypatch):
        monkeypatch.setenv("IMBUE_STATE_DIR", str(tmp_path / "x"))
        d = vu.secure_state_dir("whatever")
        assert d == tmp_path / "x"
        assert d.is_dir()

    @pytest.mark.unit
    def test_default_dir_is_private(self, vu, tmp_path, monkeypatch):
        monkeypatch.delenv("IMBUE_STATE_DIR", raising=False)
        monkeypatch.setenv("TMPDIR", str(tmp_path))
        d = vu.secure_state_dir("imbue-vow-state")
        assert (d.stat().st_mode & 0o777) == 0o700
        assert "imbue-vow-state" in d.name


@pytest.mark.skipif(
    not hasattr(os, "O_NOFOLLOW"), reason="symlink hardening is POSIX-only"
)
class TestSecureOpen:
    @pytest.mark.unit
    def test_refuses_a_symlinked_path(self, vu, tmp_path):
        victim = tmp_path / "victim"
        victim.write_text("precious")
        link = tmp_path / "link"
        link.symlink_to(victim)
        with pytest.raises(OSError):
            vu.secure_open(link, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        assert victim.read_text() == "precious"

    @pytest.mark.unit
    def test_opens_a_regular_file(self, vu, tmp_path):
        target = tmp_path / "regular.json"
        fd = vu.secure_open(target, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        try:
            os.write(fd, b'{"ok": true}')
        finally:
            os.close(fd)
        assert target.read_text() == '{"ok": true}'


class TestFdOwnedByUs:
    @pytest.mark.unit
    def test_true_for_our_own_file(self, vu, tmp_path):
        target = tmp_path / "mine"
        fd = os.open(str(target), os.O_WRONLY | os.O_CREAT, 0o600)
        try:
            assert vu.fd_owned_by_us(fd) is True
        finally:
            os.close(fd)
