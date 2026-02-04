# Citation Graph Visualizer - Quick Start

## Running the Application

### 1. Start Backend (Terminal 1)
```bash
cd /Users/jakubbares/Science/Schmidhubered/citation-graph-visualizer
./start-backend.sh
```

Backend will be available at: http://localhost:8000
API docs at: http://localhost:8000/docs

### 2. Start Frontend (Terminal 2)
```bash
cd /Users/jakubbares/Science/Schmidhubered/citation-graph-visualizer
npm run dev
```

Frontend will be available at: http://localhost:3000

## First Time Setup

If this is your first time running:

1. **Configure Backend Environment**
```bash
cd backend
cp .env.example .env
# Edit .env and add your AWS credentials or DeepSeek API key
```

2. **Install Dependencies**
```bash
# Frontend
npm install

# Backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Using the Application

1. **Upload Papers**: Click "Upload Papers" and select PDF files
2. **Build Graph**: Click "Build Graph" to construct citation network
3. **Extract Features**: Select extractors (Architecture, Contributions) and click "Extract"
4. **Visualize**: Use "Visual Encoding" panel to color/size nodes by attributes
5. **Explore**: Click nodes/edges to see details

## Troubleshooting

**Backend won't start:**
- Make sure Python 3.9+ is installed
- Activate virtual environment: `source backend/venv/bin/activate`
- Install dependencies: `pip install -r backend/requirements.txt`

**Frontend won't start:**
- Make sure Node.js 18+ is installed
- Install dependencies: `npm install`

**LLM not working:**
- Check `backend/.env` has valid API credentials
- For AWS Bedrock: Verify AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY
- For DeepSeek: Set LLM_PROVIDER=deepseek and add DEEPSEEK_API_KEY

## Demo with Test Papers

To test with actual papers, copy some PDFs from the Metascientist project:

```bash
mkdir -p test_papers
cp ../Metascientist/pdfs/*.pdf test_papers/
```

Then upload them through the UI.

---

See full documentation in README.md
