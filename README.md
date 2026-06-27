# urirun-contract-kvstore

**Format `urirun-contract-*`: README opisuje intencję, lokalny LLM proponuje kontrakt,
generator deterministycznie robi kod, bramy egzekwują — CI tylko weryfikuje.**

## Co ten projekt robi (źródło intencji dla LLM)

**Handoff skalarny command → query** między dwoma procesami:

- `kv/command/set` — **command**. Zapisuje `key → value` do współdzielonego store'u. Zwraca
  `{action: kv-set, key, stored: true}`.
- `kv/query/get` — **query**. Czyta `key`, zwraca `{action: kv-get, key, value?, found}`
  (`value` opcjonalne — obecne tylko gdy `found`).

Krawędź `WIRES` mapuje `key ← key`: klucz zapisany przez `set` zasila odczyt `get` (pełny handoff —
`key` to całe wejście `get`). Klucz przepływa **kontraktem po sieci**; wartość przepływa **przez
współdzielony store** — dwa niezależne procesy spięte jednym `contracts.json`.

Błędy: `store-unavailable`.

## Pipeline

```bash
make gen        # contracts.json → src/handlers_generated.py
make check      # conform (efekt↔czasownik query/command, przykłady) + anty-dryf — bez LLM
```

## Wariant wielopakietowy (dwa procesy, transport + współdzielony store)

```bash
KV_STORE=/tmp/kv.json PORT=8801 python packages/producer/service.py &   # kv/command/set
KV_STORE=/tmp/kv.json PORT=8802 python packages/consumer/service.py &    # kv/query/get
python orchestrator/drive.py                                             # set ─HTTP→ get, full handoff
```

Orchestrator potwierdza, że `value` zapisana przez proces producenta wraca z procesu konsumenta
(`found=true`, `value="hello world"`) — stan przeszedł granicę procesu. Konsument odrzuca brak
wymaganego `key` (→ 422).

## Licencja

Apache-2.0 · Tom Sapletta · https://tom.sapletta.com
