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
    ValidatorResponse,
)

# Load environment variables from .env file
load_dotenv()


# Load prompts from packaged resources
diagram_intent_prompt = load_prompt("diagram_intent.txt")
node_enumeration_prompt = load_prompt("node_enumeration.txt")
edge_construction_prompt = load_prompt("edge_construction.txt")
constraint_prompt = load_prompt("constraint.txt")
semantics_validator_prompt = load_prompt("semantics_validator.txt")

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

# Create graph with nodes first
graph = Graph()
graph.add_nodes(nodes_response.nodes)

print(f"\nGenerated {len(nodes_response.nodes)} nodes:")
for node in nodes_response.nodes:
    print(f"  - {node.label} [{node.id}] (type: {node.type})")

# Generate edges
edge_user_prompt = f"""Topic: {inputs['topic']}
Audience: {inputs['audience']}
Purpose: {inputs['purpose']}

Diagram Intent:
- Domain: {diagram_intent.domain}
- Diagram Family: {diagram_intent.diagram_family}
- Abstraction Levels: {', '.join(diagram_intent.abstraction_levels)}
- Expected Flow: {diagram_intent.expected_flow or 'N/A'}

Nodes in the graph:
{graph.get_all_nodes()}

Connect the nodes above with appropriate relationships. Use the node IDs for source and target."""
print("\nGenerating edges...")
edges_response = parse(
    system_prompt=edge_construction_prompt,
    user_prompt=edge_user_prompt,
    response_format=EdgesResponse,
)

# Add edges to graph
graph.add_edges(edges_response.edges)

print(f"\nGraph created with {len(graph.nodes)} nodes and {len(graph.edges)} edges")
print("\nGraph structure (before validation):")
print(graph)

# Validate graph semantics (loop until needs_correction is false)
print("\n" + "="*60)
print("Validating graph semantics...")
print("="*60)

max_iterations = 10  # Safety limit to prevent infinite loops
iteration = 0
all_warnings = []

while True:
    iteration += 1
    if iteration > max_iterations:
        print(f"\n⚠ WARNING: Reached maximum validation iterations ({max_iterations}). Stopping validation loop.")
        break
    
    print(f"\n--- Validation iteration {iteration} ---")
    
    validator_user_prompt = f"""Topic: {inputs['topic']}
Audience: {inputs['audience']}
Purpose: {inputs['purpose']}

Diagram Intent:
- Domain: {diagram_intent.domain}
- Diagram Family: {diagram_intent.diagram_family}
- Abstraction Levels: {', '.join(diagram_intent.abstraction_levels)}

Current Graph Structure:
{graph}

Validate this graph and emit edit instructions for any semantic errors.
Remember: edge IDs are 1-indexed (first edge is edge_id: 1)."""

    validator_response = parse(
        system_prompt=semantics_validator_prompt,
        user_prompt=validator_user_prompt,
        response_format=ValidatorResponse,
    )

    # Collect warnings
    all_warnings.extend(validator_response.warnings)

    # Apply validator instructions
    audit_log = []
    should_continue = graph.apply_validator_response(validator_response, audit_log)

    print(f"Validator found {len(validator_response.instructions)} instructions and {len(validator_response.warnings)} warnings")
    print(f"needs_correction: {validator_response.needs_correction}")

    if validator_response.instructions:
        print("\nApplied instructions:")
        for entry in audit_log:
            if entry.get("status") == "applied":
                print(f"  ✓ {entry.get('action')}: {entry.get('reason', 'No reason')}")
            elif entry.get("status") == "failed":
                print(f"  ✗ {entry.get('action')}: FAILED - {entry.get('reason', 'No reason')}")

    if validator_response.warnings:
        print("\nWarnings:")
        for warning in validator_response.warnings:
            node_info = f"node {warning.node_id}" if warning.node_id else f"edge {warning.edge_id}" if warning.edge_id else "unknown"
            print(f"  ⚠ {node_info}: {warning.message}")

    if not should_continue:
        print("\n" + "="*60)
        print("ERROR: Validator flagged critical error. Pipeline halted.")
        print("="*60)
        sys.exit(1)
    
    # Continue looping if needs_correction is true
    if not validator_response.needs_correction:
        print(f"\n✓ Graph validation complete after {iteration} iteration(s).")
        break

# Print all accumulated warnings
if all_warnings:
    print(f"\nTotal warnings across all iterations: {len(all_warnings)}")

print("\nGraph structure (after validation):")
print(graph)

# Save visualization
output_dir = PROJECT_ROOT / "output"
output_dir.mkdir(exist_ok=True)
output_file = output_dir / f"{inputs['topic'].lower().replace(' ', '_')}_graph"

print(f"\nVisualizing and saving graph to {output_file}...")
saved_path = graph.visualize(output_file)
print(f"Graph saved to: {saved_path}")

