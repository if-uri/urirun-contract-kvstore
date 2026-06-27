#!/usr/bin/env python3
# Part of the ifURI solution — pakiet KONSUMENTA (proces 2).
"""Serwis HTTP udostępniający ``kv/query/get``. Czyta key ze współdzielonego store'u (KV_STORE),
WALIDUJE wejście wobec inp-schematu wspólnego kontraktu, zwraca value/found walidowane wobec out.
Inny proces niż producent — łączy ich klucz przekazany kontraktem + ten sam plik store'u.

  POST /run  {key}  →  koperta kv/query/get
  GET  /health      →  {"ok": true}
"""
from __future__ import annotations

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "toolkit"))
from contract_gate import check  # noqa: E402
from contracts_io import load  # noqa: E402

ROUTE = "kv/query/get"
STORE = os.environ.get("KV_STORE", "/tmp/kvstore.json")
CONTRACTS, _ = load()
C = CONTRACTS[ROUTE]


def get_handler(key: str) -> dict:
    db = json.load(open(STORE)) if os.path.exists(STORE) else {}
    found = key in db
    env = {"ok": True, "connector": "kvstore", "action": "kv-get", "key": key, "found": found}
    if found:
        env["value"] = db[key]
    return env


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _err(self, code, msg):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"ok": False, "error": msg}).encode())

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
            return self._err(422, f"input violates {ROUTE}: {exc}")
        env = get_handler(key=payload["key"])
        try:
            check(C.out, env, "out")
        except AssertionError as exc:
            return self._err(500, f"output violates {ROUTE}: {exc}")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(env).encode())


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8802"))
    print(f"consumer: {ROUTE} na :{port} (store={STORE})", flush=True)
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
