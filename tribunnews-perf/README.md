# Why is m.tribunnews.com slow?

Audit date: **2026-11-03**. Tool: Google PageSpeed Insights API (Lighthouse 13.6.0) with Chrome UX Report field data.
Pages tested: the homepage plus 5 of the latest articles from that day.

## TL;DR

The server is **not** the main problem. The HTML arrives quickly, and the first text paints in about 1.9 s on mobile.
The page is slow because of the **advertising and tracking JavaScript loaded on top of it**:

- An article page on mobile makes **450–1,070 requests** to **135–243 different hosts**. It downloads **4.6–6.5 MB**, of which **3.1–4.9 MB is JavaScript**.
- **About 90–96 % of requests and bytes are third-party** (ads, header bidding, identity sync, analytics, widgets).
- The phone's main thread is busy for **8–21 s**. Total Blocking Time is **0.9–3.0 s**, and the page becomes interactive only after **33–48 s** (Lighthouse TTI).
- **Speed Index is 11–16 s**. The page keeps repainting for many seconds as ad slots, recommendation widgets and iframes fill in.
- Real users (CrUX, p75, mobile) rate the **whole origin as "SLOW"**: LCP is **4.7 s** (the "good" limit is 2.5 s) and TTFB is 1.7 s.

## 1. Scores and lab metrics (mobile, simulated slow 4G)

| Page | Perf | FCP | LCP | TBT | CLS | Speed Index | TTI | Requests | Transfer | JS | Hosts | Main-thread |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Homepage | 59 | 1.9 s | 4.6 s | 594 ms | 0.018 | 9.4 s | 23.9 s | 350 | 3.4 MB | 2.1 MB | 106 | 4.4 s |
| [Art 1](https://m.tribunnews.com/nasional/7906318/menko-yusril-tertawa-ditanya-kemungkinan-wapres-ikut-disadap-listyo-cs-wallahu-alam-bishawab) – nasional | 50 | 1.9 s | 3.8 s | 2,070 ms | 0.018 | 16.4 s | 44.2 s | 513 | 6.5 MB | 4.9 MB | 142 | 16.1 s |
| [Art 2](https://m.tribunnews.com/nasional/7906282/breaking-news-polri-tetapkan-jenderal-listyo-sigit-sebagai-tersangka-penyadapan-ilegal) – breaking news | 62 | 1.9 s | 2.9 s | 1,059 ms | 0.018 | 12.3 s | 33.5 s | 447 | 4.6 MB | 3.1 MB | 139 | 9.2 s |
| [Art 3](https://m.tribunnews.com/haji/7906330/kemenhaj-ingatkan-jemaah-haji-bisa-gagal-berangkat-karena-dokumen-meski-sudah-lunas) – haji | 64 | 1.9 s | 2.9 s | 867 ms | 0.018 | 14.0 s | 36.6 s | 537 | 5.7 MB | 4.3 MB | 138 | 8.2 s |
| [Art 4](https://m.tribunnews.com/internasional/7906300/sak-nah-t-rk-ye-2026-bahas-peran-keuangan-islam-dalam-menghadapi-krisis-global) – internasional | 51 | 1.9 s | 4.0 s | 1,514 ms | 0.018 | 11.6 s | 39.9 s | 491 | 5.8 MB | 4.0 MB | 135 | 11.4 s |
| [Art 5](https://m.tribunnews.com/nasional/7906299/listyo-sigit-tersangka-penyadapan-prabowo-file-penyadapan-dan-jejak-log-diduga-dihapus) – nasional | 54 | 2.0 s | 2.9 s | **2,955 ms** | 0.018 | 15.6 s | **48.0 s** | **1,067** | 6.0 MB | 4.3 MB | **243** | **21.0 s** |

On desktop the homepage scores 57 (TBT 885 ms, TTI 5.7 s) and Article 5 scores 62 (TBT 1,107 ms, 534 requests, 4.9 MB).
Even on a fast desktop CPU, ad scripts block the main thread for about 1 s.

**Best-practices scores are 23–46.** Every page logs about 28 console errors and sets 9–14 third-party cookies.

## 2. Real-user field data (CrUX, mobile, 75th percentile)

| Metric | Homepage URL | Whole origin | Rating |
|---|---|---|---|
| LCP | 4,528 ms | 4,686 ms | **SLOW** (good ≤ 2,500) |
| FCP | 2,564 ms | 2,877 ms | average |
| TTFB | 1,723 ms | 1,747 ms | average (good ≤ 800) |
| INP | 214 ms | 291 ms | average (good ≤ 200) |
| CLS | 0.04 | 0.05 | fast |

New articles don't have their own CrUX data yet, so the origin values apply to them.
Real users on Indonesian mobile networks see about **1.7 s TTFB**, which is much worse than the lab's fast server response.
That points to network distance, TLS, redirects, or cache misses at the CDN edge for real visitors.

## 3. Root causes (most to least impact)

### 3.1 Ad tech and header bidding (biggest cost)
Main-thread time per third party on Article 5 (mobile):

| Third party | Transfer | Main-thread |
|---|---|---|
| Google / DoubleClick Ads (GPT, ActiveView) | 1,161 KB | 1,370 ms |
| MGID (native "recommended" widgets, 3 separate scripts) | 1,079 KB | 1,020 ms |
| Google Tag Manager / gtag | 676 KB | 665 ms |
| ID5 Identity Cloud (`id5-api.js`) | 150 KB | 562 ms |
| Integral Ad Science | 111 KB | 448 ms |
| AdPushup | 385 KB | 444 ms |
| Rubicon Project | 85 KB | 243 ms |
| Facebook Pixel | 306 KB | 182 ms |

- **Prebid.js 11.32** (`asset-3.tribunnews.com/ads/prebid/prebid11.32.0.js`, 119 KB) runs a header-bidding auction with many SSPs: Rubicon, Index (casalemedia), PubMatic, OpenX, Criteo, SmileWanted, krushmedia, iqzonertb and others.
  On Article 5, **krushmedia.com alone made 71 requests and rubiconproject.com 68**. Article 5 also loaded **83 documents (iframes)**.
- Each bidder adds its own user-sync pixels and iframes. This is where most of the 135–243 hosts come from.
- **MGID** loads 2–3 widget scripts per article. Each one costs about 0.8–1.2 s of CPU on mobile.
- The run-to-run differences (450 vs 1,067 requests) come from **which ads win the auction**. The page weight is effectively controlled by the ad market, not by the site.

### 3.2 Duplicate analytics
GTM (`GTM-NNJ5M3B`) **and three separate GA4 gtag.js loads** (`G-DFP7BBGFWN`, `G-DJTF50RRZ2`, `G-FYJCTGV1LV`) are on every page.
That's about 150–180 KB each and roughly **680 KB in total**. Each one produces a long task of 150–220 ms.
One GTM container could send to several GA4 properties.

### 3.3 Render-blocking resources in `<head>` (about 1.2 s on mobile)
- `asset-1.tribunnews.com/js/jquery/jquery-3.6.3.min.js` blocks rendering for **about 1.2 s**.
- `mtnews_250806.min.css`, `icons-v1.0.3.min.css` and the Google Fonts Karla CSS block for about 750 ms each (in parallel).

### 3.4 Unused / uncached / unoptimized bytes
- **Unused JavaScript:** 0.8 MB on the homepage and **1.2–2.2 MB per article**.
- **Short cache lifetimes:** 0.6 MB on the homepage and **1.3–2.1 MB per article**, so repeat visits download them again.
- **Image delivery:** 450–880 KB could be saved per article (sizes and compression).
  One display-ad creative from `tpc.googlesyndication.com` was **319 KB** by itself.
- **Legacy JavaScript polyfills:** about 26 KB.

### 3.5 LCP element
On mobile, Lighthouse reports the **LCP element is the 144×35 site logo** (`#logotribun`), not the article's hero image.
This suggests the hero image isn't shown in the first mobile viewport, perhaps because it's pushed down by the header or ad slots or loads late.
On desktop, the LCP element of Article 5 is the `<h1>` headline.
Lab LCP (2.9–4.6 s) is therefore driven by CPU contention and render-blocking resources, not by image download.

### 3.6 Script errors
GPT logs `Exception in slotRenderEnded event listener: "ReferenceError: da is not defined"` repeatedly on every page tested.
The site's own ad-slot callback has a bug. Fixing it is cheap, and it removes wasted error handling during ad rendering.

## 4. Recommendations (by expected gain)

1. **Cut the header-bidding fan-out.** Reduce the number of Prebid bidders, set `bidderTimeout` to ≤ 1 s and use `userSync` limits such as `syncDelay` and `syncsPerBidder`.
   Lazy-load below-the-fold ad slots with GPT `enableLazyLoad` (fetchMarginPercent of about 100–200).
   This is the single largest cut in requests, iframes and CPU.
2. **Delay non-essential third parties until after load or first interaction.** This covers MGID widgets (load when scrolled near), ID5, IAS, AdPushup, the Facebook Pixel and Google Sign-In (`accounts.google.com/gsi/client`, 101 KB).
3. **Consolidate analytics** into one GTM container. Remove the three standalone gtag.js loads, which saves about 500 KB and roughly 450 ms of long tasks.
4. **Unblock rendering.** Use `defer` on jQuery, or remove it from the critical path. Inline critical CSS and preload the rest. Self-host the Karla font with `font-display: swap`.
5. **Give the article's hero image priority.** Use `fetchpriority="high"`, no lazy-loading, and explicit `width`/`height`. Make sure it is in the first mobile viewport so it becomes the LCP element and loads early.
6. **Set long `Cache-Control` lifetimes** (≥ 1 year with versioned file names) on `asset-*.tribunnews.com` static files. Ask ad vendors for cacheable script URLs.
7. **Look into the 1.7 s field TTFB.** Check CDN edge cache-hit ratio for HTML, POP coverage in Indonesia, redirect chains and HTTP/3.
8. **Fix the `da is not defined` bug** in the `slotRenderEnded` listener.
9. **Set a third-party budget**, for example ≤ 150 requests, ≤ 1.5 MB of JS and ≤ 500 ms TBT on a mid-range phone. Enforce it in CI with Lighthouse CI or PSI.

## 5. Caveats
- Each URL was run **once** via PSI from Google's servers (location not controlled). Lighthouse varies between runs, especially when ad auctions change what loads. Treat single numbers as indicative and compare trends.
- Lab numbers use Lighthouse's simulated Moto G Power on slow 4G. Field data (section 2) is what real users experience.
- The environment's network policy blocked direct access to the site, so there's no local Chrome DevTools trace. Everything comes from Lighthouse running in Google PSI.

## Files
- `summary.md`: full per-run details for all 8 runs, including largest requests, third parties, long tasks, render-blocking files and opportunities.
- `raw/psi-*.json.gz`: complete PageSpeed Insights / Lighthouse JSON. You can view them at https://googlechrome.github.io/lighthouse/viewer/ after gunzipping.
- `scripts/psi.sh`: re-runs a test with `PSI_KEY=<your key> scripts/psi.sh <url> mobile|desktop <out.json>`. The key is read from the environment and not stored.
- `scripts/summarize.py`: regenerates `summary.md` from raw files.
