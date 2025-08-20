from fastapi import FastAPI, File, UploadFile, APIRouter
from fastapi.responses import JSONResponse, HTMLResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer, util
import json, yaml
from pathlib import Path

# Local imports
from nlp.nlp_utils import search_endpoint
from nlp.summarizer import summarize_text, extract_keywords, format_api_summary
from nlp.snippet_generator import generate_example_request, generate_example_response
from backend.chatbot import router as chatbot_router

# ------------------------
# FastAPI App
# ------------------------
app = FastAPI(
    title="Smart API Documentation Assistant",
    description="Automates API documentation and provides NLP Q&A",
    version="0.1.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include chatbot router
app.include_router(chatbot_router)

# ------------------------
# Global variables
# ------------------------
API_SPEC = {}

# ------------------------
# Upload API Spec
# ------------------------
@app.post("/parse-spec")
async def parse_api_spec(file: UploadFile = File(...)):
    """Upload an API spec (JSON or YAML)"""
    content = await file.read()
    global API_SPEC
    try:
        # json.loads accepts bytes/str; safe to try first
        API_SPEC = json.loads(content)
    except json.JSONDecodeError:
        API_SPEC = yaml.safe_load(content)
    return {"message": "Spec uploaded successfully!"}

@app.post("/upload-api")
async def upload_api(file: UploadFile = File(...)):
    """Accept API doc (JSON or YAML) and return a small preview."""
    content = await file.read()
    text = content.decode("utf-8")
    global API_SPEC
    try:
        API_SPEC = yaml.safe_load(text)
    except Exception:
        API_SPEC = json.loads(text)

    summary_preview = {
        "title": API_SPEC.get("info", {}).get("title", "N/A"),
        "version": API_SPEC.get("info", {}).get("version", "N/A"),
        "paths": list(API_SPEC.get("paths", {}).keys())[:5],
    }
    return {"summary": summary_preview, "message": "Spec uploaded successfully!"}

# ------------------------
# Search Endpoints
# ------------------------
@app.get("/search")
def search(query: str):
    if not API_SPEC:
        return {"error": "No API spec uploaded yet"}
    results = search_endpoint(API_SPEC, query)
    return {"results": results}

# ------------------------
# Summarize Spec (JSON, kept for internal use)
# ------------------------
@app.get("/summarize")
def summarize_spec():
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

# ------------------------
# User-friendly English summary (Markdown for frontend)
# ------------------------
@app.get("/api-summary", response_class=PlainTextResponse)
def api_summary():
    """
    Return a clean Markdown string (no HTML wrappers) so the frontend
    can render it with react-markdown/bytemd + plugins (GFM, Mermaid).
    """
    if not API_SPEC:
        return "❌ No API spec uploaded yet"

    formatted_md = format_api_summary(API_SPEC)  # should already be Markdown
    return formatted_md



# ------------------------
# Chat Endpoint
# ------------------------
router = APIRouter()

model = SentenceTransformer('all-MiniLM-L6-v2')
API_DOCS = [
    {"endpoint": "/api/login", "description": "POST request to login user with username and password"},
    {"endpoint": "/api/register", "description": "POST request to create a new user account"},
]

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
    hits = util.semantic_search(query_emb, embeddings, top_k=1)
    hit_idx = hits[0][0]['corpus_id']
    matched_doc = API_DOCS[hit_idx]

    intent = "API Info"
    answer = matched_doc["description"]
    code_snippet = {"endpoint": matched_doc["endpoint"], "method": "POST", "body": {"example": "data"}}
    summary = "This explains how to use the endpoint."

    return ChatResponse(intent=intent, answer=answer, code_snippet=code_snippet, summary=summary)

app.include_router(router)

# ------------------------
# Root
# ------------------------
@app.get("/")
def read_root():
    return {"message": "Welcome to Smart API Documentation Assistant 🚀"}

# ------------------------
# Summarize APIs as HTML table (for internal use)
# ------------------------
@app.get("/summarize-table", response_class=HTMLResponse)
def summarize_apis(limit: int = 5):
    specs_path = Path("data/specs.json")
    if not specs_path.exists():
        return "<h3>❌ specs.json not found. Please download it first.</h3>"

    with open(specs_path, "r") as f:
        specs = json.load(f)

    total = len(specs)
    sample_items = list(specs.items())[:limit]

    rows = ""
    for name, details in sample_items:
        preferred = details.get("preferred", "")
        versions = ", ".join(details.get("versions", {}).keys())
        rows += f"<tr><td>{name}</td><td>{preferred}</td><td>{versions}</td></tr>"

    return f"""
    <h2>📊 API Summary</h2>
    <p>We found <b>{total}</b> APIs in specs.json. Showing {limit} examples:</p>
    <table border="1" cellspacing="0" cellpadding="6">
        <tr><th>Name</th><th>Preferred</th><th>Versions</th></tr>
        {rows}
    </table>
    """

def generate_flow_diagram(api_spec: dict) -> str:
    """
    Return a Mermaid diagram as fenced Markdown so frontend
    renderers can pick it up automatically.
    """
    paths = api_spec.get("paths", {})
    mermaid_lines = ["flowchart LR", "A[👤 User]"]

    if "/signup" in paths:
        mermaid_lines.append("A --> B[POST /signup]")
        mermaid_lines.append("B --> C[✅ Account Created]")

    if "/login" in paths:
        mermaid_lines.append("C --> D[POST /login]")
        mermaid_lines.append("D --> E[🔑 JWT Token]")

    if "/users/{userId}" in paths:
        mermaid_lines.append("E --> F[GET /users/{userId}]")
        mermaid_lines.append("F --> G[📄 User Profile Data]")

    # 🔁 Return as Markdown fenced code block (NOT HTML)
    return "```mermaid\n" + "\n".join(mermaid_lines) + "\n```"

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

# Path to React build folder (adjust if needed)
build_path = os.path.join(os.path.dirname(__file__), "../frontend/build")

# Serve static files (CSS, JS, etc.)
app.mount("/static", StaticFiles(directory=os.path.join(build_path, "static")), name="static")

# Serve React index.html for all frontend routes
@app.get("/{full_path:path}")
async def serve_react(full_path: str):
    index_file = os.path.join(build_path, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"error": "Frontend build not found. Run `npm run build` first."}

# Store uploaded spec
API_SPEC = {}

@app.post("/upload-spec/")
async def upload_spec(file: UploadFile = File(...)):
    global API_SPEC
    content = await file.read()
    try:
        if file.filename.endswith(".json"):
            API_SPEC = json.loads(content.decode("utf-8"))
        elif file.filename.endswith((".yaml", ".yml")):
            API_SPEC = yaml.safe_load(content.decode("utf-8"))
        else:
            return {"error": "File must be JSON or YAML"}
    except Exception as e:
        return {"error": f"Failed to parse: {str(e)}"}
    
    return {"message": "Spec uploaded successfully", "title": API_SPEC.get("info", {}).get("title")}

@app.get("/get-spec/")
async def get_spec():
    """Return full uploaded API spec"""
    if not API_SPEC:
        return {"error": "No API spec uploaded yet"}
    return API_SPEC

@app.get("/search/")
async def search_spec(keyword: str):
    """Search the uploaded API spec for a keyword (e.g., 'login')"""
    if not API_SPEC:
        return {"error": "No API spec uploaded yet"}

    keyword = keyword.lower()
    results = {}

    # Search in paths
    for path, methods in API_SPEC.get("paths", {}).items():
        for method, details in methods.items():
            if (keyword in path.lower()) or (keyword in method.lower()) or (keyword in str(details).lower()):
                if path not in results:
                    results[path] = {}
                results[path][method] = details

    # Search in components (if present)
    if "components" in API_SPEC:
        for comp_type, comp_defs in API_SPEC["components"].items():
            for comp_name, comp_details in comp_defs.items():
                if (keyword in comp_name.lower()) or (keyword in str(comp_details).lower()):
                    if "components" not in results:
                        results["components"] = {}
                    if comp_type not in results["components"]:
                        results["components"][comp_type] = {}
                    results["components"][comp_type][comp_name] = comp_details

    if not results:
        return {"message": f"No matches found for '{keyword}'"}
    return JSONResponse(content=results)