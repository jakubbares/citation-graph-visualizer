'use client';

import React, { useState } from 'react';
import GraphCanvas from '@/components/GraphCanvas';
import PaperUpload from '@/components/PaperUpload';
import ExtractorPanel from '@/components/ExtractorPanel';
import VisualEncodingPanel from '@/components/VisualEncodingPanel';
import EdgeDetailModal from '@/components/EdgeDetailModal';
import InnovationFlowPanel from '@/components/InnovationFlowPanel';
import {
  GraphAPI,
  type ResearchGraph,
  type ExtractorConfig,
  type CitationEdge,
  type GeneratedSchema,
} from '@/lib/api';

export default function Home() {
  const [graph, setGraph] = useState<ResearchGraph | null>(null);
  const [isBuilding, setIsBuilding] = useState(false);
  const [isExtracting, setIsExtracting] = useState(false);
  const [isExtractingEdges, setIsExtractingEdges] = useState(false);
  const [isVisualizing, setIsVisualizing] = useState(false);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [selectedEdge, setSelectedEdge] = useState<CitationEdge | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Dynamic schema state
  const [schema, setSchema] = useState<GeneratedSchema | null>(null);
  const [isGeneratingSchema, setIsGeneratingSchema] = useState(false);
  const [isExtractingDynamic, setIsExtractingDynamic] = useState(false);
  const [dynamicExtracted, setDynamicExtracted] = useState(false);
  const [activeOverlays, setActiveOverlays] = useState<string[]>([]);

  const handleBuildGraph = async (papers: Array<{type: 'arxiv' | 'doi' | 'pdf', value: string} | File>, includeIntermediate: boolean) => {
    try {
      setIsBuilding(true);
      setError(null);
      // Reset schema state for new graph
      setSchema(null);
      setDynamicExtracted(false);
      setActiveOverlays([]);
      console.log('Building graph from papers:', papers);
      console.log('Include intermediate papers:', includeIntermediate);

      const response = await GraphAPI.buildGraph(papers, {
        includeIntermediate: includeIntermediate,
        maxDepth: 1,
      });

      setGraph(response.graph);
      console.log('Graph built successfully:', response.stats);
    } catch (err: any) {
      console.error('Error building graph:', err);
      setError(err.message || 'Failed to build graph');
    } finally {
      setIsBuilding(false);
    }
  };

  const handleExtract = async (extractors: ExtractorConfig[]) => {
    if (!graph) return;

    try {
      setIsExtracting(true);
      setError(null);
      console.log('Extracting features:', extractors);

      await GraphAPI.extractFeatures(graph.id, extractors);
      
      const updatedGraph = await GraphAPI.getGraph(graph.id);
      setGraph(updatedGraph);
      
      console.log('Features extracted successfully');
    } catch (err: any) {
      console.error('Error extracting features:', err);
      setError(err.message || 'Failed to extract features');
    } finally {
      setIsExtracting(false);
    }
  };

  const handleExtractEdges = async () => {
    if (!graph) return;

    try {
      setIsExtractingEdges(true);
      setError(null);
      console.log('Extracting edge innovations...');

      const response = await GraphAPI.extractEdgeInnovations(graph.id);
      setGraph(response.graph);

      console.log('Edge innovations extracted:', response.stats);
    } catch (err: any) {
      console.error('Error extracting edge innovations:', err);
      setError(err.message || 'Failed to extract edge innovations');
    } finally {
      setIsExtractingEdges(false);
    }
  };

  const handleApplyVisualEncoding = async (encoding: any) => {
    if (!graph) return;

    try {
      setIsVisualizing(true);
      setError(null);

      const response = await GraphAPI.visualizeGraph(graph.id, encoding);
      setGraph(response.styled_graph);
    } catch (err: any) {
      console.error('Error applying visual encoding:', err);
      setError(err.message || 'Failed to apply visual encoding');
    } finally {
      setIsVisualizing(false);
    }
  };

  // ── Dynamic schema handlers ──────────────────────────────

  const handleGenerateSchema = async () => {
    if (!graph) return;

    try {
      setIsGeneratingSchema(true);
      setError(null);
      console.log('Generating custom schema...');

      const response = await GraphAPI.generateSchema(graph.id);
      setSchema(response.schema);
      // Reset extraction state since schema changed
      setDynamicExtracted(false);
      setActiveOverlays([]);

      console.log('Schema generated:', response.schema.topic);
    } catch (err: any) {
      console.error('Error generating schema:', err);
      setError(err.message || 'Failed to generate schema');
    } finally {
      setIsGeneratingSchema(false);
    }
  };

  const handleExtractDynamic = async (attributeKeys: string[]) => {
    if (!graph) return;

    try {
      setIsExtractingDynamic(true);
      setError(null);
      console.log('Extracting dynamic attributes:', attributeKeys);

      const response = await GraphAPI.extractDynamic(graph.id, attributeKeys);
      setGraph(response.graph);
      setSchema(response.schema);
      setDynamicExtracted(true);
      // Auto-enable first overlay
      if (attributeKeys.length > 0) {
        setActiveOverlays([attributeKeys[0]]);
      }

      console.log('Dynamic extraction complete:', response.stats);
    } catch (err: any) {
      console.error('Error extracting dynamic attributes:', err);
      setError(err.message || 'Failed to extract dynamic attributes');
    } finally {
      setIsExtractingDynamic(false);
    }
  };

  const handleToggleOverlay = (key: string) => {
    setActiveOverlays(prev =>
      prev.includes(key) ? prev.filter(k => k !== key) : [...prev, key],
    );
  };

  const edgesExtracted = graph?.extractors_applied?.includes('edge_innovations') ?? false;

  return (
    <div className="h-screen flex flex-col bg-slate-950">
      {/* Animated background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl animate-pulse" style={{animationDelay: '1s'}}></div>
        <div className="absolute top-1/2 left-1/2 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl animate-pulse" style={{animationDelay: '2s'}}></div>
      </div>

      {/* Header */}
      <header className="relative glass-dark border-b border-white/5 px-8 py-4 shadow-2xl z-10">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-5">
            <div className="relative">
              <div className="absolute inset-0 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl blur-xl opacity-75 animate-pulse"></div>
              <div className="relative w-14 h-14 animated-gradient rounded-2xl flex items-center justify-center shadow-2xl transform hover:scale-110 transition-transform">
                <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
            </div>
            <div>
              <h1 className="text-3xl font-black gradient-text tracking-tight">
                Science Station
              </h1>
              <p className="text-sm text-slate-400 mt-1 font-medium">
                AI-Powered Research Network Analysis
              </p>
            </div>
          </div>
          
          {graph && (() => {
            const inputIds = new Set(graph.nodes.filter(n => n.attributes?.paper_source === 'input').map(n => n.id));
            const visibleNodes = graph.nodes.filter(n => !inputIds.has(n.id));
            const visibleEdges = graph.edges.filter(e => !inputIds.has(e.from_paper) && !inputIds.has(e.to_paper));
            return (
              <div className="flex items-center gap-4">
                {/* Topic badge in header */}
                {schema && (
                  <div className="flex items-center gap-2 px-4 py-2 glass rounded-xl">
                    <div className="w-2 h-2 rounded-full bg-indigo-400 pulse-glow" />
                    <span className="text-sm font-semibold text-indigo-300">{schema.topic}</span>
                  </div>
                )}
                <div className="flex items-center gap-3 px-6 py-3 glass rounded-xl glow-blue">
                  <div className="w-3 h-3 rounded-full bg-emerald-400 pulse-glow"></div>
                  <div>
                    <span className="text-2xl font-bold text-emerald-400">{visibleNodes.length}</span>
                    <span className="text-sm text-slate-300 ml-2">papers</span>
                  </div>
                </div>
                
                <div className="flex items-center gap-3 px-6 py-3 glass rounded-xl glow-purple">
                  <div className="w-3 h-3 rounded-full bg-purple-400 pulse-glow" style={{animationDelay: '0.5s'}}></div>
                  <div>
                    <span className="text-2xl font-bold text-purple-400">{visibleEdges.length}</span>
                    <span className="text-sm text-slate-300 ml-2">citations</span>
                  </div>
                </div>

                <button className="px-6 py-3 animated-gradient text-white font-bold rounded-xl shadow-2xl hover:scale-105 transition-transform">
                  Export
                </button>
              </div>
            );
          })()}
        </div>
      </header>

      {/* Error banner */}
      {error && (
        <div className="relative glass-dark border-b border-red-500/20 px-8 py-4 z-10">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 bg-red-500/20 rounded-full flex items-center justify-center">
              <svg className="h-6 w-6 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <p className="text-red-300 font-medium flex-1">{error}</p>
            <button
              onClick={() => setError(null)}
              className="w-8 h-8 flex items-center justify-center text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded-lg transition-all"
            >
              <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
            </button>
          </div>
        </div>
      )}

      {/* Main content */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* Left sidebar */}
        <div className="w-96 glass-dark border-r border-white/5 overflow-y-auto shadow-2xl z-10">
          <div className="p-6 space-y-6">
            <PaperUpload
              onPapersSubmit={handleBuildGraph}
              isLoading={isBuilding}
            />
            
            {graph && (
              <>
                <ExtractorPanel
                  onExtract={handleExtract}
                  onExtractEdges={handleExtractEdges}
                  isLoading={isExtracting}
                  isExtractingEdges={isExtractingEdges}
                  edgesExtracted={edgesExtracted}
                  schema={schema}
                  onGenerateSchema={handleGenerateSchema}
                  isGeneratingSchema={isGeneratingSchema}
                  onExtractDynamic={handleExtractDynamic}
                  isExtractingDynamic={isExtractingDynamic}
                  dynamicExtracted={dynamicExtracted}
                  activeOverlays={activeOverlays}
                  onToggleOverlay={handleToggleOverlay}
                />
                
                <VisualEncodingPanel
                  graph={graph}
                  onApply={handleApplyVisualEncoding}
                  isLoading={isVisualizing}
                />
              </>
            )}
          </div>
        </div>

        {/* Center - Graph visualization */}
        <div className="flex-1 relative bg-slate-900/50">
          {!graph && (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center">
                <div className="relative mx-auto w-32 h-32 mb-8">
                  <div className="absolute inset-0 animated-gradient rounded-full blur-2xl opacity-50"></div>
                  <div className="relative w-full h-full glass rounded-full flex items-center justify-center">
                    <svg className="w-16 h-16 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                </div>
                <h2 className="text-2xl font-bold text-slate-200 mb-3">Start Your Analysis</h2>
                <p className="text-slate-400 max-w-md">
                  Upload papers or paste ArXiv IDs to build your citation network
                </p>
              </div>
            </div>
          )}
          <GraphCanvas
            graph={graph}
            onNodeSelect={setSelectedNodeId}
            onEdgeSelect={setSelectedEdge}
            layout="timeline"
            schema={schema}
            activeOverlays={activeOverlays}
          />
        </div>
      </div>

      {/* Edge Detail Modal */}
      <EdgeDetailModal
        edge={selectedEdge}
        graph={graph}
        onClose={() => setSelectedEdge(null)}
        onEdgeUpdated={(updatedEdge) => {
          // Update the edge in the graph state so labels refresh
          if (graph) {
            const newEdges = graph.edges.map(e =>
              e.id === updatedEdge.id ? updatedEdge : e
            );
            setGraph({ ...graph, edges: newEdges });
          }
        }}
      />
    </div>
  );
}
