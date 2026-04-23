from fastapi import FastAPI
from server.geo_router import router as geo_router

app = FastAPI(
    title="GeoRecon",
    openapi_url=None,
    redoc_url=None
)

app.include_router(geo_router)
