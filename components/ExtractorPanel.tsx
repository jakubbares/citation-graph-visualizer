'use client';

import React from 'react';
import type { ExtractorConfig, GeneratedSchema, AttributeSchema } from '@/lib/api';

interface ExtractorPanelProps {
  // Legacy extractors
  onExtract: (extractors: ExtractorConfig[]) => void;
  onExtractEdges?: () => void;
  isLoading?: boolean;
  isExtractingEdges?: boolean;
  edgesExtracted?: boolean;

  // Dynamic schema
  schema: GeneratedSchema | null;
  onGenerateSchema: () => void;
  isGeneratingSchema?: boolean;
  onExtractDynamic: (attributeKeys: string[]) => void;
  isExtractingDynamic?: boolean;
  dynamicExtracted?: boolean;

  // Overlay toggles — which attributes are shown on the graph
  activeOverlays: string[];
  onToggleOverlay: (key: string) => void;
}

export default function ExtractorPanel({
  onExtract,
  onExtractEdges,
  isLoading = false,
  isExtractingEdges = false,
  edgesExtracted = false,
  schema,
  onGenerateSchema,
  isGeneratingSchema = false,
  onExtractDynamic,
  isExtractingDynamic = false,
  dynamicExtracted = false,
  activeOverlays,
  onToggleOverlay,
}: ExtractorPanelProps) {
  const [selectedExtractors, setSelectedExtractors] = React.useState<string[]>([]);
  const [selectedSchemaKeys, setSelectedSchemaKeys] = React.useState<string[]>([]);

  // Pre-select all schema attributes when schema first arrives
  React.useEffect(() => {
    if (schema) {
      setSelectedSchemaKeys(schema.attributes.map(a => a.key));
    }
  }, [schema]);

  const standardExtractors = [
    {
      name: 'architecture',
      label: 'Architecture',
      description: 'Extract model architecture details',
    },
    {
      name: 'contributions',
      label: 'Contributions',
      description: 'Extract technical contributions',
    },
  ];

  const handleToggle = (extractorName: string) => {
    setSelectedExtractors(prev =>
      prev.includes(extractorName)
        ? prev.filter(e => e !== extractorName)
        : [...prev, extractorName],
    );
  };

  const handleExtract = () => {
    const extractors: ExtractorConfig[] = selectedExtractors.map(name => ({
      type: 'standard',
      name,
    }));
    onExtract(extractors);
  };

  const handleSchemaKeyToggle = (key: string) => {
    setSelectedSchemaKeys(prev =>
      prev.includes(key) ? prev.filter(k => k !== key) : [...prev, key],
    );
  };

  const handleExtractDynamic = () => {
    onExtractDynamic(selectedSchemaKeys);
  };

  return (
    <div className="w-full p-6 bg-white rounded-lg border border-gray-200 shadow-sm space-y-5">
      <h3 className="text-lg font-semibold">Extract Features</h3>

      {/* ────────────── 1. Topic-Aware Schema ────────────── */}
      <div className="space-y-3">
        <div className="text-sm font-medium text-gray-700">
          Topic-Aware Attributes
        </div>
        <p className="text-xs text-gray-500">
          AI will read your papers, detect the research topic, and generate 5-7
          custom attributes tailored to that field.
        </p>

        {!schema ? (
          <button
            onClick={onGenerateSchema}
            disabled={isGeneratingSchema}
            className="w-full px-4 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-lg hover:from-indigo-700 hover:to-purple-700 disabled:from-gray-300 disabled:to-gray-300 disabled:cursor-not-allowed transition-all font-bold flex items-center justify-center gap-2 shadow-md"
          >
            {isGeneratingSchema ? (
              <>
                <Spinner />
                Analyzing topic...
              </>
            ) : (
              <>
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
                Generate Custom Schema
              </>
            )}
          </button>
        ) : (
          <div className="space-y-3">
            {/* Topic badge */}
            <div className="flex items-center gap-2 p-3 bg-indigo-50 border border-indigo-200 rounded-lg">
              <div className="w-2 h-2 rounded-full bg-indigo-500 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <span className="text-sm font-bold text-indigo-900">
                  {schema.topic}
                </span>
                <p className="text-xs text-indigo-600 truncate">
                  {schema.topic_description}
                </p>
              </div>
              <button
                onClick={onGenerateSchema}
                disabled={isGeneratingSchema}
                className="text-xs text-indigo-500 hover:text-indigo-700 underline flex-shrink-0"
                title="Re-generate schema"
              >
                {isGeneratingSchema ? <Spinner /> : 'Redo'}
              </button>
            </div>

            {/* Attribute checkboxes */}
            <div className="space-y-1.5 max-h-64 overflow-y-auto pr-1">
              {schema.attributes.map((attr, idx) => {
                const palette = attr.color_palette;
                const accentColor = palette[0] || '#6366F1';
                const isSelected = selectedSchemaKeys.includes(attr.key);
                const isActive = activeOverlays.includes(attr.key);

                return (
                  <div
                    key={attr.key}
                    className="flex items-start gap-2 p-2.5 rounded-lg border border-gray-100 hover:border-gray-200 transition-colors"
                  >
                    {/* Select for extraction */}
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => handleSchemaKeyToggle(attr.key)}
                      disabled={isExtractingDynamic}
                      className="mt-0.5 accent-indigo-600"
                    />

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <div
                          className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                          style={{ backgroundColor: accentColor }}
                        />
                        <span className="text-sm font-semibold text-gray-900 truncate">
                          {attr.label}
                        </span>
                      </div>
                      <p className="text-[11px] text-gray-500 mt-0.5 line-clamp-2">
                        {attr.description}
                      </p>
                      {/* Value pills */}
                      <div className="flex flex-wrap gap-1 mt-1.5">
                        {attr.suggested_values.slice(0, 5).map((val, vi) => (
                          <span
                            key={vi}
                            className="px-1.5 py-0.5 rounded text-[10px] font-medium"
                            style={{
                              backgroundColor: `${palette[vi % palette.length]}18`,
                              color: palette[vi % palette.length],
                            }}
                          >
                            {val}
                          </span>
                        ))}
                        {attr.suggested_values.length > 5 && (
                          <span className="text-[10px] text-gray-400">
                            +{attr.suggested_values.length - 5} more
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Overlay toggle (only available after extraction) */}
                    {dynamicExtracted && (
                      <button
                        onClick={() => onToggleOverlay(attr.key)}
                        className={`mt-0.5 p-1 rounded transition-colors flex-shrink-0 ${
                          isActive
                            ? 'bg-indigo-100 text-indigo-700'
                            : 'bg-gray-100 text-gray-400 hover:text-gray-600'
                        }`}
                        title={isActive ? 'Hide on graph' : 'Show on graph'}
                      >
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          {isActive ? (
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                          ) : (
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L3 3m6.878 6.878L21 21" />
                          )}
                        </svg>
                      </button>
                    )}
                  </div>
                );
              })}
            </div>

            {/* Extract button */}
            <button
              onClick={handleExtractDynamic}
              disabled={selectedSchemaKeys.length === 0 || isExtractingDynamic}
              className="w-full px-4 py-2.5 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors font-bold flex items-center justify-center gap-2"
            >
              {isExtractingDynamic ? (
                <>
                  <Spinner />
                  Extracting attributes...
                </>
              ) : dynamicExtracted ? (
                <>
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  Re-extract ({selectedSchemaKeys.length} attributes)
                </>
              ) : (
                `Extract ${selectedSchemaKeys.length} Attributes`
              )}
            </button>

            {dynamicExtracted && (
              <p className="text-xs text-emerald-600 font-medium">
                Attributes extracted! Toggle the eye icon on each attribute to show/hide on the graph.
              </p>
            )}
          </div>
        )}
      </div>

      {/* ─── Divider ─── */}
      <div className="border-t border-gray-200" />

      {/* ────────────── 2. Standard extractors (legacy) ────────────── */}
      <details className="group">
        <summary className="text-sm font-medium text-gray-700 cursor-pointer select-none flex items-center gap-1">
          <svg className="w-4 h-4 transition-transform group-open:rotate-90" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
          Standard Extractors
        </summary>

        <div className="mt-3 space-y-2">
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

          <button
            onClick={handleExtract}
            disabled={selectedExtractors.length === 0 || isLoading}
            className="w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors font-medium"
          >
            {isLoading ? 'Extracting...' : `Extract (${selectedExtractors.length} selected)`}
          </button>
        </div>
      </details>

      {/* ─── Divider ─── */}
      <div className="border-t border-gray-200" />

      {/* ────────────── 3. Edge analysis ────────────── */}
      <div>
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
              <Spinner />
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
  );
}


function Spinner() {
  return (
    <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
      <circle
        className="opacity-25"
        cx="12" cy="12" r="10"
        stroke="currentColor" strokeWidth="4" fill="none"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      />
    </svg>
  );
}
