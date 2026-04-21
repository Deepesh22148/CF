from fastapi import APIRouter , Body , Request , Form , File , UploadFile , Response, Depends
import json 
from controllor import recommendation_controllor


recommendation_router = APIRouter(
    prefix="/recommendation",
)

@recommendation_router.post("/")
async def get_recommendation(request : Request):
    body_json = await request.body()
    body_as_str = body_json.decode("utf-8")

    return await recommendation_controllor.get_recommendation(body_as_str)