# WYGENEROWANE Z contracts.json — NIE EDYTUJ RĘCZNIE.
# Przegeneruj: `make gen`. Bramą jest ci/regen_check.py.
from typing import Any

# from .conn import conn, _ok  # zapewnione przez pakiet connectora

@conn.handler("kv/command/set", isolated=True, meta={"label": "TODO: kv/command/set"})
def set(key: str = "", value: str = "") -> dict[str, Any]:
    """WYGENEROWANE Z KONTRAKTU v1. Sygnatura i kształt koperty pochodzą z
    contracts.json — NIE edytuj ich ręcznie (build odrzuci dryf). Uzupełnij tylko ciało."""
    raise NotImplementedError("ciało kv/command/set")  # noqa: F841 — uzupełnij logikę, potem:
    return _ok(action='kv-set', key="", stored=True)

@conn.handler("kv/query/get", isolated=True, meta={"label": "TODO: kv/query/get"})
def get(key: str = "") -> dict[str, Any]:
    """WYGENEROWANE Z KONTRAKTU v1. Sygnatura i kształt koperty pochodzą z
    contracts.json — NIE edytuj ich ręcznie (build odrzuci dryf). Uzupełnij tylko ciało."""
    raise NotImplementedError("ciało kv/query/get")  # noqa: F841 — uzupełnij logikę, potem:
    return _ok(action='kv-get', key="", value="", found=False)
