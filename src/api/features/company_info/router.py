"""Router for company info endpoints."""

from fastapi import APIRouter, Query
from src.api.features.company_info.service import (
    list_company_info_names,
    get_company_info_content,
    create_company_info,
    update_company_info,
    delete_company_info,
)
from src.api.features.company_info.schema import ApiResponse, UpdateCompanyInfoRequest

router = APIRouter(prefix="/api/feature/company-info", tags=["company-info"])


@router.get("")
def list_companies() -> ApiResponse[list[str]]:
    """
    List all company info names (organizations).
    Each name corresponds to a file {org_name}.md in shared/company_information/.
    """
    try:
        names = list_company_info_names()
        return ApiResponse(
            success=True,
            message=f"Successfully retrieved {len(names)} company info file(s)",
            data=names,
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            message=f"Error listing company info: {str(e)}",
            data=[],
        )


@router.get("/content")
def get_content(
    org_name: str = Query(..., description="Organization name (e.g. 'bayes')"),
) -> ApiResponse[str]:
    """
    Get the markdown content of a company info file.
    """
    try:
        content = get_company_info_content(org_name)
        if content is not None:
            return ApiResponse(
                success=True,
                message=f"Successfully retrieved company info for '{org_name}'",
                data=content,
            )
        return ApiResponse(
            success=False,
            message=f"Company info for '{org_name}' not found",
            data="",
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            message=f"Error retrieving company info: {str(e)}",
            data="",
        )


@router.post("")
def create(
    org_name: str = Query(..., description="Organization name (e.g. 'bayes')"),
    request: UpdateCompanyInfoRequest = ...,
) -> ApiResponse[str]:
    """
    Create a new company info file.
    Fails if a file for this org_name already exists (use update instead).
    """
    try:
        success, error_message = create_company_info(org_name, request.content)
        if success:
            content = get_company_info_content(org_name)
            return ApiResponse(
                success=True,
                message=f"Successfully created company info for '{org_name}'",
                data=content or request.content,
            )
        return ApiResponse(
            success=False,
            message=error_message or f"Failed to create company info for '{org_name}'",
            data="",
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            message=f"Error creating company info: {str(e)}",
            data="",
        )


@router.put("/content")
def update(
    org_name: str = Query(..., description="Organization name (e.g. 'bayes')"),
    request: UpdateCompanyInfoRequest = ...,
) -> ApiResponse[str]:
    """
    Update the content of an existing company info file.
    """
    try:
        success = update_company_info(org_name, request.content)
        if success:
            content = get_company_info_content(org_name)
            return ApiResponse(
                success=True,
                message=f"Successfully updated company info for '{org_name}'",
                data=content or request.content,
            )
        return ApiResponse(
            success=False,
            message=f"Company info for '{org_name}' not found or update failed",
            data="",
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            message=f"Error updating company info: {str(e)}",
            data="",
        )


@router.delete("/content")
def delete(
    org_name: str = Query(..., description="Organization name (e.g. 'bayes')"),
) -> ApiResponse[str]:
    """
    Delete a company info file.
    """
    try:
        success, error_message = delete_company_info(org_name)
        if success:
            return ApiResponse(
                success=True,
                message=f"Successfully deleted company info for '{org_name}'",
                data="",
            )
        return ApiResponse(
            success=False,
            message=error_message or f"Failed to delete company info for '{org_name}'",
            data="",
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            message=f"Error deleting company info: {str(e)}",
            data="",
        )
