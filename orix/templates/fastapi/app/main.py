from fastapi import FastAPI

app = FastAPI(title="{{ project_name }}")

@app.get("/")
async def root():
    return {"message": "Welcome to {{ project_name }}"}

{% if use_auth %}
@app.post("/login")
async def login():
    return {"token": "sample_token"}
{% endif %}
