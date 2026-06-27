# toolkit/contract_gate.py — re-eksport z urirun_contract.gate (jedyne źródło definicji).
# Nie edytuj. Zainstaluj: pip install urirun-contract
#   lub: pip install git+https://github.com/if-uri/urirun-contract.git
from urirun_contract.gate import *  # noqa: F401,F403
from urirun_contract.gate import (  # noqa: F401 — explicit dla IDE / type-checkerów
    ContractViolation, Contract, Wire,
    enforce, check, validate_output, conform,
    check_wire, wire_payload, consumer_input_check, find_wire,
    attach_contracts, contract_to_dict, envelope_violation,
    dig, assignable, resolve_out_type,
)

