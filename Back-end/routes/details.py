from fastapi import APIRouter

router = APIRouter()

@router.get("/details")
async def details():
    return {"message": "Details endpoint ready"}