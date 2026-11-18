"""Shared structured failure: component + function + detail."""

from __future__ import annotations


class StructuredFailure(ValueError):
    """Base for control-plane errors with a stable ``to_dict()`` shape."""

    def __init__(self, component: str, function: str, detail: str) -> None:
        self.component = component
        self.function = function
        self.detail = detail
        super().__init__(f"FAIL {component} {function}: {detail}")

    def to_dict(self) -> dict[str, str]:
        return {
            "component": self.component,
            "function": self.function,
            "detail": self.detail,
        }
