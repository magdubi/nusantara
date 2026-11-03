# m.tribunnews.com performance check

**Status: blocked. No measurements yet.**

## What was tried (2026-11-03)

| Method | Result |
|---|---|
| Direct load from the cloud container (curl / headless Chromium) | `CONNECT tunnel failed, response 403` because the environment network policy denies `m.tribunnews.com` |
| Web-fetch tool | `getaddrinfo ENOTFOUND m.tribunnews.com` (host not allowed) |
| Google PageSpeed Insights API (no key) | HTTP 429, anonymous daily quota exhausted (`raw/psi-home-mobile.json`) |

No performance numbers are in this folder, because none could be measured.

## To unblock

Add `m.tribunnews.com`, `www.tribunnews.com`, `*.tribunnews.com` and `*.tstatic.net` under
**Network access → Allowed domains** in the cloud environment settings, or use a broader access level.
See https://code.claude.com/docs/en/cloud-environments#network-access.
Another option is to supply a PageSpeed Insights API key.

## Planned measurements (once reachable)

For the homepage and 3–4 of the latest articles, mobile emulation:

- TTFB, FCP, LCP, CLS, TBT and full load time
- Request count and transfer size, split by first party, ads, analytics and other third parties
- Slowest and largest resources
- Scripts that block rendering, unoptimized or non-lazy images, and ad slot count
- Recommendations
