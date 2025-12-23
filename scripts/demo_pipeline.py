import json
import os
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from typing import List

# Silence terminal output by default
QUIET = True
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
    DiagramGraph,
    DiagramMetadata,
)
from diagmind.utils import (  # noqa: E402
    load_prompt,
    DiagramIntent,
    NodesResponse,
    EdgesResponse,
    ConstraintsResponse,
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
    "Scientific topic": "Life Cycle of Butterfly",
    "Audience": "Middle School",
    "Purpose": "Show the life cycle of a butterfly",
    "Desired detail level": "medium"
}

# Format the user prompt with the input data
user_prompt = f"""Scientific topic: {inputs['Scientific topic']}
Audience: {inputs['Audience']}
Purpose: {inputs['Purpose']}
Desired detail level: {inputs['Desired detail level']}"""

# Step 1: Infer diagram intent
print("="*50)
print("Step 1: Inferring diagram intent...")
print("="*50)
diagram_intent_obj = parse(
    system_prompt=diagram_intent_prompt,
    user_prompt=user_prompt,
    response_format=DiagramIntent,
    model="gpt-4.1-2025-04-14",
    temperature=1,
)

diagram_intent = diagram_intent_obj.model_dump()
print("\nParsed Diagram Intent:")
print(json.dumps(diagram_intent, indent=2))

# Initialize the graph with metadata
metadata = DiagramMetadata(
    topic=inputs["Scientific topic"],
    audience=inputs["Audience"],
    purpose=inputs["Purpose"],
    detail_level=inputs["Desired detail level"],
    intent=diagram_intent,
)
graph = DiagramGraph(metadata=metadata)

# Step 2: Enumerate nodes using the diagram intent
if graph is not None:
    print("\n" + "="*50)
    print("Step 2: Enumerating nodes...")
    print("="*50)
    
    # Create prompt for node enumeration with topic and diagram intent
    node_prompt = f"""Scientific topic: {inputs['Scientific topic']}
Audience: {inputs['Audience']}
Purpose: {inputs['Purpose']}
Desired detail level: {inputs['Desired detail level']}

Inferred diagram intent:
{json.dumps(diagram_intent, indent=2)}"""
    
    # Call LLM with structured output using parse()
    nodes_result = parse(
        system_prompt=node_enumeration_prompt,
        user_prompt=node_prompt,
        response_format=NodesResponse,
        model="gpt-4.1-2025-04-14",
        temperature=1,
    )
    
    print("\nNodes Result:")
    result_dict = nodes_result.model_dump()
    print(json.dumps(result_dict, indent=2, default=str))
    
    print(f"\nTotal nodes enumerated: {len(nodes_result.nodes)}")
    # Add nodes to the graph
    graph.add_nodes(nodes_result.nodes)

    for i, node in enumerate(nodes_result.nodes, 1):
        print(f"\n  {i}. {node.label} ({node.type})")
        print(f"     ID: {node.id}")
        print(f"     Role: {node.attributes.role}")
    
    # Step 3: Construct edges using the enumerated nodes
    print("\n" + "="*50)
    print("Step 3: Constructing edges...")
    print("="*50)
    
    # Create prompt for edge construction with topic, diagram intent, and nodes
    edge_prompt = f"""Scientific topic: {inputs['Scientific topic']}
Audience: {inputs['Audience']}
Purpose: {inputs['Purpose']}
Desired detail level: {inputs['Desired detail level']}

Inferred diagram intent:
{json.dumps(diagram_intent, indent=2)}

Enumerated nodes:
{json.dumps([node.model_dump() for node in nodes_result.nodes], indent=2)}"""
    
    # Call LLM with structured output using parse()
    edges_result = parse(
        system_prompt=edge_construction_prompt,
        user_prompt=edge_prompt,
        response_format=EdgesResponse,
        model="gpt-4.1-2025-04-14",
        temperature=1,
    )
    
    print("\nEdges Result:")
    edges_dict = edges_result.model_dump()
    print(json.dumps(edges_dict, indent=2, default=str))
    
    # Add edges to the graph
    graph.add_edges(edges_result.edges)

    print(f"\nTotal edges constructed: {len(edges_result.edges)}")
    for i, edge in enumerate(edges_result.edges, 1):
        print(f"\n  {i}. {edge.source} --[{edge.operator}]--> {edge.target}")
        print(f"     Family: {edge.family}")
        print(f"     Directional: {edge.attributes.directional}")
        if edge.attributes.polarity:
            print(f"     Polarity: {edge.attributes.polarity}")
    
    # Step 4: Generate constraints using nodes and edges
    print("\n" + "="*50)
    print("Step 4: Generating constraints...")
    print("="*50)
    
    # Create prompt for constraint generation with topic, diagram intent, nodes, and edges
    constraint_prompt_text = f"""Scientific topic: {inputs['Scientific topic']}
Audience: {inputs['Audience']}
Purpose: {inputs['Purpose']}
Desired detail level: {inputs['Desired detail level']}

Inferred diagram intent:
{json.dumps(diagram_intent, indent=2)}

Enumerated nodes:
{json.dumps([node.model_dump() for node in nodes_result.nodes], indent=2)}

Constructed edges:
{json.dumps([edge.model_dump() for edge in edges_result.edges], indent=2)}"""
    
    # Call LLM with structured output using parse()
    constraints_result = parse(
        system_prompt=constraint_prompt,
        user_prompt=constraint_prompt_text,
        response_format=ConstraintsResponse,
        model="gpt-4.1-2025-04-14",
        temperature=1,
    )
    
    print("\nConstraints Result:")
    constraints_dict = constraints_result.model_dump()
    print(json.dumps(constraints_dict, indent=2, default=str))
    
    # Convert constraints into our core Constraint model and add to graph
    core_constraints = [
        Constraint(
            id=c.id,
            family=c.family,
            description=c.description,
            scope=c.scope,
            hard=c.hard,
            parameters=c.parameters,
        )
        for c in constraints_result.constraints
    ]
    graph.add_constraints(core_constraints)

    print(f"\nTotal constraints generated: {len(core_constraints)}")
    for i, constraint in enumerate(core_constraints, 1):
        print(f"\n  {i}. [{constraint.family}] {constraint.description}")
        print(f"     ID: {constraint.id}")
        print(f"     Hard: {constraint.hard}")
        if constraint.scope:
            print(f"     Scope: {constraint.scope}")

    # Final graph summary
    print("\n" + "=" * 50)
    print("Final graph summary")
    print("=" * 50)
    print(json.dumps(graph.summary(), indent=2, default=str))

    # Human-readable connections and constraints
    print("\n" + "=" * 50)
    print("Graph connections")
    print("=" * 50)
    print(graph.pretty_connections())

    print("\n" + "=" * 50)
    print("Graph constraints")
    print("=" * 50)
    print(graph.pretty_constraints())

    # Persist artifacts (JSON + PNG) into runs/
    runs_dir = PROJECT_ROOT / "runs"
    runs_dir.mkdir(exist_ok=True)
    run_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    base_path = runs_dir / f"run-{run_id}"

    # Save full graph payload as JSON
    graph_payload = {
        "inputs": inputs,
        "diagram_intent": diagram_intent,
        "graph": graph.to_dict(),
    }
    json_path = base_path.with_suffix(".json")
    json_path.write_text(json.dumps(graph_payload, indent=2, default=str))
    print(f"\nSaved graph JSON -> {json_path}")

    # Save rendered graph as PNG (if graphviz is available)
    png_path = base_path.with_suffix(".png")
    try:
        rendered_path = graph.visualize_graph(png_path)
        print(f"Saved graph PNG  -> {rendered_path}")
    except ImportError:
        print(
            "Graphviz not installed; skipped PNG render. "
            "Install with `pip install graphviz` and ensure Graphviz binaries are available."
        )
else:
    print("\nSkipping node enumeration due to diagram intent parsing error.")
