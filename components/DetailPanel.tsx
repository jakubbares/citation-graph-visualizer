'use client';

import React from 'react';
import type { PaperNode, CitationEdge, ResearchGraph } from '@/lib/api';

interface DetailPanelProps {
  graph: ResearchGraph | null;
  selectedNodeId: string | null;
  selectedEdgeId: string | null;
}

export default function DetailPanel({ graph, selectedNodeId, selectedEdgeId }: DetailPanelProps) {
  const selectedNode = React.useMemo(() => {
    if (!graph || !selectedNodeId) return null;
    return graph.nodes.find(n => n.id === selectedNodeId) || null;
  }, [graph, selectedNodeId]);

  const selectedEdge = React.useMemo(() => {
    if (!graph || !selectedEdgeId) return null;
    return graph.edges.find(e => e.id === selectedEdgeId) || null;
  }, [graph, selectedEdgeId]);

  if (!graph) {
    return (
      <div className="w-full h-full p-6 bg-gray-50 flex items-center justify-center">
        <p className="text-gray-500">No graph loaded</p>
      </div>
    );
  }

  if (!selectedNode && !selectedEdge) {
    return (
      <div className="w-full h-full p-6 bg-gray-50 flex items-center justify-center">
        <p className="text-gray-500 text-center">
          Click on a node or edge<br/>to view details
        </p>
      </div>
    );
  }

  if (selectedNode) {
    return <NodeDetails node={selectedNode} />;
  }

  if (selectedEdge) {
    return <EdgeDetails edge={selectedEdge} graph={graph} />;
  }

  return null;
}

function NodeDetails({ node }: { node: PaperNode }) {
  return (
    <div className="w-full h-full overflow-y-auto p-6 bg-white">
      <div className="space-y-6">
        {/* Title */}
        <div>
          <h2 className="text-xl font-bold text-gray-900 mb-2">
            {node.title}
          </h2>
        </div>

        {/* Authors */}
        {node.authors && node.authors.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold text-gray-700 mb-2">Authors</h3>
            <div className="text-sm text-gray-600">
              {node.authors.join(', ')}
            </div>
          </div>
        )}

        {/* Metadata */}
        <div className="grid grid-cols-2 gap-4">
          {node.venue && (
            <div>
              <h4 className="text-xs font-semibold text-gray-500 mb-1">Venue</h4>
              <div className="text-sm text-gray-900">{node.venue}</div>
            </div>
          )}
          {node.publication_date && (
            <div>
              <h4 className="text-xs font-semibold text-gray-500 mb-1">Date</h4>
              <div className="text-sm text-gray-900">{node.publication_date}</div>
            </div>
          )}
        </div>

        {/* Abstract */}
        {node.abstract && (
          <div>
            <h3 className="text-sm font-semibold text-gray-700 mb-2">Abstract</h3>
            <div className="text-sm text-gray-600 leading-relaxed">
              {node.abstract}
            </div>
          </div>
        )}

        {/* Extracted Attributes */}
        {Object.keys(node.attributes).length > 0 && (
          <div>
            <h3 className="text-sm font-semibold text-gray-700 mb-2">Extracted Features</h3>
            <div className="space-y-2">
              {Object.entries(node.attributes).map(([key, value]) => (
                <div key={key} className="p-3 bg-gray-50 rounded-lg border border-gray-200">
                  <div className="text-xs font-semibold text-gray-500 mb-1">
                    {key}
                  </div>
                  <div className="text-sm text-gray-900">
                    {typeof value === 'object' 
                      ? JSON.stringify(value, null, 2)
                      : String(value)}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function EdgeDetails({ edge, graph }: { edge: CitationEdge; graph: ResearchGraph }) {
  const fromNode = graph.nodes.find(n => n.id === edge.from_paper);
  const toNode = graph.nodes.find(n => n.id === edge.to_paper);

  return (
    <div className="w-full h-full overflow-y-auto p-6 bg-white">
      <div className="space-y-6">
        {/* Title */}
        <div>
          <h2 className="text-xl font-bold text-gray-900 mb-2">
            Citation Relationship
          </h2>
        </div>

        {/* Papers */}
        <div className="space-y-4">
          <div>
            <h3 className="text-sm font-semibold text-gray-700 mb-2">From (Citing)</h3>
            <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
              <div className="text-sm font-medium text-gray-900">
                {fromNode?.title || edge.from_paper}
              </div>
            </div>
          </div>

          <div className="text-center text-gray-400">
            ↓
          </div>

          <div>
            <h3 className="text-sm font-semibold text-gray-700 mb-2">To (Cited)</h3>
            <div className="p-3 bg-green-50 rounded-lg border border-green-200">
              <div className="text-sm font-medium text-gray-900">
                {toNode?.title || edge.to_paper}
              </div>
            </div>
          </div>
        </div>

        {/* Relationship details */}
        <div>
          <h3 className="text-sm font-semibold text-gray-700 mb-2">Relationship</h3>
          <div className="space-y-2">
            <div className="flex items-center justify-between p-2 bg-gray-50 rounded">
              <span className="text-xs text-gray-600">Type</span>
              <span className="text-sm font-medium text-gray-900">
                {edge.contribution_type}
              </span>
            </div>
            <div className="flex items-center justify-between p-2 bg-gray-50 rounded">
              <span className="text-xs text-gray-600">Strength</span>
              <span className="text-sm font-medium text-gray-900">
                {(edge.strength * 100).toFixed(0)}%
              </span>
            </div>
          </div>
        </div>

        {/* Context */}
        {edge.context && (
          <div>
            <h3 className="text-sm font-semibold text-gray-700 mb-2">Citation Context</h3>
            <div className="p-3 bg-gray-50 rounded-lg border border-gray-200 text-sm text-gray-600 leading-relaxed">
              {edge.context}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
