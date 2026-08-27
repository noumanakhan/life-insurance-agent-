from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.api import auth, coverage, chat, policy_qa, admin, products

settings = get_settings()

app = FastAPI(
    title="Life Insurance AI Agent API",
    description="Conversational AI advisor for life insurance coverage — powered by Gemini + RAG.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Global error handler — never expose raw stack traces ──────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An unexpected error occurred. Please try again.",
            "type": type(exc).__name__,
        },
    )

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(coverage.router)
app.include_router(chat.router)
app.include_router(policy_qa.router)
app.include_router(admin.router)
app.include_router(products.router)


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok", "service": settings.app_name, "version": "1.0.0"}
