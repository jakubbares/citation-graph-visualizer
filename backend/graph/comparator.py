"""
Paper Comparison Service - Analyze differences between papers
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from graph.models import ResearchGraph, PaperNode
from extractors.llm_client import get_llm_client


@dataclass
class PaperComparison:
    """Comparison between two papers"""
    paper1_id: str
    paper2_id: str
    paper1_title: str
    paper2_title: str
    
    similarities: List[str]
    differences: List[str]
    relationship_type: str  # 'extends', 'compares', 'builds_on', 'unrelated'
    
    architecture_diff: Optional[str] = None
    contribution_diff: Optional[str] = None
    method_diff: Optional[str] = None
    

class PaperComparator:
    """Service for comparing papers and finding differences"""
    
    def __init__(self):
        self.llm_client = get_llm_client()
    
    def compare_papers(
        self,
        paper1: PaperNode,
        paper2: PaperNode,
        detailed: bool = True
    ) -> PaperComparison:
        """
        Compare two papers and identify similarities and differences
        
        Args:
            paper1: First paper node
            paper2: Second paper node
            detailed: Whether to include detailed analysis
            
        Returns:
            PaperComparison object
        """
        print(f"🔍 Comparing papers:")
        print(f"   1. {paper1.title[:60]}...")
        print(f"   2. {paper2.title[:60]}...")
        
        # Create comparison prompt
        prompt = f"""
Compare these two research papers and identify their similarities and differences.

Paper 1:
Title: {paper1.title}
Authors: {', '.join(paper1.authors[:5])}
Abstract: {paper1.abstract[:1000]}

Paper 2:
Title: {paper2.title}
Authors: {', '.join(paper2.authors[:5])}
Abstract: {paper2.abstract[:1000]}

Analyze:
1. What are the key similarities between these papers?
2. What are the key differences?
3. How do they relate? (extends, compares, builds_on, addresses_similar_problem, or unrelated)
4. If applicable, differences in: architecture, contribution, methodology

Return JSON:
{{
  "similarities": ["similarity 1", "similarity 2", ...],
  "differences": ["difference 1", "difference 2", ...],
  "relationship_type": "extends|compares|builds_on|similar|unrelated",
  "architecture_diff": "Architectural differences (if applicable)",
  "contribution_diff": "Contribution differences",
  "method_diff": "Methodological differences"
}}

Return ONLY the JSON, no other text.
"""
        
        try:
            response = self.llm_client.chat_completion([
                {"role": "system", "content": "You are a helpful research assistant that compares papers."},
                {"role": "user", "content": prompt}
            ])
            
            import json
            comparison_data = json.loads(response)
            
            comparison = PaperComparison(
                paper1_id=paper1.id,
                paper2_id=paper2.id,
                paper1_title=paper1.title,
                paper2_title=paper2.title,
                similarities=comparison_data.get("similarities", []),
                differences=comparison_data.get("differences", []),
                relationship_type=comparison_data.get("relationship_type", "unrelated"),
                architecture_diff=comparison_data.get("architecture_diff"),
                contribution_diff=comparison_data.get("contribution_diff"),
                method_diff=comparison_data.get("method_diff")
            )
            
            print(f"✅ Comparison complete:")
            print(f"   - Relationship: {comparison.relationship_type}")
            print(f"   - Similarities: {len(comparison.similarities)}")
            print(f"   - Differences: {len(comparison.differences)}")
            
            return comparison
            
        except Exception as e:
            print(f"❌ Error comparing papers: {e}")
            # Return default comparison
            return PaperComparison(
                paper1_id=paper1.id,
                paper2_id=paper2.id,
                paper1_title=paper1.title,
                paper2_title=paper2.title,
                similarities=[],
                differences=[],
                relationship_type="unrelated"
            )
    
    def compare_within_cluster(
        self,
        graph: ResearchGraph,
        cluster_id: int
    ) -> List[PaperComparison]:
        """
        Compare all papers within a cluster
        
        Args:
            graph: Research graph with cluster assignments
            cluster_id: Cluster to analyze
            
        Returns:
            List of comparisons between papers in the cluster
        """
        # Get papers in cluster
        cluster_papers = [
            node for node in graph.nodes
            if node.attributes.get("cluster_id") == cluster_id
        ]
        
        if len(cluster_papers) < 2:
            print(f"⚠️  Cluster {cluster_id} has fewer than 2 papers")
            return []
        
        print(f"🔍 Comparing {len(cluster_papers)} papers in cluster {cluster_id}...")
        
        comparisons = []
        
        # Compare each paper with others (limit to avoid too many comparisons)
        max_comparisons = min(20, len(cluster_papers) * 2)
        comparison_count = 0
        
        for i, paper1 in enumerate(cluster_papers):
            if comparison_count >= max_comparisons:
                break
            
            # Compare with next few papers
            for paper2 in cluster_papers[i+1:i+4]:
                if comparison_count >= max_comparisons:
                    break
                
                comparison = self.compare_papers(paper1, paper2, detailed=False)
                comparisons.append(comparison)
                comparison_count += 1
        
        print(f"✅ Completed {len(comparisons)} comparisons")
        return comparisons
    
    def add_edge_labels_to_graph(
        self,
        graph: ResearchGraph,
        comparison: PaperComparison
    ) -> ResearchGraph:
        """
        Add comparison data as edge labels in the graph
        
        Args:
            graph: Research graph
            comparison: Paper comparison
            
        Returns:
            Updated graph
        """
        # Find edge between the two papers
        for edge in graph.edges:
            if ((edge.from_paper == comparison.paper1_id and edge.to_paper == comparison.paper2_id) or
                (edge.from_paper == comparison.paper2_id and edge.to_paper == comparison.paper1_id)):
                
                # Update edge with comparison data
                edge.contribution_type = comparison.relationship_type
                edge.context = f"Similarities: {'; '.join(comparison.similarities[:2])}. Differences: {'; '.join(comparison.differences[:2])}"
                edge.attributes["comparison"] = {
                    "similarities": comparison.similarities,
                    "differences": comparison.differences,
                    "architecture_diff": comparison.architecture_diff,
                    "contribution_diff": comparison.contribution_diff,
                    "method_diff": comparison.method_diff
                }
                
                # Update visual based on relationship type
                if comparison.relationship_type == "extends":
                    edge.visual["color"] = "#10b981"  # green
                    edge.visual["thickness"] = 3
                elif comparison.relationship_type == "compares":
                    edge.visual["color"] = "#f59e0b"  # orange
                    edge.visual["thickness"] = 2
                elif comparison.relationship_type == "builds_on":
                    edge.visual["color"] = "#3b82f6"  # blue
                    edge.visual["thickness"] = 3
                elif comparison.relationship_type == "similar":
                    edge.visual["color"] = "#8b5cf6"  # purple
                    edge.visual["thickness"] = 2
                
                break
        
        return graph


# Global instance
_comparator = None


def get_comparator() -> PaperComparator:
    """Get or create global comparator instance"""
    global _comparator
    if _comparator is None:
        _comparator = PaperComparator()
    return _comparator
