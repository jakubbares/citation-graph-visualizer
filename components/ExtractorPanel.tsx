'use client';

import React from 'react';
import type { ExtractorConfig } from '@/lib/api';

interface ExtractorPanelProps {
  onExtract: (extractors: ExtractorConfig[]) => void;
  isLoading?: boolean;
}

export default function ExtractorPanel({ onExtract, isLoading = false }: ExtractorPanelProps) {
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
      </div>
    </div>
  );
}
