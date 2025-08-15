from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allow CORS so frontend can call backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace "*" with your frontend's domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Backend is running!"}

@app.post("/upload-spec")
async def upload_spec(file: UploadFile = File(...)):
    # For now, just confirm the file upload
    return {"filename": file.filename}

@app.post("/ask")
async def ask_question(data: dict):
    question = data.get("question", "")
    return {"answer": f"You asked: {question} (Backend placeholder)"}

@app.get("/docs-data")
async def get_docs():
    return [
        {"method": "GET", "path": "/users", "description": "Get all users"},
        {"method": "POST", "path": "/users", "description": "Create a new user"},
    ]
