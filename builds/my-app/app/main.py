from fastapi import FastAPI

app = FastAPI(title="my-app")

@app.get("/")
async def root():
    return {"message": "Welcome to my-app"}
