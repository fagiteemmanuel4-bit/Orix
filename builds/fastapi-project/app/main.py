from fastapi import FastAPI

app = FastAPI(title="fastapi-project")

@app.get("/")
async def root():
    return {"message": "Welcome to fastapi-project"}
