import os
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"  # hides info & warning logs

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import identify, details, health
# main.py  ← only change: add two lines
from routes import disease_router


app = FastAPI(title="PlantVision AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(disease_router.router)
app.include_router(identify.router)
app.include_router(details.router)
app.include_router(health.router)