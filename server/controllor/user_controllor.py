from fastapi import APIRouter , Body , Request , Form , File , UploadFile , Response, HTTPException
from utils.db import db_utils

import json

def add_user(body : str):
    body = json.loads(body)
    name = body.get("name")
    age = body.get("age")
    occupation = body.get("occupation", "NA")
    password = body.get("password")

    if not name or age is None:
        raise HTTPException(
            status_code=400,
            detail="Missing required fields: name and age"
        )

    # cluster funcitonality here!
    
    new_user = db_utils("users", "add", {
        "name": name,
        "age": age,
        "occupation": occupation,
        "password": password,
        "cluster_id": 1
    })

    return {
        "message": "User created successfully",
        "data": new_user
    }
    

def update_user(body: str):
    body = json.loads(body)

    user_id = body.get("id")
    if user_id is None:
        raise HTTPException(
            status_code=400,
            detail="Missing required field: id"
        )

    update_data = {}

    if "name" in body:
        update_data["name"] = body["name"]
    if "age" in body:
        update_data["age"] = body["age"]
    if "occupation" in body:
        update_data["occupation"] = body["occupation"]

    if not update_data:
        raise HTTPException(
            status_code=400,
            detail="No fields provided to update"
        )

    updated_user = db_utils("users", "update", {
        "id": user_id,
        **update_data
    })

    if "error" in updated_user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "message": "User updated successfully",
        "data": updated_user
    }
    
def delete_user(body: str):
    body = json.loads(body)

    user_id = body.get("id")
    if user_id is None:
        raise HTTPException(
            status_code=400,
            detail="Missing required field: id"
        )

    result = db_utils("users", "delete", {
        "id": user_id
    })

    return {
        "message": "User deleted successfully",
        "data": result
    }
    
def get_user(body : str):
    body = json.loads(body)
    user_id = body.get("user_id")
    
    if not user_id:
        return {"error": "user_id required"}

    user = db_utils("users", "get", {"id": user_id})

    if "error" in user:
        return {"error": "User not found"}

    return user
    
def authenticate_user(body: str):
    body = json.loads(body)

    name = body.get("name")
    password = body.get("password")

    if not name or not password:
        return {"error": "name and password required"}

    users = db_utils("users", "search", {"name": name})

    if not users:
        return {"error": "User not found"}

    user = users[0] 

    if user.get("password") != password:
        return {"error": "Invalid credentials"}

    return {
        "message": "authenticated",
        "user_id": user["id"]
    }
    