'use client';

import React, { useEffect, useRef, useState } from 'react';
import cytoscape, { Core, NodeSingular, EdgeSingular } from 'cytoscape';
import type { ResearchGraph, PaperNode, CitationEdge } from '@/lib/api';
import { getModernCytoscapeStyle, LAYOUT_CONFIGS, COLOR_PALETTE } from '@/lib/graph-styles';

interface GraphCanvasProps {
  graph: ResearchGraph | null;
  onNodeSelect?: (nodeId: string) => void;
  onEdgeSelect?: (edgeId: string) => void;
  layout?: 'force' | 'hierarchical' | 'circular' | 'grid';
}

export default function GraphCanvas({
  graph,
  onNodeSelect,
  onEdgeSelect,
  layout = 'force'
}: GraphCanvasProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<Core | null>(null);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [selectedEdge, setSelectedEdge] = useState<string | null>(null);
  const [isAnimating, setIsAnimating] = useState(false);

  useEffect(() => {
    if (!containerRef.current || !graph) return;

    // Destroy existing instance
    if (cyRef.current) {
      cyRef.current.destroy();
    }

    // Convert graph to Cytoscape format
    const elements = convertGraphToCytoscape(graph);

    // Initialize Cytoscape with beautiful modern styles
    const cy = cytoscape({
      container: containerRef.current,
      elements,
      style: getModernCytoscapeStyle(),
      layout: LAYOUT_CONFIGS[layout],
      minZoom: 0.1,
      maxZoom: 4,
      wheelSensitivity: 0.15,
      motionBlur: true, // Smooth animations
      textureOnViewport: false, // Better performance
      pixelRatio: 'auto',
    });

    // ============ ADVANCED INTERACTIONS ============

    // Node click - highlight neighbors
    cy.on('tap', 'node', (evt) => {
      const node = evt.target;
      const nodeId = node.id();
      setSelectedNode(nodeId);
      if (onNodeSelect) {
        onNodeSelect(nodeId);
      }
      
      // Highlight connected nodes and edges
      highlightNeighborhood(cy, node);
    });

    // Edge click
    cy.on('tap', 'edge', (evt) => {
      const edge = evt.target;
      const edgeId = edge.id();
      setSelectedEdge(edgeId);
      if (onEdgeSelect) {
        onEdgeSelect(edgeId);
      }
      
      // Remove node highlights
      cy.nodes().removeClass('highlighted faded');
      cy.edges().removeClass('highlighted faded');
      
      // Highlight this edge
      edge.addClass('highlighted');
    });

    // Canvas click - clear selection
    cy.on('tap', (evt) => {
      if (evt.target === cy) {
        setSelectedNode(null);
        setSelectedEdge(null);
        
        // Remove all highlights
        cy.nodes().removeClass('highlighted faded');
        cy.edges().removeClass('highlighted faded');
      }
    });

    // Mouse over node - show tooltip effect
    cy.on('mouseover', 'node', (evt) => {
      const node = evt.target;
      node.style({
        'transition-duration': '0.2s',
      });
    });

    // Mouse out node
    cy.on('mouseout', 'node', (evt) => {
      const node = evt.target;
      node.style({
        'transition-duration': '0.3s',
      });
    });

    // Double click node - focus on it
    cy.on('dbltap', 'node', (evt) => {
      const node = evt.target;
      cy.animate({
        fit: {
          eles: node.neighborhood().add(node),
          padding: 100,
        },
        duration: 600,
        easing: 'ease-in-out-cubic',
      });
    });

    cyRef.current = cy;

    // Cleanup
    return () => {
      if (cyRef.current) {
        cyRef.current.destroy();
      }
    };
  }, [graph, layout]);

  /**
   * Highlight node's neighborhood (connected nodes and edges)
   */
  const highlightNeighborhood = (cy: Core, node: NodeSingular) => {
    // Get neighborhood
    const neighborhood = node.neighborhood();
    const connectedNodes = neighborhood.nodes();
    const connectedEdges = neighborhood.edges();

    // Fade everything
    cy.nodes().addClass('faded');
    cy.edges().addClass('faded');

    // Highlight connected elements
    node.removeClass('faded');
    connectedNodes.removeClass('faded').addClass('highlighted');
    connectedEdges.removeClass('faded').addClass('highlighted');
  };

  const fitToScreen = () => {
    if (cyRef.current) {
      cyRef.current.animate({
        fit: { padding: 50 },
        duration: 500,
        easing: 'ease-out-cubic',
      });
    }
  };

  const resetZoom = () => {
    if (cyRef.current) {
      cyRef.current.animate({
        zoom: 1,
        pan: { x: cyRef.current.width() / 2, y: cyRef.current.height() / 2 },
        duration: 400,
        easing: 'ease-in-out',
      });
    }
  };

  const changeLayout = (newLayout: typeof layout) => {
    if (cyRef.current) {
      setIsAnimating(true);
      cyRef.current
        .layout(LAYOUT_CONFIGS[newLayout])
        .run();
      
      setTimeout(() => setIsAnimating(false), 1000);
    }
  };

  const centerOnSelected = () => {
    if (cyRef.current && selectedNode) {
      const node = cyRef.current.getElementById(selectedNode);
      if (node) {
        cyRef.current.animate({
          fit: {
            eles: node.neighborhood().add(node),
            padding: 150,
          },
          duration: 600,
          easing: 'ease-in-out-cubic',
        });
      }
    }
  };

  if (!graph) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100">
        <div className="text-center p-8">
          <div className="mb-4">
            <svg className="w-24 h-24 mx-auto text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
            </svg>
          </div>
          <p className="text-gray-600 text-xl font-medium mb-2">No graph loaded</p>
          <p className="text-gray-400">Upload papers to build a citation graph</p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-full relative bg-gradient-to-br from-gray-50 to-gray-100">
      <div ref={containerRef} className="w-full h-full" />
      
      {/* Modern floating controls */}
      <div className="absolute top-4 right-4 flex flex-col gap-2">
        <button
          onClick={fitToScreen}
          className="group px-4 py-2.5 bg-white/90 backdrop-blur-sm border border-gray-200 rounded-xl shadow-lg hover:shadow-xl hover:bg-white transition-all duration-200 text-sm font-medium text-gray-700 hover:text-blue-600"
          title="Fit to screen (F)"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
          </svg>
        </button>
        
        <button
          onClick={resetZoom}
          className="group px-4 py-2.5 bg-white/90 backdrop-blur-sm border border-gray-200 rounded-xl shadow-lg hover:shadow-xl hover:bg-white transition-all duration-200 text-sm font-medium text-gray-700 hover:text-blue-600"
          title="Reset zoom"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v6m3-3H7" />
          </svg>
        </button>

        {selectedNode && (
          <button
            onClick={centerOnSelected}
            className="group px-4 py-2.5 bg-blue-600 text-white backdrop-blur-sm border border-blue-700 rounded-xl shadow-lg hover:shadow-xl hover:bg-blue-700 transition-all duration-200 text-sm font-medium"
            title="Center on selected"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
            </svg>
          </button>
        )}
      </div>

      {/* Layout selector */}
      <div className="absolute top-4 left-4">
        <div className="bg-white/90 backdrop-blur-sm border border-gray-200 rounded-xl shadow-lg p-2 flex gap-2">
          {(['force', 'hierarchical', 'circular', 'grid'] as const).map((layoutType) => (
            <button
              key={layoutType}
              onClick={() => changeLayout(layoutType)}
              disabled={isAnimating}
              className={`px-3 py-2 rounded-lg text-xs font-medium transition-all duration-200 ${
                layout === layoutType
                  ? 'bg-blue-600 text-white shadow-md'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              } disabled:opacity-50 disabled:cursor-not-allowed`}
            >
              {layoutType.charAt(0).toUpperCase() + layoutType.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Beautiful stats overlay */}
      <div className="absolute bottom-4 left-4 bg-white/90 backdrop-blur-sm px-6 py-3 rounded-xl shadow-lg border border-gray-200">
        <div className="flex items-center gap-6 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-blue-500"></div>
            <span className="font-semibold text-gray-900">{graph.nodes.length}</span>
            <span className="text-gray-500">papers</span>
          </div>
          <div className="w-px h-4 bg-gray-300"></div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-0.5 bg-gray-400"></div>
            <span className="font-semibold text-gray-900">{graph.edges.length}</span>
            <span className="text-gray-500">citations</span>
          </div>
        </div>
      </div>

      {/* Keyboard shortcuts hint */}
      <div className="absolute bottom-4 right-4 bg-gray-900/80 backdrop-blur-sm text-white px-4 py-2 rounded-lg text-xs">
        <span className="opacity-75">💡 Double-click node to focus • Drag to pan • Scroll to zoom</span>
      </div>
    </div>
  );
}

/**
 * Convert ResearchGraph to Cytoscape format with enhanced styling
 */
function convertGraphToCytoscape(graph: ResearchGraph) {
  const elements = [];

  // Add nodes with enhanced data
  for (const node of graph.nodes) {
    const citationCount = node.citation_count || 0;
    const size = Math.max(40, Math.min(70, 40 + citationCount / 10));
    
    elements.push({
      group: 'nodes',
      data: {
        id: node.id,
        label: truncateTitle(node.title, 50),
        title: node.title,
        authors: node.authors,
        abstract: node.abstract,
        citation_count: citationCount,
        size: size,
        ...node.attributes,
      },
    });
  }

  // Add edges
  for (const edge of graph.edges) {
    elements.push({
      group: 'edges',
      data: {
        id: edge.id,
        source: edge.from_paper,
        target: edge.to_paper,
        label: edge.contribution_type,
        contribution_type: edge.contribution_type,
        context: edge.context,
        strength: edge.strength,
      },
    });
  }

  return elements;
}

/**
 * Truncate title to max length
 */
function truncateTitle(title: string, maxLength: number): string {
  if (title.length <= maxLength) return title;
  return title.substring(0, maxLength - 3) + '...';
}
