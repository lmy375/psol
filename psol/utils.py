import json
from typing import Any

from solders.pubkey import Pubkey


class SolanaJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Pubkey):
            return str(obj)
        if isinstance(obj, bytes):
            return obj.hex()

        try:
            if hasattr(obj, "__dict__"):
                if obj.__dict__:
                    return super().default(obj.__dict__)
            return super().default(obj)
        except TypeError:
            return str(obj)


def to_dict(obj: Any):
    if hasattr(obj, "__dict__"):
        if obj.__dict__:
            return to_dict(obj.__dict__)

    if isinstance(obj, dict):
        return {k: to_dict(v) for k, v in obj.items() if k.startswith("_") is False}

    if hasattr(obj, "params"):
        return to_dict(obj.params)

    return obj
