/**
 * API client for interacting with the Citation Graph Visualizer backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface PaperNode {
  id: string;
  title: string;
  authors: string[];
  publication_date?: string;
  venue: string;
  abstract: string;
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

export class GraphAPI {
  /**
   * Build a graph from uploaded PDF files
   */
  static async buildGraph(
    files: File[],
    options?: {
      includeIntermediate?: boolean;
      maxDepth?: number;
    }
  ): Promise<BuildGraphResponse> {
    const formData = new FormData();
    
    files.forEach((file) => {
      formData.append('files', file);
    });

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
      throw new Error(`Failed to build graph: ${response.statusText}`);
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
}
