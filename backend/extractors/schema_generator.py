"""
Schema Generator & Dynamic Extractor

Analyzes the topic of the review papers and generates 5-7 custom attribute schemas
tailored to that specific research area, then extracts those attributes from each paper.
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict
from .llm_client import get_llm_client
from parsers.pdf_parser import ParsedPaper


# ── Colour palette for up to 8 categorical values per attribute ──────────
CATEGORY_PALETTES = [
    # Each sub-list is a palette assigned to one schema attribute
    ["#6366F1", "#818CF8", "#A5B4FC", "#C7D2FE", "#4F46E5", "#4338CA", "#3730A3", "#312E81"],  # indigo
    ["#F59E0B", "#FBBF24", "#FCD34D", "#FDE68A", "#D97706", "#B45309", "#92400E", "#78350F"],  # amber
    ["#10B981", "#34D399", "#6EE7B7", "#A7F3D0", "#059669", "#047857", "#065F46", "#064E3B"],  # emerald
    ["#EF4444", "#F87171", "#FCA5A5", "#FECACA", "#DC2626", "#B91C1C", "#991B1B", "#7F1D1D"],  # red
    ["#8B5CF6", "#A78BFA", "#C4B5FD", "#DDD6FE", "#7C3AED", "#6D28D9", "#5B21B6", "#4C1D95"],  # violet
    ["#EC4899", "#F472B6", "#F9A8D4", "#FBCFE8", "#DB2777", "#BE185D", "#9D174D", "#831843"],  # pink
    ["#14B8A6", "#2DD4BF", "#5EEAD4", "#99F6E4", "#0D9488", "#0F766E", "#115E59", "#134E4A"],  # teal
]


@dataclass
class AttributeSchema:
    """One attribute to extract, generated based on the paper topic."""
    key: str               # machine-friendly key, e.g. "message_passing_type"
    label: str             # human-readable label, e.g. "Message Passing Type"
    description: str       # what this attribute captures
    value_type: str        # "categorical" or "text"
    suggested_values: List[str] = field(default_factory=list)  # for categorical
    color_palette: List[str] = field(default_factory=list)     # assigned later

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class GeneratedSchema:
    """The full schema generated for a set of papers."""
    topic: str                         # detected research topic
    topic_description: str             # 1-sentence summary
    attributes: List[AttributeSchema] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "topic": self.topic,
            "topic_description": self.topic_description,
            "attributes": [a.to_dict() for a in self.attributes],
        }


class SchemaGenerator:
    """Generates a custom extraction schema based on the topic of the papers."""

    SCHEMA_PROMPT = """You are an expert research analyst. Given the titles and abstracts of a set of related research papers, identify their common research topic and design 5-7 attributes that would be most informative for comparing and understanding these papers.

Each attribute should be:
- Specific to this research area (not generic like "methodology" or "dataset")
- Categorical with 3-8 possible values so papers can be grouped/colored
- Useful for understanding the landscape of this research field

For example:
- If the papers are about Graph Neural Networks, good attributes might be: "Message Passing Scheme", "Aggregation Function", "Graph Pooling", "Scalability Approach", "Expressivity Guarantee"
- If the papers are about Large Language Models, good attributes might be: "Architecture Variant", "Pre-training Objective", "Context Window Strategy", "Alignment Method", "Efficiency Technique"
- If the papers are about Diffusion Models, good attributes might be: "Noise Schedule", "Sampling Strategy", "Conditioning Mechanism", "Architecture Backbone", "Generation Domain"

Return EXACTLY this JSON format:
{{
  "topic": "short topic name (2-5 words)",
  "topic_description": "one sentence describing the research area",
  "attributes": [
    {{
      "key": "snake_case_key",
      "label": "Human Readable Label",
      "description": "What this attribute captures and why it matters for comparing papers",
      "value_type": "categorical",
      "suggested_values": ["Value1", "Value2", "Value3", "Value4", "Value5"]
    }}
  ]
}}

Rules:
- Generate exactly 5-7 attributes
- Every attribute MUST be "categorical" with 3-8 suggested values
- The values should cover the realistic space — include an "Other" value as last option
- Keys must be valid snake_case identifiers
- Make attributes specific enough to be meaningfully different across papers

Output ONLY the JSON.

Here are the papers:

{papers_text}
"""

    def __init__(self):
        self.llm = get_llm_client()

    def generate(self, papers: List[ParsedPaper]) -> GeneratedSchema:
        """
        Analyze papers and generate a custom extraction schema.

        Args:
            papers: list of ParsedPaper objects (titles + abstracts at minimum)

        Returns:
            GeneratedSchema with 5-7 attributes tailored to the topic
        """
        # Build the papers summary for the prompt
        papers_text = ""
        for i, paper in enumerate(papers, 1):
            abstract = (paper.abstract or "")[:600]
            papers_text += f"Paper {i}: {paper.title}\nAbstract: {abstract}\n\n"

        prompt = self.SCHEMA_PROMPT.format(papers_text=papers_text)

        print("Generating custom extraction schema based on paper topics...")
        response = self.llm.complete_json(prompt)

        # Parse response
        topic = response.get("topic", "Research Papers")
        topic_desc = response.get("topic_description", "")
        raw_attrs = response.get("attributes", [])

        attributes: List[AttributeSchema] = []
        for i, item in enumerate(raw_attrs[:7]):  # cap at 7
            palette = CATEGORY_PALETTES[i % len(CATEGORY_PALETTES)]
            try:
                attr = AttributeSchema(
                    key=item.get("key", f"attr_{i}"),
                    label=item.get("label", f"Attribute {i+1}"),
                    description=item.get("description", ""),
                    value_type=item.get("value_type", "categorical"),
                    suggested_values=item.get("suggested_values", []),
                    color_palette=palette[:len(item.get("suggested_values", []))],
                )
                attributes.append(attr)
            except Exception as e:
                print(f"Failed to parse attribute {i}: {e}")

        schema = GeneratedSchema(
            topic=topic,
            topic_description=topic_desc,
            attributes=attributes,
        )

        print(f"Schema generated for topic: '{topic}' with {len(attributes)} attributes")
        for a in attributes:
            print(f"  - {a.label}: {', '.join(a.suggested_values[:5])}...")

        return schema


class DynamicExtractor:
    """Extract paper attributes according to a generated schema."""

    EXTRACT_PROMPT = """You are an expert ML researcher. For the paper below, extract values for each of the listed attributes.

Research topic: {topic}

Attributes to extract:
{attributes_block}

Rules:
- For each attribute, pick ONE value from the suggested values, or use a short custom value if none fit.
- If truly unknown / not applicable, use "Unknown".
- Return ONLY a JSON object mapping attribute keys to chosen values.

Example output format:
{{
{example_keys}
}}

Paper Title: {title}

Paper Abstract:
{abstract}

Paper Content (first 10000 chars):
{content}

Output ONLY the JSON object.
"""

    def __init__(self):
        self.llm = get_llm_client()

    def extract(
        self,
        paper: ParsedPaper,
        schema: GeneratedSchema,
    ) -> Dict[str, str]:
        """
        Extract attribute values for a single paper.

        Returns:
            dict mapping attribute key -> extracted value
        """
        # Build attribute description block
        attr_lines = []
        example_keys = []
        for attr in schema.attributes:
            values_str = ", ".join(attr.suggested_values)
            attr_lines.append(
                f'- {attr.label} (key: "{attr.key}"): {attr.description}\n'
                f'  Suggested values: [{values_str}]'
            )
            example_keys.append(f'  "{attr.key}": "one of the suggested values"')

        prompt = self.EXTRACT_PROMPT.format(
            topic=schema.topic,
            attributes_block="\n".join(attr_lines),
            example_keys=",\n".join(example_keys),
            title=paper.title,
            abstract=paper.abstract or "",
            content=(paper.full_text or "")[:10000],
        )

        print(f"Extracting {len(schema.attributes)} attributes from: {paper.title[:50]}...")
        response = self.llm.complete_json(prompt)

        # Normalise: make sure every schema key has a value
        result: Dict[str, str] = {}
        for attr in schema.attributes:
            val = response.get(attr.key, "Unknown")
            if isinstance(val, list):
                val = val[0] if val else "Unknown"
            result[attr.key] = str(val)

        return result

    def extract_for_graph(
        self,
        graph: "ResearchGraph",
        schema: GeneratedSchema,
    ) -> Dict[str, Dict[str, str]]:
        """
        Extract attributes for all nodes in a graph.

        Returns:
            dict mapping node_id -> {attr_key: value}
        """
        from graph.models import ResearchGraph  # avoid circular
        results: Dict[str, Dict[str, str]] = {}

        for node in graph.nodes:
            paper = ParsedPaper(
                paper_id=node.id,
                title=node.title,
                authors=node.authors,
                abstract=node.abstract,
                full_text=node.full_text or "",
            )

            values = self.extract(paper, schema)

            # Store on the node's attributes dict
            for key, val in values.items():
                node.attributes[key] = val

            results[node.id] = values

        return results


# ── Singleton helpers ────────────────────────────────────────────────────

_schema_generator: Optional[SchemaGenerator] = None
_dynamic_extractor: Optional[DynamicExtractor] = None


def get_schema_generator() -> SchemaGenerator:
    global _schema_generator
    if _schema_generator is None:
        _schema_generator = SchemaGenerator()
    return _schema_generator


def get_dynamic_extractor() -> DynamicExtractor:
    global _dynamic_extractor
    if _dynamic_extractor is None:
        _dynamic_extractor = DynamicExtractor()
    return _dynamic_extractor
