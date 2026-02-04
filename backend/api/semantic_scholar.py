"""
Semantic Scholar API Client for fetching citation data
"""
import requests
import time
from typing import Dict, List, Optional, Any
from config import settings


class SemanticScholarAPI:
    """Client for Semantic Scholar Academic Graph API"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.base_url = "https://api.semanticscholar.org/graph/v1"
        self.api_key = api_key or settings.semantic_scholar_api_key
        self.session = requests.Session()
        
        if self.api_key:
            self.session.headers.update({"x-api-key": self.api_key})
            print(f"✅ Semantic Scholar API initialized with key")
        else:
            print(f"⚠️  Semantic Scholar API initialized without key (rate limited)")
    
    def search_paper(self, title: str) -> Optional[Dict[str, Any]]:
        """
        Search for a paper by title
        
        Args:
            title: Paper title to search for
            
        Returns:
            Paper data or None if not found
        """
        try:
            # Clean title for search
            query = title.strip().replace('\n', ' ')
            
            url = f"{self.base_url}/paper/search"
            params = {
                "query": query,
                "limit": 1,
                "fields": "paperId,title,authors,year,citationCount,citations,references,abstract,venue"
            }
            
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 429:
                print(f"⚠️  Rate limited by Semantic Scholar, waiting...")
                time.sleep(5)
                return self.search_paper(title)
            
            response.raise_for_status()
            data = response.json()
            
            if data.get("data") and len(data["data"]) > 0:
                paper = data["data"][0]
                print(f"✅ Found paper: {paper.get('title', 'Unknown')[:60]}...")
                return paper
            
            print(f"⚠️  Paper not found: {title[:60]}...")
            return None
            
        except Exception as e:
            print(f"❌ Error searching paper '{title[:60]}...': {e}")
            return None
    
    def get_paper_by_id(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """
        Get paper details by Semantic Scholar ID
        
        Args:
            paper_id: Semantic Scholar paper ID
            
        Returns:
            Paper data or None if not found
        """
        try:
            url = f"{self.base_url}/paper/{paper_id}"
            params = {
                "fields": "paperId,title,authors,year,citationCount,citations,references,abstract,venue"
            }
            
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 429:
                print(f"⚠️  Rate limited, waiting...")
                time.sleep(5)
                return self.get_paper_by_id(paper_id)
            
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            print(f"❌ Error fetching paper {paper_id}: {e}")
            return None
    
    def get_citations(self, paper_id: str, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Get papers that cite this paper
        
        Args:
            paper_id: Semantic Scholar paper ID
            limit: Maximum number of citations to fetch
            
        Returns:
            List of citing papers
        """
        try:
            url = f"{self.base_url}/paper/{paper_id}/citations"
            params = {
                "fields": "paperId,title,authors,year",
                "limit": limit
            }
            
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 429:
                time.sleep(5)
                return self.get_citations(paper_id, limit)
            
            response.raise_for_status()
            data = response.json()
            
            citations = []
            for item in data.get("data", []):
                if item.get("citingPaper"):
                    citations.append(item["citingPaper"])
            
            return citations
            
        except Exception as e:
            print(f"❌ Error fetching citations for {paper_id}: {e}")
            return []
    
    def get_references(self, paper_id: str, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Get papers that this paper cites (references)
        
        Args:
            paper_id: Semantic Scholar paper ID
            limit: Maximum number of references to fetch
            
        Returns:
            List of referenced papers
        """
        try:
            url = f"{self.base_url}/paper/{paper_id}/references"
            params = {
                "fields": "paperId,title,authors,year",
                "limit": limit
            }
            
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 429:
                time.sleep(5)
                return self.get_references(paper_id, limit)
            
            response.raise_for_status()
            data = response.json()
            
            references = []
            for item in data.get("data", []):
                if item.get("citedPaper"):
                    references.append(item["citedPaper"])
            
            return references
            
        except Exception as e:
            print(f"❌ Error fetching references for {paper_id}: {e}")
            return []
    
    def build_citation_network(self, paper_titles: List[str], max_intermediate_papers: int = 50) -> Dict[str, Any]:
        """
        Build a citation network from a list of paper titles
        
        Args:
            paper_titles: List of paper titles
            max_intermediate_papers: Maximum intermediate papers to add
            
        Returns:
            Dictionary with papers and citation relationships
        """
        print(f"🔍 Building citation network for {len(paper_titles)} papers...")
        
        # Step 1: Search for all input papers
        input_papers = {}
        paper_id_to_title = {}
        
        for title in paper_titles:
            paper = self.search_paper(title)
            if paper:
                paper_id = paper["paperId"]
                input_papers[paper_id] = paper
                paper_id_to_title[paper_id] = title
                print(f"✅ Found: {paper['title'][:60]}... (citations: {paper.get('citationCount', 0)})")
                time.sleep(0.2)  # Rate limiting
        
        print(f"✅ Found {len(input_papers)} input papers on Semantic Scholar")
        
        # Step 2: Get ALL references for each input paper
        all_references = {}  # paper_id -> list of reference paper data
        reference_papers = {}  # paper_id -> paper data
        
        print(f"\n🔗 Fetching references (papers cited by input papers)...")
        for paper_id in input_papers.keys():
            references = self.get_references(paper_id, limit=500)
            all_references[paper_id] = references
            
            print(f"   {input_papers[paper_id]['title'][:50]}... → {len(references)} references")
            
            # Add reference papers to collection
            for ref in references:
                ref_id = ref.get("paperId")
                if ref_id and ref_id not in reference_papers and ref_id not in input_papers:
                    reference_papers[ref_id] = ref
            
            time.sleep(0.2)
        
        # Step 3: Get ALL citations for each input paper
        all_citations = {}  # paper_id -> list of citing paper data
        citing_papers = {}  # paper_id -> paper data
        
        print(f"\n📚 Fetching citations (papers that cite input papers)...")
        for paper_id in input_papers.keys():
            citations = self.get_citations(paper_id, limit=500)
            all_citations[paper_id] = citations
            
            print(f"   {input_papers[paper_id]['title'][:50]}... ← {len(citations)} citations")
            
            # Add citing papers to collection
            for cite in citations:
                cite_id = cite.get("paperId")
                if cite_id and cite_id not in citing_papers and cite_id not in input_papers:
                    citing_papers[cite_id] = cite
            
            time.sleep(0.2)
        
        # Step 4: Find intermediate papers (papers that appear multiple times in references/citations)
        paper_frequency = {}
        
        # Count how many times each reference appears
        for paper_id, refs in all_references.items():
            for ref in refs:
                ref_id = ref.get("paperId")
                if ref_id and ref_id not in input_papers:
                    paper_frequency[ref_id] = paper_frequency.get(ref_id, 0) + 1
        
        # Count how many times each citing paper appears
        for paper_id, cites in all_citations.items():
            for cite in cites:
                cite_id = cite.get("paperId")
                if cite_id and cite_id not in input_papers:
                    paper_frequency[cite_id] = paper_frequency.get(cite_id, 0) + 1
        
        # Select intermediate papers (papers that connect multiple input papers)
        intermediate_papers = {}
        intermediate_candidates = sorted(
            paper_frequency.items(),
            key=lambda x: x[1],
            reverse=True
        )[:max_intermediate_papers]
        
        print(f"\n🔗 Found {len(intermediate_candidates)} intermediate papers (connecting multiple input papers)")
        
        for paper_id, frequency in intermediate_candidates:
            if paper_id in reference_papers:
                intermediate_papers[paper_id] = reference_papers[paper_id]
                print(f"   + {reference_papers[paper_id].get('title', 'Unknown')[:60]}... (connects {frequency} papers)")
            elif paper_id in citing_papers:
                intermediate_papers[paper_id] = citing_papers[paper_id]
                print(f"   + {citing_papers[paper_id].get('title', 'Unknown')[:60]}... (connects {frequency} papers)")
        
        # Step 5: Combine all papers
        all_papers = {**input_papers, **intermediate_papers}
        all_paper_ids = set(all_papers.keys())
        
        # Step 6: Build edges (citations)
        edges = []
        
        # Edges from input papers to their references
        for from_id, references in all_references.items():
            for ref in references:
                to_id = ref.get("paperId")
                if to_id and to_id in all_paper_ids:
                    edges.append({
                        "from": from_id,
                        "to": to_id,
                        "from_title": input_papers[from_id]["title"],
                        "to_title": all_papers[to_id].get("title", "Unknown")
                    })
        
        # Edges from intermediate papers to input papers (citations)
        for to_id, citations in all_citations.items():
            for cite in citations:
                from_id = cite.get("paperId")
                if from_id and from_id in all_paper_ids and from_id != to_id:
                    # Check if edge doesn't already exist
                    if not any(e["from"] == from_id and e["to"] == to_id for e in edges):
                        edges.append({
                            "from": from_id,
                            "to": to_id,
                            "from_title": all_papers[from_id].get("title", "Unknown"),
                            "to_title": input_papers[to_id]["title"]
                        })
        
        print(f"\n✅ Citation network built:")
        print(f"   - Input papers: {len(input_papers)}")
        print(f"   - Intermediate papers: {len(intermediate_papers)}")
        print(f"   - Total papers: {len(all_papers)}")
        print(f"   - Total edges: {len(edges)}")
        
        return {
            "papers": all_papers,
            "citations": edges,
            "input_paper_ids": list(input_papers.keys()),
            "intermediate_paper_ids": list(intermediate_papers.keys())
        }


# Global instance
_semantic_scholar_api = None


def get_semantic_scholar_api() -> SemanticScholarAPI:
    """Get or create global Semantic Scholar API instance"""
    global _semantic_scholar_api
    if _semantic_scholar_api is None:
        _semantic_scholar_api = SemanticScholarAPI()
    return _semantic_scholar_api
