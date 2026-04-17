#!/usr/bin/env bash
# Post-deploy smoke tests. Run after `fly deploy` / `vercel --prod`.
#
# Usage:
#   API_URL=https://agents.corridor.app \
#   UI_URL=https://corridor-ui.vercel.app \
#   API_KEY=<BACKEND_API_KEY> \
#   bash scripts/smoke_test.sh

set -euo pipefail

API_URL="${API_URL:-http://127.0.0.1:8000}"
UI_URL="${UI_URL:-http://127.0.0.1:3000}"
API_KEY="${API_KEY:-}"

pass=0
fail=0

check() {
    local name="$1"
    local expected="$2"
    local cmd="$3"
    local got
    got=$(eval "$cmd" 2>/dev/null || echo "err")
    if [[ "$got" == "$expected" ]]; then
        echo "  PASS: $name ($got)"
        pass=$((pass + 1))
    else
        echo "  FAIL: $name — expected $expected, got $got"
        fail=$((fail + 1))
    fi
}

echo "─── Backend liveness ─────────────────────────────────────────"
check "healthz/live 200" "200" \
    "curl -s -o /dev/null -w '%{http_code}' ${API_URL}/api/healthz/live"

check "healthz/ready 200" "200" \
    "curl -s -o /dev/null -w '%{http_code}' ${API_URL}/api/healthz/ready"

check "root / 200" "200" \
    "curl -s -o /dev/null -w '%{http_code}' ${API_URL}/"

echo ""
echo "─── Auth gating ──────────────────────────────────────────────"
check "no-key /api/corridor/info 401" "401" \
    "curl -s -o /dev/null -w '%{http_code}' ${API_URL}/api/corridor/info"

check "bad-key /api/corridor/info 401" "401" \
    "curl -s -o /dev/null -w '%{http_code}' -H 'X-API-Key: wrong' ${API_URL}/api/corridor/info"

if [[ -n "$API_KEY" ]]; then
    check "good-key /api/corridor/info 200" "200" \
        "curl -s -o /dev/null -w '%{http_code}' -H 'X-API-Key: ${API_KEY}' ${API_URL}/api/corridor/info"
else
    echo "  SKIP: good-key check — set API_KEY env to test authenticated endpoints"
fi

echo ""
echo "─── UI liveness ──────────────────────────────────────────────"
check "UI / 200" "200" \
    "curl -s -o /dev/null -w '%{http_code}' -L ${UI_URL}/"

check "UI /agent 200" "200" \
    "curl -s -o /dev/null -w '%{http_code}' -L ${UI_URL}/agent"

check "UI /overview 200" "200" \
    "curl -s -o /dev/null -w '%{http_code}' -L ${UI_URL}/overview"

echo ""
echo "─── Security headers ─────────────────────────────────────────"
check "UI has CSP" "present" \
    "curl -sI -L ${UI_URL}/ | grep -qi 'content-security-policy' && echo present || echo missing"

check "UI has X-Frame-Options" "present" \
    "curl -sI -L ${UI_URL}/ | grep -qi 'x-frame-options' && echo present || echo missing"

echo ""
echo "─── Summary ──────────────────────────────────────────────────"
echo "  $pass passed, $fail failed"
exit $fail
