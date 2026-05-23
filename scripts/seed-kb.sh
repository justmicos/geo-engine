#!/usr/bin/env bash
set -euo pipefail
BASE_URL="${1:-http://localhost:18080}"
API_TOKEN=$(curl -s -X POST "$BASE_URL/api/v1/auth/login" -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"password"}' \
    | python3 -c "import sys,json;print(json.load(sys.stdin).get('data',{}).get('token',''))")
[ -z "$API_TOKEN" ] && echo "❌ Auth failed" && exit 1
CONTENT=$(cat seed/knowledge-base.md | python3 -c "import sys,json;print(json.dumps(sys.stdin.read()))")
curl -s -X POST "$BASE_URL/api/v1/materials/knowledge-bases" \
    -H "Authorization: Bearer $API_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"name\":\"GEOEngine Knowledge\",\"description\":\"Example knowledge base\",\"content\":$CONTENT}" > /dev/null
echo "✅ Knowledge base seeded"
