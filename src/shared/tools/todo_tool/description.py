TOOL_DESCRIPTION = """
Create and manage a structured task list for the current session.

This tool REPLACES the entire todo list each time it is called.

Each todo has: id (e.g. "1"), label (short title), status (pending | in_progress | completed), description (required; details or outcome, or "" for pending).

Use it to:
- Create a task plan after a complex request (typically after think_tool)
- Mark tasks as in_progress / completed as you work
- Set description when completing a task (e.g. what was done)

Rules of thumb:
- Use unique string ids ("1", "2", ...) for each task
- Keep label short and specific; use description for details
- Prefer only ONE task as in_progress at a time
"""
