"""
FastAPI application for Citation Graph Visualizer backend
"""
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import io
import sys
import os
import time

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from graph.models import ResearchGraph
from graph.builder import GraphBuilder
from graph.clustering import get_clusterer
from parsers.pdf_parser import PaperParser
from extractors.architecture_extractor import ArchitectureExtractor
from extractors.contribution_extractor import ContributionExtractor
from extractors.survey_extractor import get_survey_extractor
from extractors.schema_generator import (
    get_schema_generator,
    get_dynamic_extractor,
    GeneratedSchema,
    AttributeSchema,
)
from api.semantic_scholar import get_semantic_scholar_api
from api.arxiv_client import get_arxiv_client

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
schemas_store: Dict[str, GeneratedSchema] = {}  # graph_id -> generated schema

# Initialize services
graph_builder = GraphBuilder()
pdf_parser = PaperParser()


# Request/Response Models
class PaperIdentifier(BaseModel):
    type: str  # 'arxiv', 'doi', or 'pdf'
    value: str  # arxiv ID, DOI, or filename


class BuildGraphRequest(BaseModel):
    papers: List[PaperIdentifier] = []
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


class ClusterRequest(BaseModel):
    graph_id: str
    method: str = "content"  # 'content', 'citations', 'hybrid'
    n_clusters: int = 5
    content_weight: float = 0.7
    citation_weight: float = 0.3


class ExtractEdgesRequest(BaseModel):
    graph_id: str
    max_parallel: int = 5


class ExtractSingleEdgeRequest(BaseModel):
    graph_id: str
    edge_id: str


class GenerateSchemaRequest(BaseModel):
    graph_id: str


class ExtractDynamicRequest(BaseModel):
    graph_id: str
    attribute_keys: List[str] = []  # empty = extract all schema attributes


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
    files: List[UploadFile] = File(default=[]),
    paper_identifiers: Optional[str] = Form(default=None),
    include_intermediate: bool = False,
    max_depth: int = 1
):
    """
    Build citation graph from paper identifiers (ArXiv IDs, DOIs) or uploaded PDF files
    """
    try:
        print(f"📚 Starting graph build...")
        
        papers = []
        paper_titles = []
        
        # Handle paper identifiers (ArXiv/DOI)
        arxiv_id_map = {}  # Map title to ArXiv ID
        if paper_identifiers:
            import json
            identifiers = json.loads(paper_identifiers)
            print(f"📋 Processing {len(identifiers)} paper identifiers")
            
            arxiv_client = get_arxiv_client()
            s2_api = get_semantic_scholar_api()
            
            for identifier in identifiers:
                id_type = identifier.get('type')
                value = identifier.get('value')
                
                if id_type == 'arxiv':
                    print(f"📄 Fetching ArXiv paper: {value}")
                    arxiv_data = arxiv_client.get_paper_by_id(value)
                    
                    if arxiv_data:
                        # Create ParsedPaper from ArXiv data
                        from parsers.pdf_parser import ParsedPaper
                        paper = ParsedPaper(
                            paper_id=arxiv_data['arxiv_id'],
                            title=arxiv_data['title'],
                            authors=arxiv_data['authors'],
                            abstract=arxiv_data['abstract'],
                            full_text=arxiv_data['abstract'],  # Use abstract as text
                            metadata={
                                'year': arxiv_data.get('year'),
                                'arxiv_url': arxiv_data.get('arxiv_url'),
                                'pdf_url': arxiv_data.get('pdf_url'),
                                'categories': arxiv_data.get('categories', []),
                                'arxiv_id': value  # Store ArXiv ID
                            }
                        )
                        papers.append(paper)
                        paper_titles.append(arxiv_data['title'])
                        arxiv_id_map[arxiv_data['title']] = value
                    else:
                        # Fallback: use Semantic Scholar to get paper by ArXiv ID
                        print(f"⚠️  ArXiv failed for {value}, falling back to Semantic Scholar...")
                        s2_paper = s2_api.search_paper(value, arxiv_id=value)
                        
                        if s2_paper:
                            from parsers.pdf_parser import ParsedPaper
                            paper = ParsedPaper(
                                paper_id=value,
                                title=s2_paper['title'],
                                authors=[a.get('name', '') for a in s2_paper.get('authors', [])],
                                abstract=s2_paper.get('abstract', '') or '',
                                full_text=s2_paper.get('abstract', '') or '',
                                metadata={
                                    'year': s2_paper.get('year'),
                                    'arxiv_id': value,
                                    'paper_id': s2_paper.get('paperId')
                                }
                            )
                            papers.append(paper)
                            paper_titles.append(s2_paper['title'])
                            arxiv_id_map[s2_paper['title']] = value
                            print(f"✅ Got paper from S2: {s2_paper['title'][:60]}...")
                        else:
                            print(f"❌ Could not find paper {value} on ArXiv or Semantic Scholar")
                    
                    time.sleep(0.3)  # Rate limiting
                
                elif id_type == 'doi':
                    print(f"📄 Searching for DOI paper: {value}")
                    # Use Semantic Scholar to search by DOI
                    s2_paper = s2_api.search_paper(f"DOI:{value}")
                    
                    if s2_paper:
                        from parsers.pdf_parser import ParsedPaper
                        paper = ParsedPaper(
                            paper_id=s2_paper.get('paperId', value.replace('/', '_')),
                            title=s2_paper['title'],
                            authors=[a.get('name', '') for a in s2_paper.get('authors', [])],
                            abstract=s2_paper.get('abstract', ''),
                            full_text=s2_paper.get('abstract', ''),
                            metadata={
                                'year': s2_paper.get('year'),
                                'doi': value,
                                'paper_id': s2_paper.get('paperId')
                            }
                        )
                        papers.append(paper)
                        paper_titles.append(s2_paper['title'])
                    
                    time.sleep(0.3)
        
        # Handle PDF files
        if files:
            print(f"📚 Processing {len(files)} PDF files")
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
                    paper_titles.append(paper.title)
                finally:
                    # Clean up temp file
                    import os
                    os.unlink(tmp_path)
        
        if not papers:
            raise HTTPException(status_code=400, detail="No papers provided")
        
        print(f"✅ Parsed {len(papers)} papers")
        
        # Build citation network using Semantic Scholar
        print("🔍 Fetching citation data from Semantic Scholar...")
        s2_api = get_semantic_scholar_api()
        citation_network = s2_api.build_citation_network(
            paper_titles,
            max_intermediate_papers=100 if include_intermediate else 0,
            arxiv_ids=arxiv_id_map
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


@app.post("/api/graph/cluster")
async def cluster_graph(request: ClusterRequest):
    """
    Cluster papers in graph by content or citation structure
    """
    try:
        graph = graphs_store.get(request.graph_id)
        if not graph:
            raise HTTPException(status_code=404, detail="Graph not found")
        
        print(f"🔍 Clustering graph: {request.graph_id} (method: {request.method})")
        
        clusterer = get_clusterer()
        
        if request.method == "content":
            graph = clusterer.cluster_by_content(graph, n_clusters=request.n_clusters)
        elif request.method == "citations":
            graph = clusterer.cluster_by_citations(graph, n_clusters=request.n_clusters)
        elif request.method == "hybrid":
            graph = clusterer.cluster_hybrid(
                graph,
                n_clusters=request.n_clusters,
                content_weight=request.content_weight,
                citation_weight=request.citation_weight
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unknown clustering method: {request.method}")
        
        # Get cluster summaries
        summaries = clusterer.get_cluster_summaries(graph, top_terms=10)
        
        # Update stored graph
        graphs_store[request.graph_id] = graph
        
        return {
            "graph": graph.to_dict(),
            "clusters": summaries,
            "stats": {
                "n_clusters": len(summaries),
                "method": request.method
            }
        }
    
    except Exception as e:
        print(f"❌ Error clustering graph: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/graph/extract-edges")
async def extract_edge_innovations(request: ExtractEdgesRequest):
    """
    Extract innovation flow for all edges using LLM.
    For each citation edge, the LLM identifies what specific idea/method
    from the cited paper was adopted by the citing paper.
    """
    try:
        graph = graphs_store.get(request.graph_id)
        if not graph:
            raise HTTPException(status_code=404, detail="Graph not found")

        print(f"🔍 Extracting edge innovations for graph: {request.graph_id}")
        print(f"   Edges to process: {len(graph.edges)}")

        from extractors.edge_extractor import get_edge_extractor
        extractor = get_edge_extractor()

        processed = extractor.extract_for_graph(
            graph,
            max_parallel=request.max_parallel,
        )

        # Mark extractor as applied
        if "edge_innovations" not in graph.extractors_applied:
            graph.extractors_applied.append("edge_innovations")

        print(f"✅ Edge innovations extracted: {processed} edges processed")

        return {
            "graph": graph.to_dict(),
            "stats": {
                "edges_processed": processed,
                "total_edges": len(graph.edges),
            },
        }

    except Exception as e:
        print(f"❌ Error extracting edge innovations: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/graph/extract-single-edge")
async def extract_single_edge_innovation(request: ExtractSingleEdgeRequest):
    """
    Extract innovation insight for a single edge using LLM.
    Uses full paper text when available.
    """
    try:
        graph = graphs_store.get(request.graph_id)
        if not graph:
            raise HTTPException(status_code=404, detail="Graph not found")

        print(f"🔍 Extracting single edge: {request.edge_id}")

        from extractors.edge_extractor import get_edge_extractor
        extractor = get_edge_extractor()

        result = extractor.extract_single_by_id(graph, request.edge_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Edge not found or missing paper data")

        # Find the updated edge to return
        updated_edge = None
        for edge in graph.edges:
            if edge.id == request.edge_id:
                updated_edge = edge.to_dict()
                break

        print(f"✅ Single edge extracted: {result['short_label']}")

        return {
            "edge": updated_edge,
            "result": result,
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error extracting single edge: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/survey/extract")
async def extract_survey(file: UploadFile = File(...)):
    """
    Extract ground truth data from a survey/review paper PDF
    """
    try:
        print(f"📚 Extracting ground truth from survey: {file.filename}")
        
        # Read and parse PDF
        content = await file.read()
        
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        
        try:
            # Parse PDF
            parsed_paper = pdf_parser.parse_pdf(tmp_path, file.filename.replace('.pdf', ''))
            
            # Extract ground truth
            survey_extractor = get_survey_extractor()
            ground_truth = survey_extractor.extract_from_survey(
                parsed_paper.full_text,
                parsed_paper.title
            )
            
            # Convert to evaluation format
            eval_data = survey_extractor.convert_to_evaluation_format(ground_truth)
            
            print(f"✅ Extracted ground truth:")
            print(f"   - Categories: {len(ground_truth.categories)}")
            print(f"   - Papers: {len(ground_truth.papers)}")
            print(f"   - Relationships: {len(ground_truth.relationships)}")
            
            return {
                "survey_title": ground_truth.survey_title,
                "ground_truth": eval_data,
                "stats": {
                    "n_categories": len(ground_truth.categories),
                    "n_papers": len(ground_truth.papers),
                    "n_relationships": len(ground_truth.relationships)
                }
            }
            
        finally:
            import os
            os.unlink(tmp_path)
    
    except Exception as e:
        print(f"❌ Error extracting survey: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/graph/generate-schema")
async def generate_schema(request: GenerateSchemaRequest):
    """
    Analyse the papers in the graph, detect the research topic,
    and generate 5-7 custom extraction attributes tailored to that topic.
    """
    try:
        graph = graphs_store.get(request.graph_id)
        if not graph:
            raise HTTPException(status_code=404, detail="Graph not found")

        print(f"Generating custom schema for graph: {request.graph_id}")

        # Build ParsedPaper list from graph nodes
        from parsers.pdf_parser import ParsedPaper
        papers = [
            ParsedPaper(
                paper_id=node.id,
                title=node.title,
                authors=node.authors,
                abstract=node.abstract,
                full_text=node.full_text or "",
            )
            for node in graph.nodes
        ]

        generator = get_schema_generator()
        schema = generator.generate(papers)

        # Store schema for later extraction
        schemas_store[request.graph_id] = schema

        print(f"Schema generated: {schema.topic} ({len(schema.attributes)} attributes)")

        return {
            "graph_id": request.graph_id,
            "schema": schema.to_dict(),
        }

    except Exception as e:
        print(f"Error generating schema: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/graph/extract-dynamic")
async def extract_dynamic(request: ExtractDynamicRequest):
    """
    Extract paper attributes according to the previously generated schema.
    Optionally restrict to a subset of attribute keys.
    """
    try:
        graph = graphs_store.get(request.graph_id)
        if not graph:
            raise HTTPException(status_code=404, detail="Graph not found")

        schema = schemas_store.get(request.graph_id)
        if not schema:
            raise HTTPException(
                status_code=400,
                detail="No schema generated yet. Call /api/graph/generate-schema first.",
            )

        # If caller specified a subset of keys, filter the schema
        if request.attribute_keys:
            from extractors.schema_generator import GeneratedSchema
            filtered_attrs = [
                a for a in schema.attributes if a.key in request.attribute_keys
            ]
            work_schema = GeneratedSchema(
                topic=schema.topic,
                topic_description=schema.topic_description,
                attributes=filtered_attrs,
            )
        else:
            work_schema = schema

        print(f"Extracting {len(work_schema.attributes)} attributes for {len(graph.nodes)} papers...")

        extractor = get_dynamic_extractor()
        results = extractor.extract_for_graph(graph, work_schema)

        # Mark schema extraction as applied
        if "dynamic_schema" not in graph.extractors_applied:
            graph.extractors_applied.append("dynamic_schema")

        print(f"Dynamic extraction complete!")

        return {
            "graph_id": request.graph_id,
            "schema": schema.to_dict(),
            "results": results,
            "graph": graph.to_dict(),
            "stats": {
                "papers_processed": len(results),
                "attributes_extracted": len(work_schema.attributes),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error extracting dynamic attributes: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/graph/{graph_id}/schema")
async def get_schema(graph_id: str):
    """Get the generated schema for a graph."""
    schema = schemas_store.get(graph_id)
    if not schema:
        raise HTTPException(status_code=404, detail="No schema generated for this graph")
    return schema.to_dict()


if __name__ == "__main__":
    import uvicorn
    print("Starting Citation Graph Visualizer API...")
    print("API will be available at: http://localhost:8000")
    print("API docs at: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
