"""Pre-flight diagnostic: tests every live call the Austria screen makes.

    python check_setup.py

Run this before main_at.py. Nearly every failure in this build is a SILENT
one - a changed page reads as a market with no companies, a throttled Yahoo
as a market where companies vanished, and a blank market cap as a blue chip
too small to screen - and a full run is slow enough that finding out
afterwards is expensive. Each check here names what it protects against.
"""
from __future__ import annotations

import logging
import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
logging.basicConfig(level=logging.WARNING)
logging.getLogger("yfinance").setLevel(logging.CRITICAL)

RESULTS: list[tuple[str, bool, str]] = []


def check(name: str):
    def deco(fn):
        def run():
            t0 = time.time()
            try:
                detail = fn() or ""
                RESULTS.append((name, True, detail))
                print(f"  OK    {name:<44} {detail}  ({time.time() - t0:.1f}s)")
            except Exception as e:                                # noqa: BLE001
                RESULTS.append((name, False, str(e)))
                print(f"  FAIL  {name:<44} {e}")
        return run
    return deco


def _prov():
    from config_at import ScreenConfig
    from providers_at import WienerBoerseProvider
    return WienerBoerseProvider(ScreenConfig())


@check("Wiener Boerse company list (roster)")
def roster():
    r = _prov().listing_roster()
    if len(r) < 600:
        raise RuntimeError(f"only {len(r)} lines - the page moved or changed?")
    home = r[r["country"].eq("Austria")]
    for isin, name in (("AT0000652011", "Erste"), ("AT0000743059", "OMV"),
                       ("AT0000730007", "Andritz"), ("AT0000A0E9W5", "Kontron")):
        if isin not in set(home["isin"]):
            raise RuntimeError(f"{name} missing from the Austrian lines")
    seg = r["segment"].str.lower().value_counts().to_dict()
    if seg.get("global market", 0) < 300:
        raise RuntimeError(f"global market is {seg.get('global market')} lines - the "
                           "foreign-share filter reads this segment name")
    return f"{len(r)} lines, {len(home)} Austrian, {seg.get('prime market')} prime"


@check("segment pages and stock pages")
def pages():
    p = _prov()
    lines = p.segment_lines()
    if len(lines) < 80:
        raise RuntimeError(f"only {len(lines)} lines on the four segment pages")
    from providers_at import WIENER_BOERSE, parse_symbol
    sym = parse_symbol(p._req("GET", WIENER_BOERSE + lines["AT0000730007"]["path"]).text)
    if sym != "ANDR":
        raise RuntimeError(f"Andritz's symbol read as {sym!r} - every ticker comes from "
                           "this line of the stock page")
    return f"{len(lines)} lines, {len(p.exchange_caps)} caps, Andritz -> {sym}"


@check("the exchange's cap is the listed shares")
def verbund():
    """Why the exchange's cap is the last resort. If this stops being true the
    cap may have become usable; it does not break anything."""
    import yfinance as yf
    p = _prov()
    p.segment_lines()
    wb = p.exchange_caps.get("AT0000746409")
    yh = yf.Ticker("VER.VI").fast_info.get("marketCap")
    if not wb or not yh:
        raise RuntimeError(f"Verbund cap missing (exchange {wb}, Yahoo {yh})")
    return f"Verbund EUR {wb / 1e9:.1f}bn on the exchange, {yh / 1e9:.1f}bn on Yahoo"


@check("Yahoo .info on a Vienna line (rate limit)")
def info():
    import yfinance as yf
    i = yf.Ticker("EBS.VI").info
    if not i.get("marketCap") or not i.get("trailingPE"):
        raise RuntimeError("fields missing - Yahoo is throttling this IP; wait and retry")
    if i.get("currency") != "EUR":
        raise RuntimeError(f"currency {i.get('currency')!r}, expected EUR")
    return f"Erste mcap EUR {i['marketCap'] / 1e9:.0f}bn, P/E {i['trailingPE']:.1f}"


@check("blank market cap repaired by fast_info")
def fastinfo():
    """RBI, Telekom Austria, Verbund and VIG: every multiple, no marketCap. If
    fast_info stopped answering, four of the largest names would fall back on
    the exchange's cap or fail the size gate."""
    import yfinance as yf
    mc = yf.Ticker("RBI.VI").fast_info.get("marketCap")
    if not mc or mc < 5e9:
        raise RuntimeError(f"RBI fast_info marketCap {mc}")
    return f"RBI EUR {mc / 1e9:.1f}bn via fast_info"


@check("Austrian companies abroad")
def abroad():
    import yfinance as yf
    from config_at import ABROAD_LINES
    seen = []
    for isin, (sym, fund, adv, ccy, venue) in ABROAD_LINES.items():
        i = yf.Ticker(fund).info
        if i.get("currency") != "EUR" or not (i.get("marketCap") or i.get("regularMarketPrice")):
            raise RuntimeError(f"{fund}: currency {i.get('currency')}, no price - the line "
                               "for this company moved")
        seen.append(fund)
    return ", ".join(seen)


@check("ISIN -> Yahoo symbol resolution")
def isin():
    import yfinance as yf
    q = yf.Search("AT0000652011", max_results=8, news_count=0).quotes or []
    syms = [x.get("symbol") for x in q]
    if "EBS.VI" not in syms:
        raise RuntimeError(f"Erste's ISIN resolved to {syms} - renamed lines will "
                           "drop out as unpriced")
    return f"Erste -> {syms[:4]}"


@check("batched price download (liquidity)")
def download():
    import yfinance as yf
    px = yf.download(["EBS.VI", "OMV.VI", "AMS.SW"], period="30d", interval="1d",
                     progress=False, auto_adjust=False, group_by="column")
    if px.empty or "Volume" not in px.columns.get_level_values(0):
        raise RuntimeError("no Close/Volume panel")
    n = int(px["Volume"].notna().sum().min())
    if n < 10:
        raise RuntimeError(f"only {n} sessions of volume")
    return f"{n} sessions for 3 tickers"


@check("filed statements and cash flow")
def statements():
    import yfinance as yf
    tk = yf.Ticker("OMV.VI")
    inc, bs, cf = tk.income_stmt, tk.balance_sheet, tk.cashflow
    need_i = ("Total Revenue", "Operating Income", "Net Income Common Stockholders")
    need_b = ("Common Stock Equity", "Ordinary Shares Number", "Minority Interest")
    miss = [k for k in need_i if k not in inc.index] + [k for k in need_b if k not in bs.index]
    if miss:
        raise RuntimeError(f"rows missing {miss} - Yahoo renamed statement lines "
                           "(the pyramid test reads operating income and minorities)")
    if cf is None or "Operating Cash Flow" not in cf.index:
        raise RuntimeError("no cash-flow statement - P/FCF and the shareholder yield need it")
    return f"{inc.shape[1]} annual columns"


@check("FX EUR->USD, CHF->EUR")
def fx():
    p = _prov()
    r = p.eur_to_usd()
    if r == 1.17:
        raise RuntimeError("both live sources failed - hardcoded fallback in use")
    chf = p.eur_per(["CHF"])["CHF"]
    return f"1 EUR = {r:.4f} USD, 1 CHF = {chf:.4f} EUR"


def main() -> int:
    print("Austria screener pre-flight\n")
    for fn in (roster, pages, verbund, info, fastinfo, abroad, isin, download, statements, fx):
        fn()
    bad = [n for n, ok, _ in RESULTS if not ok]
    print("\n" + ("all checks passed - run python main_at.py -v"
                  if not bad else f"{len(bad)} check(s) failed: {', '.join(bad)}"))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
