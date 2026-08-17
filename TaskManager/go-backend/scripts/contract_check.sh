#!/bin/bash
# contract_check.sh — Smoke test all 24 API endpoints against Go backend.
# Usage: ./scripts/contract_check.sh [BASE_URL]

set -e

BASE_URL="${1:-http://localhost:8080}"
PASS=0
FAIL=0
TOTAL=0

check_endpoint() {
    local method="$1"
    local path="$2"
    local expected="$3"
    local body="$4"
    
    TOTAL=$((TOTAL + 1))
    
    if [ "$method" = "GET" ]; then
        status=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL$path")
    elif [ "$method" = "POST" ]; then
        if [ -n "$body" ]; then
            status=$(curl -s -o /dev/null -w "%{http_code}" -X POST -H "Content-Type: application/json" -d "$body" "$BASE_URL$path")
        else
            status=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL$path")
        fi
    elif [ "$method" = "PUT" ]; then
        if [ -n "$body" ]; then
            status=$(curl -s -o /dev/null -w "%{http_code}" -X PUT -H "Content-Type: application/json" -d "$body" "$BASE_URL$path")
        else
            status=$(curl -s -o /dev/null -w "%{http_code}" -X PUT "$BASE_URL$path")
        fi
    fi
    
    if [ "$status" = "$expected" ]; then
        echo "  ✅ $method $path → $status"
        PASS=$((PASS + 1))
    else
        echo "  ❌ $method $path → $status (expected $expected)"
        FAIL=$((FAIL + 1))
    fi
}

echo "=== CMDB Go Backend Contract Check ==="
echo "Base URL: $BASE_URL"
echo ""

echo "--- Health Check ---"
check_endpoint GET "/healthz" "200"

echo ""
echo "--- Dashboard (8 endpoints) ---"
check_endpoint GET "/api/v1/dashboard/stats/" "200"
check_endpoint GET "/api/v1/dashboard/workers/" "200"
check_endpoint GET "/api/v1/dashboard/resource-health/" "200"
check_endpoint GET "/api/v1/dashboard/task-trend/" "200"
check_endpoint GET "/api/v1/dashboard/health-ranking/" "200"
check_endpoint GET "/api/v1/dashboard/current/" "200"
check_endpoint GET "/api/v1/dashboard/recent-events/" "200"
check_endpoint GET "/api/v1/dashboard/resource-breakdown/" "200"
check_endpoint GET "/api/v1/dashboard/aws-resources/" "200"

echo ""
echo "--- Tasks (8 endpoints) ---"
check_endpoint GET "/api/v1/tasks/tree/" "200"
check_endpoint POST "/api/v1/tasks/execute/" "400" '{"account":"test"}'
check_endpoint PUT "/api/v1/tasks/schedule/" "400" '{}'
check_endpoint GET "/api/v1/tasks/locks/" "200"
check_endpoint POST "/api/v1/tasks/preview/" "200"
check_endpoint POST "/api/v1/tasks/test/run/" "400" '{}'
check_endpoint GET "/api/v1/tasks/test/status/test-1/" "200"
check_endpoint GET "/api/v1/tasks/test/file/" "200"

echo ""
echo "--- Config (3 endpoints) ---"
check_endpoint GET "/api/v1/config/regions/" "200"
check_endpoint PUT "/api/v1/config/regions/" "400" '{}'
check_endpoint GET "/api/v1/config/accounts/" "200"

echo ""
echo "--- History (3 endpoints) ---"
check_endpoint GET "/api/v1/history/" "200"
# Find the first record ID dynamically
FIRST_ID=$(curl -s "$BASE_URL/api/v1/history/" | python3 -c "import sys,json; d=json.load(sys.stdin); recs=d.get('records',[]); print(recs[0]['id'].lstrip('#') if recs else '1')" 2>/dev/null || echo "1")
check_endpoint GET "/api/v1/history/${FIRST_ID}/" "200"
# Retry: 200 (success) or 409 (lock conflict) are both valid
RETRY_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/v1/history/${FIRST_ID}/retry/")
if [ "$RETRY_STATUS" = "200" ] || [ "$RETRY_STATUS" = "409" ]; then
    echo "  ✅ POST /api/v1/history/${FIRST_ID}/retry/ → $RETRY_STATUS (dispatched or conflict)"
    PASS=$((PASS + 1))
else
    echo "  ❌ POST /api/v1/history/${FIRST_ID}/retry/ → $RETRY_STATUS (expected 200 or 409)"
    FAIL=$((FAIL + 1))
fi
TOTAL=$((TOTAL + 1))

echo ""
echo "--- Docs (2 endpoints) ---"
check_endpoint GET "/api/v1/docs/" "200"
check_endpoint GET "/api/v1/docs/architecture-design.html" "200"

echo ""
echo "=== Results ==="
echo "  Passed: $PASS / $TOTAL"
echo "  Failed: $FAIL / $TOTAL"

if [ $FAIL -gt 0 ]; then
    echo ""
    echo "❌ Some checks failed!"
    exit 1
else
    echo ""
    echo "✅ All checks passed!"
    exit 0
fi
