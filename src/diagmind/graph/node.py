from pydantic import BaseModel, Field
from typing import Optional, Literal, Dict, Any, List
from .types import NodeType, AbstractionLevel, NodeRole, Importance

class NodeAttributes(BaseModel):
    abstraction_level: AbstractionLevel = Field(
        default="structural"
    )

    role: NodeRole
    
    importance: Importance = Field(
        default="primary"
    )

    observable: bool = Field(
        ..., description="Directly observable vs inferred"
    )

    physicality: Optional[Literal["physical", "abstract", "hybrid"]] = None


class Node(BaseModel):
    id: str
    type: NodeType
    label: str
    attributes: NodeAttributes
