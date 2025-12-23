import json
import os
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from typing import List

# Silence terminal output by default
QUIET = False
if QUIET:
    def print(*args, **kwargs):  # type: ignore
        return None

# Allow running this script directly without installing the package
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.append(str(SRC_ROOT))

from diagmind.llm import parse  # noqa: E402
from diagmind.graph import (  # noqa: E402
    Constraint,
    Diagram,
    DiagramMetadata,
    Graph,
)
from diagmind.utils import (  # noqa: E402
    load_prompt,
    DiagramIntent,
    NodesResponse,
    EdgesResponse,
    ConstraintsResponse,
    ConstraintSchema,
)

# Load environment variables from .env file
load_dotenv()


# Load prompts from packaged resources
diagram_intent_prompt = load_prompt("diagram_intent.txt")
node_enumeration_prompt = load_prompt("node_enumeration.txt")
edge_construction_prompt = load_prompt("edge_construction.txt")
constraint_prompt = load_prompt("constraint.txt")

# Input data
inputs = {
  "topic": "Solar System",
  "audience": "Middle School",
  "purpose": "Draw the diagram"
}

# Print diagram intent
user_prompt = f"""Topic: {inputs['topic']}
Audience: {inputs['audience']}
Purpose: {inputs['purpose']}"""

print("Getting diagram intent...")
diagram_intent = parse(
    system_prompt=diagram_intent_prompt,
    user_prompt=user_prompt,
    response_format=DiagramIntent,
)

print("\nDiagram Intent:")
print(json.dumps(diagram_intent.model_dump(), indent=2))

# Generate nodes
node_user_prompt = f"""Topic: {inputs['topic']}
Audience: {inputs['audience']}
Purpose: {inputs['purpose']}

Diagram Intent:
- Domain: {diagram_intent.domain}
- Diagram Family: {diagram_intent.diagram_family}
- Abstraction Levels: {', '.join(diagram_intent.abstraction_levels)}
- Expected Flow: {diagram_intent.expected_flow or 'N/A'}"""

print("\nGenerating nodes...")
nodes_response = parse(
    system_prompt=node_enumeration_prompt,
    user_prompt=node_user_prompt,
    response_format=NodesResponse,
)

print(f"\nGenerated {len(nodes_response.nodes)} nodes:")
for node in nodes_response.nodes:
    print(f"  - {node.label} [{node.id}] (type: {node.type})")

# Create graph with nodes first
graph = Graph()
graph.add_nodes(nodes_response.nodes)

# Generate edges
edge_user_prompt = f"""Topic: {inputs['topic']}
Audience: {inputs['audience']}
Purpose: {inputs['purpose']}

Diagram Intent:
- Domain: {diagram_intent.domain}
- Diagram Family: {diagram_intent.diagram_family}
- Abstraction Levels: {', '.join(diagram_intent.abstraction_levels)}
- Expected Flow: {diagram_intent.expected_flow or 'N/A'}

{graph.to_llm_format()}

Connect the nodes above with appropriate relationships. Use the node IDs for source and target."""

print("\nGenerating edges...")
edges_response = parse(
    system_prompt=edge_construction_prompt,
    user_prompt=edge_user_prompt,
    response_format=EdgesResponse,
)

print(f"\nGenerated {len(edges_response.edges)} edges:")
for edge in edges_response.edges:
    polarity_str = f", polarity={edge.attributes.polarity}" if edge.attributes and edge.attributes.polarity else ""
    strength_str = f", strength={edge.attributes.strength}" if edge.attributes and edge.attributes.strength else ""
    print(f"  - {edge.source} --({edge.operator}{strength_str}{polarity_str})--> {edge.target}")

# Add edges to graph
graph.add_edges(edges_response.edges)

print(f"Graph created with {len(graph.nodes)} nodes and {len(graph.edges)} edges")

# Save visualization
output_dir = PROJECT_ROOT / "output"
output_dir.mkdir(exist_ok=True)
output_file = output_dir / f"{inputs['topic'].lower().replace(' ', '_')}_graph.png"

print(f"\nVisualizing and saving graph to {output_file}...")
saved_path = graph.visualize(output_file)
print(f"Graph saved to: {saved_path}")

