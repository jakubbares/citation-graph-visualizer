'use client';

import React, { useMemo, useState } from 'react';
import type { ResearchGraph, CitationEdge } from '@/lib/api';

interface InnovationFlowPanelProps {
  graph: ResearchGraph | null;
  onEdgeClick?: (edge: CitationEdge) => void;
}

export default function InnovationFlowPanel({ graph, onEdgeClick }: InnovationFlowPanelProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [filter, setFilter] = useState('');

  // Build node title lookup
  const nodeTitles = useMemo(() => {
    if (!graph) return new Map<string, string>();
    const map = new Map<string, string>();
    for (const n of graph.nodes) map.set(n.id, n.title);
    return map;
  }, [graph]);

  // Get ALL edges that have real innovation data
  // Include review-to-paper edges too -- the panel shows the knowledge flow
  const visibleEdges = useMemo(() => {
    if (!graph) return [];

    // Edges with actual innovation content (not just "citation" or "reference")
    const trivialLabels = new Set(['', 'reference', 'citation', 'related']);

    return graph.edges
      .filter(e => {
        const hasLabel = e.context && !trivialLabels.has(e.context.toLowerCase());
        const hasInsight = e.delta_description && e.delta_description.length > 30
          && !e.delta_description.startsWith('Extraction failed')
          && !e.delta_description.startsWith('Insufficient');
        return hasLabel || hasInsight;
      })
      .sort((a, b) => {
        if (b.strength !== a.strength) return b.strength - a.strength;
        return (a.context || '').localeCompare(b.context || '');
      });
  }, [graph]);

  // Apply text filter
  const filteredEdges = useMemo(() => {
    if (!filter.trim()) return visibleEdges;
    const q = filter.toLowerCase();
    return visibleEdges.filter(e => {
      const fromTitle = (nodeTitles.get(e.from_paper) || '').toLowerCase();
      const toTitle = (nodeTitles.get(e.to_paper) || '').toLowerCase();
      const ctx = (e.context || '').toLowerCase();
      const delta = (e.delta_description || '').toLowerCase();
      return fromTitle.includes(q) || toTitle.includes(q) || ctx.includes(q) || delta.includes(q);
    });
  }, [visibleEdges, filter, nodeTitles]);

  if (!graph) return null;

  const hasInnovations = visibleEdges.length > 0;

  return (
    <div className="w-[22rem] glass-dark border-l border-white/5 flex flex-col overflow-hidden shadow-2xl z-10">
      {/* Header */}
      <div className="px-5 py-4 border-b border-white/5 flex-shrink-0">
        <h3 className="text-sm font-bold text-white mb-1">Innovation Flow</h3>
        <p className="text-[11px] text-slate-400">
          {hasInnovations
            ? `${visibleEdges.length} paper-to-paper contributions`
            : 'Extract edge innovations to see the flow'}
        </p>
      </div>

      {hasInnovations && (
        <>
          {/* Search */}
          <div className="px-4 py-3 border-b border-white/5 flex-shrink-0">
            <input
              type="text"
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              placeholder="Search papers or innovations..."
              className="w-full px-3 py-2 text-xs bg-white/5 border border-white/10 rounded-lg text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/30"
            />
          </div>

          {/* Edge list */}
          <div className="flex-1 overflow-y-auto">
            {filteredEdges.length === 0 ? (
              <div className="p-6 text-center text-xs text-slate-500">
                No matches found
              </div>
            ) : (
              <div className="divide-y divide-white/5">
                {filteredEdges.map((edge) => {
                  const fromTitle = nodeTitles.get(edge.from_paper) || 'Unknown';
                  const toTitle = nodeTitles.get(edge.to_paper) || 'Unknown';
                  const isExpanded = expandedId === edge.id;
                  const hasInsight = edge.delta_description && edge.delta_description.length > 20;

                  return (
                    <div
                      key={edge.id}
                      className="hover:bg-white/5 transition-colors cursor-pointer"
                      onClick={() => onEdgeClick?.(edge)}
                    >
                      {/* Compact view */}
                      <div className="px-4 py-3">
                        {/* Innovation label */}
                        <div className="text-xs font-semibold text-amber-400 mb-2 leading-tight">
                          {edge.context}
                        </div>

                        {/* From -> To */}
                        <div className="flex items-start gap-2 text-[11px]">
                          <div className="flex-1 min-w-0">
                            <div className="text-slate-300 font-medium truncate" title={fromTitle}>
                              {truncate(fromTitle, 45)}
                            </div>
                            <div className="flex items-center gap-1 my-1">
                              <svg className="w-3 h-3 text-slate-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
                              </svg>
                              <span className="text-[10px] text-slate-500">cites</span>
                            </div>
                            <div className="text-slate-400 truncate" title={toTitle}>
                              {truncate(toTitle, 45)}
                            </div>
                          </div>

                          {/* Expand button */}
                          {hasInsight && (
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                setExpandedId(isExpanded ? null : edge.id);
                              }}
                              className="flex-shrink-0 mt-1 w-6 h-6 flex items-center justify-center rounded text-slate-400 hover:text-white hover:bg-white/10 transition-all"
                              title={isExpanded ? 'Collapse' : 'Expand insight'}
                            >
                              <svg
                                className={`w-3.5 h-3.5 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                                fill="none"
                                viewBox="0 0 24 24"
                                stroke="currentColor"
                              >
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                              </svg>
                            </button>
                          )}
                        </div>
                      </div>

                      {/* Expanded insight */}
                      {isExpanded && hasInsight && (
                        <div className="px-4 pb-4">
                          <div className="p-3 rounded-lg bg-white/5 border border-white/10">
                            <div className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-2">
                              Innovation Insight
                            </div>
                            <div className="text-[11px] text-slate-300 leading-relaxed whitespace-pre-wrap">
                              {edge.delta_description}
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Footer count */}
          <div className="px-4 py-2 border-t border-white/5 flex-shrink-0">
            <div className="text-[10px] text-slate-500">
              {filteredEdges.length === visibleEdges.length
                ? `${visibleEdges.length} contributions`
                : `${filteredEdges.length} of ${visibleEdges.length} contributions`}
            </div>
          </div>
        </>
      )}

      {!hasInnovations && (
        <div className="flex-1 flex items-center justify-center p-6">
          <div className="text-center">
            <div className="w-12 h-12 mx-auto mb-3 rounded-full bg-white/5 flex items-center justify-center">
              <svg className="w-6 h-6 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <p className="text-xs text-slate-400 font-medium mb-1">No innovations extracted yet</p>
            <p className="text-[10px] text-slate-500">
              Click &quot;Extract Edge Innovations&quot; in the left panel
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

function truncate(s: string, max: number): string {
  if (s.length <= max) return s;
  return s.substring(0, max - 3) + '...';
}
