'use client';

import React, { useEffect, useRef, useState, useCallback, useMemo } from 'react';
import cytoscape, { Core, NodeSingular } from 'cytoscape';
import cytoscapeDagre from 'cytoscape-dagre';
import type { ResearchGraph, CitationEdge } from '@/lib/api';
import { getModernCytoscapeStyle, LAYOUT_CONFIGS } from '@/lib/graph-styles';

// Register dagre layout extension (needed for timeline & hierarchical)
cytoscape.use(cytoscapeDagre);

type LayoutType = 'force' | 'hierarchical' | 'timeline' | 'circular' | 'grid';

interface GraphCanvasProps {
  graph: ResearchGraph | null;
  onNodeSelect?: (nodeId: string) => void;
  onEdgeSelect?: (edge: CitationEdge | null) => void;
  layout?: LayoutType;
}

interface TooltipState {
  x: number;
  y: number;
  type: 'node' | 'edge';
  // Node fields
  title?: string;
  authors?: string[];
  abstract?: string;
  venue?: string;
  date?: string;
  citations?: number;
  // Edge fields
  edgeLabel?: string;
  fromTitle?: string;
  toTitle?: string;
}

export default function GraphCanvas({
  graph,
  onNodeSelect,
  onEdgeSelect,
  layout: initialLayout = 'timeline'
}: GraphCanvasProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<Core | null>(null);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [isAnimating, setIsAnimating] = useState(false);
  const [tooltip, setTooltip] = useState<TooltipState | null>(null);
  const [activeLayout, setActiveLayout] = useState<LayoutType>(initialLayout);
  const [nodeRepulsion, setNodeRepulsion] = useState(400000);
  const [edgeLength, setEdgeLength] = useState(150);

  // Build the layout config for force with current slider values
  const getForceConfig = useCallback(() => ({
    ...LAYOUT_CONFIGS.force,
    nodeRepulsion,
    idealEdgeLength: edgeLength,
  }), [nodeRepulsion, edgeLength]);

  const getLayoutConfig = useCallback((layoutType: LayoutType) => {
    if (layoutType === 'force') return getForceConfig();
    return LAYOUT_CONFIGS[layoutType];
  }, [getForceConfig]);

  // Build an edge lookup from graph data so we can pass full edge objects on click
  const edgeLookup = useMemo(() => {
    if (!graph) return new Map<string, CitationEdge>();
    const map = new Map<string, CitationEdge>();
    for (const e of graph.edges) {
      map.set(e.id, e);
    }
    return map;
  }, [graph]);

  // Build a node title lookup for edge tooltips
  const nodeTitleLookup = useMemo(() => {
    if (!graph) return new Map<string, string>();
    const map = new Map<string, string>();
    for (const n of graph.nodes) {
      map.set(n.id, n.title);
    }
    return map;
  }, [graph]);

  // Compute visible counts (excluding hidden review papers)
  const { reviewedCount, connectingCount, visibleEdgeCount } = useMemo(() => {
    if (!graph) return { reviewedCount: 0, connectingCount: 0, visibleEdgeCount: 0 };

    const inputIds = new Set(
      graph.nodes.filter(n => n.attributes?.paper_source === 'input').map(n => n.id)
    );

    const directlyReferenced = new Set<string>();
    for (const edge of graph.edges) {
      if (inputIds.has(edge.from_paper) && !inputIds.has(edge.to_paper)) {
        directlyReferenced.add(edge.to_paper);
      }
      if (inputIds.has(edge.to_paper) && !inputIds.has(edge.from_paper)) {
        directlyReferenced.add(edge.from_paper);
      }
    }

    const nonInputNodes = graph.nodes.filter(n => !inputIds.has(n.id));
    const reviewed = nonInputNodes.filter(n => directlyReferenced.has(n.id)).length;
    const connecting = nonInputNodes.filter(n => !directlyReferenced.has(n.id)).length;
    const edges = graph.edges.filter(
      e => !inputIds.has(e.from_paper) && !inputIds.has(e.to_paper)
    ).length;

    return { reviewedCount: reviewed, connectingCount: connecting, visibleEdgeCount: edges };
  }, [graph]);

  // ===================== Initialize Cytoscape =====================
  useEffect(() => {
    if (!containerRef.current || !graph) return;

    // Destroy existing instance
    if (cyRef.current) {
      cyRef.current.destroy();
    }

    const elements = convertGraphToCytoscape(graph);

    const cy = cytoscape({
      container: containerRef.current,
      elements,
      style: getModernCytoscapeStyle(),
      layout: getLayoutConfig(activeLayout),
      minZoom: 0.1,
      maxZoom: 4,
      wheelSensitivity: 0.15,
      pixelRatio: 'auto',
      // ===== Performance optimizations =====
      textureOnViewport: true,
      hideEdgesOnViewport: true,
      hideLabelsOnViewport: true,
    });

    // ---------- Node click - highlight neighbors ----------
    cy.on('tap', 'node', (evt) => {
      const node = evt.target;
      const nodeId = node.id();
      setSelectedNode(nodeId);
      onNodeSelect?.(nodeId);
      highlightNeighborhood(cy, node);
    });

    // ---------- Edge click - open detail modal ----------
    cy.on('tap', 'edge', (evt) => {
      const edge = evt.target;
      const edgeId = edge.id();
      const edgeData = edgeLookup.get(edgeId) || null;
      onEdgeSelect?.(edgeData);
      cy.nodes().removeClass('highlighted faded');
      cy.edges().removeClass('highlighted faded');
      edge.addClass('highlighted');
    });

    // ---------- Canvas click - clear selection ----------
    cy.on('tap', (evt) => {
      if (evt.target === cy) {
        setSelectedNode(null);
        onEdgeSelect?.(null);
        cy.nodes().removeClass('highlighted faded');
        cy.edges().removeClass('highlighted faded');
      }
    });

    // ---------- Node tooltip on hover ----------
    cy.on('mouseover', 'node', (evt) => {
      const node = evt.target;
      const pos = node.renderedPosition();
      const d = node.data();
      setTooltip({
        x: pos.x,
        y: pos.y - 40,
        type: 'node',
        title: d.title || d.label,
        authors: d.authors,
        abstract: d.abstract,
        venue: d.venue,
        date: d.publication_date,
        citations: d.citation_count,
      });
    });

    cy.on('mouseout', 'node', () => {
      setTooltip(null);
    });

    // ---------- Edge tooltip on hover ----------
    cy.on('mouseover', 'edge', (evt) => {
      const edge = evt.target;
      const d = edge.data();
      const midpoint = edge.midpoint();
      const zoom = cy.zoom();
      const pan = cy.pan();
      // Convert model coords to rendered coords
      const rx = midpoint.x * zoom + pan.x;
      const ry = midpoint.y * zoom + pan.y;

      const fromTitle = nodeTitleLookup.get(d.source) || d.source;
      const toTitle = nodeTitleLookup.get(d.target) || d.target;

      setTooltip({
        x: rx,
        y: ry - 20,
        type: 'edge',
        edgeLabel: d.context && d.context !== 'reference' && d.context !== '' ? d.context : d.contribution_type,
        fromTitle: truncateTitle(fromTitle, 60),
        toTitle: truncateTitle(toTitle, 60),
      });
    });

    cy.on('mouseout', 'edge', () => {
      setTooltip(null);
    });

    // Hide tooltip on pan/zoom (position becomes stale)
    cy.on('pan zoom', () => {
      setTooltip(null);
    });

    // ---------- Double click - focus ----------
    cy.on('dbltap', 'node', (evt) => {
      const node = evt.target;
      cy.animate({
        fit: { eles: node.neighborhood().add(node), padding: 100 },
        duration: 600,
        easing: 'ease-in-out-cubic',
      });
    });

    cyRef.current = cy;

    return () => {
      if (cyRef.current) {
        cyRef.current.destroy();
        cyRef.current = null;
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [graph]);

  // ===================== Actions =====================
  const highlightNeighborhood = (cy: Core, node: NodeSingular) => {
    const neighborhood = node.neighborhood();
    cy.nodes().addClass('faded');
    cy.edges().addClass('faded');
    node.removeClass('faded');
    neighborhood.nodes().removeClass('faded').addClass('highlighted');
    neighborhood.edges().removeClass('faded').addClass('highlighted');
  };

  const fitToScreen = () => {
    const cy = cyRef.current;
    if (!cy) return;
    cy.animate({
      fit: { eles: cy.elements(), padding: 50 },
      duration: 500,
      easing: 'ease-out-cubic',
    });
  };

  const resetZoom = () => {
    const cy = cyRef.current;
    if (cy) {
      cy.animate({
        zoom: 1,
        pan: { x: cy.width() / 2, y: cy.height() / 2 },
        duration: 400,
        easing: 'ease-in-out',
      });
    }
  };

  const changeLayout = useCallback((newLayout: LayoutType) => {
    const cy = cyRef.current;
    if (!cy) return;

    setActiveLayout(newLayout);
    setIsAnimating(true);
    cy.layout(getLayoutConfig(newLayout)).run();
    setTimeout(() => setIsAnimating(false), 1200);
  }, [getLayoutConfig]);

  const applyForceParams = useCallback(() => {
    const cy = cyRef.current;
    if (!cy || activeLayout !== 'force') return;

    cy.layout(getForceConfig()).run();
  }, [activeLayout, getForceConfig]);

  const centerOnSelected = () => {
    const cy = cyRef.current;
    if (cy && selectedNode) {
      const node = cy.getElementById(selectedNode);
      if (node.length > 0) {
        cy.animate({
          fit: { eles: node.neighborhood().add(node), padding: 150 },
          duration: 600,
          easing: 'ease-in-out-cubic',
        });
      }
    }
  };

  // ===================== Render =====================
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

      {/* ===== Floating controls (top right) ===== */}
      <div className="absolute top-4 right-4 flex flex-col gap-2">
        <button
          onClick={fitToScreen}
          className="group px-4 py-2.5 bg-white/90 backdrop-blur-sm border border-gray-200 rounded-xl shadow-lg hover:shadow-xl hover:bg-white transition-all duration-200 text-sm font-medium text-gray-700 hover:text-blue-600"
          title="Fit to screen"
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

      {/* ===== Layout selector (top left) ===== */}
      <div className="absolute top-4 left-4">
        <div className="bg-white/90 backdrop-blur-sm border border-gray-200 rounded-xl shadow-lg p-2 flex gap-2">
          {(['timeline', 'force', 'hierarchical', 'circular', 'grid'] as const).map((layoutType) => (
            <button
              key={layoutType}
              onClick={() => changeLayout(layoutType)}
              disabled={isAnimating}
              className={`px-3 py-2 rounded-lg text-xs font-medium transition-all duration-200 ${
                activeLayout === layoutType
                  ? 'bg-blue-600 text-white shadow-md'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              } disabled:opacity-50 disabled:cursor-not-allowed`}
            >
              {layoutType.charAt(0).toUpperCase() + layoutType.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* ===== Force simulation controls ===== */}
      {activeLayout === 'force' && (
        <div className="absolute top-20 left-4">
          <div className="bg-white/90 backdrop-blur-sm border border-gray-200 rounded-xl shadow-lg p-4 space-y-3 w-56">
            <div className="text-xs font-semibold text-gray-700 mb-2">Force Simulation</div>

            <div>
              <label className="text-xs text-gray-600 flex justify-between mb-1">
                <span>Repulsion</span>
                <span className="font-mono text-blue-600">{(nodeRepulsion / 1000).toFixed(0)}k</span>
              </label>
              <input
                type="range"
                min="100000"
                max="1000000"
                step="50000"
                value={nodeRepulsion}
                onChange={(e) => setNodeRepulsion(Number(e.target.value))}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
              />
            </div>

            <div>
              <label className="text-xs text-gray-600 flex justify-between mb-1">
                <span>Edge Length</span>
                <span className="font-mono text-blue-600">{edgeLength}px</span>
              </label>
              <input
                type="range"
                min="50"
                max="300"
                step="10"
                value={edgeLength}
                onChange={(e) => setEdgeLength(Number(e.target.value))}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
              />
            </div>

            <button
              onClick={applyForceParams}
              className="w-full px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-medium rounded-lg transition-all"
            >
              Apply
            </button>

            <button
              onClick={() => {
                setNodeRepulsion(400000);
                setEdgeLength(150);
              }}
              className="w-full px-3 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 text-xs font-medium rounded-lg transition-all"
            >
              Reset Defaults
            </button>
          </div>
        </div>
      )}

      {/* ===== Legend + Stats (bottom left) ===== */}
      <div className="absolute bottom-4 left-4 flex gap-3">
        <div className="bg-white/90 backdrop-blur-sm px-5 py-3 rounded-xl shadow-lg border border-gray-200">
          <div className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-1.5">Legend</div>
          <div className="flex flex-col gap-1.5">
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded-full bg-emerald-500 border-2 border-emerald-700 flex-shrink-0"></div>
              <span className="text-xs font-medium text-gray-700">Reviewed papers</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded-full bg-slate-400 border-2 border-slate-500 flex-shrink-0"></div>
              <span className="text-xs font-medium text-gray-700">Connecting papers</span>
            </div>
          </div>
        </div>
        <div className="bg-white/90 backdrop-blur-sm px-5 py-3 rounded-xl shadow-lg border border-gray-200 self-end">
          <div className="flex items-center gap-5 text-sm">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-emerald-500"></div>
              <span className="font-semibold text-gray-900">{reviewedCount}</span>
              <span className="text-gray-500">reviewed</span>
            </div>
            <div className="w-px h-4 bg-gray-300"></div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-slate-400"></div>
              <span className="font-semibold text-gray-900">{connectingCount}</span>
              <span className="text-gray-500">connecting</span>
            </div>
            <div className="w-px h-4 bg-gray-300"></div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-0.5 bg-gray-400"></div>
              <span className="font-semibold text-gray-900">{visibleEdgeCount}</span>
              <span className="text-gray-500">citations</span>
            </div>
          </div>
        </div>
      </div>

      {/* ===== Hint (bottom right) ===== */}
      <div className="absolute bottom-4 right-4 bg-gray-900/80 backdrop-blur-sm text-white px-4 py-2 rounded-lg text-xs">
        <span className="opacity-75">Click edge for details | Double-click node to focus | Scroll to zoom</span>
      </div>

      {/* ===== Tooltip (node or edge) ===== */}
      {tooltip && (
        <div
          className="absolute pointer-events-none z-[9999]"
          style={{
            left: `${tooltip.x}px`,
            top: `${tooltip.y}px`,
            transform: 'translate(-50%, -100%)',
          }}
        >
          {tooltip.type === 'node' ? (
            <div className="bg-white rounded-xl shadow-2xl border border-gray-200 p-4 max-w-sm">
              <h3 className="font-bold text-gray-900 text-sm mb-1 line-clamp-2">
                {tooltip.title}
              </h3>
              {tooltip.authors && tooltip.authors.length > 0 && (
                <div className="text-xs text-gray-600 mb-1">
                  {tooltip.authors.slice(0, 3).join(', ')}
                  {tooltip.authors.length > 3 && ' et al.'}
                </div>
              )}
              <div className="flex gap-3 text-xs text-gray-500">
                {tooltip.venue && <span className="truncate">{tooltip.venue}</span>}
                {tooltip.date && <span>{tooltip.date}</span>}
              </div>
              {tooltip.citations !== undefined && tooltip.citations > 0 && (
                <div className="text-xs font-medium text-blue-600 mt-1">
                  {tooltip.citations} citations
                </div>
              )}
              {tooltip.abstract && (
                <div className="mt-2 pt-2 border-t border-gray-100 text-xs text-gray-600 line-clamp-3">
                  {tooltip.abstract}
                </div>
              )}
            </div>
          ) : (
            <div className="bg-gray-900 text-white rounded-lg shadow-2xl px-4 py-3 max-w-xs">
              <div className="text-[10px] text-gray-400 mb-1 truncate">{tooltip.fromTitle}</div>
              <div className="text-xs font-semibold text-amber-300 my-1">
                {tooltip.edgeLabel || 'citation'}
              </div>
              <div className="text-[10px] text-gray-400 truncate">{tooltip.toTitle}</div>
              <div className="text-[10px] text-gray-500 mt-1 italic">Click for details</div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ===================== Helpers =====================

function convertGraphToCytoscape(graph: ResearchGraph) {
  const elements: cytoscape.ElementDefinition[] = [];

  const inputPaperIds = new Set(
    graph.nodes
      .filter(n => n.attributes?.paper_source === 'input')
      .map(n => n.id)
  );

  const directlyReferencedIds = new Set<string>();
  for (const edge of graph.edges) {
    if (inputPaperIds.has(edge.from_paper) && !inputPaperIds.has(edge.to_paper)) {
      directlyReferencedIds.add(edge.to_paper);
    }
    if (inputPaperIds.has(edge.to_paper) && !inputPaperIds.has(edge.from_paper)) {
      directlyReferencedIds.add(edge.from_paper);
    }
  }

  // Add nodes -- skip input/review papers
  for (const node of graph.nodes) {
    if (inputPaperIds.has(node.id)) continue;

    const citationCount = node.citation_count || 0;
    const isReviewed = directlyReferencedIds.has(node.id);
    const size = isReviewed
      ? Math.max(50, Math.min(80, 50 + citationCount / 8))
      : Math.max(35, Math.min(60, 35 + citationCount / 12));

    elements.push({
      group: 'nodes',
      data: {
        id: node.id,
        label: truncateTitle(node.title, 50),
        title: node.title,
        authors: node.authors,
        abstract: node.abstract,
        citation_count: citationCount,
        publication_date: node.publication_date,
        venue: node.venue,
        size,
        ...node.attributes,
        paper_source: isReviewed ? 'reviewed' : 'connecting',
      },
    });
  }

  // Add edges -- skip any involving input/review papers
  for (const edge of graph.edges) {
    if (inputPaperIds.has(edge.from_paper) || inputPaperIds.has(edge.to_paper)) {
      continue;
    }

    // Use context (innovation label) as the edge label when available
    const hasInnovation = edge.context && edge.context !== '' && edge.context !== 'reference';
    const label = hasInnovation ? edge.context : edge.contribution_type;

    elements.push({
      group: 'edges',
      data: {
        id: edge.id,
        source: edge.from_paper,
        target: edge.to_paper,
        label,
        contribution_type: edge.contribution_type,
        context: edge.context,
        delta_description: edge.delta_description,
        strength: edge.strength,
      },
    });
  }

  return elements;
}

function truncateTitle(title: string, maxLength: number): string {
  if (title.length <= maxLength) return title;
  return title.substring(0, maxLength - 3) + '...';
}
