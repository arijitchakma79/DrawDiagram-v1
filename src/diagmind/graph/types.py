from typing import Literal

NodeType = Literal[
    "entity",
    "process",
    "state",
    "variable",
    "region",
    "annotation"
]

AbstractionLevel = Literal[
    "conceptual",
    "structural",
    "functional",
    "mechanistic",
    "quantitative",
    "computational"
]

NodeRole = Literal[
    "input",
    "intermediary",
    "output"
]

Importance = Literal[
    "primary",
    "secondary",
    "tertiary"
]

EdgeFamily = Literal[
    "structural",
    "spatial",
    "process",
    "causal",
    "functional",
    "informational",
    "temporal",
    "quantitative"
]

ConstraintFamily = Literal[
    "spatial",
    "structural",
    "process",
    "causal",
    "quantitative",
    "style"
]
