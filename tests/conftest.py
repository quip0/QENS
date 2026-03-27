"""Shared fixtures for the QENS test suite."""
from __future__ import annotations

import numpy as np
import pytest

from qens.codes.repetition import RepetitionCode
from qens.codes.surface import SurfaceCode
from qens.codes.color import ColorCode
from qens.noise.pauli import DepolarizingError


@pytest.fixture
def rng() -> np.random.Generator:
    return np.random.default_rng(42)


@pytest.fixture
def rep3() -> RepetitionCode:
    return RepetitionCode(3)


@pytest.fixture
def rep5() -> RepetitionCode:
    return RepetitionCode(5)


@pytest.fixture
def surface3() -> SurfaceCode:
    return SurfaceCode(3)


@pytest.fixture
def color3() -> ColorCode:
    return ColorCode(3)


@pytest.fixture
def simple_noise() -> DepolarizingError:
    return DepolarizingError(p=0.01)
