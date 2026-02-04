import type { Stylesheet } from 'cytoscape';

/**
 * Modern, beautiful stylesheet for citation graph visualization
 * Based on best practices from Neo4j Bloom, Gephi, and modern data viz
 */
export function getModernCytoscapeStyle(): Stylesheet[] {
  return [
    // ============ BASE NODE STYLES ============
    {
      selector: 'node',
      style: {
        // Size and shape
        'width': 'data(size)',
        'height': 'data(size)',
        'shape': 'ellipse',
        
        // Background - gradient effect
        'background-color': '#4A90E2',
        'background-opacity': 0.9,
        
        // Border - modern outline
        'border-width': 3,
        'border-color': '#2E5C8A',
        'border-opacity': 0.8,
        
        // Shadow for depth
        'box-shadow': '0 4px 12px rgba(0,0,0,0.15)',
        
        // Label styling
        'label': 'data(label)',
        'color': '#2C3E50',
        'font-family': '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
        'font-size': '12px',
        'font-weight': '600',
        'text-valign': 'center',
        'text-halign': 'center',
        'text-wrap': 'wrap',
        'text-max-width': '120px',
        
        // Text background for readability
        'text-background-color': '#ffffff',
        'text-background-opacity': 0.85,
        'text-background-padding': '4px',
        'text-background-shape': 'roundrectangle',
        
        // Text outline
        'text-outline-color': '#ffffff',
        'text-outline-width': 2,
        
        // Smooth transitions
        'transition-property': 'background-color, border-color, border-width, width, height',
        'transition-duration': '0.3s',
        'transition-timing-function': 'ease-in-out',
      },
    },

    // ============ NODE HOVER EFFECT ============
    {
      selector: 'node:hover',
      style: {
        'border-width': 5,
        'border-color': '#F39C12',
        'box-shadow': '0 8px 24px rgba(243, 156, 18, 0.4)',
        'z-index': 999,
        'overlay-color': '#F39C12',
        'overlay-padding': 8,
        'overlay-opacity': 0.2,
      },
    },

    // ============ NODE SELECTED (CLICKED) ============
    {
      selector: 'node:selected',
      style: {
        'border-width': 6,
        'border-color': '#E74C3C',
        'box-shadow': '0 0 30px rgba(231, 76, 60, 0.6)',
        'z-index': 1000,
        'overlay-color': '#E74C3C',
        'overlay-padding': 10,
        'overlay-opacity': 0.3,
      },
    },

    // ============ NODE HIGHLIGHTED (NEIGHBOR) ============
    {
      selector: 'node.highlighted',
      style: {
        'border-width': 5,
        'border-color': '#27AE60',
        'box-shadow': '0 0 25px rgba(39, 174, 96, 0.5)',
        'z-index': 998,
      },
    },

    // ============ NODE FADED (NOT SELECTED/NEIGHBOR) ============
    {
      selector: 'node.faded',
      style: {
        'opacity': 0.3,
      },
    },

    // ============ BASE EDGE STYLES ============
    {
      selector: 'edge',
      style: {
        // Line style
        'width': 3,
        'line-color': '#95A5A6',
        'line-opacity': 0.6,
        'curve-style': 'bezier',
        
        // Arrow
        'target-arrow-shape': 'triangle',
        'target-arrow-color': '#95A5A6',
        'target-arrow-fill': 'filled',
        'arrow-scale': 1.5,
        
        // Smooth curves
        'control-point-step-size': 40,
        
        // Shadow for depth
        'line-shadow-color': 'rgba(0,0,0,0.1)',
        'line-shadow-blur': 4,
        'line-shadow-offset-x': 2,
        'line-shadow-offset-y': 2,
        
        // Smooth transitions
        'transition-property': 'line-color, width, line-opacity',
        'transition-duration': '0.3s',
        'transition-timing-function': 'ease-in-out',
      },
    },

    // ============ EDGE HOVER EFFECT ============
    {
      selector: 'edge:hover',
      style: {
        'width': 5,
        'line-color': '#3498DB',
        'target-arrow-color': '#3498DB',
        'line-opacity': 1,
        'z-index': 999,
      },
    },

    // ============ EDGE SELECTED ============
    {
      selector: 'edge:selected',
      style: {
        'width': 6,
        'line-color': '#E67E22',
        'target-arrow-color': '#E67E22',
        'line-opacity': 1,
        'z-index': 1000,
      },
    },

    // ============ EDGE HIGHLIGHTED ============
    {
      selector: 'edge.highlighted',
      style: {
        'width': 5,
        'line-color': '#27AE60',
        'target-arrow-color': '#27AE60',
        'line-opacity': 1,
        'z-index': 998,
      },
    },

    // ============ EDGE FADED ============
    {
      selector: 'edge.faded',
      style: {
        'opacity': 0.15,
      },
    },

    // ============ EDGE LABELS ============
    {
      selector: 'edge[label]',
      style: {
        'label': 'data(label)',
        'font-size': '10px',
        'font-weight': '500',
        'color': '#7F8C8D',
        'text-background-color': '#ffffff',
        'text-background-opacity': 0.9,
        'text-background-padding': '3px',
        'text-background-shape': 'roundrectangle',
        'text-rotation': 'autorotate',
        'text-margin-y': -10,
      },
    },

    // ============ INPUT PAPERS (user uploaded) ============
    {
      selector: 'node[paper_source = "input"]',
      style: {
        'border-width': 4,
        'border-color': '#2980B9',
        'background-opacity': 1.0,
      },
    },

    // ============ INTERMEDIATE PAPERS (from Semantic Scholar) ============
    {
      selector: 'node[paper_source = "intermediate"]',
      style: {
        'border-width': 2,
        'border-style': 'dashed',
        'border-color': '#95A5A6',
        'background-opacity': 0.7,
      },
    },

    // ============ COLOR SCHEMES BY CATEGORY ============
    {
      selector: 'node[architecture_type = "GNN"]',
      style: {
        'background-color': '#9B59B6',
        'border-color': '#6C3483',
      },
    },
    {
      selector: 'node[architecture_type = "Transformer"]',
      style: {
        'background-color': '#3498DB',
        'border-color': '#2874A6',
      },
    },
    {
      selector: 'node[architecture_type = "CNN"]',
      style: {
        'background-color': '#E74C3C',
        'border-color': '#C0392B',
      },
    },
    {
      selector: 'node[architecture_type = "RNN"]',
      style: {
        'background-color': '#F39C12',
        'border-color': '#D68910',
      },
    },
    {
      selector: 'node[architecture_type = "Hybrid"]',
      style: {
        'background-color': '#1ABC9C',
        'border-color': '#148F77',
      },
    },

    // ============ NODE SIZE VARIATIONS ============
    {
      selector: 'node[citation_count > 100]',
      style: {
        'width': 70,
        'height': 70,
        'font-size': '14px',
      },
    },
    {
      selector: 'node[citation_count > 50][citation_count <= 100]',
      style: {
        'width': 55,
        'height': 55,
        'font-size': '13px',
      },
    },
    {
      selector: 'node[citation_count <= 50]',
      style: {
        'width': 40,
        'height': 40,
        'font-size': '11px',
      },
    },

    // ============ EDGE RELATIONSHIP TYPES ============
    {
      selector: 'edge[contribution_type = "foundation"]',
      style: {
        'line-color': '#E74C3C',
        'target-arrow-color': '#E74C3C',
        'width': 4,
      },
    },
    {
      selector: 'edge[contribution_type = "extension"]',
      style: {
        'line-color': '#3498DB',
        'target-arrow-color': '#3498DB',
        'width': 3,
      },
    },
    {
      selector: 'edge[contribution_type = "baseline"]',
      style: {
        'line-color': '#95A5A6',
        'target-arrow-color': '#95A5A6',
        'line-style': 'dashed',
        'width': 2,
      },
    },
  ];
}

/**
 * Color palette for categorical data (architecture types, etc.)
 * Based on ColorBrewer and modern data visualization best practices
 */
export const COLOR_PALETTE = {
  // Architecture types
  GNN: '#9B59B6',
  Transformer: '#3498DB',
  CNN: '#E74C3C',
  RNN: '#F39C12',
  Hybrid: '#1ABC9C',
  MLP: '#16A085',
  ResNet: '#E67E22',
  LSTM: '#D35400',
  GCN: '#8E44AD',
  GAT: '#2980B9',
  
  // Contribution types
  architecture: '#9B59B6',
  algorithm: '#3498DB',
  dataset: '#E74C3C',
  analysis: '#F39C12',
  framework: '#1ABC9C',
  
  // Relationship types
  foundation: '#E74C3C',
  extension: '#3498DB',
  baseline: '#95A5A6',
  dataset_use: '#F39C12',
  critique: '#E67E22',
  
  // UI colors
  background: '#F8F9FA',
  backgroundDark: '#ECF0F1',
  text: '#2C3E50',
  textLight: '#7F8C8D',
  border: '#BDC3C7',
  hover: '#F39C12',
  selected: '#E74C3C',
  highlighted: '#27AE60',
};

/**
 * Layout configurations for different visualization modes
 */
export const LAYOUT_CONFIGS = {
  // Modern force-directed layout with physics
  force: {
    name: 'cose',
    animate: true,
    animationDuration: 1000,
    animationEasing: 'ease-out-cubic',
    nodeRepulsion: 400000,
    nodeOverlap: 20,
    idealEdgeLength: 150,
    edgeElasticity: 200,
    gravity: 0.8,
    numIter: 1000,
    initialTemp: 200,
    coolingFactor: 0.95,
    minTemp: 1.0,
  },
  
  // Hierarchical layout (temporal/chronological)
  hierarchical: {
    name: 'dagre',
    rankDir: 'TB',
    nodeSep: 100,
    rankSep: 150,
    animate: true,
    animationDuration: 800,
    animationEasing: 'ease-in-out-cubic',
  },
  
  // Circular layout (for small graphs)
  circular: {
    name: 'circle',
    radius: 300,
    animate: true,
    animationDuration: 800,
    animationEasing: 'ease-out-quad',
    spacingFactor: 1.5,
  },
  
  // Grid layout (for comparison)
  grid: {
    name: 'grid',
    rows: undefined,
    cols: undefined,
    animate: true,
    animationDuration: 600,
    animationEasing: 'ease-in-out',
    spacingFactor: 1.5,
  },
};
