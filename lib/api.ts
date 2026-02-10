/**
 * API client for interacting with the Citation Graph Visualizer backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface PaperNode {
  id: string;
  title: string;
  authors: string[];
  publication_date?: string;
  venue?: string;
  abstract: string;
  citation_count?: number;
  attributes: Record<string, any>;
  visual: {
    color: string;
    size: number;
    shape: string;
    opacity: number;
  };
}

export interface CitationEdge {
  id: string;
  from_paper: string;
  to_paper: string;
  contribution_type: string;
  strength: number;
  context: string;
  delta_description?: string;
  visual: {
    color: string;
    thickness: number;
    style: string;
    opacity: number;
  };
}

export interface ResearchGraph {
  id: string;
  name: string;
  nodes: PaperNode[];
  edges: CitationEdge[];
  metadata: Record<string, any>;
  extractors_applied: string[];
}

export interface BuildGraphResponse {
  graph_id: string;
  graph: ResearchGraph;
  stats: {
    total_papers: number;
    intermediate_papers_added: number;
    total_citations: number;
  };
}

export interface ExtractorConfig {
  type: 'standard' | 'custom';
  name?: string;
  query?: string;
}

export interface FilterCondition {
  field: string;
  operator: string;
  value: any;
}

// ── Dynamic schema types ──────────────────────────────
export interface AttributeSchema {
  key: string;
  label: string;
  description: string;
  value_type: string;
  suggested_values: string[];
  color_palette: string[];
}

export interface GeneratedSchema {
  topic: string;
  topic_description: string;
  attributes: AttributeSchema[];
}

export interface GenerateSchemaResponse {
  graph_id: string;
  schema: GeneratedSchema;
}

export interface ExtractDynamicResponse {
  graph_id: string;
  schema: GeneratedSchema;
  results: Record<string, Record<string, string>>;
  graph: ResearchGraph;
  stats: {
    papers_processed: number;
    attributes_extracted: number;
  };
}

export class GraphAPI {
  /**
   * Build a graph from paper identifiers (ArXiv/DOI) or uploaded PDF files
   */
  static async buildGraph(
    papers: Array<{type: 'arxiv' | 'doi' | 'pdf', value: string} | File>,
    options?: {
      includeIntermediate?: boolean;
      maxDepth?: number;
    }
  ): Promise<BuildGraphResponse> {
    const formData = new FormData();
    
    // Separate files from identifiers
    const files: File[] = [];
    const identifiers: Array<{type: string, value: string}> = [];
    
    for (const paper of papers) {
      if (paper instanceof File) {
        files.push(paper);
      } else {
        identifiers.push(paper);
      }
    }
    
    // Add files to form data
    files.forEach((file) => {
      formData.append('files', file);
    });
    
    // Add identifiers as JSON string
    if (identifiers.length > 0) {
      formData.append('paper_identifiers', JSON.stringify(identifiers));
    }

    const url = new URL(`${API_BASE_URL}/api/graph/build`);
    if (options?.includeIntermediate) {
      url.searchParams.set('include_intermediate', 'true');
    }
    if (options?.maxDepth) {
      url.searchParams.set('max_depth', options.maxDepth.toString());
    }

    const response = await fetch(url.toString(), {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Failed to build graph: ${errorText}`);
    }

    return response.json();
  }

  /**
   * Extract features from papers in graph
   */
  static async extractFeatures(
    graphId: string,
    extractors: ExtractorConfig[]
  ): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/api/graph/extract`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        graph_id: graphId,
        extractors,
      }),
    });

    if (!response.ok) {
      throw new Error(`Failed to extract features: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Filter graph based on criteria
   */
  static async filterGraph(
    graphId: string,
    filters: FilterCondition[],
    logic: 'AND' | 'OR' = 'AND'
  ): Promise<{ filtered_graph: ResearchGraph; match_count: number }> {
    const response = await fetch(`${API_BASE_URL}/api/graph/filter`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        graph_id: graphId,
        filters,
        logic,
      }),
    });

    if (!response.ok) {
      throw new Error(`Failed to filter graph: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Apply visual encodings to graph
   */
  static async visualizeGraph(
    graphId: string,
    encoding: {
      color?: { attribute: string; scheme?: string };
      size?: { attribute: string; scale?: string };
      shape?: { attribute: string };
    }
  ): Promise<{ styled_graph: ResearchGraph }> {
    const response = await fetch(`${API_BASE_URL}/api/graph/visualize`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        graph_id: graphId,
        encoding,
      }),
    });

    if (!response.ok) {
      throw new Error(`Failed to visualize graph: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Find paths between papers
   */
  static async findPath(
    graphId: string,
    sourcePaperId: string,
    targetPaperId: string
  ): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/api/graph/path`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        graph_id: graphId,
        source_paper_id: sourcePaperId,
        target_paper_id: targetPaperId,
      }),
    });

    if (!response.ok) {
      throw new Error(`Failed to find path: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get graph by ID
   */
  static async getGraph(graphId: string): Promise<ResearchGraph> {
    const response = await fetch(`${API_BASE_URL}/api/graph/${graphId}`);

    if (!response.ok) {
      throw new Error(`Failed to get graph: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Extract edge innovations using LLM
   */
  static async extractEdgeInnovations(
    graphId: string,
    maxParallel: number = 5
  ): Promise<{ graph: ResearchGraph; stats: { edges_processed: number; total_edges: number } }> {
    const response = await fetch(`${API_BASE_URL}/api/graph/extract-edges`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        graph_id: graphId,
        max_parallel: maxParallel,
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Failed to extract edge innovations: ${errorText}`);
    }

    return response.json();
  }

  /**
   * Extract innovation for a single edge using LLM
   */
  static async extractSingleEdge(
    graphId: string,
    edgeId: string
  ): Promise<{ edge: CitationEdge; result: { short_label: string; full_insight: string } }> {
    const response = await fetch(`${API_BASE_URL}/api/graph/extract-single-edge`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        graph_id: graphId,
        edge_id: edgeId,
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Failed to extract edge: ${errorText}`);
    }

    return response.json();
  }

  /**
   * List all graphs
   */
  static async listGraphs(): Promise<any[]> {
    const response = await fetch(`${API_BASE_URL}/api/graphs`);

    if (!response.ok) {
      throw new Error(`Failed to list graphs: ${response.statusText}`);
    }

    const data = await response.json();
    return data.graphs;
  }

  // ── Dynamic schema endpoints ──────────────────────────────

  /**
   * Generate a custom extraction schema based on the paper topics.
   * The LLM analyses the papers and produces 5-7 attributes tailored
   * to the specific research area.
   */
  static async generateSchema(graphId: string): Promise<GenerateSchemaResponse> {
    const response = await fetch(`${API_BASE_URL}/api/graph/generate-schema`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ graph_id: graphId }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Failed to generate schema: ${errorText}`);
    }

    return response.json();
  }

  /**
   * Extract attributes from all papers using the generated schema.
   * Optionally restrict to a subset of attribute keys.
   */
  static async extractDynamic(
    graphId: string,
    attributeKeys: string[] = [],
  ): Promise<ExtractDynamicResponse> {
    const response = await fetch(`${API_BASE_URL}/api/graph/extract-dynamic`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        graph_id: graphId,
        attribute_keys: attributeKeys,
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Failed to extract dynamic attributes: ${errorText}`);
    }

    return response.json();
  }

  /**
   * Get the schema for a graph (if previously generated).
   */
  static async getSchema(graphId: string): Promise<GeneratedSchema> {
    const response = await fetch(`${API_BASE_URL}/api/graph/${graphId}/schema`);

    if (!response.ok) {
      throw new Error(`Failed to get schema: ${response.statusText}`);
    }

    return response.json();
  }
}
