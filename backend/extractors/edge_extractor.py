"""
Edge Innovation Extractor - Uses LLM to extract what innovation
from one paper was adopted/used by another paper.
Analyzes full paper text when available, falls back to abstracts.
"""
import json
import concurrent.futures
from typing import Dict, Any, Optional, List, Tuple
from graph.models import ResearchGraph, CitationEdge, PaperNode
from extractors.llm_client import get_llm_client


SYSTEM_PROMPT = """You are a research analysis expert. Given two papers where Paper A cites Paper B,
identify exactly what idea, method, technique, or result from Paper B was used by Paper A.
Be specific and technical. Focus on the concrete contribution that was adopted or built upon.
Cite specific sections, equations, algorithms, or results when possible."""

USER_PROMPT_TEMPLATE = """Paper A (the citing paper):
Title: {title_a}
{content_a}

Paper B (the cited paper):
Title: {title_b}
{content_b}

What specific idea, method, or result from Paper B does Paper A use or build upon?

Return JSON:
{{
  "short_label": "max 8 words summarizing the adopted innovation",
  "full_insight": "One concise paragraph (3-5 sentences): what Paper A took from Paper B, how it was adapted, and what is different."
}}"""


def _build_paper_content(node: PaperNode, max_chars: int = 6000) -> str:
    """Build the content section for a paper, preferring full text over abstract."""
    parts = []

    # Use full text if available
    full_text = (node.full_text or "").strip()
    abstract = (node.abstract or "").strip()

    if full_text and len(full_text) > len(abstract) + 100:
        # We have real full text (not just abstract copied into full_text)
        parts.append(f"Full text (truncated):\n{full_text[:max_chars]}")
    elif abstract:
        parts.append(f"Abstract:\n{abstract[:2000]}")
    else:
        parts.append("(no content available)")

    return "\n".join(parts)


class EdgeInnovationExtractor:
    """Extracts innovation flow information for citation edges using LLM."""

    def __init__(self):
        self.llm_client = get_llm_client()

    def extract_single(
        self,
        edge: CitationEdge,
        from_node: PaperNode,
        to_node: PaperNode,
    ) -> Dict[str, str]:
        """
        Extract innovation info for a single edge.

        Args:
            edge: The citation edge
            from_node: The citing paper (newer)
            to_node: The cited paper (older)

        Returns:
            Dict with 'short_label' and 'full_insight'
        """
        content_a = _build_paper_content(from_node)
        content_b = _build_paper_content(to_node)

        if content_a == "(no content available)" and content_b == "(no content available)":
            return {
                "short_label": "citation",
                "full_insight": "Insufficient paper data to analyze the relationship.",
            }

        prompt = USER_PROMPT_TEMPLATE.format(
            title_a=from_node.title,
            content_a=content_a,
            title_b=to_node.title,
            content_b=content_b,
        )

        try:
            result = self.llm_client.complete_json(
                prompt, system_prompt=SYSTEM_PROMPT, max_tokens=512
            )

            short_label = result.get("short_label", "citation")
            full_insight = result.get("full_insight", "")

            # Truncate short label if LLM went over
            words = short_label.split()
            if len(words) > 10:
                short_label = " ".join(words[:10]) + "..."

            return {"short_label": short_label, "full_insight": full_insight}

        except Exception as e:
            print(f"   Error extracting edge {from_node.title[:30]}... -> {to_node.title[:30]}...: {e}")
            return {
                "short_label": "citation",
                "full_insight": f"Extraction failed: {str(e)}",
            }

    def extract_single_by_id(
        self,
        graph: ResearchGraph,
        edge_id: str,
    ) -> Optional[Dict[str, str]]:
        """
        Extract innovation info for a single edge identified by ID.

        Args:
            graph: The research graph
            edge_id: The edge ID to extract for

        Returns:
            Dict with 'short_label' and 'full_insight', or None if edge not found
        """
        node_map: Dict[str, PaperNode] = {n.id: n for n in graph.nodes}

        for edge in graph.edges:
            if edge.id == edge_id:
                from_node = node_map.get(edge.from_paper)
                to_node = node_map.get(edge.to_paper)
                if not from_node or not to_node:
                    return None

                print(f"   Extracting single edge: {from_node.title[:40]}... -> {to_node.title[:40]}...")
                result = self.extract_single(edge, from_node, to_node)

                # Store on the edge object in-place
                edge.context = result["short_label"]
                edge.delta_description = result["full_insight"]

                return result

        return None

    def extract_for_graph(
        self,
        graph: ResearchGraph,
        max_parallel: int = 5,
        on_progress: Optional[callable] = None,
    ) -> int:
        """
        Extract innovation info for all edges in a graph (in-place).
        Uses thread pool for parallel LLM calls.

        Args:
            graph: The research graph (edges are modified in-place)
            max_parallel: Max concurrent LLM calls
            on_progress: Optional callback(completed, total)

        Returns:
            Number of edges processed
        """
        node_map: Dict[str, PaperNode] = {n.id: n for n in graph.nodes}

        edges_to_process: List[Tuple[CitationEdge, PaperNode, PaperNode]] = []
        for edge in graph.edges:
            from_node = node_map.get(edge.from_paper)
            to_node = node_map.get(edge.to_paper)
            if from_node and to_node:
                edges_to_process.append((edge, from_node, to_node))

        total = len(edges_to_process)
        if total == 0:
            return 0

        print(f"   Extracting innovations for {total} edges (max {max_parallel} parallel)...")

        completed = 0

        def process_edge(item: Tuple[CitationEdge, PaperNode, PaperNode]) -> None:
            nonlocal completed
            edge, from_node, to_node = item
            result = self.extract_single(edge, from_node, to_node)

            edge.context = result["short_label"]
            edge.delta_description = result["full_insight"]

            completed += 1
            if on_progress:
                on_progress(completed, total)
            print(f"   [{completed}/{total}] {from_node.title[:30]}... -> {to_node.title[:30]}...")

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_parallel) as executor:
            list(executor.map(process_edge, edges_to_process))

        return completed


# Global instance
_edge_extractor = None


def get_edge_extractor() -> EdgeInnovationExtractor:
    """Get or create global edge extractor instance."""
    global _edge_extractor
    if _edge_extractor is None:
        _edge_extractor = EdgeInnovationExtractor()
    return _edge_extractor
