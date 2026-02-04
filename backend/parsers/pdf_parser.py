"""
PDF Parser - Extract text and structure from research papers
"""
import fitz  # PyMuPDF
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass, field
import re


@dataclass
class Section:
    """Represents a section in the paper"""
    title: str
    number: str  # e.g., "3.2"
    level: int
    content: str
    start_page: int
    end_page: int


@dataclass
class ParsedPaper:
    """Structured representation of a parsed paper"""
    paper_id: str
    title: str
    authors: List[str] = field(default_factory=list)
    abstract: str = ""
    full_text: str = ""
    sections: List[Section] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    num_pages: int = 0


class PaperParser:
    """Extract text and structure from PDF research papers"""
    
    def parse_pdf(self, pdf_path: str, paper_id: str) -> ParsedPaper:
        """
        Parse a PDF file and extract structured content
        
        Args:
            pdf_path: Path to PDF file
            paper_id: Unique identifier for the paper
            
        Returns:
            ParsedPaper object with extracted content
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        
        # Extract full text
        full_text, num_pages = self._extract_text(pdf_path)
        
        # Extract title (first significant text)
        title = self._extract_title(full_text)
        
        # Extract abstract
        abstract = self._extract_abstract(full_text)
        
        # Extract authors (heuristic)
        authors = self._extract_authors(full_text)
        
        # Extract sections
        sections = self._extract_sections(full_text)
        
        return ParsedPaper(
            paper_id=paper_id,
            title=title,
            authors=authors,
            abstract=abstract,
            full_text=full_text,
            sections=sections,
            num_pages=num_pages,
            metadata={"source": str(pdf_path)}
        )
    
    def _extract_text(self, pdf_path: Path) -> tuple[str, int]:
        """Extract all text from PDF"""
        doc = fitz.open(pdf_path)
        text_parts = []
        
        for page in doc:
            text_parts.append(page.get_text())
        
        num_pages = len(doc)
        doc.close()
        
        return "\n".join(text_parts), num_pages
    
    def _extract_title(self, text: str) -> str:
        """Extract title (first non-empty line, heuristic)"""
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            # Skip very short lines and all-caps headers
            if len(line) > 10 and len(line) < 200 and not line.isupper():
                return line
        return "Unknown Title"
    
    def _extract_abstract(self, text: str) -> str:
        """Extract abstract section"""
        text_lower = text.lower()
        
        # Find "abstract" keyword
        if "abstract" not in text_lower:
            return ""
        
        start = text_lower.find("abstract")
        
        # Find next section (Introduction, 1. Introduction, etc.)
        end_keywords = ["introduction", "1 introduction", "1. introduction", "1 background"]
        end = len(text)
        
        for keyword in end_keywords:
            pos = text_lower.find(keyword, start)
            if pos != -1 and pos < end:
                end = pos
        
        abstract = text[start:end]
        # Remove the word "Abstract"
        abstract = re.sub(r'abstract', '', abstract, count=1, flags=re.IGNORECASE)
        return abstract.strip()
    
    def _extract_authors(self, text: str) -> List[str]:
        """Extract authors (simple heuristic - lines after title before abstract)"""
        # This is a simple heuristic and won't work for all papers
        # In production, you'd use more sophisticated NLP
        lines = text.split('\n')[:20]  # Check first 20 lines
        authors = []
        
        for line in lines:
            line = line.strip()
            # Look for lines with comma-separated names (heuristic)
            if ',' in line and len(line) < 100 and '@' not in line:
                # Might be author line
                potential_authors = [name.strip() for name in line.split(',')]
                if len(potential_authors) > 1:
                    authors.extend(potential_authors)
                    break
        
        return authors if authors else ["Unknown"]
    
    def _extract_sections(self, text: str) -> List[Section]:
        """Extract sections with titles and content"""
        sections = []
        
        # Common section patterns: "1. Introduction", "2.1 Method", etc.
        section_pattern = r'^(\d+(?:\.\d+)?)\s+([A-Z][^\n]+)'
        
        lines = text.split('\n')
        current_section = None
        current_content = []
        
        for i, line in enumerate(lines):
            match = re.match(section_pattern, line.strip())
            if match:
                # Save previous section
                if current_section:
                    current_section['content'] = '\n'.join(current_content)
                    sections.append(Section(**current_section))
                
                # Start new section
                number, title = match.groups()
                level = len(number.split('.'))
                current_section = {
                    'number': number,
                    'title': title.strip(),
                    'level': level,
                    'start_page': 0,  # Would need page-level parsing
                    'end_page': 0,
                    'content': ''
                }
                current_content = []
            elif current_section:
                current_content.append(line)
        
        # Save last section
        if current_section:
            current_section['content'] = '\n'.join(current_content)
            sections.append(Section(**current_section))
        
        return sections

