"""
Graph Builder Service - Constructs citation networks from papers
"""
from typing import List, Dict, Any, Optional
import networkx as nx
from graph.models import ResearchGraph, PaperNode, CitationEdge
from parsers.pdf_parser import ParsedPaper


class GraphBuilder:
    """Service for building and manipulating citation graphs"""
    
    def __init__(self):
        self.nx_graph = nx.DiGraph()
    
    def build_from_papers(
        self,
        papers: List[ParsedPaper],
        include_intermediate: bool = False,
        max_depth: int = 1
    ) -> ResearchGraph:
        """
        Build citation graph from list of papers
        
        Args:
            papers: List of ParsedPaper objects
            include_intermediate: Whether to include intermediate papers
            max_depth: Maximum depth for intermediate paper discovery
            
        Returns:
            ResearchGraph object
        """
        graph = ResearchGraph()
        
        # Create nodes for all papers
        paper_id_map = {}  # Map from title to paper ID
        for paper in papers:
            node = self._create_node_from_paper(paper)
            graph.add_node(node)
            paper_id_map[paper.title.lower()] = node.id
        
        # Note: This method doesn't create edges - use build_from_papers_with_citations for that
        
        # Update metadata
        graph.metadata = {
            "total_papers": len(graph.nodes),
            "total_citations": len(graph.edges),
            "date_range": self._compute_date_range(papers)
        }
        
        return graph
    
    def build_from_papers_with_citations(
        self,
        papers: List[ParsedPaper],
        citation_network: Dict[str, Any],
        include_intermediate: bool = False,
        max_depth: int = 1
    ) -> ResearchGraph:
        """
        Build citation graph from papers and Semantic Scholar citation data
        
        Args:
            papers: List of ParsedPaper objects (input papers uploaded by user)
            citation_network: Citation network from Semantic Scholar API
            include_intermediate: Whether to include intermediate papers
            max_depth: Maximum depth for intermediate paper discovery
            
        Returns:
            ResearchGraph object with input and intermediate papers
        """
        graph = ResearchGraph()
        
        # Create title to paper mapping for input papers
        title_to_paper = {p.title.lower().strip(): p for p in papers}
        
        # Get S2 papers data
        s2_papers = citation_network.get("papers", {})
        input_paper_ids_s2 = citation_network.get("input_paper_ids", [])
        intermediate_paper_ids_s2 = citation_network.get("intermediate_paper_ids", [])
        
        print(f"   DEBUG: s2_papers count: {len(s2_papers)}")
        print(f"   DEBUG: input_paper_ids_s2: {input_paper_ids_s2}")
        print(f"   DEBUG: First 5 s2_papers keys: {list(s2_papers.keys())[:5]}")
        
        s2_paper_id_to_node_id = {}  # Map S2 paper ID to our node ID
        
        # Step 1: Create nodes for INPUT papers (uploaded by user)
        print(f"📄 Creating nodes for {len(papers)} input papers...")
        for paper in papers:
            title_lower = paper.title.lower().strip()
            
            # Find matching S2 paper BY ID (more reliable than title matching)
            s2_paper = None
            s2_paper_id = None
            
            # First, try to match by checking if this paper's title matches any input paper in S2
            for s2_id in input_paper_ids_s2:
                if s2_id in s2_papers:
                    s2_data = s2_papers[s2_id]
                    # Match by title (fuzzy) or just take the first input paper if we only have one
                    if len(papers) == 1 and len(input_paper_ids_s2) == 1:
                        # If we only have 1 input paper, just use it
                        s2_paper = s2_data
                        s2_paper_id = s2_id
                        print(f"   📌 Matched input paper by position: {s2_id}")
                        break
                    elif s2_data["title"].lower().strip() == title_lower:
                        s2_paper = s2_data
                        s2_paper_id = s2_id
                        print(f"   📌 Matched input paper by title: {s2_id}")
                        break
            
            node = self._create_node_from_paper(paper)
            
            # Add S2 metadata if available
            if s2_paper:
                node.citation_count = s2_paper.get("citationCount", 0)
                node.venue = s2_paper.get("venue", "")
                if s2_paper.get("year"):
                    node.publication_date = str(s2_paper["year"])
                
                # Mark as input paper
                node.attributes["paper_source"] = "input"
                node.attributes["s2_paper_id"] = s2_paper_id
                
                s2_paper_id_to_node_id[s2_paper_id] = node.id
            
            graph.add_node(node)
        
        # Step 2: Create nodes for INTERMEDIATE papers (from Semantic Scholar)
        if include_intermediate:
            print(f"🔗 Creating nodes for {len(intermediate_paper_ids_s2)} intermediate papers...")
            for s2_id in intermediate_paper_ids_s2:
                if s2_id not in s2_papers:
                    continue
                
                s2_paper = s2_papers[s2_id]
                
                # Create a minimal ParsedPaper for intermediate paper
                from parsers.pdf_parser import ParsedPaper
                intermediate_paper = ParsedPaper(
                    paper_id=s2_id,
                    title=s2_paper.get("title", "Unknown"),
                    authors=[a.get("name", "") for a in s2_paper.get("authors", [])],
                    abstract=s2_paper.get("abstract", ""),
                    full_text=""  # We don't have full text for intermediate papers
                )
                
                node = self._create_node_from_paper(intermediate_paper)
                node.citation_count = s2_paper.get("citationCount", 0)
                node.venue = s2_paper.get("venue", "")
                if s2_paper.get("year"):
                    node.publication_date = str(s2_paper["year"])
                
                # Mark as intermediate paper
                node.attributes["paper_source"] = "intermediate"
                node.attributes["s2_paper_id"] = s2_id
                
                # Different visual for intermediate papers
                node.visual["opacity"] = 0.8
                node.visual["border_width"] = 1
                
                s2_paper_id_to_node_id[s2_id] = node.id
                graph.add_node(node)
                
                print(f"   + {s2_paper['title'][:60]}...")
        
        # Step 3: Create edges from citation data
        print(f"🔗 Creating edges from citation data...")
        print(f"   citation_network keys: {list(citation_network.keys())}")
        print(f"   citations in network: {len(citation_network.get('citations', []))}")
        if len(citation_network.get('citations', [])) > 0:
            print(f"   First citation: {citation_network.get('citations', [])[0]}")
        
        edges_created = 0
        for citation in citation_network.get("citations", []):
            from_s2_id = citation["from"]
            to_s2_id = citation["to"]
            
            # Map to our node IDs
            from_node_id = s2_paper_id_to_node_id.get(from_s2_id)
            to_node_id = s2_paper_id_to_node_id.get(to_s2_id)
            
            if from_node_id and to_node_id:
                edge = CitationEdge(
                    from_paper=from_node_id,
                    to_paper=to_node_id,
                    contribution_type="reference",
                    strength=0.5
                )
                graph.add_edge(edge)
                edges_created += 1
            elif edges_created < 3:  # Debug first few failures
                print(f"     SKIP edge: from_s2={from_s2_id[:20]}... to_s2={to_s2_id[:20]}... (from_node={from_node_id}, to_node={to_node_id})")
        
        print(f"✅ Created {edges_created} edges")
        
        # Update metadata
        graph.metadata = {
            "total_papers": len(graph.nodes),
            "input_papers": len(papers),
            "intermediate_papers": len(intermediate_paper_ids_s2) if include_intermediate else 0,
            "total_citations": len(graph.edges),
            "date_range": self._compute_date_range(papers),
            "source": "Semantic Scholar API"
        }
        
        return graph
    
    def _create_node_from_paper(self, paper: ParsedPaper) -> PaperNode:
        """Create a PaperNode from ParsedPaper"""
        return PaperNode(
            title=paper.title,
            authors=paper.authors,
            abstract=paper.abstract,
            full_text=paper.full_text,
            arxiv_id=getattr(paper, 'arxiv_id', None),
            publication_date=getattr(paper, 'publication_date', None)
        )
    
    def _extract_citations_from_text(self, text: str) -> List[Dict[str, str]]:
        """
        Extract citations from paper text
        This is a simplified version - in production, use proper citation parsing
        """
        citations = []
        
        # Simple pattern matching for citations [1], [Author 2023], etc.
        # In production, this should use a proper citation extraction library
        import re
        
        # Pattern for inline citations like [1] or [Author, 2023]
        citation_pattern = r'\[([^\]]+)\]'
        matches = re.finditer(citation_pattern, text)
        
        for match in matches:
            citation_text = match.group(1)
            # Extract context (surrounding sentences)
            start = max(0, match.start() - 200)
            end = min(len(text), match.end() + 200)
            context = text[start:end]
            
            citations.append({
                "citation": citation_text,
                "context": context,
                "title": "",  # Would be resolved through reference section
                "section": "unknown"
            })
        
        return citations
    
    def _classify_citation_type(self, context: str) -> str:
        """
        Classify citation type based on context
        Simple keyword-based classification
        """
        context_lower = context.lower()
        
        if any(word in context_lower for word in ["baseline", "compared to", "versus"]):
            return "baseline"
        elif any(word in context_lower for word in ["builds on", "extends", "based on"]):
            return "foundation"
        elif any(word in context_lower for word in ["improve", "enhance", "better than"]):
            return "extension"
        elif any(word in context_lower for word in ["dataset", "benchmark", "evaluation"]):
            return "dataset"
        elif any(word in context_lower for word in ["however", "limitation", "problem"]):
            return "critique"
        else:
            return "related"
    
    def _titles_match(self, title1: str, title2: str, threshold: float = 0.8) -> bool:
        """
        Check if two titles match (fuzzy matching)
        """
        # Simple substring matching for now
        title1 = title1.lower().strip()
        title2 = title2.lower().strip()
        
        if title1 == title2:
            return True
        
        # Check if one is substring of other
        if title1 in title2 or title2 in title1:
            return True
        
        return False
    
    def _compute_date_range(self, papers: List[ParsedPaper]) -> Dict[str, str]:
        """Compute date range of papers"""
        dates = []
        for paper in papers:
            if hasattr(paper, 'publication_date') and paper.publication_date:
                dates.append(paper.publication_date)
        
        if dates:
            return {
                "start": min(dates),
                "end": max(dates)
            }
        return {"start": "", "end": ""}
    
    def filter_graph(
        self,
        graph: ResearchGraph,
        filters: List[Dict[str, Any]]
    ) -> ResearchGraph:
        """
        Filter graph based on criteria
        
        Args:
            graph: Original graph
            filters: List of filter conditions
            
        Returns:
            Filtered graph
        """
        filtered_graph = ResearchGraph(
            name=f"{graph.name} (filtered)",
            layout=graph.layout
        )
        
        # Filter nodes
        visible_node_ids = set()
        for node in graph.nodes:
            if self._node_matches_filters(node, filters):
                filtered_graph.add_node(node)
                visible_node_ids.add(node.id)
        
        # Filter edges (only include if both endpoints are visible)
        for edge in graph.edges:
            if edge.from_paper in visible_node_ids and edge.to_paper in visible_node_ids:
                filtered_graph.add_edge(edge)
        
        return filtered_graph
    
    def _node_matches_filters(self, node: PaperNode, filters: List[Dict[str, Any]]) -> bool:
        """Check if node matches filter conditions"""
        for filter_cond in filters:
            field = filter_cond.get("field")
            operator = filter_cond.get("operator")
            value = filter_cond.get("value")
            
            # Get field value from node
            if field in node.attributes:
                node_value = node.attributes[field]
            elif hasattr(node, field):
                node_value = getattr(node, field)
            else:
                return False
            
            # Apply operator
            if operator == "==":
                if node_value != value:
                    return False
            elif operator == "!=":
                if node_value == value:
                    return False
            elif operator == ">":
                if not (node_value > value):
                    return False
            elif operator == ">=":
                if not (node_value >= value):
                    return False
            elif operator == "<":
                if not (node_value < value):
                    return False
            elif operator == "<=":
                if not (node_value <= value):
                    return False
            elif operator == "contains":
                if value.lower() not in str(node_value).lower():
                    return False
        
        return True
    
    def compute_shortest_path(
        self,
        graph: ResearchGraph,
        source_id: str,
        target_id: str
    ) -> List[str]:
        """
        Compute shortest path between two papers
        
        Returns:
            List of paper IDs forming the path
        """
        # Build NetworkX graph
        G = nx.DiGraph()
        for edge in graph.edges:
            G.add_edge(edge.from_paper, edge.to_paper)
        
        try:
            path = nx.shortest_path(G, source_id, target_id)
            return path
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return []
    
    def apply_visual_encoding(
        self,
        graph: ResearchGraph,
        color_by: Optional[str] = None,
        size_by: Optional[str] = None,
        shape_by: Optional[str] = None
    ) -> ResearchGraph:
        """
        Apply visual encodings to graph nodes
        
        Args:
            graph: Graph to modify
            color_by: Attribute to use for color encoding
            size_by: Attribute to use for size encoding
            shape_by: Attribute to use for shape encoding
            
        Returns:
            Modified graph with visual encodings
        """
        # Color encoding
        if color_by:
            color_map = self._generate_color_map(graph, color_by)
            for node in graph.nodes:
                value = node.attributes.get(color_by)
                if value and value in color_map:
                    node.visual["color"] = color_map[value]
        
        # Size encoding
        if size_by:
            sizes = self._generate_size_map(graph, size_by)
            for i, node in enumerate(graph.nodes):
                node.visual["size"] = sizes.get(node.id, 20)
        
        # Shape encoding
        if shape_by:
            shape_map = self._generate_shape_map(graph, shape_by)
            for node in graph.nodes:
                value = node.attributes.get(shape_by)
                if value and value in shape_map:
                    node.visual["shape"] = shape_map[value]
        
        return graph
    
    def _generate_color_map(self, graph: ResearchGraph, attribute: str) -> Dict[str, str]:
        """Generate color mapping for categorical attribute"""
        # Collect unique values
        values = set()
        for node in graph.nodes:
            value = node.attributes.get(attribute)
            if value:
                values.add(value)
        
        # Assign colors
        colors = [
            "#FF6B6B", "#4ECDC4", "#95E1D3", "#F38181",
            "#45B7D1", "#FFA07A", "#98D8C8", "#F7DC6F"
        ]
        
        color_map = {}
        for i, value in enumerate(sorted(values)):
            color_map[value] = colors[i % len(colors)]
        
        return color_map
    
    def _generate_size_map(self, graph: ResearchGraph, attribute: str) -> Dict[str, float]:
        """Generate size mapping for numeric attribute"""
        # Collect values
        values = {}
        for node in graph.nodes:
            value = node.attributes.get(attribute)
            if value is not None and isinstance(value, (int, float)):
                values[node.id] = float(value)
        
        if not values:
            return {}
        
        # Normalize to size range [10, 50]
        min_val = min(values.values())
        max_val = max(values.values())
        
        if max_val == min_val:
            return {node_id: 20 for node_id in values.keys()}
        
        size_map = {}
        for node_id, value in values.items():
            normalized = (value - min_val) / (max_val - min_val)
            size_map[node_id] = 10 + normalized * 40
        
        return size_map
    
    def _generate_shape_map(self, graph: ResearchGraph, attribute: str) -> Dict[str, str]:
        """Generate shape mapping for categorical attribute"""
        shapes = {
            "architecture": "round-rectangle",
            "algorithm": "triangle",
            "dataset": "diamond",
            "analysis": "pentagon",
            "default": "ellipse"
        }
        
        # Collect unique values
        values = set()
        for node in graph.nodes:
            value = node.attributes.get(attribute)
            if value:
                values.add(value)
        
        # Assign shapes
        shape_map = {}
        available_shapes = ["ellipse", "round-rectangle", "triangle", "diamond", "pentagon"]
        
        for i, value in enumerate(sorted(values)):
            shape_map[value] = available_shapes[i % len(available_shapes)]
        
        return shape_map
