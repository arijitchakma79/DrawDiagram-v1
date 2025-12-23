from typing import List, Optional, Dict
from pydantic import BaseModel

from ..graph import Node, Edge, ConstraintFamily


# Diagram intent model for structured output
class DiagramIntent(BaseModel):
    domain: str
    diagram_family: str
    abstraction_levels: List[str]
    intent: str


# Wrapper model for list of nodes (required for OpenAI structured output)
class NodesResponse(BaseModel):
    nodes: List[Node]


# Wrapper model for list of edges (required for OpenAI structured output)
class EdgesResponse(BaseModel):
    edges: List[Edge]


# Custom Constraint model for OpenAI structured output (fixes Dict[str, Any] issue)
class ConstraintForOpenAI(BaseModel):
    id: str
    family: ConstraintFamily
    description: str
    scope: Optional[List[str]] = None
    hard: bool = True
    parameters: Optional[Dict[str, str]] = None  # More constrained type for OpenAI


# Wrapper model for list of constraints (required for OpenAI structured output)
class ConstraintsResponse(BaseModel):
    constraints: List[ConstraintForOpenAI]

