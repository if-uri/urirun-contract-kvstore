#!/usr/bin/env python3
# Part of the ifURI solution — krok NL → kontrakt (bramkowany).
"""README (NL) → contracts.json przez lokalny LLM (LiteLLM), ale z BRAMĄ: cokolwiek model
zwróci, musi przejść conform (efekt↔czasownik, wzajemny inverse, przykłady spełniają in/out),
inaczej jest ODRZUCONE. Halucynowany kontrakt nie wejdzie. Człowiek i tak recenzuje wynik w PR.

  (domyślnie)         README.md → LLM → walidacja → contracts.json
  --mock              zwróć poprawny kanoniczny kontrakt (offline; do CI/demo)
  --mock-bad          zwróć kontrakt z NIEwzajemnym inverse (pokazuje, że brama odrzuca)
  --validate <plik>   tylko zwaliduj istniejący contracts.json (bez LLM) — używane w pre-commit
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "toolkit"))
from contract_gate import check  # noqa: E402

SCHEMA_HINT = """Zwróć WYŁĄCZNIE JSON: {"schemaVersion":1,"contracts":{<route>:{
"version","effect"(query|command),"reversible","inverseRoute","inp","out","errors","examples"}},"wires":[...]}.
Tokeny schematu: str/int/bool/obj/list, "?x" opcjonalne, "const:x", "enum:a|b", {"oneOf":[...]}.
Efekt MUSI zgadzać się z czasownikiem URI (/query/ ⇒ query). reversible ⇒ inverseRoute wzajemny.
Każdy przykład {payload,result} musi spełniać inp/out."""


def ask_llm(readme: str) -> dict:
    import litellm  # pip install litellm ; konfiguracja w litellm.config.yaml
    cfg = os.path.join(ROOT, "litellm.config.yaml")
    model = os.environ.get("LITELLM_MODEL", "ollama/llama3.1")
    resp = litellm.completion(
        model=model,
        messages=[{"role": "system", "content": SCHEMA_HINT},
                  {"role": "user", "content": f"README projektu:\n\n{readme}"}],
        config_path=cfg, temperature=0)
    text = resp["choices"][0]["message"]["content"]
    return json.loads(text[text.index("{"):text.rindex("}") + 1])


def validate_doc(doc: dict) -> list[str]:
    """Brama: ta sama logika konformansu co reszta systemu, na surowym dokumencie z LLM."""
    C = doc.get("contracts", {})
    problems: list[str] = []
    for route, c in C.items():
        if ("/query/" in route) != (c.get("effect") == "query"):
            problems.append(f"{route}: efekt {c.get('effect')!r} nie zgadza się z czasownikiem URI")
        if c.get("reversible"):
            inv = c.get("inverseRoute")
            if inv not in C:
                problems.append(f"{route}: inverseRoute {inv!r} nie istnieje")
            elif C[inv].get("inverseRoute") != route:
                problems.append(f"{route}⟂{inv} nie jest wzajemne")
        for i, ex in enumerate(c.get("examples", [])):
            try:
                check(c["inp"], ex["payload"], f"{route}#ex{i}.in")
            except AssertionError as exc:
                problems.append(str(exc))
            if ex["result"].get("ok"):
                try:
                    check(c["out"], ex["result"], f"{route}#ex{i}.out")
                except AssertionError as exc:
                    problems.append(str(exc))
    return problems


def _mock(bad: bool) -> dict:
    doc = json.load(open(os.path.join(ROOT, "contracts.json")))
    if bad:  # zepsuj wzajemność inverse — brama MUSI to złapać
        doc["contracts"]["window/command/restore"]["inverseRoute"] = "window/command/closeX"
    return doc


def main() -> int:
    args = sys.argv[1:]

    if args and args[0] == "--validate":
        doc = json.load(open(args[1]))
    elif "--mock" in args or "--mock-bad" in args:
        doc = _mock(bad="--mock-bad" in args)
    else:
        readme = open(os.path.join(ROOT, "README.md")).read()
        doc = ask_llm(readme)

    problems = validate_doc(doc)
    if problems:
        print("ODRZUCONO kontrakt (brama konformansu):", file=sys.stderr)
        for p in problems:
            print(f"  ✗ {p}", file=sys.stderr)
        return 1

    if args and args[0] == "--validate":
        print(f"OK: {args[1]} konformuje ({len(doc['contracts'])} kontraktów)")
    else:
        json.dump(doc, open(os.path.join(ROOT, "contracts.json"), "w"),
                  indent=2, ensure_ascii=False)
        print(f"OK: napisano contracts.json ({len(doc['contracts'])} kontraktów) — zrecenzuj w PR")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
