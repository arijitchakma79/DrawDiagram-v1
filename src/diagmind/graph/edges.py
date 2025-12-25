from pydantic import BaseModel, Field
from typing import Optional, Literal, Dict, Any, List

class EdgeAttributes(BaseModel):
    strength: Optional[Literal['weak', 'medium', 'strong']] = None
    polarity: Optional[Literal["positive", "negative", "neutral"]] = None

class Edge(BaseModel):
    source: str
    target: str
    operator: str = Field(
        ..., description="Semantic operator (e.g., causes, flows_to)"
    )
    birectional: bool = False
    attributes: Optional[EdgeAttributes] = None
