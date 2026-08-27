# Life Insurance AI Agent — Master Build Prompt

> Hand this file to your AI coding IDE (Cursor, Copilot, Claude Code, Antigravity, etc.) and build it phase by phase. Each phase is self-contained — complete and test one before moving to the next.

---

## 1. Project Overview

Build a **Life Insurance Coverage Advisor Agent** — a conversational AI assistant that:
1. Talks to a user, understands their financial situation (income, dependents, debt, savings, existing coverage)
2. Calculates their recommended life insurance coverage using a **deterministic formula** (never LLM-guessed math)
3. Answers questions about specific insurance policies using **RAG** (Retrieval-Augmented Generation) grounded in real policy documents, with citations
4. Recommends matching insurance products based on the user's profile

**Core design principle:** The LLM handles conversation, intent extraction, and tool orchestration. Python handles all math. RAG handles all policy-specific factual claims. Never let the LLM freely generate numbers or policy facts from memory.

---

## 2. Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React + TypeScript + Tailwind CSS |
| Backend | FastAPI (Python) |
| LLM | Google Gemini (`gemini-2.5-flash`), free tier |
| Embeddings | Gemini `embedding-001` |
| Vector DB | PostgreSQL + `pgvector` extension |
| ORM | SQLAlchemy + Alembic (migrations) |
| Auth | JWT |
| Agent/tool-calling | Gemini native function calling (no heavy framework needed; LangGraph optional later) |
| Deployment | Frontend → Vercel; Backend → Render/Railway; DB → Supabase/Neon (both support pgvector) |

---

## 3. Database Schema

```sql
-- Users
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT now()
);

-- Chat sessions
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT now()
);

-- Chat messages
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id),
    role VARCHAR(20) NOT NULL, -- 'user' | 'assistant' | 'tool'
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT now()
);

-- Extracted client profile per session
CREATE TABLE client_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id),
    age INT,
    annual_income NUMERIC,
    dependents INT,
    total_debt NUMERIC,
    available_savings NUMERIC,
    existing_life_insurance NUMERIC,
    income_replacement_years INT DEFAULT 10,
    currency VARCHAR(10) DEFAULT 'USD',
    updated_at TIMESTAMP DEFAULT now()
);

-- Policy source documents (for RAG)
CREATE TABLE policy_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    insurer_name VARCHAR(255),
    title VARCHAR(255),
    source_url TEXT,
    uploaded_at TIMESTAMP DEFAULT now()
);

-- Chunked + embedded policy text
CREATE TABLE policy_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES policy_documents(id),
    content TEXT NOT NULL,
    page_number INT,
    embedding VECTOR(768) -- Gemini embedding-001 dimension
);

-- Insurance products catalog
CREATE TABLE insurance_products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    insurer_name VARCHAR(255),
    product_name VARCHAR(255),
    min_coverage NUMERIC,
    max_coverage NUMERIC,
    term_years INT,
    premium_estimate NUMERIC,
    currency VARCHAR(10) DEFAULT 'USD',
    region VARCHAR(100)
);

CREATE INDEX ON policy_chunks USING ivfflat (embedding vector_cosine_ops);
```

---

## 4. Backend API Endpoints

```
POST   /api/auth/register
POST   /api/auth/login

POST   /api/sessions                     → create new chat session
GET    /api/sessions/{id}/messages       → fetch chat history

POST   /api/chat                         → main conversational agent endpoint
                                            body: { session_id, message }
                                            returns: { reply, profile_updated, tool_calls }

POST   /api/calculate-coverage           → deterministic calculator (standalone, callable directly)
                                            body: { annual_income, dependents, total_debt,
                                                     available_savings, existing_life_insurance,
                                                     income_replacement_years, currency }
                                            returns: { recommended_coverage, breakdown }

POST   /api/policy-qa                    → RAG Q&A over policy documents
                                            body: { question, insurer_name? }
                                            returns: { answer, citations: [{document, page, excerpt}] }

GET    /api/products?min_coverage=&region=&currency=
                                          → matching insurance products

POST   /api/admin/ingest-document        → upload + chunk + embed a policy PDF (admin only)
GET    /api/admin/documents              → list ingested documents
```

---

## 5. Coverage Calculation Formula (deterministic — implement as a pure Python function, unit test it)

```python
def calculate_coverage(
    annual_income: float,
    income_replacement_years: int,
    total_debt: float,
    available_savings: float,
    existing_life_insurance: float,
    real_discount_rate: float = 0.02,
) -> dict:
    """
    Present-value-of-annuity based income replacement + debt - assets offset.
    """
    r = real_discount_rate
    n = income_replacement_years

    if r <= 0:
        discounted_income = annual_income * n
        annuity_factor = n
    else:
        annuity_factor = (1 - (1 + r) ** (-n)) / r
        discounted_income = annual_income * annuity_factor

    assets_offset = available_savings + existing_life_insurance
    recommended = max(0.0, discounted_income + total_debt - assets_offset)

    return {
        "recommended_coverage": round(recommended, 2),
        "breakdown": {
            "discounted_income_replacement": round(discounted_income, 2),
            "annuity_factor": round(annuity_factor, 4),
            "total_debt": total_debt,
            "assets_offset": -assets_offset,
        },
        "assumptions": {
            "income_replacement_years": n,
            "real_discount_rate": r,
        },
    }
```

This must be a **standalone, unit-tested function** — never delegate this math to the LLM. The LLM only calls it as a tool once it has gathered enough profile data from the conversation.

---

## 6. RAG Pipeline (Policy Document Q&A)

**Ingestion:**
1. Admin uploads a policy PDF via `/api/admin/ingest-document`
2. Extract text (PyPDF2 / pdfplumber)
3. Chunk text — 500–700 chars per chunk, ~100 char overlap
4. Embed each chunk via Gemini `embedding-001`
5. Store chunk text + embedding + page number in `policy_chunks`

**Retrieval + Answer:**
1. User asks a policy question via `/api/policy-qa` or through the main chat agent
2. Embed the question
3. Cosine-similarity search in `policy_chunks` (top 4–6 chunks)
4. Pass retrieved chunks + question to Gemini with a strict instruction: *"Answer only using the provided context. If the context doesn't contain the answer, say you don't have that information. Always cite the document and page number."*
5. Return answer + citations (document title, page, short excerpt)

**Important:** Never let the LLM answer policy-specific factual questions (e.g., "does this cover critical illness?") without retrieved context. If retrieval returns nothing relevant, the agent must say so rather than guessing.

---

## 7. Agent / Tool-Calling Design

Use Gemini's native function calling. Define these tools:

```python
tools = [
    {
        "name": "calculate_coverage",
        "description": "Calculate recommended life insurance coverage using the client's financial profile. Call this once you have annual_income, dependents, total_debt, available_savings, and existing_life_insurance.",
        "parameters": { ... }  # matches calculate_coverage() signature
    },
    {
        "name": "search_policy_documents",
        "description": "Search ingested insurance policy documents to answer questions about coverage terms, exclusions, riders, or conditions. Always use this before answering any policy-specific factual question.",
        "parameters": { "question": "string", "insurer_name": "string (optional)" }
    },
    {
        "name": "recommend_products",
        "description": "Find matching insurance products from the product catalog based on required coverage amount, region, and currency.",
        "parameters": { "min_coverage": "number", "region": "string", "currency": "string" }
    },
]
```

**System instructions for the agent:**
```
You are a conservative, helpful life insurance advisor assistant.

Rules:
1. Never calculate coverage numbers yourself — always call `calculate_coverage` once you have the required profile fields. If fields are missing, ask the user for them conversationally, one or two at a time — don't overwhelm with a long form-like list.
2. Never answer policy-specific factual questions (coverage, exclusions, riders, claims process) from your own knowledge — always call `search_policy_documents` first and ground your answer in the returned context. If no relevant context is found, say so honestly.
3. When recommending products, call `recommend_products` — don't invent product names, prices, or insurers.
4. Keep responses concise, plain-language, and free of jargon unless the user asks for detail.
5. Always disclose: "This is educational guidance, not licensed financial advice — verify with a qualified professional."
6. Maintain conversation memory of the client profile across turns within a session.
```

---

## 8. Frontend (React + TypeScript + Tailwind)

**Pages/Components:**
- `ChatPage` — main conversational UI (message bubbles, input box, typing indicator)
- `ProfileSummaryCard` — sidebar showing extracted profile fields as they're gathered (income, dependents, debt, etc.) with live updates
- `CoverageResultCard` — displays the calculated coverage amount + breakdown (mirrors the Streamlit prototype's step-by-step math table)
- `PolicyCitation` — renders citation chips under any RAG-grounded answer (document name + page, expandable to show excerpt)
- `ProductRecommendationList` — cards showing matched insurance products
- `AdminUploadPage` — (optional, admin-only) upload policy PDFs, view ingestion status

**State management:** React Context or Zustand for session/chat state. Use `react-query` (TanStack Query) for API calls.

**Key UX principle:** Show the deterministic breakdown transparently (like a receipt) — don't just show a black-box number. This builds trust, especially for a finance-adjacent product.

---

## 9. Build Order (Milestones)

### Phase 1 — Backend Foundation (no LLM yet)
- [ ] FastAPI project skeleton, Postgres connection, SQLAlchemy models, Alembic migrations
- [ ] Implement + unit test `calculate_coverage()` as a pure function
- [ ] `/api/calculate-coverage` endpoint working standalone (test via Postman/curl)
- [ ] Auth: register/login with JWT

### Phase 2 — Basic Conversational Agent (no RAG, no tools yet)
- [ ] Gemini integration — simple chat endpoint, no function calling yet
- [ ] Session + message persistence in Postgres
- [ ] React chat UI shell — send/receive messages, display history

### Phase 3 — Tool-Calling Agent
- [ ] Wire up Gemini function calling with `calculate_coverage` as a tool
- [ ] Agent extracts profile fields conversationally across turns, stores in `client_profiles`
- [ ] `ProfileSummaryCard` in frontend updates live as fields are gathered
- [ ] `CoverageResultCard` renders when calculation tool returns

### Phase 4 — RAG Layer
- [ ] Set up `pgvector` extension in Postgres
- [ ] Document ingestion pipeline: PDF → text → chunks → embeddings → `policy_chunks`
- [ ] `/api/admin/ingest-document` + `/api/policy-qa` endpoints
- [ ] Add `search_policy_documents` as an agent tool
- [ ] `PolicyCitation` component in frontend

### Phase 5 — Product Recommendations
- [ ] Seed `insurance_products` table with sample/real product data
- [ ] `/api/products` endpoint + `recommend_products` agent tool
- [ ] `ProductRecommendationList` component

### Phase 6 — Polish & Deploy
- [ ] Error handling: LLM failures, empty RAG results, malformed tool responses — all fall back gracefully, never crash the chat
- [ ] Downloadable PDF summary of the conversation + recommendation
- [ ] Deploy: frontend → Vercel, backend → Render/Railway, DB → Supabase/Neon (pgvector-enabled)
- [ ] Basic admin dashboard for viewing sessions and managing documents

---

## 10. Non-Negotiable Guardrails (repeat to the IDE/agent building this)

1. **Math is never LLM-generated.** All coverage calculations go through the tested `calculate_coverage()` function.
2. **Policy facts are never LLM-generated.** All policy-specific answers must cite retrieved RAG context; if nothing relevant is retrieved, say so instead of guessing.
3. **Every LLM response that claims a number or a policy fact must be traceable** — either to the calculator's output or to a specific retrieved chunk with citation.
4. **Always show the disclaimer**: this is educational guidance, not licensed financial advice.
5. **Fail gracefully** — LLM/API/DB errors should degrade to a friendly message, never a raw stack trace shown to the user.

---

## 11. Environment Variables Needed

```
GOOGLE_API_KEY=
DATABASE_URL=postgresql://...
JWT_SECRET=
JWT_ALGORITHM=HS256
FRONTEND_URL=
```

---

*Build this phase by phase. Do not skip ahead to Phase 4 (RAG) before Phase 1–3 are working and tested — each phase depends on the previous one's data model and endpoints.*
