# 🎉 Citation Graph Visualizer - READY TO USE!

## ✅ Current Status

Both servers are **RUNNING** with **API keys configured**:

### Backend API (FastAPI + Python)
- **URL**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Status**: ✅ Running
- **LLM Provider**: DeepSeek (working!)
- **API Key**: Configured from Metascientist project

### Frontend (Next.js + React)
- **URL**: http://localhost:3000
- **Status**: ✅ Running
- **Features**: Full interactive UI loaded

---

## 🔑 API Keys Configured

Copied from Metascientist project and configured:

- ✅ **DeepSeek API Key**: `sk-68f53bde50014919872f056ba339ac83`
- ✅ **AWS Bedrock Credentials**: Configured (has payment issues but credentials valid)
- ✅ **LLM Provider**: Set to `deepseek` (working!)

---

## 🚀 How to Use

### 1. Open the Application
Go to: **http://localhost:3000**

### 2. Upload Papers
- Click "Upload Papers" on the left sidebar
- Select PDF files (you can test with papers from `/Users/jakubbares/Science/Metascientist/pdfs/`)
- Click "Build Graph"

### 3. Extract Features with AI
After graph is built:
- Check "Architecture" extractor (identifies model architectures: GNN, Transformer, etc.)
- Check "Contributions" extractor (extracts technical innovations)
- Click "Extract" button

The system will use **DeepSeek AI** to analyze your papers!

### 4. Visualize the Graph
Use the "Visual Encoding" panel:
- **Color by**: `architecture_type` (different colors for GNN, Transformer, etc.)
- **Size by**: `citation_count` (larger nodes = more citations)
- Click "Apply"

### 5. Explore
- **Click nodes**: View paper details (title, authors, abstract, extracted features)
- **Click edges**: View citation relationships and context
- **Zoom/Pan**: Scroll to zoom, drag to pan
- **Fit button**: Fit entire graph to screen

---

## 📊 What the AI Extractors Do

### Architecture Extractor
Identifies:
- Model architecture type (GNN, Transformer, CNN, RNN, etc.)
- Layer structure
- Number of parameters
- Novel components

### Contribution Extractor
Identifies:
- Contribution types (novel architecture, algorithm, dataset, etc.)
- Specific innovations
- Problems addressed
- Evidence locations in paper

---

## 🧪 Test with Sample Papers

Try it with papers from Metascientist:

```bash
# Papers are available at:
/Users/jakubbares/Science/Metascientist/pdfs/

# Examples:
- 2111.07568_Can_Graph_Neural_Networks_Learn_to_Solve_MaxSAT_Pr.pdf
- 2304.08738_Addressing_Variable_Dependency_in_GNN-based_SAT_So.pdf
- Learning SAT Solver.pdf
- Transformer.pdf
```

---

## 🎨 Visual Features

- **Interactive Graph**: Zoom, pan, drag nodes
- **Color Encoding**: Color nodes by any extracted attribute
- **Size Encoding**: Size nodes by numeric values
- **Detail Panels**: Click to see full information
- **Citation Analysis**: Understand paper relationships
- **Path Finding**: Trace idea evolution

---

## ⚡ Current Configuration

**LLM Provider**: DeepSeek (working!)
**Model**: `deepseek-chat`
**API Key**: Configured ✅
**Temperature**: 0.1 (more deterministic)
**Max Tokens**: 4096

---

## 🔄 Servers Running In

**Backend Terminal**: Check `/Users/jakubbares/.cursor/projects/Users-jakubbares-Science-Schmidhubered/terminals/667067.txt`

**Frontend Terminal**: Check `/Users/jakubbares/.cursor/projects/Users-jakubbares-Science-Schmidhubered/terminals/150883.txt`

Both servers auto-reload on code changes!

---

## 🎉 YOU'RE ALL SET!

Just open **http://localhost:3000** in your browser and start exploring citation networks!

The AI will analyze papers and extract features automatically using your DeepSeek API key.
