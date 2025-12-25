from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "Crux Backend is running from inside the backend folder!"}
