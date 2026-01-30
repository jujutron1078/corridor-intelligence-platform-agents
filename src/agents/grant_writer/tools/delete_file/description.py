TOOL_DESCRIPTION = """
Delete a single artifact (generated document) from the state.

**When to use:**
- User wants to remove generated document(s)
- User wants to delete artifact(s) that were created incorrectly
- User wants to clean up artifacts that are no longer needed

**Parallel execution:**
- If deleting multiple unrelated artifacts, you MAY call `delete_file` in parallel (one artifact per call)
- Up to 5 `delete_file` calls at once per batch; for more than 5, process in sequential batches

**What it does:**
1. Finds the artifact by its ID in the state
2. Removes it from the artifacts list
3. Also removes any pending edits associated with the deleted artifact
4. Returns a confirmation message listing what was deleted (artifact and associated edits)

**Args:**
    artifact_id: The artifact ID to delete. One artifact per call.
"""
