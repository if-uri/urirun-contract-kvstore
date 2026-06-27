# Part of the ifURI solution — ładowanie neutralnego contracts.json dla serwisów.
"""Wczytuje wspólny contracts.json do lekkich obiektów z .inp/.out/... które czytają
funkcje kernela (check, wire_payload, consumer_input_check). Ta sama brama, jedno źródło
kontraktu — oba procesy ładują TEN SAM plik niezależnie."""
import json, os
from types import SimpleNamespace

def load(path=None):
    path = path or os.environ.get("CONTRACTS", "contracts.json")
    doc = json.load(open(path))
    contracts = {r: SimpleNamespace(**{**c, "inverse_route": c.get("inverseRoute") or ""})
                 for r, c in doc["contracts"].items()}
    wires = [SimpleNamespace(**w) for w in doc.get("wires", [])]
    return contracts, wires
