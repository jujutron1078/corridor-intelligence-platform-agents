from .schema import Todo


def replace_todos_list(left: list[Todo], right: list[Todo]) -> list[Todo]:
    """
    Custom reducer for todos list.

    - If right is provided and is a list, it replaces left
    """
    if right is None:
        return left or []
    return right if isinstance(right, list) else (left or [])
