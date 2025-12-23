from __future__ import annotations
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field
from .constraint import Constraint
from .graph import Graph


class DiagramMetadata(BaseModel):
    topic: str = Field(..., description="Scientific topic of the diagram")
    audience: str = Field(..., description="Intended audience (e.g., Middle School)")
    purpose: str = Field(..., description="Purpose or learning goal of the diagram")
    detail_level: str = Field(..., description="Desired detail level (e.g., low/medium/high)")
    intent: Optional[dict] = Field(
        default=None,
        description="Structured diagram intent as returned by the LLM",
    )


class Diagram(BaseModel):
    metadata: DiagramMetadata
    graph: Graph = Field(default_factory=Graph)
    constraints: List[Constraint] = Field(default_factory=list)

    def add_constraints(self, constraints: List[Constraint]) -> None:
        self.constraints.extend(constraints)

    def summary(self) -> dict:
        return {
            "metadata": self.metadata.model_dump(),
            "num_nodes": len(self.graph.nodes),
            "num_edges": len(self.graph.edges),
            "num_constraints": len(self.constraints),
        }

    def to_dict(self) -> dict:
        return {
            "metadata": self.metadata.model_dump(),
            "nodes": [node.model_dump() for node in self.graph.nodes.values()],
            "edges": [edge.model_dump() for edge in self.graph.edges],
            "constraints": [constraint.model_dump() for constraint in self.constraints],
        }

    def pretty_connections(self) -> str:
        return self.graph.pretty_connections()

    def pretty_constraints(self) -> str:
        if not self.constraints:
            return "Constraints: (none)"

        lines = ["Constraints:"]
        for c in self.constraints:
            targets = f" targets={c.targets}" if c.targets else ""
            hardness = c.strength.upper()
            lines.append(f"- [{c.type}][{hardness}] {c.id}: {c.description or ''}{targets}")
        return "\n".join(lines)

    def visualize_graph(self, output_path: Path | str = "graph.png") -> Path:
        return self.graph.visualize(output_path)

