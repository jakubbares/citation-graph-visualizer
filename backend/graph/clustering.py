"""
Clustering algorithms for grouping papers by similarity
"""
from typing import List, Dict, Any, Optional
import networkx as nx
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from graph.models import ResearchGraph, PaperNode


class PaperClusterer:
    """Service for clustering papers based on content and citations"""
    
    def __init__(self):
        self.vectorizer = None
        self.embeddings = None
    
    def cluster_by_content(
        self,
        graph: ResearchGraph,
        n_clusters: int = 5,
        method: str = "kmeans"
    ) -> ResearchGraph:
        """
        Cluster papers by content similarity using text embeddings
        
        Args:
            graph: Research graph
            n_clusters: Number of clusters
            method: Clustering method ('kmeans' or 'hierarchical')
            
        Returns:
            Graph with cluster assignments added to node attributes
        """
        print(f"🔍 Clustering {len(graph.nodes)} papers by content...")
        
        # Prepare texts for clustering
        texts = []
        node_ids = []
        for node in graph.nodes:
            # Combine title and abstract for better clustering
            text = f"{node.title} {node.abstract}"
            texts.append(text)
            node_ids.append(node.id)
        
        if len(texts) < n_clusters:
            print(f"⚠️  Too few papers ({len(texts)}) for {n_clusters} clusters")
            n_clusters = max(2, len(texts) // 2)
        
        # Create TF-IDF embeddings
        self.vectorizer = TfidfVectorizer(
            max_features=500,
            stop_words='english',
            ngram_range=(1, 2)
        )
        
        self.embeddings = self.vectorizer.fit_transform(texts)
        
        # Cluster
        if method == "kmeans":
            clusterer = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        else:  # hierarchical
            clusterer = AgglomerativeClustering(n_clusters=n_clusters)
        
        labels = clusterer.fit_predict(self.embeddings.toarray())
        
        # Assign cluster IDs to nodes
        cluster_assignments = {}
        for node_id, cluster_id in zip(node_ids, labels):
            cluster_assignments[node_id] = int(cluster_id)
        
        # Update graph nodes
        cluster_sizes = {}
        for node in graph.nodes:
            cluster_id = cluster_assignments.get(node.id, 0)
            node.cluster_id = cluster_id
            node.attributes["cluster_id"] = cluster_id
            cluster_sizes[cluster_id] = cluster_sizes.get(cluster_id, 0) + 1
        
        # Add cluster metadata to graph
        graph.metadata["clusters"] = {
            "method": method,
            "n_clusters": n_clusters,
            "cluster_sizes": cluster_sizes
        }
        
        print(f"✅ Created {n_clusters} clusters:")
        for cluster_id, size in sorted(cluster_sizes.items()):
            print(f"   Cluster {cluster_id}: {size} papers")
        
        return graph
    
    def cluster_by_citations(
        self,
        graph: ResearchGraph,
        n_clusters: int = 5,
        method: str = "louvain"
    ) -> ResearchGraph:
        """
        Cluster papers by citation network structure
        
        Args:
            graph: Research graph
            n_clusters: Target number of clusters (not used for Louvain)
            method: Clustering method ('louvain', 'label_propagation')
            
        Returns:
            Graph with cluster assignments
        """
        print(f"🔍 Clustering papers by citation network ({method})...")
        
        # Build NetworkX graph
        G = nx.DiGraph()
        
        # Add nodes
        for node in graph.nodes:
            G.add_node(node.id)
        
        # Add edges
        for edge in graph.edges:
            G.add_edge(edge.from_paper, edge.to_paper)
        
        # Convert to undirected for community detection
        G_undirected = G.to_undirected()
        
        # Detect communities
        if method == "louvain":
            try:
                import community.community_louvain as community_louvain
                partition = community_louvain.best_partition(G_undirected)
            except ImportError:
                print("⚠️  python-louvain not installed, falling back to label propagation")
                method = "label_propagation"
        
        if method == "label_propagation":
            # Use NetworkX's label propagation
            communities = list(nx.community.label_propagation_communities(G_undirected))
            partition = {}
            for cluster_id, community in enumerate(communities):
                for node_id in community:
                    partition[node_id] = cluster_id
        
        # Assign cluster IDs to nodes
        cluster_sizes = {}
        for node in graph.nodes:
            cluster_id = partition.get(node.id, 0)
            node.cluster_id = cluster_id
            node.attributes["cluster_id"] = cluster_id
            cluster_sizes[cluster_id] = cluster_sizes.get(cluster_id, 0) + 1
        
        # Add cluster metadata
        graph.metadata["clusters"] = {
            "method": method,
            "n_clusters": len(cluster_sizes),
            "cluster_sizes": cluster_sizes
        }
        
        print(f"✅ Detected {len(cluster_sizes)} clusters:")
        for cluster_id, size in sorted(cluster_sizes.items()):
            print(f"   Cluster {cluster_id}: {size} papers")
        
        return graph
    
    def cluster_hybrid(
        self,
        graph: ResearchGraph,
        n_clusters: int = 5,
        content_weight: float = 0.7,
        citation_weight: float = 0.3
    ) -> ResearchGraph:
        """
        Cluster papers using both content and citation structure
        
        Args:
            graph: Research graph
            n_clusters: Number of clusters
            content_weight: Weight for content similarity (0-1)
            citation_weight: Weight for citation similarity (0-1)
            
        Returns:
            Graph with cluster assignments
        """
        print(f"🔍 Hybrid clustering (content: {content_weight}, citations: {citation_weight})...")
        
        # Get content embeddings
        texts = []
        node_ids = []
        node_id_to_idx = {}
        
        for idx, node in enumerate(graph.nodes):
            text = f"{node.title} {node.abstract}"
            texts.append(text)
            node_ids.append(node.id)
            node_id_to_idx[node.id] = idx
        
        # TF-IDF embeddings
        vectorizer = TfidfVectorizer(max_features=500, stop_words='english')
        content_matrix = vectorizer.fit_transform(texts).toarray()
        
        # Build citation similarity matrix
        n = len(node_ids)
        citation_matrix = np.zeros((n, n))
        
        # Create adjacency matrix
        G = nx.DiGraph()
        for node in graph.nodes:
            G.add_node(node.id)
        for edge in graph.edges:
            G.add_edge(edge.from_paper, edge.to_paper)
        
        # Compute citation-based similarity (using common neighbors)
        for i, node_id_i in enumerate(node_ids):
            for j, node_id_j in enumerate(node_ids):
                if i != j:
                    # Count common neighbors (both in and out)
                    neighbors_i = set(G.predecessors(node_id_i)) | set(G.successors(node_id_i))
                    neighbors_j = set(G.predecessors(node_id_j)) | set(G.successors(node_id_j))
                    
                    if neighbors_i or neighbors_j:
                        jaccard = len(neighbors_i & neighbors_j) / len(neighbors_i | neighbors_j)
                        citation_matrix[i, j] = jaccard
        
        # Normalize content similarity
        content_sim = cosine_similarity(content_matrix)
        
        # Combine similarities
        combined_sim = content_weight * content_sim + citation_weight * citation_matrix
        
        # Convert similarity to distance
        distance_matrix = 1 - combined_sim
        
        # Cluster using hierarchical clustering
        if n < n_clusters:
            n_clusters = max(2, n // 2)
        
        clusterer = AgglomerativeClustering(
            n_clusters=n_clusters,
            metric='precomputed',
            linkage='average'
        )
        labels = clusterer.fit_predict(distance_matrix)
        
        # Assign clusters
        cluster_sizes = {}
        for node_id, label in zip(node_ids, labels):
            cluster_id = int(label)
            for node in graph.nodes:
                if node.id == node_id:
                    node.cluster_id = cluster_id
                    node.attributes["cluster_id"] = cluster_id
                    break
            cluster_sizes[cluster_id] = cluster_sizes.get(cluster_id, 0) + 1
        
        graph.metadata["clusters"] = {
            "method": "hybrid",
            "n_clusters": n_clusters,
            "content_weight": content_weight,
            "citation_weight": citation_weight,
            "cluster_sizes": cluster_sizes
        }
        
        print(f"✅ Created {n_clusters} hybrid clusters:")
        for cluster_id, size in sorted(cluster_sizes.items()):
            print(f"   Cluster {cluster_id}: {size} papers")
        
        return graph
    
    def get_cluster_summaries(
        self,
        graph: ResearchGraph,
        top_terms: int = 10
    ) -> Dict[int, Dict[str, Any]]:
        """
        Generate summary for each cluster
        
        Args:
            graph: Graph with cluster assignments
            top_terms: Number of top terms to extract per cluster
            
        Returns:
            Dictionary mapping cluster ID to summary info
        """
        if self.vectorizer is None or self.embeddings is None:
            print("⚠️  No clustering performed yet")
            return {}
        
        summaries = {}
        
        # Group papers by cluster
        clusters = {}
        for node in graph.nodes:
            cluster_id = node.attributes.get("cluster_id", 0)
            if cluster_id not in clusters:
                clusters[cluster_id] = []
            clusters[cluster_id].append(node)
        
        # Get feature names from vectorizer
        feature_names = self.vectorizer.get_feature_names_out()
        
        # Summarize each cluster
        for cluster_id, nodes in clusters.items():
            # Get node indices
            node_indices = []
            for i, node_id in enumerate([n.id for n in graph.nodes]):
                if any(n.id == node_id for n in nodes):
                    node_indices.append(i)
            
            # Get average TF-IDF vector for cluster
            cluster_vector = self.embeddings[node_indices].mean(axis=0).A1
            
            # Get top terms
            top_indices = cluster_vector.argsort()[-top_terms:][::-1]
            top_terms_list = [feature_names[i] for i in top_indices]
            
            # Get paper titles
            paper_titles = [n.title for n in nodes]
            
            summaries[cluster_id] = {
                "size": len(nodes),
                "top_terms": top_terms_list,
                "sample_papers": paper_titles[:5],
                "avg_year": np.mean([
                    int(n.publication_date) if n.publication_date and n.publication_date.isdigit() else 0
                    for n in nodes
                ])
            }
        
        return summaries


# Global instance
_clusterer = None


def get_clusterer() -> PaperClusterer:
    """Get or create global clusterer instance"""
    global _clusterer
    if _clusterer is None:
        _clusterer = PaperClusterer()
    return _clusterer
