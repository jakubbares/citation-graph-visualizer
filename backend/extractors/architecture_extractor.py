"""
Architecture Extractor - Extract model architecture details
"""
from typing import List, Dict, Any
from dataclasses import dataclass, field, asdict
from .llm_client import BedrockLLMClient, get_llm_client
from parsers.pdf_parser import ParsedPaper


@dataclass
class Architecture:
    """Represents a model architecture"""
    name: str
    architecture_type: str  # Transformer, CNN, RNN, etc.
    layer_structure: str
    hidden_dimensions: List[str] = field(default_factory=list)
    num_parameters: str = ""
    novel_components: List[str] = field(default_factory=list)
    evidence_location: str = ""
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ArchitectureExtractor:
    """Extract model architecture details from research papers"""
    
    PROMPT_TEMPLATE = """Extract complete architecture details of all models in this paper.

For each model/architecture, provide:
- Name and variant
- High-level architecture type (Transformer, CNN, RNN, GNN, Hybrid, etc.)
- Layer structure and depth (e.g., "12 transformer layers", "ResNet-50 backbone")
- Hidden dimensions / channel sizes (e.g., "768 hidden dim", "256 channels")
- Number of parameters (if mentioned, e.g., "110M parameters")
- Any novel architectural components (e.g., "multi-head attention", "skip connections")
- Evidence location (section/figure where described)

Distinguish between:
- Proposed architectures (new in this paper)
- Baseline architectures (existing models used for comparison)

Return in JSON format:
{{
  "architectures": [
    {{
      "name": "string",
      "architecture_type": "string",
      "layer_structure": "string", 
      "hidden_dimensions": ["string"],
      "num_parameters": "string",
      "novel_components": ["string"],
      "evidence_location": "string",
      "notes": "string (proposed or baseline)"
    }}
  ]
}}

Output only the JSON.

Paper Title: {title}

Paper Content (first 15000 chars):
{content}
"""
    
    def __init__(self, llm_client: BedrockLLMClient = None):
        self.llm = llm_client or get_llm_client()
    
    def extract(self, paper: ParsedPaper) -> List[Architecture]:
        """
        Extract architectures from a parsed paper
        
        Args:
            paper: ParsedPaper object
            
        Returns:
            List of Architecture objects
        """
        # Format prompt
        prompt = self.PROMPT_TEMPLATE.format(
            title=paper.title,
            content=paper.full_text[:15000]
        )
        
        # Get LLM response
        print("Extracting architectures...")
        response = self.llm.complete_json(prompt)
        
        # Parse response
        architectures = []
        items = response.get("architectures", [])
        
        for item in items:
            # Handle defaults for missing fields
            if "hidden_dimensions" not in item:
                item["hidden_dimensions"] = []
            if "novel_components" not in item:
                item["novel_components"] = []
                
            architectures.append(Architecture(**item))
        
        return architectures


