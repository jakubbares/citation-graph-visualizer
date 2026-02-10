## Backend and Frontend Fixed ✅

**What was fixed:**
1. ✅ Increased Semantic Scholar API timeout from 10s to 30s
2. ✅ Added exponential backoff retry logic (3 retries with 1s, 2s, 4s delays)
3. ✅ Increased rate limit wait time from 5s to 10s
4. ✅ Created `.env.example` with instructions for getting Semantic Scholar API key

**Current Issue:**
The citation network builder only adds "intermediate" papers when they connect MULTIPLE input papers. When you input a SINGLE survey paper, it fetches 134 references and 4 citations but doesn't add them as nodes in the graph. The algorithm needs to be modified to:
- Include reference papers (papers the survey cites) as nodes
- Include citing papers (papers that cite the survey) as nodes
- Not just look for "intermediate" papers

**How to get a Semantic Scholar API key (FREE):**
1. Go to: https://www.semanticscholar.org/product/api
2. Sign up (takes 2 minutes)
3. Get your free API key (5,000 requests per 5 minutes instead of 100)
4. Add to backend/.env:
   ```
   SEMANTIC_SCHOLAR_API_KEY=your_key_here
   ```

**Next step needed:**
Modify the citation network builder to include references/citations as actual nodes in the graph, not just as intermediate connectors.
