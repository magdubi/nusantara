#!/usr/bin/env python3
"""Summarize PageSpeed Insights JSON files into markdown. Usage: summarize.py raw/*.json[.gz] > summary.md"""
import gzip, json, sys

def ms(v): return f"{v/1000:.1f} s" if v >= 1000 else f"{v:.0f} ms"
def kb(b): return f"{b/1024:,.0f} KB"

for path in sys.argv[1:]:
    d = json.load(gzip.open(path) if path.endswith(".gz") else open(path)); l = d["lighthouseResult"]; a = l["audits"]
    print(f"\n## {path}\n\n- URL: {l['finalDisplayedUrl']}\n- Form factor: {l['configSettings']['formFactor']}  | fetched {l['fetchTime']}")
    print("- Scores: " + ", ".join(f"{k} {int(v['score']*100)}" for k, v in l["categories"].items() if v["score"] is not None))
    print("\n**Lab metrics**\n")
    for k in ["first-contentful-paint","largest-contentful-paint","total-blocking-time","cumulative-layout-shift","speed-index","interactive","server-response-time"]:
        if k in a: print(f"- {a[k]['title']}: {a[k].get('displayValue','')} (score {a[k]['score']})")
    for name, le in (("URL", d.get("loadingExperience")), ("Origin", d.get("originLoadingExperience"))):
        if le and le.get("metrics"):
            print(f"\n**Field data (CrUX, {name}, p75)** overall: {le.get('overall_category')}\n")
            for m, v in le["metrics"].items(): print(f"- {m}: {v['percentile']} ({v['category']})")
    rs = a["resource-summary"]["details"]["items"]
    print("\n**Resources**\n\n| type | requests | transfer |\n|---|---|---|")
    for r in rs: print(f"| {r['label']} | {r['requestCount']} | {kb(r['transferSize'])} |")
    if "mainthread-work-breakdown" in a:
        print(f"\n- Main-thread work: {a['mainthread-work-breakdown'].get('displayValue')}; JS execution: {a['bootup-time'].get('displayValue')}")
    if "dom-size" in a: print(f"- DOM size: {a['dom-size'].get('displayValue')}")
    for it in a.get("lcp-breakdown-insight", {}).get("details", {}).get("items", []):
        if it.get("type") == "node": print(f"- LCP element: `{it.get('snippet','')[:200]}`")
        for row in it.get("items", []) if it.get("type") == "table" else []:
            print(f"  - {row['label']}: {ms(row['duration'])}")
    reqs = a.get("network-requests", {}).get("details", {}).get("items", [])
    if reqs:
        from urllib.parse import urlparse
        hosts = {urlparse(r["url"]).hostname for r in reqs}
        ends = [r.get("networkEndTime", 0) for r in reqs]
        print(f"- Network: {len(reqs)} requests to {len(hosts)} distinct hosts; last request finished at {ms(max(ends))}")
        print("\n**Largest requests**\n\n| transfer | type | url |\n|---|---|---|")
        for r in sorted(reqs, key=lambda r: -r.get("transferSize", 0))[:10]:
            print(f"| {kb(r.get('transferSize',0))} | {r.get('resourceType')} | {r['url'][:110]} |")
    tp = a.get("third-parties-insight", {}).get("details", {}).get("items", [])
    if tp:
        print("\n**Third parties (by main-thread time)**\n\n| entity | transfer | main-thread |\n|---|---|---|")
        for t in sorted(tp, key=lambda x: -x.get("mainThreadTime", 0))[:12]:
            e = t["entity"]["text"] if isinstance(t["entity"], dict) else t["entity"]
            print(f"| {e} | {kb(t.get('transferSize',0))} | {ms(t.get('mainThreadTime',0))} |")
    lt = a.get("long-tasks", {}).get("details", {}).get("items", [])
    if lt:
        print(f"\n**Long tasks**: {len(lt)} total, {ms(sum(x['duration'] for x in lt))} combined. Top:\n")
        for x in lt[:6]: print(f"- {ms(x['duration'])} at {ms(x['startTime'])}: {x['url'][:110]}")
    rb = a.get("render-blocking-resources", {}).get("details", {}).get("items", []) or a.get("render-blocking-insight", {}).get("details", {}).get("items", [])
    if rb:
        print("\n**Render-blocking resources**\n")
        for r in rb[:10]: print(f"- {r.get('url')} ({kb(r.get('totalBytes',0))}, {ms(r.get('wastedMs',0))})")
    opps = [(k, v) for k, v in a.items() if v.get("details", {}).get("type") == "opportunity" and v.get("score") is not None and v["score"] < 0.9]
    if opps:
        print("\n**Opportunities**\n")
        for k, v in sorted(opps, key=lambda x: -x[1]["details"].get("overallSavingsMs", 0)):
            print(f"- {v['title']}: {v.get('displayValue','')}")
    print("\n**Failing diagnostics**\n")
    for k, v in a.items():
        if v.get("scoreDisplayMode") in ("metricSavings","numeric","binary") and v.get("score") is not None and v["score"] < 0.5 and v.get("details",{}).get("type") != "opportunity" and "insight" in k:
            print(f"- {v['title']}: {v.get('displayValue','')}")
