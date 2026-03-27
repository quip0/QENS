"""Tests for qens.core.registry."""
from __future__ import annotations

import pytest

from qens.core.registry import Registry


class Dummy:
    pass


class DummyA(Dummy):
    pass


class DummyB(Dummy):
    pass


class TestRegistry:
    def test_register_and_get(self):
        reg: Registry[Dummy] = Registry()
        reg.register("a", DummyA)
        assert reg.get("a") is DummyA

    def test_list_registered(self):
        reg: Registry[Dummy] = Registry()
        reg.register("b", DummyB)
        reg.register("a", DummyA)
        assert reg.list_registered() == ["a", "b"]

    def test_contains(self):
        reg: Registry[Dummy] = Registry()
        reg.register("a", DummyA)
        assert "a" in reg
        assert "z" not in reg

    def test_duplicate_raises(self):
        reg: Registry[Dummy] = Registry()
        reg.register("a", DummyA)
        with pytest.raises(ValueError, match="already registered"):
            reg.register("a", DummyB)

    def test_missing_raises(self):
        reg: Registry[Dummy] = Registry()
        with pytest.raises(KeyError, match="not registered"):
            reg.get("nonexistent")

    def test_repr(self):
        reg: Registry[Dummy] = Registry()
        reg.register("a", DummyA)
        assert "a" in repr(reg)

    def test_empty_list(self):
        reg: Registry[Dummy] = Registry()
        assert reg.list_registered() == []
