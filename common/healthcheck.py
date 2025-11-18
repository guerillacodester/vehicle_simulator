from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def health_check():
    """Reusable health check endpoint for service monitoring."""
    return {"status": "healthy"}
