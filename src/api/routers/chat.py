"""
Chat endpoints — conversational AI interface.

POST /api/chat
POST /api/chat/report
"""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, HTTPException, Request

from src.api.models.requests import ChatRequest, ReportRequest
from src.api.models.responses import ChatResponse
from src.api.services.chat_service import process_chat
from src.api.services.llm_service import llm_call
from src.api.config import MODEL_ROUTES, RATE_LIMIT_CHAT
from src.api.security import limiter

logger = logging.getLogger("corridor.api.chat")

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
@limiter.limit(RATE_LIMIT_CHAT)
async def chat(request: Request, body: ChatRequest):
    """
    Main chat endpoint. The conversational AI interface.

    Classifies the query, routes to the right model, executes data tools,
    and returns a structured response with text, map layers, charts, and sources.
    """
    conversation_id = body.conversation_id or str(uuid.uuid4())

    try:
        response = await process_chat(
            message=body.message,
            conversation_id=conversation_id,
            include_map_layers=body.include_map_layers,
        )
        response.conversation_id = conversation_id
        return response
    except Exception as exc:
        logger.error("Chat processing error: %s", exc, exc_info=True)
        return ChatResponse(
            response="I encountered an error processing your request. Please try rephrasing your question.",
            conversation_id=conversation_id,
            model_used="error",
        )


@router.post("/report", response_model=ChatResponse)
@limiter.limit(RATE_LIMIT_CHAT)
async def generate_report(request: Request, body: ReportRequest):
    """
    Generate a structured report (investment brief, due diligence, etc.).

    Uses the 'report' model route for high-quality written output.
    """
    try:
        system_prompt = f"""You are an expert economic analyst writing a {body.report_type}
for the {body.corridor_segment} segment of the Lagos-Abidjan corridor.

Structure your report as a professional document with:
- Executive Summary
- Key Findings (backed by data)
- Risk Assessment
- Recommendations
- Data Sources

Use specific data points and coordinates where available."""

        response = await llm_call(
            route="report",
            messages=[{
                "role": "user",
                "content": f"Generate a {body.report_type} for the {body.corridor_segment} "
                           f"corridor segment. Include analysis of economic activity, infrastructure, "
                           f"trade flows, and investment potential.",
            }],
            system=system_prompt,
        )

        text = response["choices"][0]["message"]["content"]

        return ChatResponse(
            response=text,
            sources=["VIIRS Nightlights", "ESA WorldCover", "UN Comtrade", "USGS Minerals", "OpenStreetMap"],
            model_used=MODEL_ROUTES["report"]["model"],
        )
    except Exception as exc:
        logger.error("Report generation error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Report generation failed")
