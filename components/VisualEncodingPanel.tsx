'use client';

import React from 'react';
import type { ResearchGraph } from '@/lib/api';

interface VisualEncodingPanelProps {
  graph: ResearchGraph | null;
  onApply: (encoding: {
    color?: { attribute: string };
    size?: { attribute: string };
    shape?: { attribute: string };
  }) => void;
  isLoading?: boolean;
}

export default function VisualEncodingPanel({ graph, onApply, isLoading = false }: VisualEncodingPanelProps) {
  const [colorBy, setColorBy] = React.useState<string>('');
  const [sizeBy, setSizeBy] = React.useState<string>('');
  const [shapeBy, setShapeBy] = React.useState<string>('');

  // Extract available attributes from graph
  const availableAttributes = React.useMemo(() => {
    if (!graph || graph.nodes.length === 0) return [];
    
    const attrs = new Set<string>();
    graph.nodes.forEach(node => {
      Object.keys(node.attributes).forEach(key => attrs.add(key));
    });
    
    return Array.from(attrs);
  }, [graph]);

  const handleApply = () => {
    const encoding: any = {};
    
    if (colorBy) {
      encoding.color = { attribute: colorBy };
    }
    if (sizeBy) {
      encoding.size = { attribute: sizeBy };
    }
    if (shapeBy) {
      encoding.shape = { attribute: shapeBy };
    }
    
    onApply(encoding);
  };

  const handleReset = () => {
    setColorBy('');
    setSizeBy('');
    setShapeBy('');
  };

  if (!graph) {
    return (
      <div className="w-full p-6 bg-white rounded-lg border border-gray-200 shadow-sm">
        <h3 className="text-lg font-semibold mb-2">Visual Encoding</h3>
        <p className="text-sm text-gray-500">Load a graph first</p>
      </div>
    );
  }

  return (
    <div className="w-full p-6 bg-white rounded-lg border border-gray-200 shadow-sm">
      <h3 className="text-lg font-semibold mb-4">Visual Encoding</h3>
      
      <div className="space-y-4">
        {/* Color encoding */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Color by
          </label>
          <select
            value={colorBy}
            onChange={(e) => setColorBy(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            disabled={isLoading || availableAttributes.length === 0}
          >
            <option value="">None</option>
            {availableAttributes.map(attr => (
              <option key={attr} value={attr}>
                {attr}
              </option>
            ))}
          </select>
        </div>

        {/* Size encoding */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Size by
          </label>
          <select
            value={sizeBy}
            onChange={(e) => setSizeBy(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            disabled={isLoading || availableAttributes.length === 0}
          >
            <option value="">None</option>
            <option value="citation_count">Citation Count</option>
            {availableAttributes.map(attr => (
              <option key={attr} value={attr}>
                {attr}
              </option>
            ))}
          </select>
        </div>

        {/* Shape encoding */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Shape by
          </label>
          <select
            value={shapeBy}
            onChange={(e) => setShapeBy(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            disabled={isLoading || availableAttributes.length === 0}
          >
            <option value="">None</option>
            {availableAttributes.map(attr => (
              <option key={attr} value={attr}>
                {attr}
              </option>
            ))}
          </select>
        </div>

        {/* Action buttons */}
        <div className="flex gap-2 pt-2">
          <button
            onClick={handleApply}
            disabled={isLoading || (!colorBy && !sizeBy && !shapeBy)}
            className="flex-1 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors font-medium"
          >
            {isLoading ? 'Applying...' : 'Apply'}
          </button>
          <button
            onClick={handleReset}
            disabled={isLoading}
            className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 disabled:bg-gray-100 disabled:cursor-not-allowed transition-colors"
          >
            Reset
          </button>
        </div>

        {/* Info */}
        {availableAttributes.length === 0 && (
          <div className="text-xs text-gray-500 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
            ℹ️ Extract features first to enable visual encoding
          </div>
        )}
      </div>
    </div>
  );
}
