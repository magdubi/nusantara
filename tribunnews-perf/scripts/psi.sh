#!/usr/bin/env bash
# Usage: PSI_KEY=... ./psi.sh <url> <strategy:mobile|desktop> <out.json>
set -euo pipefail
url="$1"; strategy="$2"; out="$3"
enc=$(python3 -c 'import sys,urllib.parse;print(urllib.parse.quote(sys.argv[1],safe=""))' "$url")
curl -sS -m 300 -o "$out" -w "%{http_code} ${strategy} ${url}\n" \
  "https://pagespeedonline.googleapis.com/pagespeedonline/v5/runPagespeed?url=${enc}&strategy=${strategy}&category=performance&category=best-practices&category=seo&key=${PSI_KEY}"
