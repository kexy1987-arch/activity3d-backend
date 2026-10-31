from datetime import datetime
from enum import Enum
from typing import Type

def from_json_safe(value, enum_type: Type[Enum] | None = None):
    # Convert dict
    if isinstance(value, dict):
        return {k: from_json_safe(v, enum_type) for k, v in value.items()}

    # Convert list
    if isinstance(value, list):
        return [from_json_safe(v, enum_type) for v in value]

    # Convert ISO datetime string → datetime
    if isinstance(value, str):
        # Try datetime
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            pass

        # Try enum
        if enum_type is not None:
            try:
                return enum_type(value)
            except ValueError:
                pass

    # Return unchanged
    return value
