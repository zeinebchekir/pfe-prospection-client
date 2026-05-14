# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import LLM_generation, analyse_comportementale, enrich_lead, linkedin_posts, linkedin_url


app = FastAPI(title="Prospection LinkedIn API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(linkedin_url.router, prefix="/linkedin", tags=["LinkedIn URL"])
app.include_router(linkedin_posts.router, prefix="/linkedin", tags=["LinkedIn Posts"])
app.include_router(
    analyse_comportementale.router,
    prefix="/analyse-comportementale",
    tags=["Analyse Comportementale"],
)
app.include_router(LLM_generation.router, prefix="/ia", tags=["Analyse Lead"])
app.include_router(enrich_lead.router, prefix="/enrich", tags=["LinkedIn URL"])


@app.get("/health")
async def health():
    return {"status": "ok"}
