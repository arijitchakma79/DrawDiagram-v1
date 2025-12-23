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

ConstraintType = Literal[
    "presence",
    "spatial_relation",
    "ordering",
    "containment",
    "causal_validity",
    "quantitative_relation"
]

