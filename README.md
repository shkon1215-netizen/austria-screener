# Austria (Wiener Börse) Relative Valuation Screener

**Live:** https://shkon1215-netizen.github.io/austria-screener/ · rebuilt each
weekday after the Vienna close

Finds Austrian stocks trading at a discount to their peers on P/E, P/B,
EV/EBITDA and P/FCF and, independently, stocks that are cheap in absolute terms
or cheap against their own filed history. Each row also carries three years of
revenue, EBITDA and net profit.

**Defaults:** market cap ≥ USD 600M · median daily traded value ≥ USD 250k ·
≥20% below peer median on ≥2 of 4 metrics · ROE ≥ 5%.

This is the ninth market, after [Korea](https://github.com/shkon1215-netizen/korea-screener),
the UK, Japan, [Germany](https://github.com/shkon1215-netizen/germany-screener),
[Poland](https://github.com/shkon1215-netizen/poland-screener),
[France](https://github.com/shkon1215-netizen/france-screener), Hong Kong and the
US. `screener.py` is the same maths throughout. The data layer, the peer
fallback and the ownership tags are specific to Austria.

**Also:** the outright screen's 2% payout floor counts buybacks (shareholder
yield = dividends + buybacks − issuance), and trailing profit far above
operating profit, such as a disposal gain, is capped at operating profit after
tax before scoring (tagged `one-off`).

## Setup

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
python test_austria.py    # offline logic check, no network needed
python check_setup.py     # tests every live call individually
python main_at.py -v      # full run, ~3 minutes cold, seconds warm
```

```bash
python main_at.py --skip-liquidity           # size alone gates
python main_at.py --min-adv 1e6              # the bar France and Poland use
python main_at.py --include-property         # keep CA Immo, CPI Europe
python main_at.py --include-secondary        # keep RHI Magnesita
python main_at.py --exclude-state            # drop named public-sector holdings
python main_at.py --exclude-holdcos          # drop named holding companies
```

Results cache to `.at_cache/` per session date, so re-runs are fast, and a
throttled Yahoo cannot silently shrink the universe.

## The dashboard

Every run writes a self-contained `at_dashboard.html`. Open it directly, or run
`python serve.py` (on Windows, double-click `dashboard.cmd`) to make the
**Refresh** button work. The browser re-evaluates every threshold on the page.
Two things cannot be re-evaluated, and the page says so: the peer medians, and
companies below the run's market-cap floor.

## Where the data comes from

| | source |
|---|---|
| roster, segment, security type | Wiener Börse's company list |
| symbols | Wiener Börse's stock pages (a month's cache) |
| sector, multiples, EPS, book, yield, insider holding | Yahoo `.info` on the `.VI` line |
| liquidity | one batched Yahoo price download, 60-session median traded value |
| filed statements | Yahoo annual income statement, balance sheet and cash flow |
| state holders, holdcos, structural notes | named lists in `config_at.py`, kept by hand |

## Austrian traps this handles

**Most of the list is not Austrian.** 685 of 779 lines are the global market,
where Vienna trades foreign shares. They are not read. RHI Magnesita is listed
in the prime market and the exchange's country column says Austria, but it is a
Dutch company whose home is London, so the ISIN is read too.

**Three Austrian companies trade elsewhere.** Kontron, Fabasoft and ams-OSRAM
are on Vienna's global market with almost no volume there, so each is read on
its real market.

**The exchange's numbers need care.** Its traded value is double-counted, by
its own footnote, and its market cap covers listed shares only: Verbund is
EUR 11.8bn there and EUR 24.1bn in reality. Yahoo meanwhile gives no market cap
in `.info` for RBI, Telekom Austria, Verbund or VIG, so these are repaired from
`fast_info`, with the exchange's figure as the last resort.

**"Holding" in a name means nothing.** Semperit AG Holding and Polytec Holding
are operating companies. Holdcos are a named list.

**Recurring income below the operating line.** EVN earns from associates and
its Verbund stake every year. The one-off guard reads three filed years here,
so that is treated as structure while Kontron's single disposal year is still
capped.

## Read this before acting on it

**Vienna is thin.** About 25 names pass the gates across eight sectors, so 13 of
them are benchmarked against the rest of the market rather than an industry.
Those rows carry a `vs market` tag: a discount there means cheap against Vienna.

**The liquidity floor is low on purpose.** At USD 250k it sits in a real gap in
the data, but it is a quarter of what France and Poland use. If you need
capacity, run `--min-adv 1e6`.

**The ownership tags and notes are hand-kept**, and some rest on older sources.
Confirm the current position before relying on one. See `CLAUDE.md`.

Research tool, not investment advice.
