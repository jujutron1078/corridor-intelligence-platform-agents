TOOL_DESCRIPTION = """
Delete one or more artifacts (generated documents) from the state.

**When to use:**
- User wants to remove generated document(s)
- User wants to delete artifact(s) that were created incorrectly
- User wants to clean up artifacts that are no longer needed

**What it does:**
1. Finds the artifact(s) by their ID(s) in the state
2. Removes them from the artifacts list
3. Also removes any pending edits associated with the deleted artifact(s)
4. Returns a confirmation message listing what was deleted (artifacts and associated edits)

**Args:**
    artifact_ids: A list of artifact IDs to delete. Can contain one or multiple IDs.
"""
