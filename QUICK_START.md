# Quick Start Guide

## 🚀 Installation (First Time Only)

```bash
cd /Users/jakubbares/Science/Schmidhubered/citation-graph-visualizer

# Install Python dependencies
cd backend
pip install -r requirements.txt

# Install Node dependencies (if not already done)
cd ..
npm install
```

## 🏃 Running the App

**Terminal 1 - Backend:**
```bash
cd /Users/jakubbares/Science/Schmidhubered/citation-graph-visualizer/backend
python api/app.py
```

**Terminal 2 - Frontend:**
```bash
cd /Users/jakubbares/Science/Schmidhubered/citation-graph-visualizer
npm run dev
```

**Open:** http://localhost:3000

---

## 📊 Quick Test Examples

### Example 1: Build Graph from ArXiv IDs

1. Open http://localhost:3000
2. Select "ArXiv / DOI Links" tab
3. Paste:
   ```
   2301.12345
   2302.23456
   2303.34567
   ```
4. Check "Include intermediate papers" ✓
5. Click "Build Graph"

### Example 2: Cluster Papers

**Via UI (TODO - not yet built):**
- After building graph, click "Cluster" button

**Via API:**
```bash
curl -X POST http://localhost:8000/api/graph/cluster \
  -H "Content-Type: application/json" \
  -d '{
    "graph_id": "YOUR_GRAPH_ID_HERE",
    "method": "hybrid",
    "n_clusters": 5
  }'
```

### Example 3: Timeline View

**Via UI:**
- After building graph, select "Timeline" from layout dropdown (TODO - add dropdown)

**Via Code:**
```typescript
<GraphCanvas graph={graph} layout="timeline" />
```

### Example 4: Extract from Survey

```bash
curl -X POST http://localhost:8000/api/survey/extract \
  -F "file=@path/to/your/survey.pdf"
```

---

## 🎨 Visual Guide

### What You'll See

**Input Papers (the ones you added):**
- Thick solid borders
- Bold text
- Full opacity
- Example: Blue paper with thick border

**Intermediate Papers (from Semantic Scholar):**
- Dashed borders
- Faded (60% opacity)
- Smaller text
- Example: Gray dashed paper

**Clusters (after clustering):**
- Each cluster gets a color:
  - Cluster 0: Blue
  - Cluster 1: Red
  - Cluster 2: Green
  - Cluster 3: Orange
  - Cluster 4: Purple

**Edges (relationships):**
- Extends: Green
- Compares: Orange
- Builds on: Blue
- Similar: Purple
- Default: Gray

---

## 🔧 Troubleshooting

### Backend won't start
```bash
# Make sure you're in the right directory
cd backend

# Check Python version (need 3.8+)
python --version

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Frontend won't start
```bash
# Delete node_modules and reinstall
rm -rf node_modules
npm install

# Try again
npm run dev
```

### "Module not found" errors
```bash
# Backend
cd backend
pip install scikit-learn numpy

# Frontend
cd ..
npm install
```

### Can't connect to API
- Make sure backend is running on port 8000
- Check: http://localhost:8000 (should show API info)
- Check CORS settings in `backend/api/app.py`

---

## 📖 API Reference

### Build Graph
```bash
POST /api/graph/build
Content-Type: multipart/form-data

# With links:
paper_identifiers: [{"type": "arxiv", "value": "2301.12345"}]
include_intermediate: true
max_depth: 1

# With PDFs:
files: [file1.pdf, file2.pdf]
include_intermediate: true
```

### Cluster Graph
```bash
POST /api/graph/cluster
Content-Type: application/json

{
  "graph_id": "abc123",
  "method": "hybrid",  # or "content" or "citations"
  "n_clusters": 5,
  "content_weight": 0.7,
  "citation_weight": 0.3
}
```

### Extract Survey
```bash
POST /api/survey/extract
Content-Type: multipart/form-data

file: survey.pdf
```

### Extract Features
```bash
POST /api/graph/extract
Content-Type: application/json

{
  "graph_id": "abc123",
  "extractors": [
    {"type": "standard", "name": "architecture"},
    {"type": "standard", "name": "contributions"}
  ]
}
```

---

## 💾 Data Flow

```
1. Input: ArXiv IDs or PDFs
   ↓
2. Fetch metadata from ArXiv/Semantic Scholar
   ↓
3. Build citation network
   ↓
4. Create graph with nodes & edges
   ↓
5. (Optional) Cluster papers
   ↓
6. (Optional) Compare papers
   ↓
7. Visualize with colors & layout
```

---

## 🎯 Best Practices

1. **Start with 5-10 papers** - test the system
2. **Use ArXiv links** - much faster than PDFs
3. **Include intermediate papers** - shows full network
4. **Cluster after building** - groups similar work
5. **Use timeline view** - see chronological flow
6. **Extract survey first** - get ground truth

---

## 📞 Need Help?

Check these files:
- `IMPLEMENTATION_COMPLETE.md` - Full feature list
- `READY_TO_TEST.md` - What to test
- `README.md` - Original project docs

---

**Last Updated:** February 2026
**Version:** 2.0.0
