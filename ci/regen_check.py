#!/usr/bin/env python3
# Part of the ifURI solution — brama anty-dryfu generacji.
"""Przegeneruj src/handlers_generated.py z contracts.json do bufora i porównaj z tym, co
w repo. Różnica = albo ktoś ręcznie zedytował generowany plik, albo zmienił kontrakt i
zapomniał przegenerować. Egzekwuje regułę 'kształtu nie pisze się ręcznie'.

  python ci/regen_check.py                                  # domyślne ścieżki
  python ci/regen_check.py path/contracts.json path/out.py  # jawne ścieżki
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "ci"))
import emit_handlers as eh  # noqa: E402

contracts_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "contracts.json")
committed_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "src", "handlers_generated.py")

fresh = eh.emit(contracts_path)
have = open(committed_path).read() if os.path.exists(committed_path) else ""
if have != fresh:
    print(f"DRYF: {committed_path} != generacja z {contracts_path}", file=sys.stderr)
    print("  uruchom `make gen` i scommituj (albo cofnij ręczną edycję generowanego pliku)",
          file=sys.stderr)
    sys.exit(1)
print(f"OK: wygenerowany kod zgodny z kontraktem (brak ręcznego dryfu)")
