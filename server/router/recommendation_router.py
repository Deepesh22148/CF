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


@recommendation_router.get("/evaluate")
async def get_recommendation_eval(split: str = "u1", ks: str = "5,10,15"):
    parsed_ks = [int(x.strip()) for x in ks.split(",") if x.strip()]
    body_as_str = json.dumps({
        "mode": "evaluate",
        "split": split,
        "ks": parsed_ks,
    })
    return await recommendation_controllor.get_recommendation(body_as_str)