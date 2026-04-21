from fastapi import FastAPI
from router import recommendation_router

app = FastAPI()

app.include_router(recommendation_router)


@app.get("/")
async def read_route():
    return {"message" : "Hello World"}

@app.get("/health")
async def read_route():
    return {"status" : 200 ,"detail" : "route is up!"}


