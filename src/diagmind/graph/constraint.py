from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Literal, Dict, Any, List
from .types import ConstraintFamily

class Constraint(BaseModel):
    model_config = ConfigDict(extra='forbid')
    
    id: str

    family: ConstraintFamily

    description: str = Field(
        ..., description="Human-readable rule"
    )

    scope: Optional[List[str]] = Field(
        default=None,
        description="Node or edge IDs this constraint applies to"
    )

    hard: bool = Field(
        default=True,
        description="Hard constraint vs soft preference"
    )

    parameters: Optional[Dict[str, str]] = Field(
        default=None,
        description="Constraint-specific parameters"
    )
