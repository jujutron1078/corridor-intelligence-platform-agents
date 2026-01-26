"""Service layer for template operations."""

from pathlib import Path
from typing import Optional


def get_template_names_by_agent(agent_name: str) -> list[str]:
    """
    Scan templates directory for a specific agent and return a list of template names.
    Template names are derived from the filename without extension.
    
    Args:
        agent_name: The name of the agent (e.g., "grant_writer", "solar")
                   This determines which subdirectory to read from.
    
    Returns:
        List of template names for the specified agent.
    """
    # Get the templates directory relative to the project root
    templates_dir = Path(__file__).parent.parent.parent.parent / "shared" / "templates"
    template_names: list[str] = []
    
    if not templates_dir.exists():
        return template_names
    
    # Get the specific agent's template directory
    agent_templates_dir = templates_dir / agent_name
    
    if not agent_templates_dir.exists() or not agent_templates_dir.is_dir():
        return template_names
    
    # Find all .md files in the agent's directory
    for template_file in agent_templates_dir.glob("*.md"):
        # Get template name from filename (without extension)
        template_name = template_file.stem
        template_names.append(template_name)
    
    # Sort and return
    return sorted(template_names)


def get_template_content(agent_name: str, template_name: str) -> Optional[str]:
    """
    Load the content of a specific template file.
    
    Args:
        agent_name: The name of the agent (e.g., "grant_writer", "solar")
        template_name: The name of the template (without .md extension)
    
    Returns:
        The template content as a string, or None if the template doesn't exist.
    """
    # Get the templates directory relative to the project root
    templates_dir = Path(__file__).parent.parent.parent.parent / "shared" / "templates"
    
    if not templates_dir.exists():
        return None
    
    # Get the specific agent's template directory
    agent_templates_dir = templates_dir / agent_name
    
    if not agent_templates_dir.exists() or not agent_templates_dir.is_dir():
        return None
    
    # Construct the template file path
    template_file = agent_templates_dir / f"{template_name}.md"
    
    if not template_file.exists():
        return None
    
    # Read and return the template content
    try:
        content = template_file.read_text(encoding="utf-8")
        return content
    except Exception:
        return None


def update_template_content(agent_name: str, template_name: str, content: str) -> bool:
    """
    Update the content of a specific template file.
    
    Args:
        agent_name: The name of the agent (e.g., "grant_writer", "solar")
        template_name: The name of the template (without .md extension)
        content: The new content to write to the template
    
    Returns:
        True if the template was successfully updated, False otherwise.
    """
    # Get the templates directory relative to the project root
    templates_dir = Path(__file__).parent.parent.parent.parent / "shared" / "templates"
    
    if not templates_dir.exists():
        return False
    
    # Get the specific agent's template directory
    agent_templates_dir = templates_dir / agent_name
    
    # Create the directory if it doesn't exist
    if not agent_templates_dir.exists():
        try:
            agent_templates_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            return False
    
    # Construct the template file path
    template_file = agent_templates_dir / f"{template_name}.md"
    
    # Write the content to the template file
    try:
        template_file.write_text(content, encoding="utf-8")
        return True
    except Exception:
        return False


def create_template_content(agent_name: str, template_name: str, content: str) -> tuple[bool, str]:
    """
    Create a new template file.
    
    Args:
        agent_name: The name of the agent (e.g., "grant_writer", "solar")
        template_name: The name of the template (without .md extension)
        content: The content to write to the template
    
    Returns:
        Tuple of (success: bool, error_message: str).
        If success is True, error_message will be empty.
        If success is False, error_message will contain the reason.
    """
    # Get the templates directory relative to the project root
    templates_dir = Path(__file__).parent.parent.parent.parent / "shared" / "templates"
    
    if not templates_dir.exists():
        try:
            templates_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            return False, "Failed to create templates directory"
    
    # Get the specific agent's template directory
    agent_templates_dir = templates_dir / agent_name
    
    # Create the directory if it doesn't exist
    if not agent_templates_dir.exists():
        try:
            agent_templates_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            return False, f"Failed to create directory for agent '{agent_name}'"
    
    # Construct the template file path
    template_file = agent_templates_dir / f"{template_name}.md"
    
    # Check if template already exists
    if template_file.exists():
        return False, f"Template '{template_name}' already exists for agent '{agent_name}'"
    
    # Write the content to the template file
    try:
        template_file.write_text(content, encoding="utf-8")
        return True, ""
    except Exception as e:
        return False, f"Failed to write template file: {str(e)}"


def delete_template_content(agent_name: str, template_name: str) -> tuple[bool, str]:
    """
    Delete a template file.
    
    Args:
        agent_name: The name of the agent (e.g., "grant_writer", "solar")
        template_name: The name of the template (without .md extension)
    
    Returns:
        Tuple of (success: bool, error_message: str).
        If success is True, error_message will be empty.
        If success is False, error_message will contain the reason.
    """
    # Get the templates directory relative to the project root
    templates_dir = Path(__file__).parent.parent.parent.parent / "shared" / "templates"
    
    if not templates_dir.exists():
        return False, "Templates directory does not exist"
    
    # Get the specific agent's template directory
    agent_templates_dir = templates_dir / agent_name
    
    if not agent_templates_dir.exists() or not agent_templates_dir.is_dir():
        return False, f"Agent directory '{agent_name}' does not exist"
    
    # Construct the template file path
    template_file = agent_templates_dir / f"{template_name}.md"
    
    # Check if template exists
    if not template_file.exists():
        return False, f"Template '{template_name}' not found for agent '{agent_name}'"
    
    # Delete the template file
    try:
        template_file.unlink()
        return True, ""
    except Exception as e:
        return False, f"Failed to delete template file: {str(e)}"
