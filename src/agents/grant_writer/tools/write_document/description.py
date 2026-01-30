TOOL_DESCRIPTION = """
Write a complete, final document based on gathered structured context.

Use this tool when you want to generate a full final document in ONE call.

**Generation Modes:**

- **open_generation** (default): Use when you need to generate a document (e.g. technical proposal, concept note, cover letter) but:
  - You do NOT have an uploaded example/template of that document type, AND
  - The uploaded documents do NOT instruct you to fill a required form and submit it.
  You use internal templates and reference documents (ToR, compliance, etc.) to create the document.

- **fill_template**: Use when:
  - A document with category **FILL_AND_SUBMIT** or **TEMPLATE** was uploaded (e.g. application form, budget form, proposal template), OR
  - The uploaded documents explicitly require you to fill a specific form/template and submit it.
  You must use `template_document_id` to specify which uploaded document to fill.

**When to use each mode:**
- No uploaded template/form to fill, no “fill and submit” instructions → **open_generation** with `document_type`
- Uploaded FILL_AND_SUBMIT or TEMPLATE document, or instructions to fill a form → **fill_template** with `template_document_id`

**Required parameters:**
- `document_name`: Name for the generated document
- `context`: All relevant context and requirements
- `reasoning`: Why this document is being generated

**For open_generation mode:**
- `document_type`: The type of document (e.g., technical_proposal, cover_letter)

**For fill_template mode:**
- `template_document_id`: The ID of the uploaded template document to fill

**Optional parameters:**
- `reference_document_ids`: Documents to use as evidence/source material
- `constraints`, `must_include`, `must_not_include`: Content rules
- `audience`, `tone`: Style guidance
"""
