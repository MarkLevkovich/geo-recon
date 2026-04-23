from fastapi import APIRouter



router = APIRouter(
    prefix="/geo",
    tags=["GeoReconRouter"],
)

@router.get("/hi")
async def hi():
    return {
        "Message": "Hello from GeoRecon!"
    }