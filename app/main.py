from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.api.v1.router import api_router

app = FastAPI()

app.include_router(api_router, prefix='/api/v1')