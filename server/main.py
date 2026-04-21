from fastapi import FastAPI
from dotenv import load_dotenv
import os
from router.recommendation_router import recommendation_router
from router.user_router import user_router
from services.recommender_engine import get_recommender

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

app = FastAPI()


@app.on_event("startup")
async def startup_event():
    # Build SVD + clusters once at server startup for low-latency runtime requests.
    get_recommender()

app.include_router(recommendation_router)
app.include_router(user_router)

@app.get("/")
async def read_route():
    return {"message" : "Hello World"}

@app.get("/health")
async def read_route():
    return {"status" : 200 ,"detail" : "route is up!"}