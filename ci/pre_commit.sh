#!/usr/bin/env bash
# Part of the ifURI solution — bramy lokalne PRZED commitem (i te same w CI).
set -euo pipefail
cd "$(dirname "$0")/.."
export URIRUN_CONTRACT_CHECK=1
echo "== 1/2 kontrakt konformuje (efekt, wzajemny inverse, przykłady) =="
python ci/nl_to_contract.py --validate contracts.json
echo "== 2/2 wygenerowany kod zgodny z kontraktem (anty-dryf) =="
python ci/regen_check.py
echo "OK: gotowe do commitu."
