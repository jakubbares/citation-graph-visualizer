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
    
    def search_paper(self, title: str, retry_count: int = 0, arxiv_id: str = None) -> Optional[Dict[str, Any]]:
        """
        Search for a paper by title or ArXiv ID
        
        Args:
            title: Paper title to search for
            retry_count: Number of retries attempted
            arxiv_id: Optional ArXiv ID to search by
            
        Returns:
            Paper data or None if not found
        """
        max_retries = 3
        try:
            # If ArXiv ID is provided, try to get paper directly by ArXiv ID
            if arxiv_id:
                try:
                    # Try using ARXIV: prefix (no "arXiv:" in the ID itself)
                    clean_arxiv_id = arxiv_id.replace('arXiv:', '').replace('arxiv:', '').strip()
                    url = f"{self.base_url}/paper/ARXIV:{clean_arxiv_id}"
                    params = {
                        "fields": "paperId,title,authors,year,citationCount,citations,references,abstract,venue"
                    }
                    response = self.session.get(url, params=params, timeout=30)
                    if response.status_code == 200:
                        paper = response.json()
                        print(f"✅ Found paper by ArXiv ID: {paper.get('title', 'Unknown')[:60]}...")
                        return paper
                    else:
                        print(f"⚠️  Failed to fetch by ArXiv ID (status {response.status_code}), trying search")
                except Exception as e:
                    print(f"⚠️  Could not fetch by ArXiv ID, trying search: {e}")
            
            # Clean title for search
            query = title.strip().replace('\n', ' ')
            
            url = f"{self.base_url}/paper/search"
            params = {
                "query": query,
                "limit": 1,
                "fields": "paperId,title,authors,year,citationCount,citations,references,abstract,venue"
            }
            
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code == 429:
                print(f"⚠️  Rate limited by Semantic Scholar, waiting...")
                time.sleep(10)
                return self.search_paper(title, retry_count, arxiv_id)
            
            response.raise_for_status()
            data = response.json()
            
            if data.get("data") and len(data["data"]) > 0:
                paper = data["data"][0]
                print(f"✅ Found paper: {paper.get('title', 'Unknown')[:60]}...")
                return paper
            
            print(f"⚠️  Paper not found: {title[:60]}...")
            return None
            
        except requests.exceptions.Timeout as e:
            if retry_count < max_retries:
                wait_time = 2 ** retry_count  # Exponential backoff: 1s, 2s, 4s
                print(f"⚠️  Timeout searching '{title[:60]}...', retrying in {wait_time}s (attempt {retry_count + 1}/{max_retries})")
                time.sleep(wait_time)
                return self.search_paper(title, retry_count + 1, arxiv_id)
            else:
                print(f"❌ Failed after {max_retries} retries: {e}")
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
            
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code == 429:
                print(f"⚠️  Rate limited, waiting...")
                time.sleep(10)
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
            
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code == 429:
                time.sleep(10)
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
            
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code == 429:
                time.sleep(10)
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
    
    def get_references_batch(self, paper_ids: List[str]) -> Dict[str, List[str]]:
        """
        Fetch reference paper IDs for multiple papers using batch API.
        Returns dict mapping paper_id -> list of referenced paper IDs.
        """
        result = {}
        batch_size = 100  # S2 batch limit is 500, but keep it safe
        
        for i in range(0, len(paper_ids), batch_size):
            batch = paper_ids[i:i + batch_size]
            try:
                url = f"{self.base_url}/paper/batch"
                params = {"fields": "references.paperId"}
                response = self.session.post(
                    url, params=params,
                    json={"ids": batch},
                    timeout=60,
                )
                
                if response.status_code == 429:
                    print(f"⚠️  Rate limited on batch, waiting 10s...")
                    time.sleep(10)
                    # Retry this batch
                    response = self.session.post(
                        url, params=params,
                        json={"ids": batch},
                        timeout=60,
                    )
                
                if response.status_code == 200:
                    data = response.json()
                    for paper_data in data:
                        if paper_data is None:
                            continue
                        pid = paper_data.get("paperId")
                        refs = paper_data.get("references") or []
                        ref_ids = [r["paperId"] for r in refs if r and r.get("paperId")]
                        result[pid] = ref_ids
                else:
                    print(f"⚠️  Batch API returned {response.status_code}, falling back to individual calls")
                    for pid in batch:
                        refs = self.get_references(pid, limit=500)
                        result[pid] = [r.get("paperId") for r in refs if r.get("paperId")]
                        time.sleep(0.2)
                
                time.sleep(0.3)
            except Exception as e:
                print(f"❌ Batch references error: {e}, falling back to individual calls")
                for pid in batch:
                    refs = self.get_references(pid, limit=500)
                    result[pid] = [r.get("paperId") for r in refs if r.get("paperId")]
                    time.sleep(0.2)
        
        return result

    def build_citation_network(self, paper_titles: List[str], max_intermediate_papers: int = 50, arxiv_ids: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Build a citation network from a list of paper titles.
        
        Strategy:
        1. Find the input/review papers on Semantic Scholar
        2. Get ALL papers referenced by the input papers
        3. For each referenced paper, get ITS references
        4. Create edges wherever one referenced paper cites another
        5. This creates a rich interconnected network between the papers
        """
        print(f"🔍 Building citation network for {len(paper_titles)} papers...")
        
        if arxiv_ids is None:
            arxiv_ids = {}
        
        # ===== Step 1: Find input papers on Semantic Scholar =====
        input_papers = {}
        paper_id_to_title = {}
        
        for title in paper_titles:
            arxiv_id = arxiv_ids.get(title)
            paper = self.search_paper(title, arxiv_id=arxiv_id)
            if paper:
                paper_id = paper["paperId"]
                input_papers[paper_id] = paper
                paper_id_to_title[paper_id] = title
                print(f"✅ Found: {paper['title'][:60]}... (citations: {paper.get('citationCount', 0)})")
                time.sleep(0.2)
        
        print(f"✅ Found {len(input_papers)} input papers on Semantic Scholar")
        
        # ===== Step 2: Get all references for input papers =====
        # These are the "reviewed" papers — the ones actually discussed in the review
        reference_papers = {}  # s2_id -> paper data
        
        print(f"\n🔗 Fetching references (papers cited by input papers)...")
        for paper_id, paper_data in input_papers.items():
            references = self.get_references(paper_id, limit=500)
            print(f"   {paper_data['title'][:50]}... → {len(references)} references")
            
            for ref in references:
                ref_id = ref.get("paperId")
                if ref_id and ref_id not in input_papers:
                    reference_papers[ref_id] = ref
            
            time.sleep(0.2)
        
        print(f"📚 Found {len(reference_papers)} unique referenced papers")
        
        # ===== Step 3: Select which referenced papers to include =====
        # Sort by citation count, take top N
        reviewed_list = sorted(
            reference_papers.items(),
            key=lambda x: x[1].get("citationCount", 0),
            reverse=True
        )[:max_intermediate_papers]
        
        reviewed_papers = {pid: data for pid, data in reviewed_list}
        reviewed_ids = set(reviewed_papers.keys())
        
        print(f"📊 Selected top {len(reviewed_papers)} reviewed papers for visualization")
        
        # ===== Step 4: Fetch inter-references between reviewed papers =====
        # This is the KEY step — find how reviewed papers cite EACH OTHER
        print(f"\n🔗 Fetching inter-references between {len(reviewed_ids)} reviewed papers...")
        print(f"   (Using batch API to find who cites whom)")
        
        reviewed_id_list = list(reviewed_ids)
        inter_references = self.get_references_batch(reviewed_id_list)
        
        print(f"   Got references for {len(inter_references)} papers")
        
        # ===== Step 5: Build edges between reviewed papers =====
        edges = []
        edge_set = set()  # for dedup: (from_id, to_id)
        
        # 5a. Edges from input papers to reviewed papers (review → paper)
        for input_id, input_data in input_papers.items():
            input_refs = self.get_references(input_id, limit=500)
            for ref in input_refs:
                ref_id = ref.get("paperId")
                if ref_id and ref_id in reviewed_ids:
                    key = (input_id, ref_id)
                    if key not in edge_set:
                        edge_set.add(key)
                        edges.append({
                            "from": input_id,
                            "to": ref_id,
                            "from_title": input_data["title"],
                            "to_title": reviewed_papers[ref_id].get("title", "Unknown")
                        })
            time.sleep(0.2)
        
        print(f"   Edges from review → papers: {len(edges)}")
        
        # 5b. Edges between reviewed papers (paper ↔ paper) — THE IMPORTANT ONES
        inter_edge_count = 0
        for from_id, ref_ids in inter_references.items():
            if from_id not in reviewed_ids:
                continue
            for to_id in ref_ids:
                if to_id in reviewed_ids and to_id != from_id:
                    key = (from_id, to_id)
                    if key not in edge_set:
                        edge_set.add(key)
                        edges.append({
                            "from": from_id,
                            "to": to_id,
                            "from_title": reviewed_papers[from_id].get("title", "Unknown"),
                            "to_title": reviewed_papers[to_id].get("title", "Unknown")
                        })
                        inter_edge_count += 1
        
        print(f"   Edges between reviewed papers: {inter_edge_count}")
        print(f"   Total edges: {len(edges)}")
        
        # ===== Step 6: Combine everything =====
        all_papers = {**input_papers, **reviewed_papers}
        
        print(f"\n✅ Citation network built:")
        print(f"   - Input/review papers: {len(input_papers)}")
        print(f"   - Reviewed papers: {len(reviewed_papers)}")
        print(f"   - Total papers: {len(all_papers)}")
        print(f"   - Total edges: {len(edges)}")
        print(f"   - Inter-paper edges: {inter_edge_count}")
        
        return {
            "papers": all_papers,
            "citations": edges,
            "input_paper_ids": list(input_papers.keys()),
            "intermediate_paper_ids": list(reviewed_papers.keys())
        }


# Global instance
_semantic_scholar_api = None


def get_semantic_scholar_api() -> SemanticScholarAPI:
    """Get or create global Semantic Scholar API instance"""
    global _semantic_scholar_api
    if _semantic_scholar_api is None:
        _semantic_scholar_api = SemanticScholarAPI()
    return _semantic_scholar_api
