"""
Survey Paper Extraction - Extract ground truth from survey/review papers
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from extractors.llm_client import get_llm_client


@dataclass
class PaperInSurvey:
    """Paper mentioned in a survey"""
    title: str
    authors: List[str]
    year: Optional[int]
    contribution: str
    category: str
    

@dataclass
class SurveyGroundTruth:
    """Ground truth data extracted from a survey paper"""
    survey_title: str
    survey_authors: List[str]
    survey_year: Optional[int]
    
    # Taxonomy/categories
    categories: List[Dict[str, Any]]  # [{name, description, papers}]
    
    # Papers with their relationships
    papers: List[PaperInSurvey]
    
    # Relationships between papers
    relationships: List[Dict[str, Any]]  # [{from_paper, to_paper, relationship_type, description}]
    

class SurveyExtractor:
    """Extract structured ground truth data from survey papers"""
    
    def __init__(self):
        self.llm_client = get_llm_client()
    
    def extract_from_survey(self, survey_text: str, survey_title: str = "Unknown") -> SurveyGroundTruth:
        """
        Extract ground truth data from a survey paper
        
        Args:
            survey_text: Full text of the survey paper
            survey_title: Title of the survey
            
        Returns:
            SurveyGroundTruth object with extracted data
        """
        print(f"📚 Extracting ground truth from survey: {survey_title}")
        
        # Step 1: Extract taxonomy/categories
        categories = self._extract_categories(survey_text)
        
        # Step 2: Extract papers and their contributions
        papers = self._extract_papers(survey_text, categories)
        
        # Step 3: Extract relationships between papers
        relationships = self._extract_relationships(survey_text, papers)
        
        return SurveyGroundTruth(
            survey_title=survey_title,
            survey_authors=[],
            survey_year=None,
            categories=categories,
            papers=papers,
            relationships=relationships
        )
    
    def _extract_categories(self, survey_text: str) -> List[Dict[str, Any]]:
        """Extract categories/taxonomy from survey"""
        prompt = f"""
You are analyzing a survey/review paper. Extract the main categories or taxonomy used to organize the papers.

Survey text (first 8000 chars):
{survey_text[:8000]}

Extract:
1. Category names (e.g., "Transformer-based Models", "CNN Architectures", "Optimization Methods")
2. Category descriptions
3. How papers are grouped

Return a JSON array of categories:
[
  {{
    "name": "Category Name",
    "description": "Brief description of what papers in this category focus on",
    "keywords": ["keyword1", "keyword2"]
  }}
]

Return ONLY the JSON array, no other text.
"""
        
        try:
            response = self.llm_client.chat_completion([
                {"role": "system", "content": "You are a helpful research assistant that extracts structured data from survey papers."},
                {"role": "user", "content": prompt}
            ])
            
            import json
            categories = json.loads(response)
            print(f"✅ Extracted {len(categories)} categories")
            return categories
            
        except Exception as e:
            print(f"❌ Error extracting categories: {e}")
            return []
    
    def _extract_papers(self, survey_text: str, categories: List[Dict[str, Any]]) -> List[PaperInSurvey]:
        """Extract papers mentioned in survey with their contributions"""
        
        # Split text into chunks for processing
        chunk_size = 6000
        chunks = [survey_text[i:i+chunk_size] for i in range(0, len(survey_text), chunk_size)]
        
        all_papers = []
        
        for i, chunk in enumerate(chunks[:10]):  # Limit to first 10 chunks
            print(f"📄 Processing chunk {i+1}/{min(10, len(chunks))}...")
            
            category_names = [c["name"] for c in categories]
            
            prompt = f"""
Analyze this section of a survey paper and extract all papers mentioned along with their contributions.

Categories identified: {', '.join(category_names)}

Text section:
{chunk}

For each paper mentioned, extract:
1. Title (exact title if available)
2. Authors (first author or "Author et al.")
3. Year
4. Key contribution (1-2 sentences)
5. Which category it belongs to (from the list above)

Return a JSON array:
[
  {{
    "title": "Paper Title",
    "authors": ["Author Name"],
    "year": 2023,
    "contribution": "Brief description of contribution",
    "category": "Category Name"
  }}
]

Return ONLY the JSON array, no other text. If no papers are mentioned, return [].
"""
            
            try:
                response = self.llm_client.chat_completion([
                    {"role": "system", "content": "You are a helpful research assistant."},
                    {"role": "user", "content": prompt}
                ])
                
                import json
                papers_in_chunk = json.loads(response)
                
                for paper_data in papers_in_chunk:
                    paper = PaperInSurvey(
                        title=paper_data.get("title", ""),
                        authors=paper_data.get("authors", []),
                        year=paper_data.get("year"),
                        contribution=paper_data.get("contribution", ""),
                        category=paper_data.get("category", "Uncategorized")
                    )
                    all_papers.append(paper)
                
            except Exception as e:
                print(f"⚠️  Error extracting papers from chunk {i+1}: {e}")
                continue
        
        # Deduplicate papers by title
        unique_papers = {}
        for paper in all_papers:
            title_key = paper.title.lower().strip()
            if title_key and title_key not in unique_papers:
                unique_papers[title_key] = paper
        
        papers_list = list(unique_papers.values())
        print(f"✅ Extracted {len(papers_list)} unique papers")
        
        return papers_list
    
    def _extract_relationships(
        self,
        survey_text: str,
        papers: List[PaperInSurvey]
    ) -> List[Dict[str, Any]]:
        """Extract relationships between papers"""
        
        if len(papers) < 2:
            return []
        
        paper_titles = [p.title for p in papers[:30]]  # Limit for prompt size
        
        prompt = f"""
Analyze this survey paper and identify how papers relate to each other.

Papers in the survey:
{chr(10).join([f"{i+1}. {title}" for i, title in enumerate(paper_titles)])}

Survey text (first 8000 chars):
{survey_text[:8000]}

Identify relationships such as:
- "Paper A builds upon Paper B"
- "Paper A compares against Paper B"
- "Paper A extends Paper B"
- "Paper A and Paper B address similar problems"

Return a JSON array:
[
  {{
    "from_paper": "Paper A Title",
    "to_paper": "Paper B Title",
    "relationship_type": "extends|builds_on|compares|similar",
    "description": "Brief description of relationship"
  }}
]

Return ONLY the JSON array. If no clear relationships, return [].
"""
        
        try:
            response = self.llm_client.chat_completion([
                {"role": "system", "content": "You are a helpful research assistant."},
                {"role": "user", "content": prompt}
            ])
            
            import json
            relationships = json.loads(response)
            print(f"✅ Extracted {len(relationships)} relationships")
            return relationships
            
        except Exception as e:
            print(f"❌ Error extracting relationships: {e}")
            return []
    
    def convert_to_evaluation_format(self, ground_truth: SurveyGroundTruth) -> Dict[str, Any]:
        """
        Convert ground truth to evaluation format
        
        Returns:
            Dictionary suitable for evaluation
        """
        # Group papers by category
        category_papers = {}
        for paper in ground_truth.papers:
            if paper.category not in category_papers:
                category_papers[paper.category] = []
            category_papers[paper.category].append({
                "title": paper.title,
                "authors": paper.authors,
                "year": paper.year,
                "contribution": paper.contribution
            })
        
        return {
            "survey": {
                "title": ground_truth.survey_title,
                "authors": ground_truth.survey_authors,
                "year": ground_truth.survey_year
            },
            "taxonomy": {
                "categories": ground_truth.categories,
                "papers_by_category": category_papers
            },
            "papers": [
                {
                    "title": p.title,
                    "authors": p.authors,
                    "year": p.year,
                    "contribution": p.contribution,
                    "category": p.category
                }
                for p in ground_truth.papers
            ],
            "relationships": ground_truth.relationships
        }


# Global instance
_survey_extractor = None


def get_survey_extractor() -> SurveyExtractor:
    """Get or create global survey extractor instance"""
    global _survey_extractor
    if _survey_extractor is None:
        _survey_extractor = SurveyExtractor()
    return _survey_extractor
