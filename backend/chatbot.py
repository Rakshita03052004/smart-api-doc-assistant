from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

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

    # Placeholder logic — replace with ML/DL models later
    intent = "Authentication"
    answer = "To make a POST request to login, send username and password in JSON."
    code_snippet = {
        "endpoint": "/api/login",
        "method": "POST",
        "body": {"username": "your_username", "password": "your_password"}
    }
    summary = "This explains how to login via POST request."

    return ChatResponse(intent=intent, answer=answer, code_snippet=code_snippet, summary=summary)