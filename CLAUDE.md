# CLAUDE.md — Austria (Wiener Börse) Valuation Screener

Ninth market after Korea, the UK, Japan, Germany, Poland, France, Hong Kong
and the US, built on France's copy because the currency and vendor match and
France had already combined what the others learned. Same maths
(`screener.py`), same three screens (vs peers, outright, vs own history), same
thresholds except the liquidity gate and `min_peers`. Universe: the Austrian
lines on Wiener Börse's company list (72 of 779 on 2026-11-01).

## Run order

```bash
python test_austria.py    # offline, must pass
python check_setup.py     # ten live checks
python main_at.py -v      # full run, ~3 min cold, seconds warm
python serve.py           # dashboard with working Refresh (dashboard.cmd)
python sync_dashboard_from_korea.py ../Korea/dashboard.py   # dashboard.py is generated
```

```bash
python main_at.py --min-adv 1e6          # the bar France, Poland and Hong Kong use
python main_at.py --include-property     # keep CA Immo, CPI Europe
python main_at.py --include-secondary    # keep RHI Magnesita
python main_at.py --exclude-state        # drop OMV, Verbund, Post, Telekom, EVN, Flughafen
```

## Files

| File | Role |
|---|---|
| `screener.py` | Core engine, Korea's maths. Do not edit the maths here first. |
| `config_at.py` | Thresholds, bounds, segments, `ABROAD_LINES`, named holdcos, state holders, structural notes, `macro_of`. |
| `providers_at.py` | Wiener Börse company list, segment pages, stock-page symbols; Yahoo snapshot, liquidity, FX, statements (UK's `build_statement_record`, unchanged). |
| `at_filters.py` | Roster hygiene, market-cap repair, sector, landlords, one line per issuer, control, pyramids, currency repair, then the shared screens. |
| `main_at.py` | CLI. Orders the gates so per-ticker work runs last. |
| `dashboard.py` | Generated — do not edit. Run `sync_dashboard_from_korea.py` (72 substitutions, each must match once). |
| `serve.py`, `build_site.py`, `dashboard.cmd` | Local server, GitHub Pages site, double-click launcher. |
| `check_setup.py`, `test_austria.py` | Live pre-flight; offline tests with planted traps. Keep green. |

## Where each piece came from

| piece | from | Austrian change |
|---|---|---|
| roster from the operator | Germany, France | Wiener Börse's company list page, one request |
| classification | UK, Hong Kong (Yahoo industry / sector) | Wiener Börse's per-company sectors are not free |
| thin-cohort fallback | Poland's `--fallback-peer-keys board` idea | made the default, split at financials |
| market-cap repair | Germany (fast_info), Poland (exchange cap) | exchange cap last, because of Verbund |
| one line per issuer | Germany | Gurktaler St / Vz, Austriacard's Verkauf line |
| holdcos and control | France, Hong Kong | named list only: "Holding" in a name means nothing here |
| state flag | Poland's register | a named list, since the holders are few and public |
| pyramids, currency repair, splits, TTM flag | France, UK, Germany | none. Both pyramids and the repair find nothing today |
| one-off guard | US | structural needs the gap in two filed years, the latest included (invariant 7) |

## Austrian invariants

1. **The universe is the exchange's own labels, and the ISIN.** 685 of the 779
   lines are the global market, the MTF on which Vienna trades foreign shares.
   They are not read. Foreign issuers on Vienna's own segments are dropped too,
   and **the country column is not enough**: it says Austria for RHI Magnesita
   (`NL...`, home market London), which was only leaving at the liquidity gate
   until the ISIN prefix was added. Fund lines go by security type.
2. **Three Austrian companies are read on their real market**
   (`ABROAD_LINES`). Vienna has them on the global market and sees almost none
   of their volume: Kontron 1,400 shares a day there against 56,000 in
   Frankfurt, ams-OSRAM 5,700 against 470,000 in Zurich. Kontron and Fabasoft
   use the `.DE` line outright. ams-OSRAM keeps `AMS2.VI` for fundamentals,
   because it quotes in euros like the accounts, and takes its volume from
   `AMS.SW`, converted from francs. Board `ABROAD`.
3. **Wiener Börse's turnover is double-counted, by its own footnote.** Andritz
   on 2026-10-30: 223,222 shares and EUR 18.0m on the exchange, 111,611 on
   Yahoo. The gate reads Yahoo. Using the exchange's figure would have doubled
   every ADV.
4. **Wiener Börse's market cap is the listed shares, so it comes last.**
   Verbund reads EUR 11.8bn there (Category A only) and EUR 24.1bn on Yahoo.
   Yahoo's `.info` gives no market cap at all for RBI, Telekom Austria, Verbund
   and VIG, so `fast_info` (invariant 11 in Germany) carries four blue chips,
   and `check_setup.py` asserts it. `mcap_via_wiener_boerse` was 0 on the
   reference run.
5. **Symbols come from the stock page.** The list has none. One request per
   line, a month's cache, and every symbol checked resolved on Yahoo as
   `SYMBOL.VI`. ISIN resolution is kept for renames.
6. **Holdcos by a named list.** Semperit AG Holding, Polytec Holding, Frauenthal
   Holding and Austriacard Holdings are operating companies, so no name token
   works (Hong Kong's lesson). Add to `KNOWN_HOLDCOS` rather than invent a
   heuristic. EVN is listed because of its Verbund stake.
7. **The one-off guard calls a gap structural only if it shows in two filed
   years, and reads the latest filed year when the tested figure is four
   quarters.** This differs from the other eight markets, and EVN is why: it
   earns from associates and its Verbund stake below Yahoo's operating line,
   1.60x in FY2024 and 1.58x in FY2025 after a windfall 1.09x in FY2023. The
   earlier rule saw only the two years before the latest, a median of 1.34,
   flagged it, doubled its P/E to 20 and dropped its ROE below the floor.
   Where the figure is the filed year itself, that year is under test and is
   left out. Kontron's 2025 disposal (1.35, 1.19, 2.57) stays capped.

   **It is a count of years above 1.5, not a median** (fixed 2026-11-08). The
   first version took `median(skipna=True)`, which is not "two years": a
   company with one profitable filed year let the one-off year vouch for
   itself, and with two readings the median was a mean that one gain could
   carry. Porr was spared that way: it reports half-yearly, so FY2025 (1.53)
   is under test, and its evidence was FY2023 3.37 and FY2024 0.94, a mean of
   2.15. It is now capped (P/E 10.0 → 15.4, ROE 16.4 → 10.7) and still passes.
   Porr's FY2023 operating line on Yahoo (EUR 33m) looks low, unchecked
   against its report.

   **Do not port this to the other markets.** Measured 2026-11-01 on the
   10-30 close: it moved nothing in Germany, Poland, France, Hong Kong or the
   UK, and in the US it released 24 capped names, 15 of them wrongly
   (tax-credit and disposal years, checked against EDGAR). The corrected count
   still releases a few US names wrongly, so it does not earn a port either.
   No other market has an EVN-shaped company.
8. **Financials = Yahoo sector "Financial Services"**; real estate is its own
   sector, so no carve-out.
9. Germany's invariants 2, 4, 5, 7, 8, 11 and 14 hold unchanged.

## Excluded by default (2026-11-01)

| class | rule | dropped |
|---|---|---|
| global-market foreign lines | segment, unless in `ABROAD_LINES` | 682 |
| fund lines | security type | 10 |
| foreign issuers on Vienna's segments | country or ISIN | 15 |
| listed landlords | Yahoo sector Real Estate | 2 past the size gate |

**Landlords** are Germany's judgement call: CPI Europe at P/E 4.5 and 0.46×
book is an appraiser's year. `--include-property` adds CA Immo and CPI Europe:
27 names, 10 passing.

## Thin cohorts: the main weakness, stated plainly

25 survivors across eight Yahoo sectors: Industrials 7, Financials 5,
Technology 4, Consumer Cyclical 3, Basic Materials 2, Utilities 2, Energy 1,
Communication 1. Peer P/E basis on the reference run: 12 names on a sector, 13
on the market fallback.

| peers | any screen passing |
|---|---|
| sector only, `min_peers` 5 (Poland's way) | 4 |
| sector → market, `min_peers` 5 | 8 |
| sector → market, `min_peers` 4 (default) | 9 |
| sector → market, `min_peers` 3 | same as 4 |

`min_peers` is 4 only because five financials pass the gates, so each has four
peers; at 5 the whole sector goes unscored (RBI still clears outright; VIG is
the name lost). Banks and insurers share that cohort, which is crude: VIG at
P/E 6.5 is against mostly bank multiples.

The market fallback means OMV, Verbund, voestalpine, Telekom Austria and AT&S
are compared with a non-financial Vienna median (P/E about 18), not with their
industries. The page tags these `vs market`. **A real fix is a European peer
set, which this build does not have.**

## Liquidity gate: USD 250k, measured 2026-10-30

| ADV floor | names | relative / absolute / history / any |
|---|---|---|
| none | 36 | 10 / 1 / 0 / 10 |
| USD 250k (default) | 25 | 9 / 1 / 0 / 9 |
| USD 500k | 22 | 8 / 1 / 0 / 8 |
| USD 1m | 20 | 7 / 1 / 0 / 7 |
| USD 2m | 14 | 5 / 1 / 0 / 5 |
| USD 4m | 10 | 2 / 1 / 0 / 3 |

The lowest bar of any market, on purpose, because the names split in two.
Above the gap sit ordinary ATX Prime companies: Bajaj Mobility USD 456k,
Frequentis 484k, Telekom Austria 487k, FACC 559k, Post 884k. Below it,
Rosenbauer 185k, Oberbank 176k, then Agrana 82k, Flughafen Wien 41k, AMAG 19k,
BKS 10k, BTV near zero: controlled or auction lines, where a USD 3–6bn bank can
go 37 of 60 sessions without a trade. USD 250k sits in that gap. At USD 1m the
screen loses Telekom Austria, Post, Frequentis, FACC and Bajaj. It is Vienna's
order book only (Cboe and Turquoise are not in Yahoo's figure), so a lower
bound.

A reader who needs real capacity should treat USD 250k as an information
screen and use `--min-adv 1e6`.

## Calibration, measured rather than inherited

25 names past the default gates, 2026-10-30:

| | p10 | p25 | median | p75 | p90 |
|---|---|---|---|---|---|
| P/E | 8.55 | 10.93 | **13.88** | 20.79 | 28.98 |
| P/B | 0.85 | 1.01 | **1.65** | 2.92 | 4.17 |
| EV/EBITDA | 5.42 | 6.74 | **8.21** | 10.96 | 12.39 |
| P/FCF | 5.48 | 7.04 | **11.92** | 18.18 | 32.79 |
| ROE % | −1.61 | 6.50 | **11.78** | 16.45 | 19.57 |
| Yield % | 0.00 | 0.69 | **2.87** | 3.35 | 4.63 |

P/B < 1 passes 24% (6 of 25), EV/EBITDA < 8 passes 42% of the 19 with one. The
EV test is loose here, but P/B binds: of the six below book, only RBI (via the
financial carve-out) clears ROE, fair P/B and the payout together. voestalpine
misses fair P/B, Wienerberger, Mayr-Melnhof and Lenzing miss ROE, and EVN
misses 8× EBITDA. Cost of equity 8 / 9 / 10 / 12% leaves the absolute count at
1 throughout; 10% stays.

**The history screen passes nobody, and that is the finding.** Vienna has
re-rated: on P/B, RBI is ~2.8× its filed-year median, Strabag ~2.3×, Erste
~1.9×. 23 names have a benchmark. Only one metric on one name is 30% below.

## Results, reference run (2026-10-30 close)

```
779 lines (682 global market, 10 funds, 15 foreign dropped)
 72 lines sent to Yahoo, 71 priced (5 market caps via fast_info)
 37 cleared USD 600m (-2 landlords)
 25 cleared USD 250k/day
  9 cheap vs peers, after ROE >= 5% (11 before it)
  1 cheap outright (RBI, via the financials carve-out, also on the peer screen)
  0 cheap vs own history
  9 passing at least one screen
```

Telekom Austria, RBI, VIG, Palfinger, Porr, EVN, voestalpine, Strabag, OMV
(OMV on the local run only: see Publishing).
Browser verdict at default thresholds equals Python's: 9 / 9 / 1 / 0, and every
per-test count (P/B < 1 6, EV < 8 8, fair 4, shareholder yield 14, carve-out 1).
Two one-offs capped (Kontron, Bajaj Mobility), two structural gaps spared (EVN,
Porr). No foreign reporters, no pyramids. Since the guard fix of 2026-11-08,
Porr is capped too (three capped, EVN alone spared); the 2026-11-06 close
still gives 25 names and 9 passing, the same nine.

## Cash flow, shareholder yield and the one-off guard

As in the other eight markets (added there 2026-10-18), from the US build:
P/FCF is the fourth peer metric, the outright payout test is the shareholder
yield, and earnings above 1.5× after-tax operating profit are capped before
peer medians are built, at the 23% Körperschaftsteuer rate. See invariant 7 for
the one difference. `--no-oneoff-guard` scores earnings as reported.

## Known gaps (ranked by value of fixing)

1. **No European peers.** See "Thin cohorts". 13 of 25 names are scored against
   the market rather than an industry.
2. **State stakes and structural notes are hand-kept.** `STATE_HOLDERS` was
   confirmed for the federal stakes from a parliamentary paper and ÖBAG's
   portfolio, not re-confirmed for 2026. The provincial stakes (EVN, Flughafen
   Wien) and EVN's Verbund stake are from general knowledge, not checked
   against a filing. `STRUCTURAL_NOTES` (RBI's Russian subsidiary, Rasperia's
   frozen Strabag stake) rests on reporting mostly from 2024; a search found
   nothing later. Re-check them.
3. **The closely-held flag is coarse.** 15 of 25 carry it. OMV reads 56%,
   Verbund 30% although the Republic holds a majority.
4. **ADV is Vienna's order book only.**
5. **Yahoo's classification is rough** (DO & CO under Airports, Lenzing under
   Textile Manufacturing). With sector-level cohorts this matters only for
   Industrials.
6. Four filed years for the history screen; trailing multiples only.

## Likely first failures

- **Wiener Börse changes a page.** The list must parse to 600+ lines or the run
  stops; `check_setup.py` asserts Erste, OMV, Andritz, Kontron and Andritz's
  symbol. `Reference data` on stock pages loads by script and is not read.
- **Yahoo throttles silently.** The run refuses under half the lines priced by
  Yahoo itself. The cache per session date fills gaps on re-run.
- **A blank market cap reads as too small.** Watch `mcap_via_fast_info` (5
  here); a sudden drop means RBI, Verbund and VIG are at risk.
- **A company moves.** ams-OSRAM and Kontron have changed listing plans before.
  If `ABROAD_LINES` goes stale, `check_setup.py` fails on that line.
- **The statements cache stores derived records.** Bump
  `STATEMENTS_CACHE_VERSION` when `build_statement_record` changes.
- **pandas 3.x** — pinned `<3`.

## Keeping in step with Korea

```bash
python sync_dashboard_from_korea.py ../Korea/dashboard.py
```

Every substitution must match exactly once; misses exit 1. Then grep for
Korean text, KOSPI, PER/PBR and `ticker`, and confirm in a browser that the
page's verdict equals the Python funnel at default thresholds.

## Publishing

`.github/workflows/screen.yml` runs at 17:00 UTC on weekdays (after Vienna's
close in both CET and CEST), builds `site/` and deploys to GitHub Pages, with a
retry after a pause for Yahoo throttling.

Live: https://shkon1215-netizen.github.io/austria-screener/. Unlisted -
`noindex` plus a blanket `robots.txt` - but the repo is public, which free
Pages requires. No screen output is committed.

**Wiener Börse and Yahoo both answer GitHub's runners** - confirmed on the
first run, 2026-11-01: about 4 minutes cold, no retry, 72 lines, 71 priced, 37
past size, 25 past liquidity, the same names as the local run.

**The first two cloud runs passed 8, not the local 9, and OMV is the whole
difference.** Every other multiple matched. GitHub's runners got an older Yahoo
record for OMV on both runs (EPS 4.77, book 46.4, P/E 16.0, P/B 1.64) while this
machine got EPS 6.39, book 54.77, P/E 11.9, P/B 1.39 on four calls. OMV reported
Q3 on 2026-10-29. The local book value equals June's equity over today's shares;
the runners' equals no filed quarter (Dec 2025 is 50.1, Sep 2026 is 55.7), so the
runners' record is the stale one. It costs one name and cannot add a false one.
No repair was built: Yahoo's own quarters do not reconcile to its EPS for OMV
(they sum to about EUR 9.6 a share), so restating from them would swap one doubt
for another. If the two still differ after a week, suspect Yahoo serving
different records by region, and look for the same thing after any Q results.

A docs-only push does not trigger a run (`paths-ignore: **.md`); start one with
`gh workflow run screen.yml`.

## Interpretation

Sort by `avg_discount`, then read `roe_pct` immediately, then look for tags.
`vs market` means the discount is against Vienna, not the industry. `state` and
`close` mean the free float is a minority. `note` is a discount no multiple
shows. `holdco` on EVN means its P/B carries Verbund's share price. Low P/B with
low ROE is arithmetic, not opportunity.

Research tool, not investment advice.
