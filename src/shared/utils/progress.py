from typing import Callable, Any


class ProgressTracker:
    """Helper class to manage progress updates with less boilerplate.

    This is a shared utility for tools that stream progress events.
    """

    def __init__(
        self,
        writer: Callable[[dict], None],
        *,
        event_type: str,
        id: str,
        name: str | None = None,
        name_field: str = "document_name",
    ):
        self._writer = writer
        self._event_type = event_type
        self._id = id
        self._name = name
        self._name_field = name_field

    def _send(
        self,
        message: str,
        status: str = "running",
        progress: int | None = None,
        sub_messages: list[str] | None = None,
        **extras: Any,
    ) -> None:
        payload: dict[str, Any] = {
            "type": self._event_type,
            "id": self._id,
            "message": message,
        }

        if self._name:
            payload[self._name_field] = self._name
        if status:
            payload["status"] = status
        if progress is not None:
            payload["progress"] = progress
        if sub_messages is not None:
            payload["sub_messages"] = sub_messages

        payload.update(extras)
        self._writer(payload)

    def update(
        self,
        message: str,
        sub_messages: list[str] | None = None,
        progress: int | None = None,
        **extras: Any,
    ) -> None:
        self._send(
            message,
            status="running",
            sub_messages=sub_messages,
            progress=progress,
            **extras,
        )

    def complete(self, message: str) -> None:
        self._send(message, status="completed")

    def complete_with_progress(self, message: str, progress: int = 100, **extras: Any) -> None:
        """Send a completion status update with an explicit progress value."""
        self._send(message, status="completed", progress=progress, **extras)

    def error(self, message: str) -> None:
        self._send(message, status="error")

    def error_with_progress(self, message: str, progress: int | None = None, **extras: Any) -> None:
        """Send an error status update with an optional progress value."""
        self._send(message, status="error", progress=progress, **extras)

