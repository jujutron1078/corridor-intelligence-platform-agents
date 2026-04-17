from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse

from src.api.features.opportunities.brief_generator import generate_investment_brief
from src.api.features.opportunities.schema import (
    ExportRequest,
    OpportunityCreate,
    OpportunityUpdate,
)
from src.api.features.opportunities.service import (
    create_opportunity,
    delete_opportunity,
    get_opportunities_for_export,
    get_opportunity,
    list_opportunities,
    update_opportunity_status,
)
from src.api.schemas import success_response

router = APIRouter(prefix="/opportunities", tags=["opportunities"])


@router.post("/{project_id}")
def create_opportunity_endpoint(project_id: str, request: OpportunityCreate):
    """Save a new opportunity to a project."""
    try:
        opportunity = create_opportunity(project_id, request)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    return success_response("Opportunity saved", opportunity.model_dump())


@router.get("/{project_id}")
def list_opportunities_endpoint(
    project_id: str,
    sector: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
):
    """List opportunities with optional filters."""
    try:
        result = list_opportunities(project_id, sector=sector, country=country, status=status)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    return success_response("Opportunities retrieved", result.model_dump())


@router.get("/{project_id}/{opportunity_id}")
def get_opportunity_endpoint(project_id: str, opportunity_id: str):
    """Get a single opportunity by ID."""
    try:
        opportunity = get_opportunity(project_id, opportunity_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

    return success_response("Opportunity retrieved", opportunity.model_dump())


@router.patch("/{project_id}/{opportunity_id}/status")
def update_status_endpoint(
    project_id: str, opportunity_id: str, request: OpportunityUpdate
):
    """Update the status of an opportunity."""
    try:
        opportunity = update_opportunity_status(project_id, opportunity_id, request.status)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    return success_response("Status updated", opportunity.model_dump())


@router.delete("/{project_id}/{opportunity_id}")
def delete_opportunity_endpoint(project_id: str, opportunity_id: str):
    """Delete an opportunity."""
    try:
        delete_opportunity(project_id, opportunity_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

    return success_response("Opportunity deleted", None)


@router.post("/{project_id}/export")
def export_brief_endpoint(project_id: str, request: ExportRequest):
    """Generate an investment brief from selected opportunities."""
    try:
        opportunities = get_opportunities_for_export(project_id, request.opportunity_ids)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

    brief = generate_investment_brief(opportunities)
    return PlainTextResponse(
        content=brief,
        media_type="text/markdown",
        headers={"Content-Disposition": "attachment; filename=investment-brief.md"},
    )
