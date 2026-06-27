#!/usr/bin/env python3
# Part of the ifURI solution — generator deterministyczny (kontrakt → kod).
"""Czyta contracts.json i emituje src/handlers_generated.py: sygnatury + kształt koperty
z kontraktu. To jest artefakt GENEROWANY i commitowany — regen_check pilnuje, że nikt go
ręcznie nie zedytował ani nie zapomniał przegenerować po zmianie kontraktu.

  python ci/emit_handlers.py                         # contracts.json → src/handlers_generated.py
  python ci/emit_handlers.py path/to/contracts.json  # inny plik
  python ci/emit_handlers.py contracts.json -        # stdout
"""
from __future__ import annotations

import json
import os
import sys
from types import SimpleNamespace
from typing import Any

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── mini codegen (kopia z urirun_contract/codegen.py) ──────────────────────

_PY = {"str": ("str", '""'), "int": ("int", "0"), "num": ("float", "0.0"),
       "bool": ("bool", "False"), "obj": ("dict | None", "None"),
       "list": ("list | None", "None"), "any": ("object", "None")}


def _base(tok: str) -> str:
    return tok[1:] if (isinstance(tok, str) and tok.startswith("?")) else tok


def _snake(route: str) -> str:
    return route.split("/")[-1].replace("-", "_")


def _const(tok: str) -> Any:
    lit = tok[len("const:"):]
    return True if lit == "true" else False if lit == "false" else lit


def _py_value(schema: Any) -> str:
    if isinstance(schema, dict):
        if set(schema) == {"oneOf"}:
            return "{}  # oneOf: " + " | ".join(
                "{" + ",".join(sorted(b)) + "}" for b in schema["oneOf"])
        inner = ", ".join(f'"{k}": {_py_value(v)}' for k, v in schema.items())
        return "{" + inner + "}"
    if isinstance(schema, list):
        return "[]"
    s = _base(schema)
    if isinstance(s, str) and s.startswith("const:"):
        v = _const(s)
        return repr(v) if isinstance(v, str) else str(v)
    return {"str": '""', "int": "0", "num": "0.0", "bool": "False",
            "obj": "{}", "list": "[]", "any": "None"}.get(s, "None")


def py_stub(route: str, c) -> str:
    inp = c.inp if isinstance(c.inp, dict) else {}
    params = []
    for key, tok in inp.items():
        if not isinstance(tok, str):
            continue
        pytype, default = _PY.get(_base(tok), ("object", "None"))
        params.append(f"{key}: {pytype} = {default}")
    sig = ", ".join(params)
    out = c.out if isinstance(c.out, dict) else {}
    if set(out) == {"oneOf"}:
        succ = out["oneOf"][0]
        body_kv = ", ".join(f'{k}={_py_value(v)}' for k, v in succ.items())
        ret = f"return _ok({body_kv})  # oneOf — wariant Degraded zwróć osobną gałęzią"
    else:
        body_kv = ", ".join(f'{k}={_py_value(v)}' for k, v in out.items())
        ret = f"return _ok({body_kv})"
    version = getattr(c, "version", "v1")
    return (f'@conn.handler("{route}", isolated=True, meta={{"label": "TODO: {route}"}})\n'
            f"def {_snake(route)}({sig}) -> dict[str, Any]:\n"
            f'    """WYGENEROWANE Z KONTRAKTU {version}. Sygnatura i kształt koperty pochodzą z\n'
            f'    contracts.json — NIE edytuj ich ręcznie (build odrzuci dryf). Uzupełnij tylko ciało."""\n'
            f'    raise NotImplementedError("ciało {route}")  # noqa: F841 — uzupełnij logikę, potem:\n'
            f"    {ret}")


def _load(path: str) -> dict:
    doc = json.load(open(path))
    return {r: SimpleNamespace(**{**c, "inverse_route": c.get("inverseRoute") or ""})
            for r, c in doc.get("contracts", {}).items()}


def emit(contracts_path: str) -> str:
    contracts = _load(contracts_path)
    header = ("# WYGENEROWANE Z contracts.json — NIE EDYTUJ RĘCZNIE.\n"
              "# Przegeneruj: `make gen`. Bramą jest ci/regen_check.py.\n"
              "from typing import Any\n\n"
              "# from .conn import conn, _ok  # zapewnione przez pakiet connectora\n\n")
    blocks = [py_stub(route, c) for route, c in sorted(contracts.items())]
    return header + "\n\n".join(blocks) + "\n"


# ── CLI ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    contracts_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "contracts.json")
    out_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "src", "handlers_generated.py")
    code = emit(contracts_path)
    if out_path == "-":
        sys.stdout.write(code)
    else:
        open(out_path, "w").write(code)
        print(f"napisano {out_path} ({code.count(chr(10))} linii)")
