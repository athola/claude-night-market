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
import tempfile
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
        # tempfile caches gettempdir() on first use, so setting TMPDIR here
        # was ignored and the test checked the shared real temp dir, where a
        # leftover directory from any earlier run decided the outcome.
        monkeypatch.delenv("IMBUE_STATE_DIR", raising=False)
        monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))
        d = vu.secure_state_dir("imbue-vow-state")
        assert d.parent == tmp_path
        assert (d.stat().st_mode & 0o777) == 0o700
        assert "imbue-vow-state" in d.name

    @pytest.mark.unit
    def test_uncreatable_dir_falls_back_to_the_temp_root(
        self, vu, tmp_path, monkeypatch
    ):
        blocker = tmp_path / "a-file"
        blocker.write_text("")
        monkeypatch.setenv("IMBUE_STATE_DIR", str(blocker / "sub"))
        monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))
        assert vu.secure_state_dir("whatever") == tmp_path


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

    @pytest.mark.unit
    def test_false_for_a_file_owned_by_another_user(self, vu, tmp_path, monkeypatch):
        target = tmp_path / "planted"
        fd = os.open(str(target), os.O_WRONLY | os.O_CREAT, 0o600)
        try:
            other_uid = os.fstat(fd).st_uid + 1
            monkeypatch.setattr(vu.os, "geteuid", lambda: other_uid, raising=False)
            assert vu.fd_owned_by_us(fd) is False
        finally:
            os.close(fd)

    @pytest.mark.unit
    def test_false_when_the_fd_cannot_be_inspected(self, vu, tmp_path):
        fd = os.open(str(tmp_path / "gone"), os.O_WRONLY | os.O_CREAT, 0o600)
        os.close(fd)
        assert vu.fd_owned_by_us(fd) is False

    @pytest.mark.unit
    def test_true_on_a_platform_with_no_uid_model(self, vu, monkeypatch):
        monkeypatch.delattr(vu.os, "geteuid", raising=False)
        assert vu.fd_owned_by_us(-1) is True
