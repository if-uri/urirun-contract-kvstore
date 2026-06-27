#!/usr/bin/env python3
# Part of the ifURI solution — pakiet PRODUCENTA (proces 1).
"""Serwis HTTP udostępniający ``kv/command/set``. Zapisuje key→value do współdzielonego store'u
(plik JSON wskazany przez KV_STORE) i zwraca kopertę walidowaną wobec out-schematu kontraktu.
Klucz z odpowiedzi zasila potem ``kv/query/get`` w innym procesie.

  POST /run  {key, value}  →  koperta kv/command/set
  GET  /health             →  {"ok": true}
"""
from __future__ import annotations

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "toolkit"))
from contract_gate import check  # noqa: E402
from contracts_io import load  # noqa: E402

ROUTE = "kv/command/set"
STORE = os.environ.get("KV_STORE", "/tmp/kvstore.json")
CONTRACTS, _ = load()
C = CONTRACTS[ROUTE]


def set_handler(key: str, value: str) -> dict:
    db = json.load(open(STORE)) if os.path.exists(STORE) else {}
    db[key] = value
    json.dump(db, open(STORE, "w"))
    return {"ok": True, "connector": "kvstore", "action": "kv-set", "key": key, "stored": True}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"ok": true}')

    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", 0) or 0))
        payload = json.loads(body or b"{}")
        try:
            check(C.inp, payload, "inp")
        except AssertionError as exc:
            self.send_response(422)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"ok": False, "error": f"input violates {ROUTE}: {exc}"}).encode())
            return
        env = set_handler(key=payload["key"], value=payload["value"])
        check(C.out, env, "out")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(env).encode())


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8801"))
    print(f"producer: {ROUTE} na :{port} (store={STORE})", flush=True)
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
