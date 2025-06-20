#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

# CONFIG – set these environment variables before running
#   export CALENDLY_API_KEY="pat_..."
#   export WEBHOOK_URL="https://your-domain.com/api/webhook/booking"
PAT="${CALENDLY_API_KEY:-}"
CALLBACK_RAW="${WEBHOOK_URL:-}"
EVENTS='["invitee.created"]'
FORCED_KEY="rusteze-auto-spa-demo-key"   # use any 24+ char random string

[[ -z "$PAT"  ]] && { echo >&2 "❌ CALENDLY_API_KEY not set"; exit 1; }
[[ -z "$CALLBACK_RAW" || "$CALLBACK_RAW" != https://* ]] && {
  echo >&2 "❌ WEBHOOK_URL must be public HTTPS"; exit 1; }

CALLBACK="${CALLBACK_RAW%/}"   # strip trailing /

# Helper: JSON path extractor
json() { python3 - <<'PY' "$1" "$2"
import json,sys,functools,operator
try:
    print(functools.reduce(operator.getitem,
                            sys.argv[2].split('.'),
                            json.loads(sys.argv[1])))
except Exception:
    pass
PY
}

# 1. Get user + organization URIs
ME=$(curl -s -H "Authorization: Bearer $PAT" https://api.calendly.com/users/me)
USER=$(json "$ME" resource.uri)
ORG=$(json  "$ME" resource.current_organization)

[[ -z "$USER" || -z "$ORG" ]] && { echo "$ME"; exit 1; }
echo "✅ user → $USER"
echo "✅ org  → $ORG"

# 2. List existing webhook subs (include signing_key)
LIST() { curl -s -G "https://api.calendly.com/webhook_subscriptions" \
             --data-urlencode "include=signing_key" \
             --data-urlencode "scope=user" \
             --data-urlencode "user=$USER" \
             -H "Authorization: Bearer $PAT"; }

SUBS=$(LIST)

# Locate any sub that targets our callback URL
SUB_UUID=$(python3 - <<'PY' "$SUBS" "$CALLBACK"
import json,sys; url=sys.argv[2].rstrip('/')
for s in json.loads(sys.argv[1]).get('collection',[]):
    if s.get('callback_url','').rstrip('/')==url:
        print(s['uri'].rpartition('/')[-1]); break
PY
)

SIGN_KEY=$(python3 - <<'PY' "$SUBS" "$CALLBACK"
import json,sys; url=sys.argv[2].rstrip('/')
for s in json.loads(sys.argv[1]).get('collection',[]):
    if s.get('callback_url','').rstrip('/')==url:
        print(s.get('signing_key','')); break
PY
)

# 3. Handle legacy subs (no key) or create new one
if [[ -n "$SUB_UUID" && -n "$SIGN_KEY" ]]; then
    echo "✅ existing sub & key found"
    KEY="$SIGN_KEY"

elif [[ -n "$SUB_UUID" ]]; then
    echo "🗑  legacy sub (no key) → deleting"
    curl -s -X DELETE "https://api.calendly.com/webhook_subscriptions/$SUB_UUID" \
         -H "Authorization: Bearer $PAT" >/dev/null
    SUB_UUID=""
fi

if [[ -z "${SUB_UUID:-}" ]]; then
    echo "➡  creating new sub"
    CREATE=$(curl -s -X POST \
      "https://api.calendly.com/webhook_subscriptions?include=signing_key" \
      -H "Authorization: Bearer $PAT" -H "Content-Type: application/json" \
      -d "{\"url\":\"$CALLBACK\",\"events\":$EVENTS,\
           \"scope\":\"user\",\"user\":\"$USER\",\"organization\":\"$ORG\",\
           \"signing_key\":\"$FORCED_KEY\"}")

    SUB_UUID=$(json "$CREATE" resource.uri | awk -F/ '{print $NF}')
    KEY=$(json  "$CREATE" resource.signing_key)
    [[ -z "$KEY" ]] && KEY="$FORCED_KEY"   # Std plan: API won’t return key
    echo "✅ new sub $SUB_UUID created"
fi

# 4. Verify we have a key
[[ -z "${KEY:-}" ]] && { echo >&2 "❌ failed to obtain signing_key"; exit 1; }
echo "🔑 signing_key → ${KEY:0:6}…"

# 5. Craft sample payload & signature
cat > payload.json <<'EOF'
{"event":"invitee.created","payload":{"invitee":{"event_type":{"slug":"test-shop"},"email":"frajcastillo@gmail.com","event":{"start_time":"2025-06-18T15:00:00Z"}}}}
EOF

TS=$(date +%s)
SIG=$(printf '%s' "$TS.$(<payload.json)" \
      | openssl dgst -sha256 -hmac "$KEY" -binary | xxd -p -c256)

# 6. POST to local FastAPI endpoint
curl -i -X POST "http://localhost:8000/api/webhook/booking" \
     -H "Content-Type: application/json" \
     -H "X-Calendly-Signature: t=$TS,v1=$SIG" \
     -d @payload.json
echo -e "\n🎉 Done."
