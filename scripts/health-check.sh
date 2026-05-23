#!/usr/bin/env bash
set -euo pipefail
BASE_URL="${1:-http://localhost:18080}"; PASS=0; FAIL=0
check() { local n="$1" u="$2" e="${3:-200}"; s=$(curl -s -o /dev/null -w "%{http_code}" "$u" 2>/dev/null||echo "000"); [ "$s" = "$e" ] && echo "  ✅ $n — $s" && PASS=$((PASS+1)) || echo "  ❌ $n — expected $e, got $s" && FAIL=$((FAIL+1)); }
echo "🔍 GEOEngine Health Check"; echo ""
check "Front Page" "$BASE_URL/"
check "Admin Login" "$BASE_URL/geo_admin/login"
echo ""; echo "📊 Results: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
