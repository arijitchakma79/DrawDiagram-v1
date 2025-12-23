from pydantic import BaseModel, Field
from typing import Optional, Literal, Dict, Any, List
from .types import EdgeFamily

class EdgeAttributes(BaseModel):
    directional: bool = True

    temporal: Optional[Literal["before", "during", "after", "continuous"]] = None

    strength: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Relative influence or magnitude"
    )

    certainty: bool = True

    polarity: Optional[Literal["positive", "negative", "neutral"]] = None


class Edge(BaseModel):
    source: str
    target: str

    family: EdgeFamily

    operator: str = Field(
        ..., description="Semantic operator (e.g., causes, flows_to)"
    )

    attributes: EdgeAttributes
