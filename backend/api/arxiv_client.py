"""
ArXiv API Client for fetching paper metadata and PDFs
"""
import requests
import xml.etree.ElementTree as ET
from typing import Dict, Optional, Any
import time


class ArXivClient:
    """Client for ArXiv API"""
    
    def __init__(self):
        self.base_url = "http://export.arxiv.org/api/query"
    
    def get_paper_by_id(self, arxiv_id: str, retry_count: int = 0) -> Optional[Dict[str, Any]]:
        """
        Get paper metadata from ArXiv
        
        Args:
            arxiv_id: ArXiv ID (e.g., "2301.12345")
            retry_count: Internal retry counter
            
        Returns:
            Paper metadata or None if not found
        """
        max_retries = 3
        try:
            # Clean ArXiv ID - strip version suffix like v1, v2 but keep the digits in the ID
            import re
            arxiv_id = arxiv_id.strip().replace('arxiv:', '').replace('arXiv:', '')
            arxiv_id = re.sub(r'v\d+$', '', arxiv_id)
            
            url = f"{self.base_url}?id_list={arxiv_id}"
            response = requests.get(url, timeout=30)
            
            if response.status_code == 429:
                if retry_count < max_retries:
                    wait_time = 3 * (retry_count + 1)
                    print(f"⚠️  ArXiv rate limited, waiting {wait_time}s (attempt {retry_count + 1}/{max_retries})")
                    time.sleep(wait_time)
                    return self.get_paper_by_id(arxiv_id, retry_count + 1)
                else:
                    print(f"❌ ArXiv rate limited after {max_retries} retries for {arxiv_id}")
                    return None
            
            response.raise_for_status()
            
            # Parse XML response
            root = ET.fromstring(response.content)
            
            # ArXiv namespace
            ns = {'atom': 'http://www.w3.org/2005/Atom', 
                  'arxiv': 'http://arxiv.org/schemas/atom'}
            
            entries = root.findall('atom:entry', ns)
            if not entries:
                print(f"⚠️  ArXiv paper not found: {arxiv_id}")
                return None
            
            entry = entries[0]
            
            # Extract data
            title = entry.find('atom:title', ns)
            summary = entry.find('atom:summary', ns)
            published = entry.find('atom:published', ns)
            updated = entry.find('atom:updated', ns)
            
            # Authors
            authors = []
            for author in entry.findall('atom:author', ns):
                name = author.find('atom:name', ns)
                if name is not None:
                    authors.append(name.text.strip())
            
            # Categories
            categories = []
            for category in entry.findall('atom:category', ns):
                term = category.get('term')
                if term:
                    categories.append(term)
            
            # PDF URL
            pdf_url = None
            for link in entry.findall('atom:link', ns):
                if link.get('title') == 'pdf':
                    pdf_url = link.get('href')
            
            # ArXiv URL
            arxiv_url = entry.find('atom:id', ns)
            
            paper_data = {
                'arxiv_id': arxiv_id,
                'title': title.text.strip() if title is not None else None,
                'abstract': summary.text.strip() if summary is not None else None,
                'authors': authors,
                'published': published.text if published is not None else None,
                'updated': updated.text if updated is not None else None,
                'categories': categories,
                'pdf_url': pdf_url,
                'arxiv_url': arxiv_url.text if arxiv_url is not None else f"https://arxiv.org/abs/{arxiv_id}",
                'year': int(published.text[:4]) if published is not None else None
            }
            
            print(f"✅ Found ArXiv paper: {paper_data['title'][:60]}...")
            return paper_data
            
        except requests.exceptions.Timeout as e:
            if retry_count < max_retries:
                wait_time = 3 * (retry_count + 1)
                print(f"⚠️  ArXiv timeout for {arxiv_id}, retrying in {wait_time}s (attempt {retry_count + 1}/{max_retries})")
                time.sleep(wait_time)
                return self.get_paper_by_id(arxiv_id, retry_count + 1)
            else:
                print(f"❌ ArXiv timeout after {max_retries} retries for {arxiv_id}: {e}")
                return None
        except Exception as e:
            print(f"❌ Error fetching ArXiv paper {arxiv_id}: {e}")
            return None
    
    def search_papers(self, query: str, max_results: int = 10) -> list[Dict[str, Any]]:
        """
        Search ArXiv papers by query
        
        Args:
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            List of paper metadata
        """
        try:
            params = {
                'search_query': query,
                'max_results': max_results,
                'sortBy': 'relevance'
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            
            papers = []
            for entry in root.findall('atom:entry', ns):
                # Extract ArXiv ID from URL
                arxiv_url = entry.find('atom:id', ns)
                if arxiv_url is not None:
                    arxiv_id = arxiv_url.text.split('/')[-1]
                    paper = self.get_paper_by_id(arxiv_id)
                    if paper:
                        papers.append(paper)
                        time.sleep(0.2)  # Rate limiting
            
            return papers
            
        except Exception as e:
            print(f"❌ Error searching ArXiv: {e}")
            return []


# Global instance
_arxiv_client = None


def get_arxiv_client() -> ArXivClient:
    """Get or create global ArXiv client instance"""
    global _arxiv_client
    if _arxiv_client is None:
        _arxiv_client = ArXivClient()
    return _arxiv_client
