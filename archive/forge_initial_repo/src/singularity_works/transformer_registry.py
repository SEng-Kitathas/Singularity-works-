from __future__ import annotations

from collections.abc import Callable


Transformer = Callable[[str], str]


class TransformerRegistry:
    def __init__(self) -> None:
        self._registry: dict[str, Transformer] = {}

    def register(self, name: str, transformer: Transformer) -> None:
        self._registry[name] = transformer

    def get(self, name: str) -> Transformer:
        try:
            return self._registry[name]
        except KeyError as exc:
            raise KeyError(f"Unknown transformer: {name}") from exc

    def names(self) -> list[str]:
        return sorted(self._registry)
