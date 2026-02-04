'use client';

import React, { useState } from 'react';
import GraphCanvas from '@/components/GraphCanvas';
import PaperUpload from '@/components/PaperUpload';
import ExtractorPanel from '@/components/ExtractorPanel';
import VisualEncodingPanel from '@/components/VisualEncodingPanel';
import DetailPanel from '@/components/DetailPanel';
import { GraphAPI, type ResearchGraph, type ExtractorConfig } from '@/lib/api';

export default function Home() {
  const [graph, setGraph] = useState<ResearchGraph | null>(null);
  const [isBuilding, setIsBuilding] = useState(false);
  const [isExtracting, setIsExtracting] = useState(false);
  const [isVisualizing, setIsVisualizing] = useState(false);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [selectedEdgeId, setSelectedEdgeId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleBuildGraph = async (files: File[], includeIntermediate: boolean) => {
    try {
      setIsBuilding(true);
      setError(null);
      console.log('Building graph from files:', files.map(f => f.name));
      console.log('Include intermediate papers:', includeIntermediate);

      const response = await GraphAPI.buildGraph(files, {
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

      const response = await GraphAPI.extractFeatures(graph.id, extractors);
      
      // Refresh graph
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

  const handleApplyVisualEncoding = async (encoding: any) => {
    if (!graph) return;

    try {
      setIsVisualizing(true);
      setError(null);
      console.log('Applying visual encoding:', encoding);

      const response = await GraphAPI.visualizeGraph(graph.id, encoding);
      setGraph(response.styled_graph);
      
      console.log('Visual encoding applied successfully');
    } catch (err: any) {
      console.error('Error applying visual encoding:', err);
      setError(err.message || 'Failed to apply visual encoding');
    } finally {
      setIsVisualizing(false);
    }
  };

  return (
    <div className="h-screen flex flex-col bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      {/* Modern Header with gradient */}
      <header className="bg-white/80 backdrop-blur-md border-b border-gray-200/50 px-6 py-4 shadow-sm">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg">
              <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
              </svg>
            </div>
            <div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                Citation Graph Visualizer
              </h1>
              <p className="text-sm text-gray-600 mt-0.5">
                Interactive research paper citation network analysis
              </p>
            </div>
          </div>
          {graph && (
            <div className="flex items-center gap-6">
              <div className="flex items-center gap-2 px-4 py-2 bg-blue-100 rounded-lg">
                <div className="w-2 h-2 rounded-full bg-blue-600 animate-pulse"></div>
                <span className="text-sm font-semibold text-blue-900">{graph.nodes.length}</span>
                <span className="text-sm text-blue-700">papers</span>
              </div>
              <div className="flex items-center gap-2 px-4 py-2 bg-indigo-100 rounded-lg">
                <div className="w-2 h-2 rounded-full bg-indigo-600 animate-pulse"></div>
                <span className="text-sm font-semibold text-indigo-900">{graph.edges.length}</span>
                <span className="text-sm text-indigo-700">citations</span>
              </div>
            </div>
          )}
        </div>
      </header>

      {/* Error banner */}
      {error && (
        <div className="bg-red-50 border-b border-red-200 px-6 py-3">
          <div className="flex items-start">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-800">{error}</p>
            </div>
            <div className="ml-auto pl-3">
              <button
                onClick={() => setError(null)}
                className="inline-flex text-red-400 hover:text-red-500"
              >
                <span className="sr-only">Dismiss</span>
                <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Main content with modern panels */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left sidebar - Modern glass morphism design */}
        <div className="w-80 bg-white/60 backdrop-blur-lg border-r border-gray-200/50 overflow-y-auto shadow-xl">
          <div className="p-4 space-y-4">
            <PaperUpload
              onFilesSelected={handleBuildGraph}
              isLoading={isBuilding}
            />
            
            {graph && (
              <>
                <ExtractorPanel
                  onExtract={handleExtract}
                  isLoading={isExtracting}
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

        {/* Center - Graph visualization with modern styling */}
        <div className="flex-1 relative">
          <GraphCanvas
            graph={graph}
            onNodeSelect={setSelectedNodeId}
            onEdgeSelect={setSelectedEdgeId}
            layout="force"
          />
        </div>

        {/* Right sidebar - Modern glass morphism design */}
        <div className="w-96 bg-white/60 backdrop-blur-lg border-l border-gray-200/50 overflow-hidden shadow-xl">
          <DetailPanel
            graph={graph}
            selectedNodeId={selectedNodeId}
            selectedEdgeId={selectedEdgeId}
          />
        </div>
      </div>
    </div>
  );
}
