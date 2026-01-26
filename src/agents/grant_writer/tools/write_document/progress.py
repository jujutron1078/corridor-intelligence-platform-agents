from typing import Callable, Any


class ProgressTracker:
    """Helper class to manage progress updates with less boilerplate."""

    def __init__(
        self,
        writer: Callable[[dict], None],
        doc_id: str,
        document_name: str,
    ):
        self._writer = writer
        self._doc_id = doc_id
        self._document_name = document_name

    def _send(
        self,
        message: str,
        status: str = "running",
        progress: int | None = None,
        sub_messages: list[str] | None = None,
        **extras: Any,
    ) -> None:
        """Send a progress update.
        
        Payload structure matches frontend expectations:
        {
            type: "write_document_progress"  // Required
            id: string                        // Required
            message: string                  // Required
            progress?: number                // Optional: 0-100
            document_name?: string          // Optional
            status?: "running" | "completed" | "error"  // Optional
            sub_messages?: string[]         // Optional: for cycling messages
        }
        """
        payload: dict[str, Any] = {
            "type": "write_document_progress",
            "id": self._doc_id,
            "message": message,
        }
        
        # Add optional fields only if they have values
        if self._document_name:
            payload["document_name"] = self._document_name
        if status:
            payload["status"] = status
        if progress is not None:
            payload["progress"] = progress
        if sub_messages is not None:
            payload["sub_messages"] = sub_messages
        
        # Add any additional extras
        payload.update(extras)
        
        self._writer(payload)

    def update(
        self,
        message: str,
        sub_messages: list[str] | None = None,
        progress: int | None = None,
        **extras: Any,
    ) -> None:
        """Send a running status update."""
        self._send(
            message,
            status="running",
            sub_messages=sub_messages,
            progress=progress,
            **extras,
        )

    def complete(self, message: str) -> None:
        """Send a completion status update."""
        self._send(message, status="completed")

    def error(self, message: str) -> None:
        """Send an error status update."""
        self._send(message, status="error")
