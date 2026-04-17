"""Tests for the opportunities feature (CRUD, export, brief generation)."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from src.api.features.opportunities.brief_generator import generate_investment_brief
from src.api.features.opportunities.schema import Opportunity, OpportunityCreate
from src.api.features.opportunities.service import (
    create_opportunity,
    delete_opportunity,
    get_opportunity,
    get_opportunities_for_export,
    list_opportunities,
    update_opportunity_status,
)


@pytest.fixture()
def tmp_workspaces(tmp_path):
    """Create a temp workspaces dir with a test project."""
    project_dir = tmp_path / "test-project"
    project_dir.mkdir()
    (project_dir / "PROJECT.md").write_text('---\nproject_name: "Test"\n---\n\n')
    with patch("src.api.features.opportunities.service.WORKSPACES_DIR", tmp_path):
        yield tmp_path


def _make_create_request(**overrides) -> OpportunityCreate:
    defaults = {
        "title": "Cassava Processing Facility",
        "sector": "agriculture",
        "country": "Nigeria",
        "location": {"lat": 6.5, "lng": 3.3, "name": "Ogun State"},
        "summary": "High cassava output with no nearby processing.",
        "bankability_score": 0.78,
        "estimated_value_usd": 5_000_000,
        "risk_level": "medium",
    }
    defaults.update(overrides)
    return OpportunityCreate(**defaults)


class TestCreateOpportunity:
    def test_create_and_persist(self, tmp_workspaces):
        opp = create_opportunity("test-project", _make_create_request())

        assert opp.id
        assert opp.title == "Cassava Processing Facility"
        assert opp.sector == "agriculture"
        assert opp.status == "identified"
        assert opp.project_id == "test-project"

        # Verify persisted to disk
        data = json.loads((tmp_workspaces / "test-project" / "opportunities.json").read_text())
        assert len(data["opportunities"]) == 1
        assert data["opportunities"][0]["id"] == opp.id

    def test_create_multiple(self, tmp_workspaces):
        create_opportunity("test-project", _make_create_request(title="Opp 1"))
        create_opportunity("test-project", _make_create_request(title="Opp 2"))

        result = list_opportunities("test-project")
        assert result.total == 2

    def test_create_invalid_project(self, tmp_workspaces):
        with pytest.raises(FileNotFoundError):
            create_opportunity("nonexistent", _make_create_request())

    def test_create_path_traversal(self, tmp_workspaces):
        with pytest.raises(ValueError):
            create_opportunity("../etc", _make_create_request())


class TestListOpportunities:
    def test_list_empty(self, tmp_workspaces):
        result = list_opportunities("test-project")
        assert result.total == 0
        assert result.opportunities == []

    def test_filter_by_sector(self, tmp_workspaces):
        create_opportunity("test-project", _make_create_request(sector="agriculture"))
        create_opportunity("test-project", _make_create_request(sector="trade"))

        result = list_opportunities("test-project", sector="agriculture")
        assert result.total == 1
        assert result.opportunities[0].sector == "agriculture"

    def test_filter_by_country(self, tmp_workspaces):
        create_opportunity("test-project", _make_create_request(country="Nigeria"))
        create_opportunity("test-project", _make_create_request(country="Ghana"))

        result = list_opportunities("test-project", country="Ghana")
        assert result.total == 1
        assert result.opportunities[0].country == "Ghana"

    def test_filter_by_status(self, tmp_workspaces):
        opp = create_opportunity("test-project", _make_create_request())
        update_opportunity_status("test-project", opp.id, "shortlisted")

        result = list_opportunities("test-project", status="shortlisted")
        assert result.total == 1

        result = list_opportunities("test-project", status="identified")
        assert result.total == 0

    def test_sector_counts(self, tmp_workspaces):
        create_opportunity("test-project", _make_create_request(sector="agriculture"))
        create_opportunity("test-project", _make_create_request(sector="agriculture"))
        create_opportunity("test-project", _make_create_request(sector="trade"))

        result = list_opportunities("test-project")
        assert result.sectors == {"agriculture": 2, "trade": 1}


class TestGetOpportunity:
    def test_get_existing(self, tmp_workspaces):
        created = create_opportunity("test-project", _make_create_request())
        fetched = get_opportunity("test-project", created.id)
        assert fetched.id == created.id
        assert fetched.title == created.title

    def test_get_nonexistent(self, tmp_workspaces):
        with pytest.raises(FileNotFoundError):
            get_opportunity("test-project", "nonexistent-id")


class TestUpdateStatus:
    def test_update_valid_status(self, tmp_workspaces):
        opp = create_opportunity("test-project", _make_create_request())
        updated = update_opportunity_status("test-project", opp.id, "shortlisted")
        assert updated.status == "shortlisted"

    def test_update_invalid_status(self, tmp_workspaces):
        opp = create_opportunity("test-project", _make_create_request())
        with pytest.raises(ValueError):
            update_opportunity_status("test-project", opp.id, "invalid")

    def test_update_nonexistent(self, tmp_workspaces):
        with pytest.raises(FileNotFoundError):
            update_opportunity_status("test-project", "nonexistent-id", "shortlisted")


class TestDeleteOpportunity:
    def test_delete_existing(self, tmp_workspaces):
        opp = create_opportunity("test-project", _make_create_request())
        delete_opportunity("test-project", opp.id)

        result = list_opportunities("test-project")
        assert result.total == 0

    def test_delete_nonexistent(self, tmp_workspaces):
        with pytest.raises(FileNotFoundError):
            delete_opportunity("test-project", "nonexistent-id")


class TestBriefGenerator:
    def test_generate_brief(self, tmp_workspaces):
        opp = create_opportunity("test-project", _make_create_request(
            estimated_return_usd=15_000_000,
            employment_impact=200,
            gdp_multiplier=2.5,
            analysis_detail="Detailed analysis of cassava value chain.",
            data_sources=["FAO", "World Bank"],
            nearby_infrastructure=["Lagos-Cotonou Highway"],
        ))

        opportunities = get_opportunities_for_export("test-project", [opp.id])
        brief = generate_investment_brief(opportunities)

        assert "Investment Brief" in brief
        assert "Cassava Processing Facility" in brief
        assert "$5.0M" in brief
        assert "200 jobs" in brief
        assert "2.50x" in brief
        assert "FAO" in brief
        assert "Value Detective" in brief

    def test_generate_brief_multiple(self, tmp_workspaces):
        opp1 = create_opportunity("test-project", _make_create_request(title="Opp 1", country="Nigeria"))
        opp2 = create_opportunity("test-project", _make_create_request(title="Opp 2", country="Ghana"))

        opportunities = get_opportunities_for_export("test-project", [opp1.id, opp2.id])
        brief = generate_investment_brief(opportunities)

        assert "Opp 1" in brief
        assert "Opp 2" in brief
        assert "2 investment opportunities" in brief
