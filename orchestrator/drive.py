#!/usr/bin/env python3
# Part of the ifURI solution — ORCHESTRATOR / brama międzyprocesowa (handoff skalarny).
"""Wiąże dwa procesy po HTTP wspólnym kontraktem (command → query):

  1. POST producent  →  koperta kv/command/set (zapisuje do współdzielonego store'u)
  2. krawędź WIRES (set→get: key←key) → wejście konsumenta {key}
  3. consumer_input_check → mode=FULL (key to całe wejście get)
  4. POST konsument {key}  →  koperta kv/query/get (czyta ten sam store)
  5. zwaliduj odpowiedź + potwierdź, że value wróciło przez granicę procesu; exit 0/1

Stan przepływa przez współdzielony plik store'u; KLUCZ przepływa kontraktem po sieci."""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "toolkit"))
from urirun_contract.gate import check, consumer_input_check, find_wire, wire_payload  # noqa: E402
from contracts_io import load  # noqa: E402

PRODUCER = os.environ.get("PRODUCER_URL", "http://localhost:8801")
CONSUMER = os.environ.get("CONSUMER_URL", "http://localhost:8802")
CONSUMER_GO = os.environ.get("CONSUMER_GO_URL")
PROD_ROUTE = "kv/command/set"
CONS_ROUTE = "kv/query/get"
CONTRACTS, WIRES = load()


def post(url: str, payload: dict) -> dict:
    req = urllib.request.Request(url + "/run", data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())


def wait_ready(url, tries=40):
    for _ in range(tries):
        try:
            urllib.request.urlopen(url + "/health", timeout=1); return True
        except Exception:
            time.sleep(0.5)
    raise SystemExit(f"serwis {url} nie wstał")


def _run_pair(label: str, producer_url: str, consumer_url: str) -> int:
    prod_env = post(producer_url, {"key": "greeting", "value": "hello world"})
    check(CONTRACTS[PROD_ROUTE].out, prod_env, "producer.out")

    wire = find_wire(WIRES, PROD_ROUTE, CONS_ROUTE)
    payload = wire_payload(wire, prod_env)            # {key} dug from set's output
    mode, problems = consumer_input_check(CONTRACTS[CONS_ROUTE], payload, wire)
    if problems:
        print(f"  ✗ [{label}] krawędź niezgodna ({mode}): {problems}")
        return 1

    cons_env = post(consumer_url, payload)
    check(CONTRACTS[CONS_ROUTE].out, cons_env, "consumer.out")
    if not (cons_env.get("found") and cons_env.get("value") == "hello world"):
        print(f"  ✗ [{label}] wartość nie przeszła przez granicę procesu: {cons_env}")
        return 1

    print(f"  [OK ] {label}  ({mode} handoff)")
    print(f"        set key   = {prod_env['key']}")
    print(f"        get value = {cons_env['value']!r} (found={cons_env['found']})")
    return 0


def main() -> int:
    wait_ready(PRODUCER); wait_ready(CONSUMER)
    code = 0
    code |= _run_pair("producer(py) ──HTTP──▶ consumer(py)", PRODUCER, CONSUMER)
    if CONSUMER_GO:
        wait_ready(CONSUMER_GO)
        code |= _run_pair("producer(py) ──HTTP──▶ consumer(go)", PRODUCER, CONSUMER_GO)
    if code == 0:
        print("  klucz przez kontrakt, wartość przez współdzielony store, dwa języki: OK")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
