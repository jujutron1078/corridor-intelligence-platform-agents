TODO_TOOL_PROMPT = """
You write the assistant's next message based on the todo list.

Input: a list of todos with status (pending/in_progress/completed).

Output: ONLY a single, very short sentence describing the immediate next action.

Rules:
- Extremely short (ideally 6-12 words).
- First-person ("I will ...").
- Prefer the current in_progress task; otherwise pick the top pending task.
- No bullet points, no extra text.
"""
