from __future__ import annotations
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field
from .graph import Graph


class DiagramMetadata(BaseModel):
    topic: str = Field(..., description="Scientific topic of the diagram")
    description: str = Field(..., description="Additional description about the scientific topic")
    intent: Optional[dict] = Field(
        default=None,
        description="Structured diagram intent as returned by the LLM",
    )


class Diagram(BaseModel):
    metadata: DiagramMetadata
    graph: Graph = Field(default_factory=Graph)


    def summary(self) -> dict:
        return {
            "metadata": self.metadata.model_dump(),
            "num_nodes": len(self.graph.nodes),
            "num_edges": len(self.graph.edges),
        }

    def to_dict(self) -> dict:
        return {
            "metadata": self.metadata.model_dump(),
            "nodes": [node.model_dump() for node in self.graph.nodes.values()],
            "edges": [edge.model_dump() for edge in self.graph.edges],
        }

    def pretty_connections(self) -> str:
        return self.graph.pretty_connections()

    def visualize_graph(self, output_path: Path | str = "graph.png") -> Path:
        return self.graph.visualize(output_path)

