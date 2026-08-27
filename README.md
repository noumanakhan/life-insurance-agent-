# Life Insurance AI Agent

A full-stack conversational AI advisor for life insurance coverage.

## Architecture
- **Frontend:** React + TypeScript + Tailwind CSS (Vite)  
- **Backend:** FastAPI (Python)  
- **LLM:** Google Gemini `gemini-2.5-flash` with native function calling  
- **Embeddings:** Gemini `embedding-001` (768 dims)  
- **Vector DB:** PostgreSQL + pgvector  
- **Auth:** JWT  

## Quick Start

### 1. Prerequisites
- Python 3.9+
- Node.js 18+
- PostgreSQL with **pgvector** extension (`CREATE EXTENSION vector;`)

### 2. Backend Setup
```bash
cd backend
cp .env.example .env
# Edit .env — add your GOOGLE_API_KEY and DATABASE_URL

python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Seed sample insurance products
python seed_products.py

# Start the API server
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
# Runs at http://localhost:5173
```

### 4. Environment Variables (`.env`)
```
GOOGLE_API_KEY=your_gemini_api_key
DATABASE_URL=postgresql://postgres:password@localhost:5432/life_insurance
JWT_SECRET=your_super_secret_key
JWT_ALGORITHM=HS256
FRONTEND_URL=http://localhost:5173
```

## Running Tests
```bash
cd backend
source venv/bin/activate
pytest tests/ -v
```

## API Docs
Once the server is running: http://localhost:8000/docs

## Phase Status
- ✅ Phase 1 — Backend Foundation (models, auth, calculator, migrations)
- ✅ Phase 2 — Basic Conversational Agent (Gemini chat, session persistence)
- ✅ Phase 3 — Tool-Calling Agent (calculate_coverage, search_policy, recommend_products)
- ✅ Phase 4 — RAG Layer (PDF ingestion, pgvector search, citations)
- ✅ Phase 5 — Product Recommendations (catalog, seeded products)
- 🔲 Phase 6 — Polish & Deploy (PDF export, admin dashboard, Vercel/Render deploy)

## Key Design Principles
1. **Math is never LLM-generated** — all coverage calculations use the deterministic `calculate_coverage()` function
2. **Policy facts are never LLM-generated** — all policy answers cite retrieved RAG context
3. **Fail gracefully** — all errors degrade to friendly messages
4. **Always show the disclaimer** — educational guidance, not licensed advice