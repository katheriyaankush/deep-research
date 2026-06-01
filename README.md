---
title: Deep Research API
emoji: 🔬
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
---

# Deep Research API

A FastAPI-based deep research agent that:
1. Plans web searches for a given query
2. Runs searches in parallel using DuckDuckGo
3. Synthesizes a detailed markdown report
4. Sends the report via email

## API Endpoints

### `GET /`
Health check.

### `POST /research`
Run deep research on a topic. Streams status updates and the final report as Server-Sent Events.

**Request:**
```json
{
  "query": "latest trends in AI 2026"
}
```

**Response:** SSE stream with status updates and final markdown report.

## Environment Variables

Set these in your HF Space secrets:
- `OPENAI_API_KEY_D` — OpenRouter API key
- `SENDGRID_API_KEY` — SendGrid API key for email delivery
