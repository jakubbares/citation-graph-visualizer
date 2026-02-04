"""
Data models for the Citation Graph Visualizer
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
import uuid


@dataclass
class PaperNode:
    """Represents a paper as a node in the citation graph"""
    # Identity
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    authors: List[str] = field(default_factory=list)
    publication_date: Optional[str] = None
    venue: str = ""
    doi: Optional[str] = None
    arxiv_id: Optional[str] = None
    url: Optional[str] = None
    
    # Content
    abstract: str = ""
    full_text: Optional[str] = None
    
    # Metadata
    citation_count: int = 0
    h_index_avg: float = 0.0
    venue_prestige: float = 0.0
    
    # Extracted attributes (dynamic)
    attributes: Dict[str, Any] = field(default_factory=dict)
    
    # Graph-specific
    position: Optional[Dict[str, float]] = None
    cluster_id: Optional[str] = None
    
    # Visual encoding
    visual: Dict[str, Any] = field(default_factory=lambda: {
        "color": "#4A90E2",
        "size": 20,
        "shape": "ellipse",
        "opacity": 1.0,
        "border_color": "#2C3E50",
        "border_width": 2
    })
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class CitationEdge:
    """Represents a citation relationship as an edge in the graph"""
    # Identity
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    from_paper: str = ""  # Paper that cites (newer)
    to_paper: str = ""    # Paper being cited (older)
    
    # Relationship
    contribution_type: str = "related"  # baseline, foundation, extension, etc.
    strength: float = 0.5  # 0-1, importance of citation
    centrality: str = "supporting"  # foundational, supporting, peripheral
    
    # Context
    context: str = ""
    section: str = ""
    sentiment: str = "positive"
    
    # Delta (what changed)
    delta_description: Optional[str] = None
    novelty_score: Optional[float] = None
    
    # Visual encoding
    visual: Dict[str, Any] = field(default_factory=lambda: {
        "color": "#95A5A6",
        "thickness": 2,
        "style": "solid",
        "opacity": 0.7
    })
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class ResearchGraph:
    """Represents the complete citation graph"""
    # Identity
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Untitled Graph"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # Structure
    nodes: List[PaperNode] = field(default_factory=list)
    edges: List[CitationEdge] = field(default_factory=list)
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Extractors applied
    extractors_applied: List[str] = field(default_factory=list)
    
    # Visual state
    layout: Dict[str, Any] = field(default_factory=lambda: {
        "algorithm": "cose",
        "parameters": {}
    })
    
    # Clusters
    clusters: Optional[List[Dict[str, Any]]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with serialized nodes and edges"""
        return {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "nodes": [node.to_dict() for node in self.nodes],
            "edges": [edge.to_dict() for edge in self.edges],
            "metadata": self.metadata,
            "extractors_applied": self.extractors_applied,
            "layout": self.layout,
            "clusters": self.clusters
        }
    
    def add_node(self, node: PaperNode) -> None:
        """Add a node to the graph"""
        self.nodes.append(node)
        self.updated_at = datetime.now().isoformat()
    
    def add_edge(self, edge: CitationEdge) -> None:
        """Add an edge to the graph"""
        self.edges.append(edge)
        self.updated_at = datetime.now().isoformat()
    
    def get_node_by_id(self, node_id: str) -> Optional[PaperNode]:
        """Get node by ID"""
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None
    
    def get_edges_for_node(self, node_id: str) -> List[CitationEdge]:
        """Get all edges connected to a node"""
        return [
            edge for edge in self.edges
            if edge.from_paper == node_id or edge.to_paper == node_id
        ]
