TOOL_DESCRIPTION = """
Edit an existing document (artifact) based on user instructions. Call once per artifact; for multiple artifacts, call edit_file in parallel (up to 5 at once) for each artifact in artifacts_to_edit.

**When to use:**
- User wants to modify an existing generated document
- User requests specific changes to content, sections, or formatting
- User wants to update information in a document that was already created
- After read_file: when artifacts_to_edit contains one or more artifact IDs

**Parallel execution (like read_file):**
- When multiple artifacts need the same or similar edit, call edit_file once per artifact in parallel
- Up to 5 edit_file calls at once per batch; for more than 5, process in sequential batches
- Check artifacts_to_edit state (populated by read_file) and call edit_file for each ID with the appropriate edit_instructions

**What it does:**
1. Retrieves the specified artifact from the state
2. Uses LLM to identify the exact text to replace in the document
3. Generates replacement content for the identified text
4. Creates edits with exact text matching (text_to_replace and edited_content)
5. Stores the edit as a pending edit (status: "pending") that requires user approval
6. Does NOT modify the original artifact until user accepts the edit

**Important:**
- The original artifact remains unchanged until the user accepts the edit through the UI
- The edits are stored in `artifact_edits` state field for UI review (grouped by artifact ID)
- Edits use exact text matching: `text_to_replace` must match the document character-for-character
- The system uses string find-and-replace to apply edits when accepted
- Users can see the text to replace and replacement content in the UI and choose to accept or reject the changes
- If accepted, the artifact content is updated using string find-and-replace and version is incremented
- If rejected, the pending edit is marked as rejected and the artifact remains unchanged
- If the same text appears multiple times, separate edits are created or context is included to target specific occurrences

**Args:**
    artifact_id: The ID of the artifact to edit (one artifact per call)
    edit_instructions: Detailed instructions for what changes to make (e.g., "Update the address", "Change timeline to 6 months")
"""
