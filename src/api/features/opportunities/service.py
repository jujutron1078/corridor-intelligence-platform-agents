import json
import logging
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src.api.features.opportunities.schema import (
    Opportunity,
    OpportunityCreate,
    OpportunityListResponse,
)

logger = logging.getLogger("corridor.api.opportunities")

WORKSPACES_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent / "workspaces"

OPPORTUNITIES_FILE = "opportunities.json"

VALID_STATUSES = {"identified", "under_review", "shortlisted", "archived"}
VALID_SECTORS = {"agriculture", "trade", "energy", "manufacturing"}


def _validate_project_id(project_id: str) -> Path:
    """Validate project_id against path traversal and return resolved path."""
    if not project_id or ".." in project_id or project_id.startswith(("/", "\\")):
        raise ValueError("Invalid project_id.")
    project_path = (WORKSPACES_DIR / project_id).resolve()
    if not project_path.is_relative_to(WORKSPACES_DIR.resolve()):
        raise ValueError("Invalid project_id.")
    return project_path


def _load_opportunities(project_path: Path) -> list[dict]:
    path = project_path / OPPORTUNITIES_FILE
    if not path.exists():
        return []
    raw = path.read_text(encoding="utf-8")
    data = json.loads(raw)
    opportunities = data.get("opportunities")
    if not isinstance(opportunities, list):
        return []
    return opportunities


def _save_opportunities(project_path: Path, opportunities: list[dict]) -> None:
    path = project_path / OPPORTUNITIES_FILE
    path.write_text(
        json.dumps({"opportunities": opportunities}, indent=2),
        encoding="utf-8",
    )


def create_opportunity(project_id: str, data: OpportunityCreate) -> Opportunity:
    """
    Save a new opportunity to the project's opportunities.json.
    Returns the created Opportunity.
    """
    project_path = _validate_project_id(project_id)
    if not project_path.is_dir():
        raise FileNotFoundError(f"Project '{project_id}' not found.")

    opportunities = _load_opportunities(project_path)

    record = {
        "id": str(uuid.uuid4()),
        "title": data.title,
        "sector": data.sector,
        "sub_sector": data.sub_sector,
        "country": data.country,
        "location": data.location,
        "bankability_score": data.bankability_score,
        "estimated_value_usd": data.estimated_value_usd,
        "estimated_return_usd": data.estimated_return_usd,
        "employment_impact": data.employment_impact,
        "gdp_multiplier": data.gdp_multiplier,
        "risk_level": data.risk_level,
        "summary": data.summary,
        "analysis_detail": data.analysis_detail,
        "data_sources": data.data_sources,
        "nearby_infrastructure": data.nearby_infrastructure,
        "status": "identified",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "thread_id": data.thread_id,
        "project_id": project_id,
    }

    opportunities.append(record)
    _save_opportunities(project_path, opportunities)

    return Opportunity(**record)


def list_opportunities(
    project_id: str,
    sector: Optional[str] = None,
    country: Optional[str] = None,
    status: Optional[str] = None,
) -> OpportunityListResponse:
    """
    List opportunities with optional filters.
    Returns sorted by created_at desc (newest first).
    """
    project_path = _validate_project_id(project_id)
    if not project_path.is_dir():
        raise FileNotFoundError(f"Project '{project_id}' not found.")

    opportunities = _load_opportunities(project_path)

    # Apply filters
    if sector:
        opportunities = [o for o in opportunities if o.get("sector") == sector]
    if country:
        opportunities = [o for o in opportunities if o.get("country") == country]
    if status:
        opportunities = [o for o in opportunities if o.get("status") == status]

    # Sort newest first
    opportunities.sort(key=lambda o: o.get("created_at", ""), reverse=True)

    # Sector counts (from filtered results)
    sector_counts = dict(Counter(o.get("sector", "unknown") for o in opportunities))

    return OpportunityListResponse(
        opportunities=[Opportunity(**o) for o in opportunities],
        total=len(opportunities),
        sectors=sector_counts,
    )


def get_opportunity(project_id: str, opportunity_id: str) -> Opportunity:
    """Get a single opportunity by ID."""
    project_path = _validate_project_id(project_id)
    if not project_path.is_dir():
        raise FileNotFoundError(f"Project '{project_id}' not found.")

    opportunities = _load_opportunities(project_path)
    for o in opportunities:
        if o.get("id") == opportunity_id:
            return Opportunity(**o)

    raise FileNotFoundError(f"Opportunity '{opportunity_id}' not found.")


def update_opportunity_status(
    project_id: str, opportunity_id: str, new_status: str
) -> Opportunity:
    """Update the status of an opportunity."""
    if new_status not in VALID_STATUSES:
        raise ValueError(f"Invalid status '{new_status}'. Must be one of: {VALID_STATUSES}")

    project_path = _validate_project_id(project_id)
    if not project_path.is_dir():
        raise FileNotFoundError(f"Project '{project_id}' not found.")

    opportunities = _load_opportunities(project_path)
    for o in opportunities:
        if o.get("id") == opportunity_id:
            o["status"] = new_status
            _save_opportunities(project_path, opportunities)
            return Opportunity(**o)

    raise FileNotFoundError(f"Opportunity '{opportunity_id}' not found.")


def delete_opportunity(project_id: str, opportunity_id: str) -> None:
    """Delete an opportunity by ID."""
    project_path = _validate_project_id(project_id)
    if not project_path.is_dir():
        raise FileNotFoundError(f"Project '{project_id}' not found.")

    opportunities = _load_opportunities(project_path)
    new_opportunities = [o for o in opportunities if o.get("id") != opportunity_id]
    if len(new_opportunities) == len(opportunities):
        raise FileNotFoundError(f"Opportunity '{opportunity_id}' not found.")

    _save_opportunities(project_path, new_opportunities)


def get_opportunities_for_export(
    project_id: str, opportunity_ids: list[str]
) -> list[Opportunity]:
    """Get multiple opportunities by IDs for export."""
    project_path = _validate_project_id(project_id)
    if not project_path.is_dir():
        raise FileNotFoundError(f"Project '{project_id}' not found.")

    opportunities = _load_opportunities(project_path)
    result = []
    id_set = set(opportunity_ids)
    for o in opportunities:
        if o.get("id") in id_set:
            result.append(Opportunity(**o))

    if not result:
        raise FileNotFoundError("No matching opportunities found.")

    return result
