from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from .node import Node
from .edges import Edge
from .constraint import Constraint


class DiagramMetadata(BaseModel):
    """High-level description of what the diagram is about and for whom."""

    topic: str = Field(..., description="Scientific topic of the diagram")
    audience: str = Field(..., description="Intended audience (e.g., Middle School)")
    purpose: str = Field(..., description="Purpose or learning goal of the diagram")
    detail_level: str = Field(..., description="Desired detail level (e.g., low/medium/high)")

    # Parsed diagram intent from the first LLM call
    intent: Optional[dict] = Field(
        default=None,
        description="Structured diagram intent as returned by the LLM",
    )


class DiagramGraph(BaseModel):
    """In-memory representation of a diagram graph being built incrementally."""

    metadata: DiagramMetadata

    # Store nodes by id for easy lookup and de-duplication
    nodes: Dict[str, Node] = Field(default_factory=dict)

    # Edges and constraints are usually naturally ordered lists
    edges: List[Edge] = Field(default_factory=list)
    constraints: List[Constraint] = Field(default_factory=list)

    def add_nodes(self, nodes: List[Node]) -> None:
        """Add or update nodes in the graph."""
        for node in nodes:
            self.nodes[node.id] = node

    def add_edges(self, edges: List[Edge]) -> None:
        """Append edges to the graph."""
        self.edges.extend(edges)

    def add_constraints(self, constraints: List[Constraint]) -> None:
        """Append constraints to the graph."""
        self.constraints.extend(constraints)

    def summary(self) -> dict:
        """Return a lightweight JSON-serializable summary of the graph."""
        return {
            "metadata": self.metadata.model_dump(),
            "num_nodes": len(self.nodes),
            "num_edges": len(self.edges),
            "num_constraints": len(self.constraints),
        }

    def to_dict(self) -> dict:
        """Return a full JSON-serializable representation of the graph."""
        return {
            "metadata": self.metadata.model_dump(),
            "nodes": [node.model_dump() for node in self.nodes.values()],
            "edges": [edge.model_dump() for edge in self.edges],
            "constraints": [constraint.model_dump() for constraint in self.constraints],
        }

    def pretty_connections(self) -> str:
        """Render edges in a human-readable list with node labels and operators."""
        if not self.edges:
            return "Connections: (none)"

        def label_for(node_id: str) -> str:
            node = self.nodes.get(node_id)
            if node:
                return f"{node.label} [{node.id}]"
            return f"{node_id} [missing]"

        lines = ["Connections:"]
        for edge in self.edges:
            src = label_for(edge.source)
            tgt = label_for(edge.target)
            polarity = f", polarity={edge.attributes.polarity}" if edge.attributes.polarity else ""
            lines.append(
                f"- {src} --({edge.family}/{edge.operator}, directional={edge.attributes.directional}{polarity})--> {tgt}"
            )
        return "\n".join(lines)

    def pretty_constraints(self) -> str:
        """Render constraints in a concise, readable list."""
        if not self.constraints:
            return "Constraints: (none)"

        lines = ["Constraints:"]
        for c in self.constraints:
            scope = f" scope={c.scope}" if c.scope else ""
            hardness = "HARD" if c.hard else "SOFT"
            lines.append(f"- [{c.family}][{hardness}] {c.id}: {c.description}{scope}")
        return "\n".join(lines)

    def to_graphviz(self):
        """
        Convert to a graphviz.Digraph object (requires `graphviz` package).

        Returns:
            graphviz.Digraph
        """
        try:
            from graphviz import Digraph
        except ImportError as exc:
            raise ImportError(
                "graphviz is required for visualization. Install with `pip install graphviz`."
            ) from exc

        dot = Digraph(comment=self.metadata.topic)

        # Color palette per node type
        type_colors = {
            "entity": "lightblue",
            "process": "lightgreen",
            "state": "khaki",
            "variable": "plum",
            "region": "lightgray",
            "annotation": "white",
        }

        # Add nodes with colors by type
        for node in self.nodes.values():
            fillcolor = type_colors.get(node.type, "white")
            dot.node(
                node.id,
                f"{node.label}\\n({node.type})",
                style="filled",
                fillcolor=fillcolor,
                shape="box",
            )

        # Add edges; clean operator labels; omit polarity
        for edge in self.edges:
            attrs = {}
            # Normalize operator name for readability
            op_label = edge.operator.replace("_", " ")
            if not edge.attributes.directional:
                attrs["dir"] = "none"
            dot.edge(edge.source, edge.target, label=op_label, **attrs)

        return dot

    def visualize_graph(self, output_path: Path | str = "graph.png") -> Path:
        """
        Render the graph to an image via graphviz. Returns the output path.
        """
        dot = self.to_graphviz()
        output_path = Path(output_path)
        rendered_path = dot.render(str(output_path), format=output_path.suffix.lstrip("."), cleanup=True)
        return Path(rendered_path)
