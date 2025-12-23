from typing import List, Optional, Dict
from pydantic import BaseModel

from ..graph import Node, Edge, ConstraintType


class DiagramIntent(BaseModel):
    domain: str
    diagram_family: str
    abstraction_levels: List[str]
    expected_flow: Optional[str] = None


class NodesResponse(BaseModel):
    nodes: List[Node]


class EdgesResponse(BaseModel):
    edges: List[Edge]


class ConstraintForOpenAI(BaseModel):
    id: str
    type: ConstraintType
    targets: str
    strength: str = "hard"
    description: Optional[str] = None


class ConstraintsResponse(BaseModel):
    constraints: List[ConstraintForOpenAI]


class ConstraintSchema(BaseModel):
    diagram_family: str
    semantic_constraints: List[str]
    structural_constraints: List[str]
    spatial_constraints: List[str]
    joint_constraints: List[str]

