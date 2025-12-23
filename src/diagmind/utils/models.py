from typing import List, Optional, Dict
from pydantic import BaseModel, Field

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


class ValidatorWarning(BaseModel):
    node_id: Optional[str] = None
    edge_id: Optional[int] = None
    message: str


class ValidatorInstruction(BaseModel):
    action: str  # reverse_edge, remove_edge, change_relation, merge_nodes, rename_node, flag_error
    edge_id: Optional[int] = None
    node_id: Optional[str] = None
    source_node_id: Optional[str] = None
    target_node_id: Optional[str] = None
    new_relation: Optional[str] = None
    new_label: Optional[str] = None
    reason: str


class ValidatorResponse(BaseModel):
    needs_correction: bool = Field(default=False, description="Set to true if instructions were emitted that modify the graph. Set to false if graph is correct or only warnings/flag_error were emitted.")
    instructions: List[ValidatorInstruction] = Field(default_factory=list)
    warnings: List[ValidatorWarning] = Field(default_factory=list)

