"""
FastAPI application for Citation Graph Visualizer backend
"""
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import io
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from graph.models import ResearchGraph
from graph.builder import GraphBuilder
from parsers.pdf_parser import PaperParser
from extractors.architecture_extractor import ArchitectureExtractor
from extractors.contribution_extractor import ContributionExtractor
from api.semantic_scholar import get_semantic_scholar_api

# Initialize FastAPI app
app = FastAPI(
    title="Citation Graph Visualizer API",
    description="API for building and analyzing citation graphs",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state (in production, use proper database)
graphs_store: Dict[str, ResearchGraph] = {}

# Initialize services
graph_builder = GraphBuilder()
pdf_parser = PaperParser()


# Request/Response Models
class BuildGraphRequest(BaseModel):
    include_intermediate_papers: bool = False
    max_intermediate_depth: int = 1
    min_citation_strength: float = 0.2


class ExtractRequest(BaseModel):
    graph_id: str
    extractors: List[Dict[str, Any]]


class FilterRequest(BaseModel):
    graph_id: str
    filters: List[Dict[str, Any]]
    logic: str = "AND"


class VisualizeRequest(BaseModel):
    graph_id: str
    encoding: Dict[str, Any]


class PathRequest(BaseModel):
    graph_id: str
    source_paper_id: str
    target_paper_id: str
    ranking: str = "shortest"


# Endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Citation Graph Visualizer API",
        "version": "1.0.0",
        "endpoints": {
            "build": "/api/graph/build",
            "extract": "/api/graph/extract",
            "filter": "/api/graph/filter",
            "visualize": "/api/graph/visualize",
            "path": "/api/graph/path"
        }
    }


@app.post("/api/graph/build")
async def build_graph(
    files: List[UploadFile] = File(...),
    include_intermediate: bool = False,
    max_depth: int = 1
):
    """
    Build citation graph from uploaded PDF files
    """
    try:
        print(f"📚 Received {len(files)} files for graph building")
        
        # Parse all papers
        papers = []
        for file in files:
            print(f"📄 Parsing: {file.filename}")
            content = await file.read()
            
            # Save temporarily to parse
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                tmp.write(content)
                tmp_path = tmp.name
            
            try:
                # Generate paper ID from filename
                paper_id = file.filename.replace('.pdf', '').replace(' ', '_')
                
                # Parse PDF
                paper = pdf_parser.parse_pdf(tmp_path, paper_id)
                papers.append(paper)
            finally:
                # Clean up temp file
                import os
                os.unlink(tmp_path)
        
        print(f"✅ Parsed {len(papers)} papers")
        
        # Get paper titles
        paper_titles = [p.title for p in papers]
        
        # Build citation network using Semantic Scholar
        print("🔍 Fetching citation data from Semantic Scholar...")
        s2_api = get_semantic_scholar_api()
        citation_network = s2_api.build_citation_network(
            paper_titles,
            max_intermediate_papers=100 if include_intermediate else 0
        )
        
        # Build graph
        print("🔨 Building citation graph...")
        graph = graph_builder.build_from_papers_with_citations(
            papers,
            citation_network,
            include_intermediate=include_intermediate,
            max_depth=max_depth
        )
        
        # Store graph
        graphs_store[graph.id] = graph
        
        print(f"✅ Graph built: {graph.id}")
        print(f"   - Nodes: {len(graph.nodes)}")
        print(f"   - Edges: {len(graph.edges)}")
        
        return {
            "graph_id": graph.id,
            "graph": graph.to_dict(),
            "stats": {
                "total_papers": len(graph.nodes),
                "input_papers": graph.metadata.get("input_papers", len(papers)),
                "intermediate_papers_added": graph.metadata.get("intermediate_papers", 0),
                "total_citations": len(graph.edges),
                "date_range": graph.metadata.get("date_range", {})
            }
        }
    
    except Exception as e:
        print(f"❌ Error building graph: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/graph/extract")
async def extract_features(request: ExtractRequest):
    """
    Extract features from papers in graph
    """
    try:
        graph = graphs_store.get(request.graph_id)
        if not graph:
            raise HTTPException(status_code=404, detail="Graph not found")
        
        print(f"🔍 Extracting features for graph: {request.graph_id}")
        
        results = {}
        
        # Initialize extractors
        architecture_extractor = ArchitectureExtractor()
        contribution_extractor = ContributionExtractor()
        
        for node in graph.nodes:
            print(f"📄 Processing: {node.title[:60]}...")
            
            # Create ParsedPaper-like object
            from parsers.pdf_parser import ParsedPaper
            paper = ParsedPaper(
                paper_id=node.id,
                title=node.title,
                authors=node.authors,
                abstract=node.abstract,
                full_text=node.full_text or ""
            )
            
            node_results = {}
            
            # Run requested extractors
            for extractor_config in request.extractors:
                extractor_type = extractor_config.get("type")
                extractor_name = extractor_config.get("name")
                
                if extractor_type == "standard":
                    if extractor_name == "architecture":
                        archs = architecture_extractor.extract(paper)
                        node_results["architecture"] = [a.to_dict() for a in archs]
                        
                        # Add to node attributes
                        if archs:
                            node.attributes["architecture_type"] = archs[0].architecture_type
                            node.attributes["architecture_name"] = archs[0].name
                    
                    elif extractor_name == "contributions":
                        contribs = contribution_extractor.extract(paper)
                        node_results["contributions"] = [c.to_dict() for c in contribs]
                        
                        # Add to node attributes
                        if contribs:
                            node.attributes["contribution_types"] = [
                                c.contribution_type for c in contribs
                            ]
            
            results[node.id] = node_results
        
        # Update graph
        graph.extractors_applied.extend([
            e.get("name") for e in request.extractors if e.get("type") == "standard"
        ])
        
        print(f"✅ Extraction complete!")
        
        return {
            "extraction_id": graph.id,
            "status": "completed",
            "results": results,
            "stats": {
                "papers_processed": len(graph.nodes),
                "cache_hits": 0,
                "new_extractions": len(results)
            }
        }
    
    except Exception as e:
        print(f"❌ Error extracting features: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/graph/filter")
async def filter_graph(request: FilterRequest):
    """
    Filter graph based on criteria
    """
    try:
        graph = graphs_store.get(request.graph_id)
        if not graph:
            raise HTTPException(status_code=404, detail="Graph not found")
        
        print(f"🔍 Filtering graph: {request.graph_id}")
        
        filtered_graph = graph_builder.filter_graph(graph, request.filters)
        
        return {
            "filtered_graph": filtered_graph.to_dict(),
            "match_count": len(filtered_graph.nodes)
        }
    
    except Exception as e:
        print(f"❌ Error filtering graph: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/graph/visualize")
async def visualize_graph(request: VisualizeRequest):
    """
    Apply visual encodings to graph
    """
    try:
        graph = graphs_store.get(request.graph_id)
        if not graph:
            raise HTTPException(status_code=404, detail="Graph not found")
        
        print(f"🎨 Applying visual encodings to graph: {request.graph_id}")
        
        encoding = request.encoding
        
        # Apply visual encodings
        graph = graph_builder.apply_visual_encoding(
            graph,
            color_by=encoding.get("color", {}).get("attribute"),
            size_by=encoding.get("size", {}).get("attribute"),
            shape_by=encoding.get("shape", {}).get("attribute")
        )
        
        return {
            "styled_graph": graph.to_dict()
        }
    
    except Exception as e:
        print(f"❌ Error visualizing graph: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/graph/path")
async def find_path(request: PathRequest):
    """
    Find paths between papers
    """
    try:
        graph = graphs_store.get(request.graph_id)
        if not graph:
            raise HTTPException(status_code=404, detail="Graph not found")
        
        print(f"🔍 Finding path in graph: {request.graph_id}")
        
        path = graph_builder.compute_shortest_path(
            graph,
            request.source_paper_id,
            request.target_paper_id
        )
        
        if not path:
            return {"paths": []}
        
        # Build path details
        path_edges = []
        for i in range(len(path) - 1):
            from_id = path[i]
            to_id = path[i + 1]
            
            # Find edge
            edge = None
            for e in graph.edges:
                if e.from_paper == from_id and e.to_paper == to_id:
                    edge = e
                    break
            
            if edge:
                path_edges.append({
                    "from": from_id,
                    "to": to_id,
                    "label": edge.contribution_type,
                    "context": edge.context
                })
        
        return {
            "paths": [
                {
                    "papers": path,
                    "edges": path_edges,
                    "length": len(path) - 1
                }
            ]
        }
    
    except Exception as e:
        print(f"❌ Error finding path: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/graph/{graph_id}")
async def get_graph(graph_id: str):
    """Get graph by ID"""
    graph = graphs_store.get(graph_id)
    if not graph:
        raise HTTPException(status_code=404, detail="Graph not found")
    
    return graph.to_dict()


@app.get("/api/graphs")
async def list_graphs():
    """List all graphs"""
    return {
        "graphs": [
            {
                "id": g.id,
                "name": g.name,
                "created_at": g.created_at,
                "node_count": len(g.nodes),
                "edge_count": len(g.edges)
            }
            for g in graphs_store.values()
        ]
    }


if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Citation Graph Visualizer API...")
    print("📍 API will be available at: http://localhost:8000")
    print("📖 API docs at: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
