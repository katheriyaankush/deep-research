import os
import json
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from core.research_manager import ResearchManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

load_dotenv(override=True)

app = FastAPI(
    title="Deep Research API",
    description="API for running deep research on any topic",
    version="1.0.0",
)

# Allow frontend to consume the API from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ResearchRequest(BaseModel):
    query: str
    email: str


@app.get("/")
async def root():
    return {"message": "Deep Research API is running. POST to /research to start."}


@app.post("/research")
async def research(request: ResearchRequest):
    """
    Run deep research on a given query.
    Streams structured JSON events via Server-Sent Events (SSE).

    Event types:
    - status: Progress updates (planning, searching, writing, etc.)
    - search_plan: The planned search queries
    - search_progress: Individual search completion updates
    - report: The final research report with summary and follow-up questions
    - error: Any errors that occurred
    - done: Research complete signal
    """
    async def stream():
        async for event in ResearchManager().run(request.query, request.email):
            # Each event is already a dict from ResearchManager
            yield f"event: {event['type']}\ndata: {json.dumps(event['data'])}\n\n"

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port)
