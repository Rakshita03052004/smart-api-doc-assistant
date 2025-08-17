from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import json, yaml

from nlp.nlp_utils import search_endpoint
from nlp.summarizer import summarize_text, extract_keywords
from nlp.snippet_generator import generate_example_request, generate_example_response
from backend.chatbot import router as chatbot_router  # Chatbot router
from fastapi import APIRouter
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer, util

# 1️⃣ Define FastAPI app
app = FastAPI(
    title="Smart API Documentation Assistant",
    description="Automates API documentation and provides NLP Q&A",
    version="0.1.0"
)

# 2️⃣ Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3️⃣ Include chatbot router
app.include_router(chatbot_router)

# 4️⃣ Global variable to store uploaded API spec
API_SPEC = {}

# 5️⃣ Endpoints

@app.post("/parse-spec")
async def parse_api_spec(file: UploadFile = File(...)):
    """Upload an API spec (JSON or YAML)"""
    content = await file.read()
    global API_SPEC
    try:
        API_SPEC = json.loads(content)
    except json.JSONDecodeError:
        API_SPEC = yaml.safe_load(content)
    return {"message": "Spec uploaded successfully!"}


@app.get("/search")
def search(query: str):
    """Search API endpoints using NLP"""
    if not API_SPEC:
        return {"error": "No API spec uploaded yet"}
    results = search_endpoint(API_SPEC, query)
    return {"results": results}


@app.get("/summarize")
def summarize_spec():
    """Return summaries and keywords for all endpoints"""
    if not API_SPEC:
        return {"error": "No API spec uploaded yet"}

    result = {}
    paths = API_SPEC.get("paths", {})
    for endpoint, methods in paths.items():
        result[endpoint] = {}
        for method, details in methods.items():
            description = details.get("description", "")
            result[endpoint][method] = {
                "summary": summarize_text(description),
                "keywords": extract_keywords(description)
            }
    return JSONResponse(result)


@app.get("/examples")
def get_examples():
    """Return example requests/responses for all endpoints"""
    if not API_SPEC:
        return {"error": "No API spec uploaded yet"}

    examples = {}
    paths = API_SPEC.get("paths", {})
    for endpoint, methods in paths.items():
        examples[endpoint] = {}
        for method, details in methods.items():
            examples[endpoint][method] = {
                "request": generate_example_request(details),
                "response": generate_example_response(details)
            }
    return JSONResponse(examples)

router = APIRouter()

# Load model once
model = SentenceTransformer('all-MiniLM-L6-v2')

# Temporary storage of API docs for demo
API_DOCS = [
    {"endpoint": "/api/login", "description": "POST request to login user with username and password"},
    {"endpoint": "/api/register", "description": "POST request to create a new user account"},
]

# Encode docs
embeddings = model.encode([doc["description"] for doc in API_DOCS], convert_to_tensor=True)

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    intent: str
    answer: str
    code_snippet: dict
    summary: str = None

@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    user_msg = request.message
    query_emb = model.encode(user_msg, convert_to_tensor=True)

    # Semantic search
    hits = util.semantic_search(query_emb, embeddings, top_k=1)
    hit_idx = hits[0][0]['corpus_id']
    matched_doc = API_DOCS[hit_idx]

    intent = "API Info"
    answer = matched_doc["description"]
    code_snippet = {"endpoint": matched_doc["endpoint"], "method": "POST", "body": {"example": "data"}}
    summary = "This explains how to use the endpoint."

    return ChatResponse(intent=intent, answer=answer, code_snippet=code_snippet, summary=summary)    