TOOL_DESCRIPTION = """
Read all artifacts to answer a user's question or determine if editing is needed.

**When to use:**
- User asks questions about generated documents (artifacts) - e.g., "What's in the technical proposal?", "What did we write about the methodology?"
- User wants to edit or modify a document - e.g., "Update the budget section", "Change the timeline", "Edit the technical proposal"
- User needs information about what documents have been created
- User requests changes to existing artifacts

**What it does:**
1. Reads ALL artifacts (generated documents) in the state
2. Analyzes the user's question/request to determine the appropriate action
3. Returns a structured response with:
   - The action needed: "provide_response" (just answer) or "edit" (identify artifacts to edit)
   - A response answering the question or explaining what will be edited
   - If editing is needed: artifact IDs are added to the `artifacts_to_edit` state field

**Response actions:**
- "provide_response": User asked a question about artifacts - just provide an answer
- "edit": User wants to edit/modify documents - identifies which artifact(s) need editing (returns list of artifact IDs)

**After using this tool:**
- If artifacts are identified for editing, check the `artifacts_to_edit` state field
- Use `write_document` to regenerate those artifacts with the requested changes
- Include the original artifact content and the specific changes requested in the `write_document` call

**Args:**
    question: The user's question or request about the artifacts. Can be a question to answer or a request to edit a document.
"""
