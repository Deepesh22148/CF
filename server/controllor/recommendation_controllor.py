import json

async def get_recommendation(body : str):
    
    body = json.loads(body)
    mode = body.get("mode")
    user_id = body.get("user_id")
    
    if mode == "dataset":
        # dataset mode
        return await get_recommendation_dataset_mode()
    else:
        # personel mode
        await get_recommendation_personel_mode()
        
async def get_recommendation_dataset_mode():
    return None

async def get_recommendation_personel_mode():
    return None