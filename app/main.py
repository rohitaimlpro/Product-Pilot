from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router

app = FastAPI(
    title="ProductPilot API",
    description="Backend for product recommendation and comparison",
    version="1.0.0"
)

# Allow frontend calls (Streamlit / React etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(router, prefix="/api")

@app.get("/")
def root():
    return {"message": "ProductPilot FastAPI backend is running 🚀"}
