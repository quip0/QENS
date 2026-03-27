"""Tests for qens.core.types."""
from __future__ import annotations

from qens.core.types import PauliOp, Outcome


class TestPauliOp:
    def test_values(self):
        assert PauliOp.I == 0
        assert PauliOp.X == 1
        assert PauliOp.Y == 2
        assert PauliOp.Z == 3

    def test_is_int(self):
        assert isinstance(PauliOp.X, int)
        assert PauliOp.X + PauliOp.Z == 4

    def test_members_count(self):
        assert len(PauliOp) == 4

    def test_name_lookup(self):
        assert PauliOp["X"] is PauliOp.X
        assert PauliOp(1) is PauliOp.X


class TestOutcome:
    def test_values(self):
        assert Outcome.ZERO == 0
        assert Outcome.ONE == 1

    def test_is_int(self):
        assert isinstance(Outcome.ZERO, int)

    def test_members_count(self):
        assert len(Outcome) == 2
