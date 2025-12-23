from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Literal, Dict, Any, List
from .types import ConstraintType

class Constraint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str

    type: ConstraintType = Field(
        ..., description="Executable constraint type"
    )

    targets: Literal["node", "edge", "pair", "graph"]
    strength: Literal["hard", "soft"] = "hard"

    description: Optional[str] = Field(
        default=None,
        description="Human-readable explanation (non-executable)"
    )
