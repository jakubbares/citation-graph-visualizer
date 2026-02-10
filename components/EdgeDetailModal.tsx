'use client';

import React, { useState } from 'react';
import type { CitationEdge, ResearchGraph } from '@/lib/api';
import { GraphAPI } from '@/lib/api';

interface EdgeDetailModalProps {
  edge: CitationEdge | null;
  graph: ResearchGraph | null;
  onClose: () => void;
  onEdgeUpdated?: (updatedEdge: CitationEdge) => void;
}

export default function EdgeDetailModal({ edge, graph, onClose, onEdgeUpdated }: EdgeDetailModalProps) {
  const [isExtracting, setIsExtracting] = useState(false);
  const [localEdge, setLocalEdge] = useState<CitationEdge | null>(null);

  // Use localEdge if we just extracted, otherwise use prop
  const displayEdge = localEdge?.id === edge?.id ? localEdge : edge;

  if (!displayEdge || !graph) return null;

  const fromNode = graph.nodes.find(n => n.id === displayEdge.from_paper);
  const toNode = graph.nodes.find(n => n.id === displayEdge.to_paper);

  const hasInnovation = displayEdge.context && displayEdge.context !== '' && displayEdge.context !== 'reference';
  const hasInsight = displayEdge.delta_description && displayEdge.delta_description !== '' && !displayEdge.delta_description.startsWith('Extraction failed');

  const handleExtractSingle = async () => {
    if (!graph || !displayEdge) return;
    try {
      setIsExtracting(true);
      const response = await GraphAPI.extractSingleEdge(graph.id, displayEdge.id);
      // Update local state with the result
      setLocalEdge(response.edge);
      onEdgeUpdated?.(response.edge);
    } catch (err: any) {
      console.error('Error extracting single edge:', err);
    } finally {
      setIsExtracting(false);
    }
  };

  const handleClose = () => {
    setLocalEdge(null);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-[10000] flex items-center justify-center p-4" onClick={handleClose}>
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" />

      {/* Modal */}
      <div
        className="relative bg-white rounded-2xl shadow-2xl border border-gray-200 max-w-2xl w-full max-h-[85vh] overflow-hidden flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-6 py-5 border-b border-gray-100 flex-shrink-0">
          <div className="flex items-start justify-between">
            <div className="flex-1 pr-4">
              <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
                Citation Relationship
              </div>
              <div className="flex items-center gap-3">
                {displayEdge.contribution_type && (
                  <span className="px-2.5 py-1 text-xs font-bold rounded-full bg-blue-100 text-blue-700">
                    {displayEdge.contribution_type}
                  </span>
                )}
                {displayEdge.strength > 0 && (
                  <span className="text-xs text-gray-400">
                    Strength: {(displayEdge.strength * 100).toFixed(0)}%
                  </span>
                )}
              </div>
            </div>
            <button
              onClick={handleClose}
              className="w-8 h-8 flex items-center justify-center text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-all"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Paper flow */}
        <div className="px-6 py-4 border-b border-gray-100 flex-shrink-0">
          {/* From paper (citing) */}
          <div className="p-3 bg-blue-50 rounded-lg border border-blue-200 mb-3">
            <div className="text-[10px] font-semibold text-blue-500 uppercase tracking-wider mb-1">
              Citing paper (newer)
            </div>
            <div className="text-sm font-semibold text-gray-900">
              {fromNode?.title || displayEdge.from_paper}
            </div>
            {fromNode?.authors && fromNode.authors.length > 0 && (
              <div className="text-xs text-gray-500 mt-1">
                {fromNode.authors.slice(0, 4).join(', ')}
                {fromNode.authors.length > 4 && ' et al.'}
              </div>
            )}
          </div>

          {/* Arrow with short label */}
          <div className="flex items-center justify-center gap-3 my-2">
            <div className="flex-1 h-px bg-gray-200"></div>
            <div className="flex items-center gap-2">
              <svg className="w-4 h-4 text-amber-500 rotate-90" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
              </svg>
              {hasInnovation && (
                <span className="px-3 py-1 bg-amber-50 border border-amber-200 rounded-full text-xs font-semibold text-amber-700">
                  {displayEdge.context}
                </span>
              )}
              <span className="text-xs text-gray-400">cites</span>
            </div>
            <div className="flex-1 h-px bg-gray-200"></div>
          </div>

          {/* To paper (cited) */}
          <div className="p-3 bg-emerald-50 rounded-lg border border-emerald-200">
            <div className="text-[10px] font-semibold text-emerald-500 uppercase tracking-wider mb-1">
              Cited paper (older)
            </div>
            <div className="text-sm font-semibold text-gray-900">
              {toNode?.title || displayEdge.to_paper}
            </div>
            {toNode?.authors && toNode.authors.length > 0 && (
              <div className="text-xs text-gray-500 mt-1">
                {toNode.authors.slice(0, 4).join(', ')}
                {toNode.authors.length > 4 && ' et al.'}
              </div>
            )}
          </div>
        </div>

        {/* Full insight */}
        <div className="px-6 py-5 overflow-y-auto flex-1">
          {isExtracting ? (
            <div className="text-center py-8">
              <div className="w-12 h-12 mx-auto mb-3 rounded-full bg-amber-50 flex items-center justify-center">
                <svg className="w-6 h-6 text-amber-500 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
              </div>
              <p className="text-sm text-gray-600 font-medium">Analyzing papers...</p>
              <p className="text-xs text-gray-400 mt-1">Using full paper text when available</p>
            </div>
          ) : hasInsight ? (
            <div>
              <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
                Innovation Insight
              </div>
              <div className="prose prose-sm max-w-none text-gray-700 leading-relaxed whitespace-pre-wrap">
                {displayEdge.delta_description}
              </div>
            </div>
          ) : (
            <div className="text-center py-8">
              <div className="w-12 h-12 mx-auto mb-3 rounded-full bg-gray-100 flex items-center justify-center">
                <svg className="w-6 h-6 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
              </div>
              <p className="text-sm text-gray-500 font-medium">No innovation analysis yet</p>
              <p className="text-xs text-gray-400 mt-1">
                Click the button below to analyze this specific citation.
              </p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-gray-100 flex-shrink-0 flex items-center justify-between">
          <button
            onClick={handleExtractSingle}
            disabled={isExtracting}
            className="px-4 py-2 text-sm font-bold bg-amber-500 text-white rounded-lg hover:bg-amber-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-all flex items-center gap-2"
          >
            {isExtracting ? (
              <>
                <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Analyzing...
              </>
            ) : hasInsight ? (
              <>
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Re-analyze
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
                Analyze this edge
              </>
            )}
          </button>
          <button
            onClick={handleClose}
            className="px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-all"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
