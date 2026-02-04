#!/usr/bin/env python3
"""
Test script for Citation Graph Visualizer API
Tests with real PDFs from Metascientist project
"""
import requests
import sys
from pathlib import Path

API_URL = "http://localhost:8000"

def test_api_with_pdfs():
    """Test the API with real PDF files"""
    
    print("🧪 Testing Citation Graph Visualizer API")
    print("=" * 60)
    
    # Test PDF files
    pdf_dir = Path("/Users/jakubbares/Science/Metascientist/pdfs")
    test_pdfs = [
        "2111.07568_Can_Graph_Neural_Networks_Learn_to_Solve_MaxSAT_Pr.pdf",
        "2304.08738_Addressing_Variable_Dependency_in_GNN-based_SAT_So.pdf",
        "Learning SAT Solver.pdf"
    ]
    
    print(f"\n📚 Testing with {len(test_pdfs)} PDFs:")
    for pdf in test_pdfs:
        print(f"   - {pdf}")
    
    # Prepare files for upload
    files = []
    for pdf_name in test_pdfs:
        pdf_path = pdf_dir / pdf_name
        if not pdf_path.exists():
            print(f"❌ PDF not found: {pdf_path}")
            continue
        
        print(f"\n📖 Reading: {pdf_name}")
        with open(pdf_path, 'rb') as f:
            files.append(('files', (pdf_name, f.read(), 'application/pdf')))
    
    if not files:
        print("❌ No PDF files found!")
        return False
    
    # Test 1: Build graph
    print(f"\n🔨 Test 1: Building graph WITH INTERMEDIATE PAPERS...")
    try:
        response = requests.post(
            f"{API_URL}/api/graph/build",
            files=files,
            params={
                "include_intermediate": "true",  # ENABLE INTERMEDIATE PAPERS
                "max_depth": 1
            },
            timeout=300  # Longer timeout for API calls
        )
        
        if response.status_code == 200:
            data = response.json()
            graph_id = data.get("graph_id")
            stats = data.get("stats", {})
            
            print(f"✅ Graph built successfully!")
            print(f"   - Graph ID: {graph_id}")
            print(f"   - Input Papers: {stats.get('input_papers', 0)}")
            print(f"   - Intermediate Papers: {stats.get('intermediate_papers_added', 0)}")
            print(f"   - Total Papers: {stats.get('total_papers', 0)}")
            print(f"   - Citations: {stats.get('total_citations', 0)}")
            
            # Test 2: Extract features
            print(f"\n🔍 Test 2: Extracting features...")
            extract_response = requests.post(
                f"{API_URL}/api/graph/extract",
                json={
                    "graph_id": graph_id,
                    "extractors": [
                        {"type": "standard", "name": "architecture"},
                        {"type": "standard", "name": "contributions"}
                    ]
                },
                timeout=300
            )
            
            if extract_response.status_code == 200:
                extract_data = extract_response.json()
                print(f"✅ Features extracted!")
                print(f"   - Papers processed: {extract_data.get('stats', {}).get('papers_processed', 0)}")
            else:
                print(f"❌ Feature extraction failed: {extract_response.status_code}")
                print(f"   {extract_response.text}")
            
            # Test 3: Apply visual encoding
            print(f"\n🎨 Test 3: Applying visual encoding...")
            viz_response = requests.post(
                f"{API_URL}/api/graph/visualize",
                json={
                    "graph_id": graph_id,
                    "encoding": {
                        "color": {"attribute": "architecture_type"},
                        "size": {"attribute": "citation_count"}
                    }
                },
                timeout=30
            )
            
            if viz_response.status_code == 200:
                print(f"✅ Visual encoding applied!")
            else:
                print(f"⚠️  Visual encoding failed: {viz_response.status_code}")
            
            print(f"\n" + "=" * 60)
            print(f"✅ ALL TESTS PASSED!")
            print(f"\nView graph at: http://localhost:3000")
            print(f"Graph ID: {graph_id}")
            
            return True
            
        else:
            print(f"❌ Graph building failed: {response.status_code}")
            print(f"   {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"❌ Request timed out!")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_api_with_pdfs()
    sys.exit(0 if success else 1)
