from fastapi import APIRouter , Body , Request , Form , File , UploadFile , Response, Depends
import json 

from controllor import user_controllor

user_router = APIRouter(
    prefix="/user",
)

@user_router.post("/add-user")
async def add_user(request : Request):
    body_json = await request.body()
    body_as_str = body_json.decode("utf-8")

    return user_controllor.add_user(body_as_str)

@user_router.post("/update-user")
async def update_user(request: Request):
    body_json = await request.body()
    body_as_str = body_json.decode("utf-8")
    return user_controllor.update_user(body_as_str)

@user_router.post("/delete-user")
async def delete_user(request: Request):
    body_json = await request.body()
    body_as_str = body_json.decode("utf-8")

    return user_controllor.delete_user(body_as_str)

@user_router.post("/auth-user")
async def authenticate_user(request: Request):
    body_json = await request.body()
    body_as_str = body_json.decode("utf-8")
    return user_controllor.authenticate_user(body_as_str)