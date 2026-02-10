'use client';

import React from 'react';
import type { ExtractorConfig } from '@/lib/api';

interface ExtractorPanelProps {
  onExtract: (extractors: ExtractorConfig[]) => void;
  onExtractEdges?: () => void;
  isLoading?: boolean;
  isExtractingEdges?: boolean;
  edgesExtracted?: boolean;
}

export default function ExtractorPanel({
  onExtract,
  onExtractEdges,
  isLoading = false,
  isExtractingEdges = false,
  edgesExtracted = false,
}: ExtractorPanelProps) {
  const [selectedExtractors, setSelectedExtractors] = React.useState<string[]>([]);

  const standardExtractors = [
    {
      name: 'architecture',
      label: 'Architecture',
      description: 'Extract model architecture details'
    },
    {
      name: 'contributions',
      label: 'Contributions',
      description: 'Extract technical contributions'
    },
  ];

  const handleToggle = (extractorName: string) => {
    setSelectedExtractors(prev =>
      prev.includes(extractorName)
        ? prev.filter(e => e !== extractorName)
        : [...prev, extractorName]
    );
  };

  const handleExtract = () => {
    const extractors: ExtractorConfig[] = selectedExtractors.map(name => ({
      type: 'standard',
      name
    }));
    onExtract(extractors);
  };

  return (
    <div className="w-full p-6 bg-white rounded-lg border border-gray-200 shadow-sm">
      <h3 className="text-lg font-semibold mb-4">Extract Features</h3>
      
      <div className="space-y-4">
        {/* Standard extractors */}
        <div className="space-y-2">
          <div className="text-sm font-medium text-gray-700 mb-3">
            Standard Extractors
          </div>
          {standardExtractors.map(extractor => (
            <label
              key={extractor.name}
              className="flex items-start space-x-3 p-3 rounded-lg hover:bg-gray-50 cursor-pointer border border-gray-200"
            >
              <input
                type="checkbox"
                checked={selectedExtractors.includes(extractor.name)}
                onChange={() => handleToggle(extractor.name)}
                className="mt-1"
                disabled={isLoading}
              />
              <div className="flex-1">
                <div className="text-sm font-medium text-gray-900">
                  {extractor.label}
                </div>
                <div className="text-xs text-gray-500">
                  {extractor.description}
                </div>
              </div>
            </label>
          ))}
        </div>

        {/* Extract button */}
        <button
          onClick={handleExtract}
          disabled={selectedExtractors.length === 0 || isLoading}
          className="w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors font-medium"
        >
          {isLoading ? 'Extracting...' : `Extract (${selectedExtractors.length} selected)`}
        </button>

        {/* Divider */}
        <div className="border-t border-gray-200 pt-4">
          <div className="text-sm font-medium text-gray-700 mb-3">
            Edge Analysis
          </div>
          <p className="text-xs text-gray-500 mb-3">
            Use AI to analyze what innovation each paper adopted from the papers it cites. Results appear as labels on edges.
          </p>
          <button
            onClick={onExtractEdges}
            disabled={isExtractingEdges || !onExtractEdges}
            className="w-full px-4 py-3 bg-amber-500 text-white rounded-lg hover:bg-amber-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors font-bold flex items-center justify-center gap-2"
          >
            {isExtractingEdges ? (
              <>
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Analyzing edges...
              </>
            ) : edgesExtracted ? (
              <>
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                Re-extract Edge Innovations
              </>
            ) : (
              'Extract Edge Innovations'
            )}
          </button>
          {edgesExtracted && (
            <p className="text-xs text-emerald-600 mt-2 font-medium">
              Edge innovations extracted. Click edges in the graph to see details.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
