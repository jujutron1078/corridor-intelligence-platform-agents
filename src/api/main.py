from fastapi import FastAPI
from src.api.features.templates import router as templates_router

app = FastAPI()

app.include_router(templates_router)

@app.get("/hello")
def read_root():
    return {"message": "Hello, World!"}