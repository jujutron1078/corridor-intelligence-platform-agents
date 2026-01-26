"""Router for template endpoints."""

from fastapi import APIRouter, Query
from src.api.features.templates.service import get_template_names_by_agent, get_template_content, update_template_content, create_template_content, delete_template_content
from src.api.features.templates.schema import ApiResponse, UpdateTemplateRequest

router = APIRouter(prefix="/api/feature/templates", tags=["templates"])


@router.get("")
def get_templates(
    agent_name: str = Query(..., description="The name of the agent to get templates for (e.g., 'grant_writer', 'solar')")
) -> ApiResponse[list[str]]:
    """
    Get a list of template names for a specific agent.
    
    Args:
        agent_name: The name of the agent to get templates for
    
    Returns:
        Structured response with success, message, and data containing template names.
    """
    try:
        template_names = get_template_names_by_agent(agent_name)
        
        if template_names:
            return ApiResponse(
                success=True,
                message=f"Successfully retrieved {len(template_names)} template(s) for agent '{agent_name}'",
                data=template_names,
            )
        else:
            return ApiResponse(
                success=False,
                message=f"No templates found for agent '{agent_name}'",
                data=[],
            )
    except Exception as e:
        return ApiResponse(
            success=False,
            message=f"Error retrieving templates: {str(e)}",
            data=[],
        )


@router.get("/content")
def get_template_body(
    agent_name: str = Query(..., description="The name of the agent (e.g., 'grant_writer', 'solar')"),
    template_name: str = Query(..., description="The name of the template to retrieve")
) -> ApiResponse[str]:
    """
    Get the content/body of a specific template.
    
    Args:
        agent_name: The name of the agent
        template_name: The name of the template (without .md extension)
    
    Returns:
        Structured response with success, message, and data containing template content.
    """
    try:
        template_content = get_template_content(agent_name, template_name)
        
        if template_content is not None:
            return ApiResponse(
                success=True,
                message=f"Successfully retrieved template '{template_name}' for agent '{agent_name}'",
                data=template_content,
            )
        else:
            return ApiResponse(
                success=False,
                message=f"Template '{template_name}' not found for agent '{agent_name}'",
                data="",
            )
    except Exception as e:
        return ApiResponse(
            success=False,
            message=f"Error retrieving template: {str(e)}",
            data="",
        )


@router.put("/content")
def update_template(
    agent_name: str = Query(..., description="The name of the agent (e.g., 'grant_writer', 'solar')"),
    template_name: str = Query(..., description="The name of the template to update"),
    request: UpdateTemplateRequest = ...,
) -> ApiResponse[str]:
    """
    Update the content of a specific template.
    
    Args:
        agent_name: The name of the agent
        template_name: The name of the template (without .md extension)
        request: Request body containing the new template content
    
    Returns:
        Structured response with success, message, and data containing the updated template content.
    """
    try:
        success = update_template_content(agent_name, template_name, request.content)
        
        if success:
            # Return the updated content
            updated_content = get_template_content(agent_name, template_name)
            return ApiResponse(
                success=True,
                message=f"Successfully updated template '{template_name}' for agent '{agent_name}'",
                data=updated_content or request.content,
            )
        else:
            return ApiResponse(
                success=False,
                message=f"Failed to update template '{template_name}' for agent '{agent_name}'",
                data="",
            )
    except Exception as e:
        return ApiResponse(
            success=False,
            message=f"Error updating template: {str(e)}",
            data="",
        )


@router.post("")
def create_template(
    agent_name: str = Query(..., description="The name of the agent (e.g., 'grant_writer', 'solar')"),
    template_name: str = Query(..., description="The name of the template to create"),
    request: UpdateTemplateRequest = ...,
) -> ApiResponse[str]:
    """
    Create a new template.
    
    Args:
        agent_name: The name of the agent
        template_name: The name of the template to create (without .md extension)
        request: Request body containing the template content
    
    Returns:
        Structured response with success, message, and data containing the created template content.
    """
    try:
        success, error_message = create_template_content(agent_name, template_name, request.content)
        
        if success:
            # Return the created content
            created_content = get_template_content(agent_name, template_name)
            return ApiResponse(
                success=True,
                message=f"Successfully created template '{template_name}' for agent '{agent_name}'",
                data=created_content or request.content,
            )
        else:
            return ApiResponse(
                success=False,
                message=error_message or f"Failed to create template '{template_name}' for agent '{agent_name}'",
                data="",
            )
    except Exception as e:
        return ApiResponse(
            success=False,
            message=f"Error creating template: {str(e)}",
            data="",
        )


@router.delete("/content")
def delete_template(
    agent_name: str = Query(..., description="The name of the agent (e.g., 'grant_writer', 'solar')"),
    template_name: str = Query(..., description="The name of the template to delete"),
) -> ApiResponse[str]:
    """
    Delete a specific template.
    
    Args:
        agent_name: The name of the agent
        template_name: The name of the template to delete (without .md extension)
    
    Returns:
        Structured response with success, message, and empty data.
    """
    try:
        success, error_message = delete_template_content(agent_name, template_name)
        
        if success:
            return ApiResponse(
                success=True,
                message=f"Successfully deleted template '{template_name}' for agent '{agent_name}'",
                data="",
            )
        else:
            return ApiResponse(
                success=False,
                message=error_message or f"Failed to delete template '{template_name}' for agent '{agent_name}'",
                data="",
            )
    except Exception as e:
        return ApiResponse(
            success=False,
            message=f"Error deleting template: {str(e)}",
            data="",
        )
