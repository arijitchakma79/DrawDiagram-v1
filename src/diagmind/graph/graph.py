from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Union

from pydantic import BaseModel, Field

from .node import Node
from .edges import Edge


class Graph(BaseModel):
    nodes: Dict[str, Node] = Field(default_factory=dict)
    edges: List[Edge] = Field(default_factory=list)

    def add_nodes(self, nodes: List[Node]) -> None:
        """Add multiple nodes to the graph."""
        for node in nodes:
            self.nodes[node.id] = node

    def add_node(self, node: Node) -> None:
        """Add a single node to the graph."""
        self.nodes[node.id] = node

    def remove_node(self, node_id: str) -> bool:
        """
        Remove a node from the graph by ID.
        Also removes all edges connected to this node.
        Returns True if the node was removed, False if it didn't exist.
        """
        if node_id not in self.nodes:
            return False

        # Remove the node
        del self.nodes[node_id]

        # Remove all edges connected to this node
        self.edges = [
            edge for edge in self.edges
            if edge.source != node_id and edge.target != node_id
        ]

        return True

    def add_edges(self, edges: List[Edge]) -> None:
        """Add multiple edges to the graph."""
        self.edges.extend(edges)

    def add_edge(self, edge: Edge) -> None:
        """Add a single edge to the graph."""
        self.edges.append(edge)

    def remove_edge(self, source: str, target: str, operator: str | None = None) -> bool:
        """
        Remove an edge from the graph.
        If operator is provided, only removes edges with that operator.
        Returns True if an edge was removed, False otherwise.
        """
        initial_count = len(self.edges)
        self.edges = [
            edge for edge in self.edges
            if not (
                edge.source == source
                and edge.target == target
                and (operator is None or edge.operator == operator)
            )
        ]
        return len(self.edges) < initial_count

    def get_all_nodes(self) -> str:
        """Return a formatted string listing all nodes in the graph."""
        if not self.nodes:
            return "Nodes: []"
        nodes = [f'{node.label} ({node.id}) (type={node.type})' for node in self.nodes.values()]
        return "\n".join(nodes)
    
    def to_llm_format(self) -> str:
        """
        Convert the graph to a human-readable format suitable for LLM prompts.
        Lists all nodes with their IDs, labels, and types.
        """
        if not self.nodes:
            return "No nodes in the graph."
        
        lines = ["Nodes in the graph:"]
        for node in self.nodes.values():
            lines.append(f"  - {node.label} (ID: {node.id}, Type: {node.type})")
        
        return "\n".join(lines)
    
    def __str__(self) -> str:
        """Return a string representation of the graph showing all edges in the format:
        source (label (id) type) -> edge (id, operator, birectional, strength-polarity) -> target (label (id) type)
        """
        if not self.edges:
            return "Graph with no edges."
        
        lines = []
        for i, edge in enumerate(self.edges, 1):
            # Get source node - format: label (id) type
            source_node = self.nodes.get(edge.source)
            if source_node:
                source_str = f"{source_node.label} ({source_node.id}) {source_node.type}"
            else:
                source_str = f"Unknown ({edge.source})"
            
            # Get target node - format: label (id) type
            target_node = self.nodes.get(edge.target)
            if target_node:
                target_str = f"{target_node.label} ({target_node.id}) {target_node.type}"
            else:
                target_str = f"Unknown ({edge.target})"
            
            # Format edge attributes
            strength = edge.attributes.strength if edge.attributes and edge.attributes.strength else "none"
            polarity = edge.attributes.polarity if edge.attributes and edge.attributes.polarity else "none"
            edge_attrs = f"{strength}-{polarity}"
            birectional_str = "bidirectional" if edge.birectional else "unidirectional"
            
            # Format: source (label (id) type) -> edge (id, operator, birectional, strength-polarity) -> target (label (id) type)
            lines.append(
                f"{source_str} -> edge ({i}, {edge.operator}, {birectional_str}, {edge_attrs}) -> {target_str}"
            )
        
        return "\n".join(lines)

    def get_all_edges(self) -> str:
        """Return a formatted string listing all edges in the graph."""
        if not self.edges:
            return "Edges: []"
        lines = []
        for i, edge in enumerate(self.edges, 1):
            source_label = self.nodes.get(edge.source, Node(id=edge.source, type="entity", label=edge.source)).label
            target_label = self.nodes.get(edge.target, Node(id=edge.target, type="entity", label=edge.target)).label
            arrow = "<-->" if edge.birectional else "-->"
            lines.append(f"{i}) {source_label} --[{edge.operator}]--{arrow} {target_label}")
        return "\n".join(lines)

    def convert_to_json(self, indent: int = 2) -> str:
        """Convert the graph to a JSON string representation."""
        graph_dict = {
            "nodes": [node.model_dump() for node in self.nodes.values()],
            "edges": [edge.model_dump() for edge in self.edges]
        }
        return json.dumps(graph_dict, indent=indent)

    def to_dict(self) -> Dict:
        """Convert the graph to a dictionary representation."""
        return {
            "nodes": [node.model_dump() for node in self.nodes.values()],
            "edges": [edge.model_dump() for edge in self.edges]
        }

    def to_graphviz(self, comment: str = "Graph"):
        """Convert the graph to a Graphviz Digraph object."""
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
        """Generate a visualization of the graph and save it to a file."""
        dot = self.to_graphviz()
        output_path = Path(output_path)
        
        # Get format from extension, default to 'png' if no extension
        format_str = output_path.suffix.lstrip(".")
        if not format_str:
            format_str = "png"
            # Add .png extension if no extension was provided
            output_path = output_path.with_suffix(".png")
        
        rendered_path = dot.render(
            str(output_path),
            format=format_str,
            cleanup=True
        )
        return Path(rendered_path)
    
    def apply_instruction(self, instruction: Dict, audit_log: List[Dict] | None = None) -> bool:
        """
        Apply a single validator instruction to the graph.
        Returns True if instruction was applied successfully, False otherwise.
        Updates audit_log if provided.
        """
        action = instruction.get("action")
        reason = instruction.get("reason", "No reason provided")
        
        if audit_log is None:
            audit_log = []
        
        try:
            if action == "reverse_edge":
                edge_id = instruction.get("edge_id")
                if edge_id is None or edge_id < 1 or edge_id > len(self.edges):
                    audit_log.append({"action": action, "status": "failed", "reason": f"Invalid edge_id: {edge_id}"})
                    return False
                
                edge = self.edges[edge_id - 1]  # Convert to 0-based index
                edge.source, edge.target = edge.target, edge.source
                audit_log.append({"action": action, "edge_id": edge_id, "status": "applied", "reason": reason})
                return True
            
            elif action == "remove_edge":
                edge_id = instruction.get("edge_id")
                if edge_id is None or edge_id < 1 or edge_id > len(self.edges):
                    audit_log.append({"action": action, "status": "failed", "reason": f"Invalid edge_id: {edge_id}"})
                    return False
                
                removed_edge = self.edges.pop(edge_id - 1)  # Convert to 0-based index
                audit_log.append({"action": action, "edge_id": edge_id, "status": "applied", "reason": reason})
                return True
            
            elif action == "change_relation":
                edge_id = instruction.get("edge_id")
                new_relation = instruction.get("new_relation")
                if edge_id is None or edge_id < 1 or edge_id > len(self.edges):
                    audit_log.append({"action": action, "status": "failed", "reason": f"Invalid edge_id: {edge_id}"})
                    return False
                if new_relation is None:
                    audit_log.append({"action": action, "status": "failed", "reason": "Missing new_relation"})
                    return False
                
                edge = self.edges[edge_id - 1] 
                old_operator = edge.operator
                edge.operator = new_relation
                audit_log.append({
                    "action": action,
                    "edge_id": edge_id,
                    "old_relation": old_operator,
                    "new_relation": new_relation,
                    "status": "applied",
                    "reason": reason
                })
                return True
            
            elif action == "merge_nodes":
                source_node_id = instruction.get("source_node_id")
                target_node_id = instruction.get("target_node_id")
                if source_node_id not in self.nodes or target_node_id not in self.nodes:
                    audit_log.append({"action": action, "status": "failed", "reason": "Invalid node IDs"})
                    return False
                if source_node_id == target_node_id:
                    audit_log.append({"action": action, "status": "failed", "reason": "Cannot merge node with itself"})
                    return False
                
                # Merge: keep target, update all edges pointing to source to point to target
                for edge in self.edges:
                    if edge.source == source_node_id:
                        edge.source = target_node_id
                    if edge.target == source_node_id:
                        edge.target = target_node_id
                
                # Remove source node
                del self.nodes[source_node_id]
                audit_log.append({
                    "action": action,
                    "source_node_id": source_node_id,
                    "target_node_id": target_node_id,
                    "status": "applied",
                    "reason": reason
                })
                return True
            
            elif action == "rename_node":
                node_id = instruction.get("node_id")
                new_label = instruction.get("new_label")
                if node_id not in self.nodes:
                    audit_log.append({"action": action, "status": "failed", "reason": f"Invalid node_id: {node_id}"})
                    return False
                if new_label is None:
                    audit_log.append({"action": action, "status": "failed", "reason": "Missing new_label"})
                    return False
                
                node = self.nodes[node_id]
                old_label = node.label
                node.label = new_label
                audit_log.append({
                    "action": action,
                    "node_id": node_id,
                    "old_label": old_label,
                    "new_label": new_label,
                    "status": "applied",
                    "reason": reason
                })
                return True
            
            elif action == "flag_error":
                audit_log.append({
                    "action": action,
                    "status": "error",
                    "reason": reason,
                    "message": instruction.get("message", "Pipeline halted due to validator error")
                })
                return False  # Signal to halt pipeline
            
            else:
                audit_log.append({"action": action, "status": "failed", "reason": f"Unknown action: {action}"})
                return False
        
        except Exception as e:
            audit_log.append({"action": action, "status": "error", "reason": f"Exception: {str(e)}"})
            return False
    
    def apply_validator_response(self, validator_response, audit_log: List[Dict] | None = None) -> bool:
        """
        Apply all instructions from a ValidatorResponse to the graph.
        Returns False if flag_error was encountered (should halt pipeline), True otherwise.
        Updates audit_log if provided.
        
        Note: remove_edge instructions are applied in reverse order of edge_id to avoid
        index shifting issues. Other instructions are applied in the order provided.
        """
        if audit_log is None:
            audit_log = []
        
        # Separate remove_edge instructions and sort them in reverse order
        remove_instructions = []
        other_instructions = []
        
        for instruction in validator_response.instructions:
            if instruction.action == "remove_edge":
                remove_instructions.append(instruction)
            else:
                other_instructions.append(instruction)
        
        # Sort remove instructions by edge_id in descending order
        remove_instructions.sort(key=lambda x: x.edge_id or 0, reverse=True)
        
        # Apply all instructions: first removals (in reverse order), then others (in original order)
        all_instructions = remove_instructions + other_instructions
        
        for instruction in all_instructions:
            result = self.apply_instruction(instruction.model_dump(), audit_log)
            if not result and instruction.action == "flag_error":
                return False  # Halt pipeline
        
        return True
