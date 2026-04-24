import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import db
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import analytics, links, redirect

app = FastAPI(
    title="Oracle URL Shortener API",
    description="REST API for the Oracle URL shortener with Redis caching and rate limiting. Part 5 of a 5-part series.",
    version="3.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

db.init_db()

app.include_router(links.router)
app.include_router(analytics.router)
app.include_router(redirect.router)
