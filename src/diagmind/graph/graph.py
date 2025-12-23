from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from pydantic import BaseModel, Field

from .node import Node
from .edges import Edge


class Graph(BaseModel):
    nodes: Dict[str, Node] = Field(default_factory=dict)
    edges: List[Edge] = Field(default_factory=list)

    def add_nodes(self, nodes: List[Node]) -> None:
        for node in nodes:
            self.nodes[node.id] = node

    def add_edges(self, edges: List[Edge]) -> None:
        self.edges.extend(edges)

    def pretty_connections(self) -> str:
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
            polarity = f", polarity={edge.attributes.polarity}" if edge.attributes and edge.attributes.polarity else ""
            lines.append(
                f"- {src} --({edge.operator}{polarity})--> {tgt}"
            )
        return "\n".join(lines)

    def to_graphviz(self, comment: str = "Graph"):
        try:
            from graphviz import Digraph
        except ImportError as exc:
            raise ImportError(
                "graphviz is required for visualization. Install with `pip install graphviz`."
            ) from exc

        dot = Digraph(comment=comment)

        type_colors = {
            "entity": "lightblue",
            "process": "lightgreen",
            "state": "khaki",
            "variable": "plum",
            "region": "lightgray",
            "annotation": "white",
        }

        for node in self.nodes.values():
            fillcolor = type_colors.get(node.type, "white")
            dot.node(
                node.id,
                f"{node.label}\\n({node.type})",
                style="filled",
                fillcolor=fillcolor,
                shape="box",
            )

        for edge in self.edges:
            attrs = {}
            op_label = edge.operator.replace("_", " ")
            dot.edge(edge.source, edge.target, label=op_label, **attrs)

        return dot

    def visualize(self, output_path: Path | str = "graph.png") -> Path:
        dot = self.to_graphviz()
        output_path = Path(output_path)
        rendered_path = dot.render(str(output_path), format=output_path.suffix.lstrip("."), cleanup=True)
        return Path(rendered_path)

    def to_llm_format(self) -> str:
        """
        Convert graph to a pretty format suitable for LLM input.
        Returns a string with Nodes and Edges in a readable format.
        """
        nodes_list = [f"{node.label} [{node.id}] ({node.type})" for node in self.nodes.values()]
        nodes_str = f"Nodes: [{', '.join(nodes_list)}]"
        
        edges_list = []
        for edge in self.edges:
            source_node = self.nodes.get(edge.source)
            target_node = self.nodes.get(edge.target)
            source_label = source_node.label if source_node else edge.source
            target_label = target_node.label if target_node else edge.target
            edge_str = f"{source_label} -> {edge.operator} -> {target_label}"
            edges_list.append(edge_str)
        
        edges_str = f"Edges: [{', '.join(edges_list)}]"
        
        return f"{nodes_str}\n{edges_str}"
