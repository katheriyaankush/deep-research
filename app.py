import os
import logging
from fastapi import FastAPI
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


class ResearchRequest(BaseModel):
    query: str


@app.get("/")
async def root():
    return {"message": "Deep Research API is running. POST to /research to start."}


@app.post("/research")
async def research(request: ResearchRequest):
    """
    Run deep research on a given query.
    Streams status updates and the final markdown report as Server-Sent Events.
    """
    async def stream():
        async for chunk in ResearchManager().run(request.query):
            # Format as Server-Sent Events (SSE)
            yield f"data: {chunk}\n\n"

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port)
