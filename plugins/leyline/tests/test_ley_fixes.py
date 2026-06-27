"""Tests for LEY-001 and LEY-002 -- exception narrowing fixes."""

from __future__ import annotations

import sqlite3
from unittest.mock import MagicMock, patch

import pytest

from leyline import tokens
from leyline.sqlite_graph_base import SqliteGraphBase


class _SchemaRaisingGraph(SqliteGraphBase):
    """SqliteGraphBase subclass that raises a given error from _init_schema."""

    _exc_to_raise: BaseException

    def __init__(self, db_path: str, exc: BaseException) -> None:
        self._exc_to_raise = exc
        super().__init__(db_path)

    def _init_schema(self) -> None:
        raise self._exc_to_raise


class TestLey001GraphConnectionHandler:
    """LEY-001: narrow bare Exception to (OSError, sqlite3.Error) in graph
    connection handler."""

    def test_oserror_from_init_schema_propagates(
        self, tmp_path: pytest.FixtureRequest
    ) -> None:
        """OSError raised during _init_schema propagates out of the constructor."""
        with pytest.raises(OSError, match="disk full"):
            _SchemaRaisingGraph(str(tmp_path / "g.db"), OSError("disk full"))

    def test_sqlite_operational_error_from_init_schema_propagates(
        self, tmp_path: pytest.FixtureRequest
    ) -> None:
        """sqlite3.OperationalError (sqlite3.Error subclass) propagates."""
        with pytest.raises(sqlite3.OperationalError, match="bad DDL"):
            _SchemaRaisingGraph(
                str(tmp_path / "g.db"),
                sqlite3.OperationalError("bad DDL"),
            )

    def test_connection_closed_before_reraise_on_sqlite_error(
        self, tmp_path: pytest.FixtureRequest
    ) -> None:
        """conn.close() is called before re-raising sqlite3.Error."""
        mock_conn = MagicMock()
        mock_conn.execute.return_value = None
        mock_conn.row_factory = None

        with patch("sqlite3.connect", return_value=mock_conn):
            with pytest.raises(sqlite3.OperationalError):
                _SchemaRaisingGraph(
                    str(tmp_path / "g.db"),
                    sqlite3.OperationalError("schema error"),
                )

        mock_conn.close.assert_called_once()


@pytest.fixture(autouse=True)
def _clear_encoder_cache() -> object:
    """Clear _get_encoder lru_cache before and after each test."""
    tokens._get_encoder.cache_clear()
    yield
    tokens._get_encoder.cache_clear()


class TestLey002TokenEncoderExceptionNarrowing:
    """LEY-002: narrow bare Exception to (ValueError, KeyError, OSError) in
    _get_encoder."""

    def _mock_tiktoken(self, side_effect: BaseException) -> MagicMock:
        mock = MagicMock()
        mock.get_encoding.side_effect = side_effect
        return mock

    def test_value_error_from_get_encoding_returns_none(self) -> None:
        """ValueError from tiktoken.get_encoding returns None (caught)."""
        mock_tk = self._mock_tiktoken(ValueError("unknown encoding"))
        with patch.object(tokens, "tiktoken", mock_tk):
            assert tokens._get_encoder() is None

    def test_key_error_from_get_encoding_returns_none(self) -> None:
        """KeyError from tiktoken.get_encoding returns None (caught)."""
        mock_tk = self._mock_tiktoken(KeyError("missing key"))
        with patch.object(tokens, "tiktoken", mock_tk):
            assert tokens._get_encoder() is None

    def test_oserror_from_get_encoding_returns_none(self) -> None:
        """OSError from tiktoken.get_encoding returns None (caught)."""
        mock_tk = self._mock_tiktoken(OSError("no disk space"))
        with patch.object(tokens, "tiktoken", mock_tk):
            assert tokens._get_encoder() is None

    def test_runtime_error_from_get_encoding_propagates(self) -> None:
        """RuntimeError is NOT caught by the narrowed handler and propagates.

        Before LEY-002 fix, bare ``except Exception`` silently swallowed
        RuntimeError and returned None.  After fix, it propagates.
        """
        mock_tk = self._mock_tiktoken(RuntimeError("internal tiktoken error"))
        with patch.object(tokens, "tiktoken", mock_tk):
            with pytest.raises(RuntimeError, match="internal tiktoken error"):
                tokens._get_encoder()
