import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.api import api_router
from app.core.config import settings

app = FastAPI(
    title="Ostrich Service Support API",
    description="API for Service Technician Mobile App",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def read_root():
    return {
        "message": "Ostrich Service Support API",
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "service": "ostrich-service-api",
        "environment": os.getenv("ENVIRONMENT", "development")
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8002))
    uvicorn.run(app, host="0.0.0.0", port=port)
