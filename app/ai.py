"""Optional presentation-only adapter. It receives trusted results, never decides authenticity."""
from typing import Protocol


class LocalAI(Protocol):
    def explain(self, trusted_result: dict) -> str: ...


class TemplateExplainer:
    def explain(self, trusted_result: dict) -> str:
        code = trusted_result.get("result", "SYSTEM_UNAVAILABLE")
        name = trusted_result.get("product", {}).get("name")
        return f"{name}: {code}" if name else code.replace("_", " ").title()


def optional_explanation(trusted_result: dict, adapter: LocalAI | None = None) -> str:
    return (adapter or TemplateExplainer()).explain(trusted_result)
