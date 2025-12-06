import uvicorn
import fastapi

app = fastapi.FastAPI()

@app.get("/health")
@app.get("/")
def health():
    return {"message": "The server is running!"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)