# Citation Graph Visualizer

An interactive research paper citation network visualization system that helps researchers explore how scientific ideas evolve across papers through citation relationships.

![Citation Graph Visualizer](https://img.shields.io/badge/Next.js-16-black) ![FastAPI](https://img.shields.io/badge/FastAPI-Python-green) ![Cytoscape.js](https://img.shields.io/badge/Cytoscape.js-Visualization-blue)

## 🎯 Features

- **Interactive Graph Visualization**: Explore citation networks with zoom, pan, and interactive node selection
- **Intelligent Feature Extraction**: Automatically extract architectures, contributions, and methodologies from papers using LLMs
- **Visual Encoding System**: Color, size, and shape nodes based on paper characteristics
- **Citation Analysis**: Understand relationships between papers with edge labels and contribution types
- **Real-time Filtering**: Filter papers by attributes to find relevant subsets
- **Detail Panels**: View comprehensive information about selected papers and citations
- **Path Finding**: Trace the evolution of ideas through citation paths

## 📋 Architecture

### Frontend (Next.js + TypeScript)
- **Framework**: Next.js 16 with App Router
- **Visualization**: Cytoscape.js for graph rendering
- **Styling**: Tailwind CSS
- **State Management**: React hooks

### Backend (Python + FastAPI)
- **API Framework**: FastAPI for REST endpoints
- **Graph Processing**: NetworkX for graph algorithms
- **LLM Integration**: AWS Bedrock or DeepSeek for feature extraction
- **PDF Parsing**: PyMuPDF for paper processing

## 🚀 Quick Start

### Prerequisites

- **Node.js** 18+ and npm
- **Python** 3.9+
- **AWS Bedrock** account (or DeepSeek API key)

### Installation

1. **Clone the repository**
```bash
cd citation-graph-visualizer
```

2. **Install frontend dependencies**
```bash
npm install
```

3. **Install backend dependencies**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

4. **Configure environment variables**

**Backend** (`backend/.env`):
```bash
# Copy example and edit
cp backend/.env.example backend/.env

# Edit backend/.env and add your credentials:
# - AWS_ACCESS_KEY_ID
# - AWS_SECRET_ACCESS_KEY
# - Or DEEPSEEK_API_KEY if using DeepSeek
```

**Frontend** (`.env.local`):
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Running the Application

**Terminal 1 - Start Backend:**
```bash
./start-backend.sh
# Or manually:
# cd backend && source venv/bin/activate && python -m uvicorn api.app:app --reload
```

**Terminal 2 - Start Frontend:**
```bash
npm run dev
```

Open your browser to:
- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs

## 📖 Usage Guide

### 1. Build a Citation Graph

1. Click "Upload Papers" in the left sidebar
2. Select PDF files of research papers (drag & drop supported)
3. Click "Build Graph" to construct the citation network

The system will:
- Parse all PDFs
- Extract citations from papers
- Build a directed graph of citation relationships
- Display the interactive visualization

### 2. Extract Features

After building a graph:

1. Select extractors from the "Extract Features" panel:
   - **Architecture**: Identifies model architectures (GNN, Transformer, CNN, etc.)
   - **Contributions**: Extracts technical contributions and innovations

2. Click "Extract" to run LLM analysis on all papers

Features are stored as node attributes and become available for visualization.

### 3. Apply Visual Encodings

Customize the visualization:

- **Color by**: Attribute (e.g., architecture_type)
  - Papers with same architecture type get the same color
  
- **Size by**: Numeric attribute (e.g., citation_count)
  - Larger nodes = higher values
  
- **Shape by**: Categorical attribute (e.g., contribution_type)
  - Different shapes for different contribution types

Click "Apply" to update the visualization.

### 4. Explore the Graph

**Interactions:**
- **Click node**: View paper details in right panel
- **Click edge**: View citation relationship details
- **Drag node**: Temporarily reposition
- **Scroll**: Zoom in/out
- **Drag canvas**: Pan around
- **Fit button**: Fit entire graph to screen
- **Reset button**: Reset zoom level

### 5. Analyze Citation Relationships

When you click an edge, the detail panel shows:
- Source paper (citing)
- Target paper (cited)
- Contribution type (baseline, foundation, extension, etc.)
- Citation context (where/why the paper was cited)
- Relationship strength

## 🏗️ Project Structure

```
citation-graph-visualizer/
├── app/                      # Next.js app directory
│   ├── page.tsx             # Main application page
│   ├── layout.tsx           # Root layout
│   └── globals.css          # Global styles
├── components/              # React components
│   ├── GraphCanvas.tsx      # Cytoscape.js visualization
│   ├── PaperUpload.tsx      # File upload component
│   ├── ExtractorPanel.tsx   # Feature extraction UI
│   ├── VisualEncodingPanel.tsx  # Visual encoding controls
│   └── DetailPanel.tsx      # Node/edge details display
├── lib/
│   └── api.ts              # API client for backend
├── backend/
│   ├── api/
│   │   └── app.py          # FastAPI application
│   ├── graph/
│   │   ├── models.py       # Graph data models
│   │   └── builder.py      # Graph construction logic
│   ├── extractors/         # LLM-based feature extractors
│   │   ├── llm_client.py
│   │   ├── architecture_extractor.py
│   │   └── contribution_extractor.py
│   ├── parsers/
│   │   └── pdf_parser.py   # PDF parsing
│   ├── config.py           # Configuration
│   └── requirements.txt    # Python dependencies
├── start-backend.sh        # Backend startup script
├── package.json            # Node dependencies
└── README.md               # This file
```

## 🔌 API Endpoints

### `POST /api/graph/build`
Build citation graph from uploaded PDFs.

**Request:**
- Form data with PDF files

**Response:**
```json
{
  "graph_id": "uuid",
  "graph": {...},
  "stats": {
    "total_papers": 50,
    "total_citations": 120
  }
}
```

### `POST /api/graph/extract`
Extract features from papers in graph.

**Request:**
```json
{
  "graph_id": "uuid",
  "extractors": [
    {"type": "standard", "name": "architecture"},
    {"type": "standard", "name": "contributions"}
  ]
}
```

### `POST /api/graph/visualize`
Apply visual encodings to graph.

**Request:**
```json
{
  "graph_id": "uuid",
  "encoding": {
    "color": {"attribute": "architecture_type"},
    "size": {"attribute": "citation_count"}
  }
}
```

### `POST /api/graph/filter`
Filter graph by attributes.

### `POST /api/graph/path`
Find paths between papers.

### `GET /api/graph/{graph_id}`
Get graph by ID.

### `GET /api/graphs`
List all graphs.

Full API documentation: http://localhost:8000/docs

## 🎨 Customization

### Adding Custom Extractors

Create a new extractor in `backend/extractors/`:

```python
from dataclasses import dataclass
from .llm_client import get_llm_client

@dataclass
class MyFeature:
    field1: str
    field2: str

class MyExtractor:
    def __init__(self):
        self.llm = get_llm_client()
    
    def extract(self, paper):
        prompt = f"""Extract ... from this paper:
        {paper.full_text}
        
        Output as JSON: {{"field1": "...", "field2": "..."}}
        """
        response = self.llm.complete_json(prompt)
        return MyFeature(**response)
```

Register it in `backend/api/app.py` to make it available via API.

### Customizing Visual Styles

Edit `components/GraphCanvas.tsx` to modify:
- Node shapes and sizes
- Edge styles
- Color schemes
- Layout algorithms

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest
```

### Frontend Tests
```bash
npm test
```

### Manual Testing
1. Use sample PDFs from `backend/test_papers/`
2. Upload to UI and verify graph construction
3. Run extractors and check results
4. Test visual encodings and filters

## 🛠️ Troubleshooting

### "ModuleNotFoundError" in Backend
- Ensure virtual environment is activated
- Run `pip install -r requirements.txt`

### "AWS Bedrock Access Denied"
- Verify AWS credentials in `backend/.env`
- Check model access in AWS Console
- Alternatively, switch to DeepSeek:
  ```bash
  LLM_PROVIDER=deepseek
  DEEPSEEK_API_KEY=your_key_here
  ```

### Cytoscape.js Not Rendering
- Check browser console for errors
- Verify graph data format in Network tab
- Try clearing browser cache

### CORS Errors
- Ensure backend is running on port 8000
- Check `NEXT_PUBLIC_API_URL` in `.env.local`
- Verify CORS middleware in `backend/api/app.py`

## 📚 Technology Stack

### Frontend
- **Next.js 16**: React framework with App Router
- **TypeScript**: Type-safe JavaScript
- **Cytoscape.js**: Graph visualization library
- **Tailwind CSS**: Utility-first CSS framework
- **Axios**: HTTP client

### Backend
- **FastAPI**: Modern Python web framework
- **NetworkX**: Graph algorithms and analysis
- **PyMuPDF**: PDF text extraction
- **AWS Bedrock**: LLM API (Llama 3.3 70B)
- **DeepSeek**: Alternative LLM provider
- **Pydantic**: Data validation

## 🤝 Contributing

Contributions are welcome! Areas for improvement:

- [ ] Add more extractors (datasets, metrics, training methods)
- [ ] Implement graph clustering algorithms
- [ ] Add export functionality (JSON, GraphML, PNG)
- [ ] Improve citation extraction accuracy
- [ ] Add support for ArXiv/DOI import
- [ ] Implement real-time collaboration
- [ ] Add graph database backend (Neo4j)

## 📄 License

MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

Built using extractors adapted from the [Metascientist](../Metascientist) project.

Based on the comprehensive [Citation Graph Visualizer Specification](../Citation-Graph-Visualizer-Specification.md).

## 📞 Support

For issues or questions:
1. Check [Troubleshooting](#troubleshooting) section
2. Review API docs at http://localhost:8000/docs
3. Open an issue on GitHub

---

**Built with ❤️ for researchers exploring scientific knowledge graphs**
