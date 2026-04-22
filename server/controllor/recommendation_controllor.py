import json
from fastapi import HTTPException

from services.recommender_engine import get_recommender

async def get_recommendation(body : str):

    payload = json.loads(body)
    mode = payload.get("mode", "dataset")

    recommender = get_recommender()

    if mode == "dataset":
        return await get_recommendation_dataset_mode(recommender, payload)
    if mode in {"personal", "personel"}:
        return await get_recommendation_personal_mode(recommender, payload)
    if mode == "evaluate":
        return await get_evaluation_metrics(recommender, payload)

    raise HTTPException(status_code=400, detail="Unsupported mode. Use dataset/personal/evaluate")

async def get_recommendation_dataset_mode(recommender, payload):
    user_id = payload.get("user_id")
    top_k = int(payload.get("top_k", 15))
    session_genres = payload.get("session_genres", [])
    similar_movies = payload.get("similar_movies", [])
    disliked_movies = payload.get("disliked_movies", [])

    if user_id is None:
        raise HTTPException(status_code=400, detail="user_id is required for dataset mode")

    try:
        result = recommender.recommend_existing_user(
            int(user_id),
            top_k=top_k,
            session_genres=session_genres,
            similar_movies=similar_movies,
            disliked_movies=disliked_movies,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    result["rate_limited"] = not bool(result.get("llm_used", False))
    return result

async def get_recommendation_personal_mode(recommender, payload):
    age = payload.get("age")
    gender = payload.get("gender")
    occupation = payload.get("occupation")
    genres = payload.get("genres", [])
    similar_movies = payload.get("similar_movies", [])
    disliked_movies = payload.get("disliked_movies", [])
    top_k = int(payload.get("top_k", 15))

    if age is None or not gender or not occupation:
        raise HTTPException(status_code=400, detail="age, gender and occupation are required for personal mode")

    try:
        result = recommender.recommend_fresh_user(
            age=float(age),
            gender=str(gender),
            occupation=str(occupation),
            genres=list(genres),
            top_k=top_k,
            similar_movies=similar_movies,
            disliked_movies=disliked_movies,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    result["rate_limited"] = not bool(result.get("llm_used", False))
    return result

async def get_evaluation_metrics(recommender, payload):
    split = str(payload.get("split", "u1"))
    ks = payload.get("ks", [5, 10, 15])
    use_llm = bool(payload.get("use_llm", True))

    if not isinstance(ks, list) or not ks:
        raise HTTPException(status_code=400, detail="ks must be a non-empty list")

    ks = [int(k) for k in ks]
    try:
        return recommender.evaluate_binary_metrics(split_name=split, ks=ks, use_llm=use_llm)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


async def get_movie_suggestions(query: str, limit: int = 8):
    recommender = get_recommender()
    try:
        suggestions = recommender.suggest_movie_titles(query=query, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "query": query,
        "suggestions": suggestions,
    }