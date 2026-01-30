from fastapi import FastAPI
from src.api.features.templates import router as templates_router
from src.api.features.company_info import router as company_info_router

app = FastAPI()

app.include_router(templates_router)
app.include_router(company_info_router)

@app.get("/hello")
def read_root():
    return {"message": "Hello, World!"}