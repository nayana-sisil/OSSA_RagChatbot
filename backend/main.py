import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from rag_engine import query_tutor
import uvicorn

app = FastAPI(title="OSSA AI Tutor API")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    question: str
    exam_mode: bool = False

class Source(BaseModel):
    file: str
    page: str

class QueryResponse(BaseModel):
    answer: str
    sources: List[Source]

@app.get("/", tags=["General"])
async def root():
    """Health check endpoint to verify backend connectivity."""
    return {
        "name": "OSSA AI Tutor API",
        "version": "1.0.0",
        "status": "online"
    }

@app.post("/ask", response_model=QueryResponse, tags=["AI Tutor"])
async def ask_question(request: QueryRequest):
    """
    Core RAG endpoint. Accepts a question and optional exam_mode flag.
    Retrieves relevant lecture context and generates a grounded response.
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    
    try:
        result = query_tutor(request.question, request.exam_mode)
        return result
    except Exception as e:
        print(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
