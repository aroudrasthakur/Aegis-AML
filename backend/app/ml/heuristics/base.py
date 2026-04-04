"""Base class and result types for the 185-typology heuristic engine."""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class Applicability(str, Enum):
    APPLICABLE = "applicable"
    INAPPLICABLE_MISSING_DATA = "inapplicable_missing_data"
    INAPPLICABLE_OUT_OF_SCOPE = "inapplicable_out_of_scope"


class Environment(str, Enum):
    TRADITIONAL = "traditional"
    BLOCKCHAIN = "blockchain"
    HYBRID = "hybrid"
    AI_ENABLED = "ai_enabled"


@dataclass
class HeuristicResult:
    triggered: bool = False
    confidence: float = 0.0
    explanation: str = ""
    applicability: Applicability = Applicability.APPLICABLE
    evidence: dict[str, Any] = field(default_factory=dict)


class BaseHeuristic(ABC):
    """Every heuristic must subclass this and implement evaluate()."""
    
    id: int
    name: str
    environment: Environment
    lens_tags: list[str]
    description: str
    data_requirements: list[str]
    
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
    
    @abstractmethod
    def evaluate(
        self,
        tx: Optional[dict] = None,
        wallet: Optional[dict] = None,
        graph: Any = None,
        features: Optional[dict] = None,
        context: Optional[dict] = None,
    ) -> HeuristicResult:
        """Run detection logic. Return HeuristicResult."""
        ...
    
    def check_data_requirements(self, context: Optional[dict] = None) -> Applicability:
        """Check if required data is available. Override for custom logic.

        ``timestamp`` (singular) is satisfied if ``timestamps`` is a non-empty list
        (pipeline uses plural in wallet profiles) or ``timestamp`` is set.
        """
        if not context:
            if self.data_requirements:
                return Applicability.INAPPLICABLE_MISSING_DATA
            return Applicability.APPLICABLE
        for req in self.data_requirements:
            if self._requirement_satisfied(req, context):
                continue
            return Applicability.INAPPLICABLE_MISSING_DATA
        return Applicability.APPLICABLE

    @staticmethod
    def _requirement_satisfied(req: str, context: dict) -> bool:
        if req == "timestamp":
            v = context.get("timestamp")
            if v not in (None, ""):
                return True
            ts = context.get("timestamps")
            return isinstance(ts, list) and len(ts) > 0
        if req not in context or context[req] is None:
            return False
        return True
