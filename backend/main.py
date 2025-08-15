from fastapi import FastAPI, File, UploadFile
import json, yaml
from nlp.nlp_utils import search_endpoint  # import your NLP function

app = FastAPI(
    title="Smart API Documentation Assistant",
    description="Automates API documentation and provides NLP Q&A",
    version="0.1.0"
)

# Store the uploaded spec globally for simplicity
API_SPEC = {}

@app.post("/parse-spec")
async def parse_api_spec(file: UploadFile = File(...)):
    content = await file.read()
    global API_SPEC
    try:
        API_SPEC = json.loads(content)
    except json.JSONDecodeError:
        API_SPEC = yaml.safe_load(content)

    return {"message": "Spec uploaded successfully!"}

@app.get("/search")
def search(query: str):
    """
    Search API endpoints using NLP
    """
    if not API_SPEC:
        return {"error": "No API spec uploaded yet"}
    results = search_endpoint(API_SPEC, query)
    return {"results": results}