from fastapi import FastAPI
from routes import ingest_route

app = FastAPI(title="Marketflow Ingestion Service")

app.include_router(router=ingest_route.router)

@app.get("/")
def root():
    return {"message": "Ingestion Service is running"}