from __future__ import annotations

from typing import Generic, TypeVar

T = TypeVar("T")


class Registry(Generic[T]):
    """A generic plugin registry for extensible subsystems.

    Usage:
        error_registry = Registry[ErrorModel]()
        error_registry.register("depolarizing", DepolarizingError)
        cls = error_registry.get("depolarizing")
    """

    def __init__(self) -> None:
        self._registry: dict[str, type[T]] = {}

    def register(self, name: str, cls: type[T]) -> None:
        """Register a class under a name."""
        if name in self._registry:
            raise ValueError(f"Name '{name}' is already registered.")
        self._registry[name] = cls

    def get(self, name: str) -> type[T]:
        """Retrieve a registered class by name."""
        if name not in self._registry:
            available = ", ".join(sorted(self._registry.keys()))
            raise KeyError(
                f"'{name}' is not registered. Available: {available}"
            )
        return self._registry[name]

    def list_registered(self) -> list[str]:
        """List all registered names."""
        return sorted(self._registry.keys())

    def __contains__(self, name: str) -> bool:
        return name in self._registry

    def __repr__(self) -> str:
        return f"Registry({self.list_registered()})"
