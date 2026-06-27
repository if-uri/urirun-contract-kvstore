// Author: Tom Sapletta · https://tom.sapletta.com
// Part of the ifURI solution.
//
// Konsument w Go dla kv/query/get. Czyta TEN SAM contracts.json co producent Python ORAZ ten sam
// współdzielony store (KV_STORE). KLUCZ przepływa kontraktem po sieci, WARTOŚĆ przez store —
// dokładnie jak w wariancie Python. Różni się TYLKO językiem; orchestrator widzi tylko JSON.
package main

import (
	"encoding/json"
	"fmt"
	"math"
	"net/http"
	"os"
	"path/filepath"
	"strings"
)

const ROUTE = "kv/query/get"

var (
	contractsDoc map[string]interface{}
	routeInp     map[string]interface{}
	routeOut     map[string]interface{}
)

func loadContracts() {
	path := os.Getenv("CONTRACTS")
	if path == "" {
		exe, _ := os.Executable()
		for _, c := range []string{filepath.Join(filepath.Dir(exe), "contracts.json"), "contracts.json"} {
			if _, err := os.Stat(c); err == nil {
				path = c
				break
			}
		}
	}
	raw, err := os.ReadFile(path)
	if err != nil {
		fmt.Fprintln(os.Stderr, "brak contracts.json:", err)
		os.Exit(2)
	}
	if err := json.Unmarshal(raw, &contractsDoc); err != nil {
		fmt.Fprintln(os.Stderr, "zły JSON:", err)
		os.Exit(2)
	}
	r := contractsDoc["contracts"].(map[string]interface{})[ROUTE].(map[string]interface{})
	routeInp = r["inp"].(map[string]interface{})
	routeOut = r["out"].(map[string]interface{})
}

// ── walidator mini-języka schematu (generyczny) ─────────────────────────────
func typeOK(tok string, v interface{}) bool {
	switch tok {
	case "str":
		_, ok := v.(string)
		return ok
	case "int":
		f, ok := v.(float64)
		return ok && f == math.Trunc(f)
	case "num":
		_, ok := v.(float64)
		return ok
	case "bool":
		_, ok := v.(bool)
		return ok
	case "obj":
		_, ok := v.(map[string]interface{})
		return ok
	case "list":
		_, ok := v.([]interface{})
		return ok
	case "any":
		return true
	}
	return false
}

func checkSchema(schema, value interface{}, where string) error {
	if m, ok := schema.(map[string]interface{}); ok {
		if alts, has := m["oneOf"]; has {
			var errs []string
			for i, alt := range alts.([]interface{}) {
				if e := checkSchema(alt, value, fmt.Sprintf("%s|oneOf[%d]", where, i)); e == nil {
					return nil
				} else {
					errs = append(errs, e.Error())
				}
			}
			return fmt.Errorf("%s: nie pasuje do żadnego wariantu oneOf: %v", where, errs)
		}
		vm, ok := value.(map[string]interface{})
		if !ok {
			return fmt.Errorf("%s: oczekiwano obiektu", where)
		}
		for key, sub := range m {
			subStr, isStr := sub.(string)
			optional := isStr && strings.HasPrefix(subStr, "?")
			if optional {
				if _, present := vm[key]; !present {
					continue
				}
				sub = subStr[1:]
			}
			val, present := vm[key]
			if !present {
				return fmt.Errorf("%s.%s: brak wymaganego klucza", where, key)
			}
			if e := checkSchema(sub, val, fmt.Sprintf("%s.%s", where, key)); e != nil {
				return e
			}
		}
		return nil
	}
	if tok, ok := schema.(string); ok {
		if strings.HasPrefix(tok, "?") {
			if value == nil {
				return nil
			}
			tok = tok[1:]
		}
		if strings.HasPrefix(tok, "const:") {
			lit := tok[6:]
			var expected interface{} = lit
			if lit == "true" {
				expected = true
			} else if lit == "false" {
				expected = false
			}
			if value != expected {
				return fmt.Errorf("%s: oczekiwano const:%s, jest %v", where, lit, value)
			}
			return nil
		}
		if strings.HasPrefix(tok, "enum:") {
			vals := strings.Split(tok[5:], "|")
			vs, ok := value.(string)
			if !ok {
				return fmt.Errorf("%s: oczekiwano str dla enum", where)
			}
			for _, a := range vals {
				if a == vs {
					return nil
				}
			}
			return fmt.Errorf("%s: %q nie w enum %v", where, vs, vals)
		}
		if !typeOK(tok, value) {
			return fmt.Errorf("%s: %v nie spełnia %s", where, value, tok)
		}
		return nil
	}
	if arr, ok := schema.([]interface{}); ok && len(arr) > 0 {
		va, ok := value.([]interface{})
		if !ok {
			return fmt.Errorf("%s: oczekiwano listy", where)
		}
		for i, item := range va {
			if e := checkSchema(arr[0], item, fmt.Sprintf("%s[%d]", where, i)); e != nil {
				return e
			}
		}
		return nil
	}
	return nil
}

// ── ciało handlera (czyta współdzielony store) ──────────────────────────────
func getHandler(key string) map[string]interface{} {
	store := os.Getenv("KV_STORE")
	if store == "" {
		store = "/tmp/kvstore.json"
	}
	db := map[string]interface{}{}
	if raw, err := os.ReadFile(store); err == nil {
		json.Unmarshal(raw, &db)
	}
	v, found := db[key]
	env := map[string]interface{}{
		"ok": true, "connector": "kvstore-go", "action": "kv-get", "key": key, "found": found,
	}
	if found {
		env["value"] = v
	}
	return env
}

func writeJSON(w http.ResponseWriter, code int, body map[string]interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(code)
	json.NewEncoder(w).Encode(body)
}

func handleRun(w http.ResponseWriter, r *http.Request) {
	var payload map[string]interface{}
	if r.Method == http.MethodPost {
		if err := json.NewDecoder(r.Body).Decode(&payload); err != nil || payload == nil {
			payload = map[string]interface{}{}
		}
	}
	if err := checkSchema(routeInp, payload, "inp"); err != nil {
		writeJSON(w, 422, map[string]interface{}{"ok": false, "error": fmt.Sprintf("input violates %s: %v", ROUTE, err)})
		return
	}
	key, _ := payload["key"].(string)
	env := getHandler(key)
	if err := checkSchema(routeOut, env, "out"); err != nil {
		writeJSON(w, 500, map[string]interface{}{"ok": false, "error": fmt.Sprintf("output violates %s: %v", ROUTE, err)})
		return
	}
	writeJSON(w, 200, env)
}

func main() {
	loadContracts()
	port := os.Getenv("PORT")
	if port == "" {
		port = "8803"
	}
	mux := http.NewServeMux()
	mux.HandleFunc("/run", handleRun)
	mux.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, 200, map[string]interface{}{"ok": true})
	})
	fmt.Printf("consumer-go: %s na :%s\n", ROUTE, port)
	if err := http.ListenAndServe(":"+port, mux); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
