from typing import List, Optional, Dict, Literal, Tuple
from pathlib import Path
import math
from pydantic import BaseModel, Field

from ..graph import Node, Edge, ConstraintType


class DiagramIntent(BaseModel):
    diagram_family: str
    abstraction_levels: List[str]
    expected_flow: Optional[str] = None


class NodesResponse(BaseModel):
    nodes: List[Node]


class EdgesResponse(BaseModel):
    edges: List[Edge]



class ValidatorWarning(BaseModel):
    node_id: Optional[str] = None
    edge_id: Optional[int] = None
    message: str


class ValidatorInstruction(BaseModel):
    action: str  
    edge_id: Optional[int] = None
    node_id: Optional[str] = None
    source_node_id: Optional[str] = None
    target_node_id: Optional[str] = None
    new_relation: Optional[str] = None
    new_label: Optional[str] = None
    reason: str


class ValidatorResponse(BaseModel):
    needs_correction: bool = Field(default=False, description="Set to true if instructions were emitted that modify the graph. Set to false if graph is correct or only warnings/flag_error were emitted.")
    instructions: List[ValidatorInstruction] = Field(default_factory=list)
    warnings: List[ValidatorWarning] = Field(default_factory=list)


class LayoutPlanResponse(BaseModel):
    """Response from layout planner containing drawing instructions."""
    instructions: List[str] = Field(..., description="List of drawing instructions, each starting with 'Draw'")


# Layout Constraint Types
LayoutConstraintType = Literal[
    "centrality",
    "ordering",
    "grouping",
    "containment",
    "spacing",
    "alignment",
    "non_overlap",
    "readability",
    "labeling"
]

LayoutConstraintScope = Literal[
    "global",
    "group",
    "local"
]

LayoutConstraintPriority = Literal[
    "must",
    "should",
    "may"
]


class LayoutConstraint(BaseModel):
    id: str = Field(..., description="Unique identifier for the constraint")
    type: LayoutConstraintType = Field(..., description="Type of layout constraint")
    scope: LayoutConstraintScope = Field(..., description="Scope of the constraint: global, group, or local")
    targets: List[str] = Field(default_factory=list, description="List of target node/edge IDs or groups this constraint applies to")
    description: str = Field(..., description="One clear enforceable spatial rule")
    priority: LayoutConstraintPriority = Field(..., description="Priority level: must, should, or may")


class LayoutConstraintsResponse(BaseModel):
    layout_constraints: List[LayoutConstraint] = Field(default_factory=list)


# Layout Generator Types
OrganizationType = Literal[
    "radial",
    "linear_horizontal",
    "linear_vertical",
    "layered",
    "grid",
    "clustered",
    "mixed"
]

EntityShape = Literal[
    "circle",
    "box",
    "ellipse"
]

PositionType = Literal[
    "absolute",
    "orbit"
]

RegionGeometryType = Literal[
    "enclosure",
    "annulus"
]


# Layout Generator Models
class Canvas(BaseModel):
    width: float = Field(default=1.0, description="Canvas width (normalized to [0,1])")
    height: float = Field(default=1.0, description="Canvas height (normalized to [0,1])")


class Point(BaseModel):
    cx: float = Field(..., description="Center x coordinate")
    cy: float = Field(..., description="Center y coordinate")


class Point2D(BaseModel):
    x: float = Field(..., description="X coordinate")
    y: float = Field(..., description="Y coordinate")


class Orbit(BaseModel):
    center: str = Field(..., description="Node ID of the orbit center")
    radius: float = Field(..., description="Orbit radius")
    angle_deg: float = Field(..., description="Angle in degrees")


class EntitySize(BaseModel):
    radius: float = Field(default=0.0, description="Radius for circle/ellipse shapes")
    width: Optional[float] = Field(default=None, description="Width for box/ellipse shapes")
    height: Optional[float] = Field(default=None, description="Height for box/ellipse shapes")


class EntityPosition(BaseModel):
    type: PositionType = Field(..., description="Position type: absolute or orbit")
    x: float = Field(..., description="X coordinate (for absolute) or initial x")
    y: float = Field(..., description="Y coordinate (for absolute) or initial y")
    orbit: Optional[Orbit] = Field(default=None, description="Orbit parameters if type is 'orbit'")


class Entity(BaseModel):
    id: str = Field(..., description="Node ID")
    kind: Literal["entity"] = Field(default="entity", description="Entity kind")
    shape: EntityShape = Field(..., description="Shape type: circle, box, or ellipse")
    size: EntitySize = Field(..., description="Size specifications")
    position: EntityPosition = Field(..., description="Position specifications")
    parent: Optional[str] = Field(default=None, description="Parent node ID if contained in a region")
    notes: str = Field(default="", description="Spatial intent notes")


class RegionGeometry(BaseModel):
    type: RegionGeometryType = Field(..., description="Geometry type: enclosure or annulus")
    center: Point = Field(..., description="Center point of the region")
    inner_radius: float = Field(default=0.0, description="Inner radius (for annulus) or 0 (for enclosure)")
    outer_radius: float = Field(..., description="Outer radius")


class Region(BaseModel):
    id: str = Field(..., description="Node ID")
    geometry: RegionGeometry = Field(..., description="Region geometry specifications")
    contains: List[str] = Field(default_factory=list, description="List of node IDs contained in this region")


class Annotation(BaseModel):
    id: str = Field(..., description="Node ID")
    anchors: List[str] = Field(default_factory=list, description="List of node IDs this annotation anchors to")
    position: Point2D = Field(..., description="Annotation position")
    avoid_overlap_with: List[str] = Field(default_factory=list, description="List of node IDs to avoid overlapping with")


class GlobalStructure(BaseModel):
    organization: OrganizationType = Field(..., description="Overall organization archetype")
    center: Point = Field(..., description="Center point of the global structure")
    description: str = Field(..., description="Why this archetype was chosen")


class LayoutPlan(BaseModel):
    canvas: Canvas = Field(..., description="Canvas specifications")
    global_structure: GlobalStructure = Field(..., description="Global structure specifications")
    entities: List[Entity] = Field(default_factory=list, description="List of entities")
    regions: List[Region] = Field(default_factory=list, description="List of regions")
    annotations: List[Annotation] = Field(default_factory=list, description="List of annotations")
    
    def _get_entity_position(self, entity: Entity) -> Tuple[float, float]:
        """Calculate the actual x, y position of an entity, handling orbit positions."""
        if entity.position.type == "orbit" and entity.position.orbit:
            # Find the center entity
            center_entity = next((e for e in self.entities if e.id == entity.position.orbit.center), None)
            if center_entity:
                center_x, center_y = self._get_entity_position(center_entity)
                angle_rad = math.radians(entity.position.orbit.angle_deg)
                x = center_x + entity.position.orbit.radius * math.cos(angle_rad)
                y = center_y + entity.position.orbit.radius * math.sin(angle_rad)
                return (x, y)
        return (entity.position.x, entity.position.y)
    
    def visualize(self, output_path: Path | str = "layout.png", figsize: Tuple[int, int] = (10, 10)) -> Path:
        """Generate a visualization of the layout plan and save it to a file."""
        try:
            import matplotlib.pyplot as plt
            import matplotlib.patches as mpatches
        except ImportError as exc:
            raise ImportError(
                "matplotlib is required for layout visualization. Install with `pip install matplotlib`."
            ) from exc
        
        output_path = Path(output_path)
        
        # Create figure with normalized coordinates [0,1] x [0,1]
        fig, ax = plt.subplots(figsize=figsize)
        ax.set_xlim(0, self.canvas.width)
        ax.set_ylim(0, self.canvas.height)
        ax.set_aspect('equal')
        ax.invert_yaxis()  # Origin at top-left, y increases downward
        ax.axis('off')
        
        # Create a mapping of entity IDs to their positions for orbit calculations
        entity_positions = {}
        for entity in self.entities:
            entity_positions[entity.id] = self._get_entity_position(entity)
        
        # Draw regions first (so they appear behind entities)
        for region in self.regions:
            center = region.geometry.center
            if region.geometry.type == "enclosure":
                # Draw a circle
                circle = mpatches.Circle(
                    (center.cx, center.cy),
                    region.geometry.outer_radius,
                    fill=True,
                    facecolor='lightgray',
                    edgecolor='gray',
                    alpha=0.3,
                    linewidth=2
                )
                ax.add_patch(circle)
            elif region.geometry.type == "annulus":
                # Draw outer circle
                outer = mpatches.Circle(
                    (center.cx, center.cy),
                    region.geometry.outer_radius,
                    fill=True,
                    facecolor='lightgray',
                    edgecolor='gray',
                    alpha=0.3,
                    linewidth=2
                )
                ax.add_patch(outer)
                # Draw inner circle (hole)
                inner = mpatches.Circle(
                    (center.cx, center.cy),
                    region.geometry.inner_radius,
                    fill=True,
                    facecolor='white',
                    edgecolor='gray',
                    linewidth=2
                )
                ax.add_patch(inner)
        
        # Draw entities
        for entity in self.entities:
            x, y = entity_positions[entity.id]
            
            if entity.shape == "circle":
                circle = mpatches.Circle(
                    (x, y),
                    entity.size.radius,
                    fill=True,
                    facecolor='steelblue',
                    edgecolor='darkblue',
                    linewidth=2
                )
                ax.add_patch(circle)
                # Add label
                ax.text(x, y, entity.id, ha='center', va='center', fontsize=8, color='white', weight='bold')
            
            elif entity.shape == "ellipse":
                width = entity.size.width or entity.size.radius * 2
                height = entity.size.height or entity.size.radius * 2
                ellipse = mpatches.Ellipse(
                    (x, y),
                    width,
                    height,
                    fill=True,
                    facecolor='steelblue',
                    edgecolor='darkblue',
                    linewidth=2
                )
                ax.add_patch(ellipse)
                ax.text(x, y, entity.id, ha='center', va='center', fontsize=8, color='white', weight='bold')
            
            elif entity.shape == "box":
                width = entity.size.width or entity.size.radius * 2
                height = entity.size.height or entity.size.radius * 2
                rect = mpatches.Rectangle(
                    (x - width/2, y - height/2),
                    width,
                    height,
                    fill=True,
                    facecolor='steelblue',
                    edgecolor='darkblue',
                    linewidth=2
                )
                ax.add_patch(rect)
                ax.text(x, y, entity.id, ha='center', va='center', fontsize=8, color='white', weight='bold')
        
        # Draw annotations
        for annotation in self.annotations:
            x, y = annotation.position.x, annotation.position.y
            # Draw annotation as a small text box
            ax.text(
                x, y,
                f"Annot: {annotation.id}",
                ha='left',
                va='bottom',
                fontsize=7,
                color='darkgreen',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='lightgreen', alpha=0.5, edgecolor='green')
            )
        
        # Draw orbit paths for entities with orbit positions
        for entity in self.entities:
            if entity.position.type == "orbit" and entity.position.orbit:
                center_entity = next((e for e in self.entities if e.id == entity.position.orbit.center), None)
                if center_entity:
                    cx, cy = entity_positions[center_entity.id]
                    radius = entity.position.orbit.radius
                    circle = mpatches.Circle(
                        (cx, cy),
                        radius,
                        fill=False,
                        edgecolor='lightgray',
                        linestyle='--',
                        linewidth=1,
                        alpha=0.5
                    )
                    ax.add_patch(circle)
        
        plt.title("Layout Plan Visualization", fontsize=14, pad=20)
        plt.tight_layout()
        
        # Save the figure
        output_path = output_path.with_suffix('.png') if not output_path.suffix else output_path
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return output_path

