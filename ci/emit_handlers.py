#!/usr/bin/env python3
# Part of the ifURI solution — generator deterministyczny (kontrakt → szkielet).
"""Czyta contracts.json i emituje src/handlers_generated.py.
Importuje codegen z urirun_contract (jedyne źródło — nie przepisuj tu py_stub/go_stub).

  python ci/emit_handlers.py                         # contracts.json → src/handlers_generated.py
  python ci/emit_handlers.py path/to/contracts.json  # inny plik
  python ci/emit_handlers.py contracts.json -        # stdout

Wymaga: pip install urirun-contract
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

from urirun_contract.codegen import _load_contracts_json, emit_py_module  # noqa: E402


def emit(contracts_path: str) -> str:
    contracts = _load_contracts_json(contracts_path)
    return emit_py_module(contracts)


if __name__ == "__main__":
    contracts_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "contracts.json")
    out_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "src", "handlers_generated.py")
    code = emit(contracts_path)
    if out_path == "-":
        sys.stdout.write(code)
    else:
        open(out_path, "w").write(code)
        print(f"napisano {out_path} ({code.count(chr(10))} linii)")
