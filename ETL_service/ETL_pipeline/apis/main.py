from fastapi import FastAPI
from db.database import Base, engine
from routers import sync, entreprises

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Scraping Data Extraction Service")

app.include_router(sync.router,         prefix="/sync",        tags=["Sync"])
app.include_router(entreprises.router,  prefix="/entreprises", tags=["Entreprises"])