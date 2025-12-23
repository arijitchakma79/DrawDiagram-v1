from pydantic import BaseModel
from .types import NodeType

class Node(BaseModel):
    id: str
    type: NodeType
    label: str
