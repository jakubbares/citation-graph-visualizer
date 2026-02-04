"""
Contribution Extractor - Extract technical contributions from papers
"""
from typing import List, Dict, Any
from dataclasses import dataclass, asdict
import os
from parsers.pdf_parser import ParsedPaper


@dataclass
class Contribution:
    """Represents a single contribution from a paper"""
    contribution_type: str
    specific_innovation: str
    problem_addressed: str
    evidence_location: str
    comment: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ContributionExtractor:
    """Extract technical contributions from research papers"""
    
    SYSTEM_PROMPT = """You are an expert machine learning researcher analyzing academic papers.
Your task is to extract technical contributions accurately and systematically.
Always output valid JSON only."""
    
    USER_PROMPT_TEMPLATE = """Analyze the provided paper and extract its primary technical contributions.

Categorize each contribution using a simple phrase. Here are several examples:
• Novel Architecture
• Novel Loss Function
• Activation Function
• Training/Optimization Procedure
• Data Augmentation Strategy
• Evaluation Metric
• New Dataset
• Theoretical Proof/Framework
• Novel Algorithm
• Sampling Procedure
• Integration into Solver
• Attention Mechanism
• Regularization Method
• Pre-training Strategy

You can define new categories as needed.

Return the results in a structured JSON format with a list of dicts with the following keys:
• "contribution_type": The category/phrase.
• "specific_innovation": A 1-sentence description of the new component.
• "problem_addressed": What specific issue this contribution solves.
• "evidence_location": The section name where this is introduced.
• "comment": [this can be empty string]

Output ONLY the JSON array. No explanations.

Paper Title: {title}

Paper Abstract:
{abstract}

Paper Content (first 15000 characters):
{content}

Output format:
[
  {{
    "contribution_type": "...",
    "specific_innovation": "...",
    "problem_addressed": "...",
    "evidence_location": "...",
    "comment": ""
  }}
]
"""
    
    def __init__(self):
        """Initialize with LLM client (DeepSeek or Bedrock)"""
        from .llm_client import get_llm_client
        self.llm = get_llm_client()
    
    def extract(self, paper: ParsedPaper) -> List[Contribution]:
        """
        Extract contributions from a parsed paper
        
        Args:
            paper: ParsedPaper object
            
        Returns:
            List of Contribution objects
        """
        # Format prompt
        prompt = self.USER_PROMPT_TEMPLATE.format(
            title=paper.title,
            abstract=paper.abstract,
            content=paper.full_text[:15000]  # Limit for token budget
        )
        
        # Get LLM response
        print(f"🔍 Extracting contributions from: {paper.title[:60]}...")
        response = self.llm.complete_json(prompt, self.SYSTEM_PROMPT)
        
        # Parse response
        contributions = []
        
        # Response might be wrapped in a key or be direct list
        if isinstance(response, dict):
            if "contributions" in response:
                items = response["contributions"]
            elif "error" in response:
                print(f"⚠️  LLM returned error: {response['error']}")
                return []
            else:
                # Assume first list value is contributions
                items = next((v for v in response.values() if isinstance(v, list)), [])
        elif isinstance(response, list):
            items = response
        else:
            print(f"⚠️  Unexpected response type: {type(response)}")
            return []
        
        # Convert to Contribution objects
        for item in items:
            try:
                # Ensure all required fields exist
                contribution = Contribution(
                    contribution_type=item.get("contribution_type", "Unknown"),
                    specific_innovation=item.get("specific_innovation", ""),
                    problem_addressed=item.get("problem_addressed", ""),
                    evidence_location=item.get("evidence_location", ""),
                    comment=item.get("comment", "")
                )
                contributions.append(contribution)
            except Exception as e:
                print(f"⚠️  Failed to parse contribution: {e}")
                continue
        
        print(f"✅ Found {len(contributions)} contributions")
        return contributions

