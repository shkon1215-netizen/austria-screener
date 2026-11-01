"""Offline validation of the Austria screener. No network required.

Run: python test_austria.py

Every planted case is something a naive screener gets wrong, and most were
measured on the first live run (2026-10-30): 685 foreign lines on the global
market, Verbund's half-sized exchange market cap, Austrian companies that
trade abroad, a sector too thin to hold a median, operating companies with
"Holding" in their names, and an equity-method earner the one-off guard would
have halved.
"""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd

import at_filters as FF
import config_at as K
from config_at import ScreenConfig
from main_at import display_name
from providers_at import (parse_market_cap, parse_roster, parse_segment_page,
                          parse_symbol, to_yahoo)
from screener import run_screen

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

rng = np.random.default_rng(7)

USD_PER_EUR = 1.13
MCAP = 2.0e9           # ~USD 2.3bn, clears the gate
ADV = 5.0e6            # ~USD 5.7m, clears the gate

FAILURES: list[str] = []


def ok(cond, label):
    print(f"  {'OK  ' if cond else 'FAIL'} {label}")
    if not cond:
        FAILURES.append(label)


def base(sector="Industrials", **kw):
    r = dict(name="", symbol="", isin="", board="PRIME", segment="prime market",
             sec_type="Equity Share", country="Austria", quote_type="EQUITY",
             yf_sector=sector, yf_industry=sector + " sub",
             market_cap_local=MCAP, adv_local=ADV, close_local=50.0,
             currency="EUR", fin_ccy="EUR", yf_name="",
             trailing_pe=np.nan, price_to_book=np.nan, ev_to_ebitda=np.nan,
             trailing_eps=4.0, book_value_ps=32.0, div_yield=1.5)
    r.update(kw)
    r["ticker"] = to_yahoo(r["symbol"])
    if not r["isin"]:
        r["isin"] = "AT" + (r["symbol"] + "XXXXXXXX")[:8] + "01"
    return r


def make_universe() -> pd.DataFrame:
    rows = []
    specs = [("Industrials", 15.0, 1.8, 9.0, 9), ("Financial Services", 9.0, 0.9, np.nan, 5),
             ("Basic Materials", 12.0, 1.2, 7.0, 3), ("Technology", 28.0, 4.0, 15.0, 3)]
    n = 0
    for sector, pe, pb, ev, count in specs:
        for _ in range(count):
            n += 1
            rows.append(base(sector, symbol=f"P{n:02d}", name=f"Peer {n} AG",
                             trailing_pe=pe * rng.uniform(0.93, 1.09),
                             price_to_book=pb * rng.uniform(0.93, 1.09),
                             ev_to_ebitda=ev * rng.uniform(0.93, 1.09),
                             trailing_eps=pb / pe * 32.0 * rng.uniform(0.95, 1.05),
                             market_cap_local=MCAP * rng.uniform(0.9, 2.5),
                             adv_local=ADV * rng.uniform(0.9, 2.5)))

    # PASS: genuinely cheap vs its engineering peers, good ROE, a dividend.
    rows.append(base(symbol="GOOD", name="Echter Wert AG", trailing_pe=8.5, price_to_book=0.75,
                     ev_to_ebitda=5.0, trailing_eps=5.0, book_value_ps=40.0, div_yield=4.2))
    # A bank below book: EV/EBITDA suppressed though Yahoo gives one, and it
    # clears the absolute screen through the carve-out. RBI's shape.
    rows.append(base("Financial Services", symbol="RBI", isin="AT0000606306",
                     name="Raiffeisen Bank International AG", trailing_pe=6.0,
                     price_to_book=0.8, ev_to_ebitda=4.0, trailing_eps=4.0,
                     book_value_ps=30.0, div_yield=7.0))
    # Alone in Communication Services: no sector cohort, benchmarked against
    # the other non-financials. Telekom Austria's shape.
    rows.append(base("Communication Services", symbol="TKA", isin="AT0000720008",
                     name="Telekom Austria AG", trailing_pe=8.5, price_to_book=1.0,
                     ev_to_ebitda=4.2, trailing_eps=1.0, book_value_ps=8.0, div_yield=5.0))
    # Named as a holding company because it is one in part; tagged, kept. Its
    # state holder is named too. EVN's shape.
    rows.append(base("Utilities", symbol="EVN", isin="AT0000741053", name="EVN AG",
                     trailing_pe=10.5, price_to_book=0.8, ev_to_ebitda=9.3,
                     trailing_eps=2.8, book_value_ps=36.0, div_yield=3.0))
    # "Holding" in the name, operating company. No tag. Semperit's shape.
    rows.append(base(symbol="SEM", isin="AT0000785555", name="Semperit AG Holding",
                     trailing_pe=15.0, price_to_book=1.8, ev_to_ebitda=9.0))
    # FAIL: listed landlord. P/E of 4.5 is an IAS 40 revaluation. CPI's shape.
    rows.append(base("Real Estate", symbol="CPI", name="CPI Europe AG", trailing_pe=4.5,
                     price_to_book=0.46, ev_to_ebitda=18.0, trailing_eps=3.4,
                     book_value_ps=33.0))
    # FAIL: loss-maker. Yahoo sometimes reports P/E 0; it must read as missing.
    rows.append(base(symbol="LOSS", name="Verlust AG", trailing_pe=0.0, price_to_book=0.6,
                     trailing_eps=-2.0, book_value_ps=30.0))
    # FAIL (size): too small.
    rows.append(base(symbol="TINY", name="Klein AG", market_cap_local=3e8, trailing_pe=6.0,
                     price_to_book=0.5, ev_to_ebitda=3.0))
    return pd.DataFrame(rows)


ROSTER_HTML = """<table class="x"><thead><tr><th>ISIN</th><th>Issuer</th><th>Country</th>
<th>Market</th><th>Market Segment</th><th>Type of Security</th></tr></thead><tbody>
<tr><td><span>AT0000730007</span></td><td><a href="/en/?ISIN=AT0000730007">Andritz AG</a></td>
<td>Austria</td><td>Regulated Market</td><td>prime market</td><td>Equity Share</td></tr>
<tr><td>AT0000969985</td><td>AT&amp;S Austria Technologie &amp; Systemtechnik Aktiengesellschaft</td>
<td>Austria</td><td>Regulated Market</td><td>prime market</td><td>Equity Share</td></tr>
<tr><td colspan="6">Showing 2 of 2</td></tr></tbody></table>"""

SEGMENT_HTML = """<table><tr><th>Name</th></tr>
<tr data-key="2"><td class="multi-cell"><div><a id="c" href="/en/stock-standard-market/bks-bank-ag-AT0000624705/"
data-isin="AT0000624705">BKS Bank AG</a></div></td><td class="kv-align-right">22.0000</td>
<td><span class="not-set">-</span></td><td>10/30/2026<br>13:30:12</td><td>1,007.7 mn</td>
<td class="kv-align-right">990</td><td class="kv-align-right">21,780</td></tr>
<tr data-key="3"><td><a href="/en/stock-standard-market/austriacard-holdings-verkauf-AT0000A3UZH4/">X</a></td>
<td>-</td><td>-</td><td>-</td><td>-</td></tr></table>"""


def check_parsers():
    print("=== Wiener Boerse parsers and helpers ===")
    r = parse_roster(ROSTER_HTML)
    ok(len(r) == 2 and r.iloc[0]["isin"] == "AT0000730007" and r.iloc[0]["segment"] == "prime market",
       "company list parsed; a row with no ISIN is not a company")
    ok("AT&S" in r.iloc[1]["name"], "an escaped ampersand in a name is unescaped")
    p = parse_segment_page(SEGMENT_HTML)
    ok(p["AT0000624705"]["cap"] == 1007.7e6 and p["AT0000624705"]["path"].endswith("AT0000624705/"),
       "segment page: market cap and stock-page link, not the turnover cells")
    ok(np.isnan(p["AT0000A3UZH4"]["cap"]), "no trade yet -> no market cap, not zero")
    ok(parse_market_cap("8,382.4 mn") == 8382.4e6 and parse_market_cap("1.2 bn") == 1.2e9
       and np.isnan(parse_market_cap("-")), "market-cap text parsed")
    ok(parse_symbol("Price data &amp; news · ISIN: AT0000730007 · Symbol: ANDR Last") == "ANDR"
       and parse_symbol('Symbol: <span>4X0</span>') == "4X0", "symbol read off the stock page")
    ok(to_yahoo("ANDR") == "ANDR.VI" and to_yahoo("4X0") == "4X0.VI", "Vienna symbol -> .VI")
    ok(K.board_of("standard market auction") == "STANDARD" and K.board_of("global market") == "",
       "segments map to boards; the global market is none of them")
    ok(K.issuer_key("Gurktaler AG St") == K.issuer_key("Gurktaler AG Vz"),
       "Gurktaler's ordinary and preferred lines are one issuer")
    ok(K.issuer_key("AUSTRIACARD HOLDINGS AG") == K.issuer_key("AUSTRIACARD HOLDINGS VERKAUF"),
       "Austriacard's temporary line is the same issuer")
    ok(K.issuer_key("Wienerberger AG") != K.issuer_key("Wiener Privatbank SE"),
       "similar names stay apart")
    ok(K.is_financial("Financial Services") and not K.is_financial("Real Estate"),
       "financials by Yahoo's sector; real estate is not one")
    ok(K.macro_of("Utilities") == "Non-financials" and K.macro_of("Financial Services") == "Financials"
       and K.macro_of("") == "", "one line through the market; no sector, no cohort")
    ok(not K.is_holdco("Semperit AG Holding", "AT0000785555")
       and not K.is_holdco("POLYTEC Holding AG", "AT0000A00XX9"),
       "'Holding' in a name is not a holding company")
    ok(display_name("Vienna Insurance Group AG", "Vienna Insurance Group AG Wiener Versicherung Gruppe")
       == "Vienna Insurance Group", "the German restatement after AG is trimmed")
    ok(display_name("Strabag SE", "STRABAG SE") == "Strabag", "Yahoo's casing over the exchange's capitals")
    ok(display_name("Andritz AG", "Andritz AG") == "Andritz", "legal form removed")


def check_roster():
    print("\n=== roster filters ===")
    cfg = ScreenConfig()
    rows = [
        ("AT0000730007", "Andritz AG", "Austria", "prime market", "Equity Share"),
        ("DE000ENER6Y0", "Siemens Energy AG", "Germany", "global market", "Registered Ordinary Share"),
        ("AT0000A0E9W5", "KONTRON AG", "Austria", "global market", "Equity Share"),
        ("AT9999999999", "Unmapped Austrian AG", "Austria", "global market", "Equity Share"),
        # The exchange's country column really does say Austria for this one.
        ("NL0012650360", "RHI Magnesita N.V.", "Austria", "prime market", "Depository Interest"),
        ("NL0000289783", "Robeco Fund", "Netherlands", "standard market auction", "UCITS share"),
        ("GG00BPQVBL98", "Orbitus PCC", "Guernsey", "direct market", "Investment Certificate"),
    ]
    df = pd.DataFrame(rows, columns=["isin", "name", "country", "segment", "sec_type"])
    out, st = FF.apply_roster_filters(df, cfg)
    names = set(out["name"])
    ok(names == {"Andritz AG", "KONTRON AG"},
       f"Austrian home line and a mapped Austrian abroad survive ({sorted(names)})")
    ok(st["dropped_global_market"] == 2 and st["dropped_fund_line"] == 2
       and st["dropped_foreign_secondary"] == 1, f"each drop counted once ({st})")
    out2, _ = FF.apply_roster_filters(df, ScreenConfig(exclude_secondary=False))
    ok("RHI Magnesita N.V." in set(out2["name"]) and "Siemens Energy AG" not in set(out2["name"]),
       "--include-secondary keeps RHI Magnesita, never the global market")


def check_market_cap():
    print("\n=== market-cap repair ===")
    df = pd.DataFrame([
        # Verbund: Yahoo's fast_info found the whole company. The exchange's
        # smaller listed-shares figure must not replace it.
        dict(isin="AT0000746409", market_cap_local=24.1e9, mcap_source="fast_info", close_local=69.5),
        # Thin line: Yahoo has a price, no cap, no shares.
        dict(isin="AT0000698253", market_cap_local=np.nan, mcap_source="", close_local=10.5),
        # Nobody has anything.
        dict(isin="AT0000000000", market_cap_local=np.nan, mcap_source="", close_local=np.nan),
    ])
    out, st = FF.repair_market_cap(df, {"AT0000746409": 11.8e9, "AT0000698253": 5.3e6})
    i = out.set_index("isin")
    ok(i.loc["AT0000746409", "market_cap_local"] == 24.1e9,
       "Yahoo's whole-company cap is not replaced by the exchange's listed-shares cap")
    ok(i.loc["AT0000698253", "market_cap_local"] == 5.3e6
       and i.loc["AT0000698253", "mcap_source"] == "wiener boerse", "a blank is filled, and says so")
    ok(pd.isna(i.loc["AT0000000000", "market_cap_local"]) and st["mcap_via_wiener_boerse"] == 1,
       "no source -> still missing, never zero")


def check_oneoff_structural():
    print("\n=== one-off guard: new vs recurring ===")
    cfg = ScreenConfig()

    def row(t, ni, op, y1, y2, y3, q=True, pe=10.0):
        return dict(ticker=t, sector="Utilities", ttm_ni=ni if q else np.nan,
                    ttm_op=op if q else np.nan, lf_np_rep=ni, lf_op=op, trailing_pe=pe,
                    trailing_eps=2.8, np_y1=y1[0], op_y1=y1[1], np_y2=y2[0], op_y2=y2[1],
                    np_y3=y3[0], op_y3=y3[1])
    df = pd.DataFrame([
        # EVN: Verbund dividend and associates below Yahoo's operating line.
        # FY2023 1.09, FY2024 1.60, FY2025 1.58; four quarters 1.91.
        row("EVNX", 526.0, 332.0, (530.0, 633.0), (472.0, 384.0), (437.0, 359.0)),
        # Kontron: one disposal year. 1.35, 1.19, 2.57.
        row("KTNX", 141.0, 71.3, (77.7, 74.5), (90.7, 98.6), (141.1, 71.3), q=True),
        # The same disposal with no quarters: the filed year is what is under
        # test, so it cannot also be its own evidence.
        row("HALF", 141.0, 71.3, (77.7, 74.5), (90.7, 98.6), (141.1, 71.3), q=False),
    ])
    out, _ = FF.apply_oneoff_guard(df, cfg)
    i = out.set_index("ticker")
    ok(not bool(i.loc["EVNX", "oneoff_capped"]) and i.loc["EVNX", "trailing_pe"] == 10.0,
       "a gap in two of the last three filed years is structural: EVN's P/E stands")
    ok(bool(i.loc["KTNX", "oneoff_capped"]), "a single disposal year is still capped")
    ok(bool(i.loc["HALF", "oneoff_capped"]), "a filed-year test does not vouch for itself")


def check_pyramids():
    print("\n=== pyramids ===")
    cfg = ScreenConfig()

    def row(name, rev, op, eq, mi, ccy="EUR", fy="2023,2024,2025"):
        return dict(name=name, ticker=name[:4] + ".VI", rev_y3=rev, op_y3=op,
                    lf_equity=eq, lf_mi=mi, fin_ccy=ccy, fin_years=fy, is_holdco=False)
    df = pd.DataFrame([
        # Christian Dior / LVMH: identical revenue and operating profit; Dior's
        # equity is mostly LVMH's other shareholders.
        row("LVMH", 80807.0, 17668.0, 67.5e9, 1.5e9),
        row("CHRISTIAN DIOR", 80807.0, 17650.0, 25.0e9, 40.0e9),
        # Accor and Sopra Steria: revenue within 0.2%, nothing else in common.
        row("ACCOR", 5639.0, 900.0, 4.0e9, 0.3e9),
        row("SOPRA STERIA", 5648.0, 450.0, 2.5e9, 0.05e9),
        # Same revenue and margin by chance, neither carrying minorities.
        row("TWIN A", 3000.0, 300.0, 2.0e9, 0.0),
        row("TWIN B", 3010.0, 302.0, 2.2e9, 0.0),
    ])
    out, stats = FF.flag_pyramids(df, cfg)
    names = set(out["name"])
    ok(stats["pyramid_pairs"] == 1 and "CHRISTIAN DIOR" not in names and "LVMH" in names,
       f"Dior dropped as LVMH's consolidating parent, and only that pair ({stats})")
    ok(out.set_index("name").loc["LVMH", "pyramid_child_of"] == "CHRISTIAN DIOR",
       "LVMH tagged with its listed parent")
    ok({"ACCOR", "SOPRA STERIA", "TWIN A", "TWIN B"} <= names,
       "a revenue coincidence is not a pyramid (the first run's ten false pairs)")


def check_currency():
    print("\n=== currency repair (euro quote, dollar accounts) ===")
    R = 0.888                       # EUR per USD
    shares = 100e6
    common = dict(currency="EUR", fin_ccy="USD", close_local=50.0,
                  market_cap_local=50.0 * shares, yf_shares=shares, yf_roe=0.15,
                  lf_shares=shares, share_basis_g=1.0)
    rows = [
        # TotalEnergies shape: EPS in euros (k = R), book ALREADY in euros
        # against quarterly USD equity (k = R) -> P/B untouched; EV in euros
        # over USD EBITDA -> repaired.
        dict(symbol="TTEX", ticker="TTEX.VI", **common, trailing_eps=5.0 * R,
             trailing_pe=50.0 / (5.0 * R), yf_ni=500e6, book_value_ps=30.0 * R,
             price_to_book=50.0 / (30.0 * R), lf_equity=3.2e9,
             yf_ev=6e9, yf_ebitda=1e9, ev_to_ebitda=6.0),
        # Vallourec shape: book in DOLLARS (k = 1) -> P/B repaired.
        dict(symbol="VKX", ticker="VKX.VI", **common, trailing_eps=5.0 * R,
             trailing_pe=50.0 / (5.0 * R), yf_ni=500e6, book_value_ps=30.0,
             price_to_book=50.0 / 30.0, lf_equity=3.2e9,
             yf_ev=6e9, yf_ebitda=1e9, ev_to_ebitda=6.0),
        # Maurel & Prom shape: EPS ratio 0.828, 7% off the rate (four quarters
        # at four rates) - still read as euros, not refused.
        dict(symbol="MAUX", ticker="MAUX.VI", **common, trailing_eps=5.0 * 0.828,
             trailing_pe=50.0 / (5.0 * 0.828), yf_ni=500e6, book_value_ps=30.0 * R,
             price_to_book=50.0 / (30.0 * R), lf_equity=3.2e9,
             yf_ev=6e9, yf_ebitda=1e9, ev_to_ebitda=6.0),
        # STMicro shape: EPS rounded to 0.03 - ratio 0.06, evidence of nothing.
        dict(symbol="STMX", ticker="STMX.VI", **common, trailing_eps=0.03,
             trailing_pe=1725.0, yf_ni=466e6, book_value_ps=30.0 * R,
             price_to_book=50.0 / (30.0 * R), lf_equity=3.2e9,
             yf_ev=6e9, yf_ebitda=1e9, ev_to_ebitda=6.0),
        # A Swiss-franc reporter: 1 CHF ~ 1.07 EUR, too close to tell apart.
        dict(symbol="CHFX", ticker="CHFX.VI", **{**common, "fin_ccy": "CHF"},
             trailing_eps=5.0, trailing_pe=10.0, yf_ni=500e6, book_value_ps=30.0,
             price_to_book=1.67, lf_equity=3e9, yf_ev=6e9, yf_ebitda=1e9, ev_to_ebitda=6.0),
        # A euro reporter: untouched.
        dict(symbol="EURX", ticker="EURX.VI", currency="EUR", fin_ccy="EUR", close_local=50.0,
             market_cap_local=5e9, yf_shares=shares, trailing_eps=5.0, trailing_pe=10.0,
             yf_ni=500e6, yf_roe=0.15, book_value_ps=33.0, price_to_book=1.5, yf_ev=6e9,
             yf_ebitda=1e9, ev_to_ebitda=6.0, lf_equity=3.3e9, lf_shares=shares,
             share_basis_g=1.0),
    ]
    q_equity = {"TTEX.VI": 3.0e9, "VKX.VI": 3.0e9, "MAUX.VI": 3.0e9, "STMX.VI": 3.0e9}
    df, stats = FF.repair_foreign_reporters(pd.DataFrame(rows),
                                            {"EUR": 1.0, "USD": R, "CHF": 1.07}, q_equity)
    i = df.set_index("symbol")
    ok(abs(i.loc["TTEX", "price_to_book"] - 50.0 / (30.0 * R)) < 1e-9,
       "book already in euros: P/B left alone (assuming Poland's behaviour would break it)")
    ok(abs(i.loc["TTEX", "ev_to_ebitda"] - 6e9 / (1e9 * R)) < 1e-9,
       f"euro EV over dollar EBITDA repaired ({i.loc['TTEX', 'ev_to_ebitda']:.2f})")
    ok(abs(i.loc["VKX", "price_to_book"] - 50.0 / (30.0 * R)) < 1e-9,
       f"book in dollars: P/B repaired ({i.loc['VKX', 'price_to_book']:.3f})")
    ok(pd.notna(i.loc["MAUX", "trailing_pe"]),
       "an EPS ratio 7% off the rate is still read as euros, not refused")
    ok(np.isnan(i.loc["STMX", "trailing_pe"]) and pd.notna(i.loc["STMX", "price_to_book"]),
       "a rounded EPS refuses the P/E only")
    ok(i.loc["CHFX", ["trailing_pe", "price_to_book", "ev_to_ebitda"]].isna().all()
       and i.loc["CHFX", "fx_note"] == "fx basis untestable",
       "a currency near 1 EUR cannot be tested -> refused, not guessed")
    ok(i.loc["EURX", "price_to_book"] == 1.5 and i.loc["EURX", "fx_note"] == "",
       "euro reporter untouched")
    ok(stats["fx_pb_repaired"] == 1 and stats["fx_pe_refused"] == 1,
       f"funnel counts the repair ({stats})")


def check_statements():
    from providers_at import build_statement_record
    print("\n=== filed statements ===")
    years = pd.to_datetime(["2021-12-31", "2022-12-31", "2023-12-31",
                            "2024-12-31", "2025-12-31"])

    def stmt(rows: dict) -> pd.DataFrame:
        df = pd.DataFrame({k: [np.nan] + list(v) for k, v in rows.items()}, index=years).T
        return df[df.columns[::-1]]

    inc = stmt({"Total Revenue": (1000e6, 1100e6, 1200e6, 1300e6),
                "Operating Income": (150e6, 160e6, 170e6, 180e6),
                "EBITDA": (200e6, 210e6, 220e6, 230e6),
                "Net Income Common Stockholders": (100e6, 110e6, 120e6, 130e6)})
    bs = stmt({"Common Stock Equity": (1000e6,) * 4, "Ordinary Shares Number": (1e8,) * 4,
               "Total Debt": (300e6,) * 4, "Cash And Cash Equivalents": (100e6,) * 4})
    px = pd.Series(20.0, index=pd.date_range("2020-01-01", "2026-10-02", freq="B"))
    rec = build_statement_record(inc, bs, px, None, "EUR", "EUR", close_now=20.0, mcap_now=2e9)
    ok(rec["hist_pbr"] == [2.0] * 4, f"P/B history in euros ({rec['hist_pbr']})")
    # A DOLLAR reporter quoted in euros - TotalEnergies. EUR 2bn at 1.13
    # USD/EUR is USD 2.26bn over USD 1bn of equity: P/B 2.26.
    fx = pd.Series(1.13, index=px.index)
    rec = build_statement_record(inc, bs, px, fx, "EUR", "USD", close_now=20.0, mcap_now=2e9)
    ok(rec["hist_pbr"] == [2.26] * 4, f"USD reporter converted at each year-end ({rec['hist_pbr']})")




def check_cashflow_oneoff() -> list[str]:
    """P/FCF, the shareholder yield and the one-off guard - the US build's
    cases, which are Yahoo's rules and hold for every market."""
    from providers_at import cashflow_fields
    fails: list[str] = []

    def chk(cond, label):
        print(f"  {'OK  ' if cond else 'FAIL'} {label}")
        if not cond:
            fails.append(label)

    print("\n=== cash flow, shareholder yield, one-off guard ===")
    lf = pd.Timestamp("2025-12-31")
    cf = pd.DataFrame({lf: {"Operating Cash Flow": 150e6, "Capital Expenditure": -50e6,
                            "Free Cash Flow": 100e6, "Cash Dividends Paid": -20e6,
                            "Repurchase Of Capital Stock": -30e6,
                            "Issuance Of Capital Stock": 10e6}})
    f = cashflow_fields(cf, lf)
    chk(f == {"lf_fcf": 100e6, "lf_div_paid": 20e6, "lf_buyback": 30e6, "lf_issuance": 10e6},
        "cash-flow rows read as positive amounts")
    chk(all(np.isnan(v) for v in cashflow_fields(cf, pd.Timestamp("2024-12-31")).values()),
        "no column for the filed year -> missing, never zero")

    base = dict(market_cap_local=2e9, fx_now=1.0, currency="X", fin_ccy="X")
    df = pd.DataFrame([
        dict(ticker="CASH", sector="Industrials", lf_fcf=100e6, lf_div_paid=20e6,
             lf_buyback=30e6, lf_issuance=10e6, **base),
        dict(ticker="SBC", sector="Technology", lf_fcf=50e6, lf_div_paid=0.0,
             lf_buyback=40e6, lf_issuance=40e6, **base),
        dict(ticker="BANK", sector="Financial Services", lf_fcf=900e6, lf_div_paid=60e6,
             lf_buyback=0.0, lf_issuance=0.0, **base),
        dict(ticker="BURN", sector="Technology", lf_fcf=-80e6, lf_div_paid=0.0,
             lf_buyback=0.0, lf_issuance=0.0, **base),
    ])
    out, _ = FF.add_cashflow_metrics(df)
    i = out.set_index("ticker")
    chk(i.loc["CASH", "price_to_fcf"] == 20.0 and abs(i.loc["CASH", "sh_yield"] - 2.0) < 1e-9,
        "P/FCF 20, shareholder yield 2% (dividends + buybacks - issuance)")
    chk(i.loc["SBC", "sh_yield"] == 0.0, "buybacks that only offset share grants earn no yield")
    chk(np.isnan(i.loc["BANK", "price_to_fcf"]) and np.isnan(i.loc["BURN", "price_to_fcf"]),
        "no P/FCF for a bank (invariant 6) or a negative free cash flow")

    cfg = ScreenConfig()
    rows = pd.DataFrame([
        dict(ticker=t, sector="Industrials", price_to_book=0.8, ev_to_ebitda=5.0, roe_pct=15.0,
             div_yield=dv, sh_yield=sh, passes=False, avg_discount=0.0)
        for t, dv, sh in (("BUYB", 0.5, 4.0), ("NOCF", 3.0, np.nan), ("DILU", 3.0, -1.0))])
    r, _ = FF.apply_absolute_screen(rows, cfg)
    a = r.set_index("ticker")["abs_passes"]
    chk(bool(a["BUYB"]) and bool(a["NOCF"]) and not bool(a["DILU"]),
        "payout test: buybacks count, no statement falls back to dividends, dilution fails")

    tax = cfg.oneoff_tax_pct / 100.0

    def row(t, ni, rev, opm, pe=10.0, eps=5.0, sector="Technology",
            hist=((100, 100), (100, 100))):
        r = dict(ticker=t, sector=sector, ttm_ni=ni, ttm_op=rev * opm,
                 trailing_pe=pe, trailing_eps=eps)
        for k, (n_, o) in enumerate(hist, 1):
            r[f"np_y{k}"], r[f"op_y{k}"] = n_, o
        return r
    g = pd.DataFrame([
        row("ONEOFF", 2.87e9, 6.77e9, 0.0258, pe=2.5, eps=7.0, hist=((-340, -100), (22, -70))),
        row("PLAIN", 100e6, 1000e6, 0.13 / (1 - tax) * 1.0, pe=15.0),
        row("TRADER", 896e9, 19878e9, 0.029, sector="Industrials",
            hist=((950 * (1 - tax) / 0.75, 630), (960 * (1 - tax) / 0.75, 640))),
        row("BANK", 64.5e9, 190.7e9, 0.10, sector="Financial Services"),
    ])
    o, _ = FF.apply_oneoff_guard(g, cfg)
    j = o.set_index("ticker")
    k = 6.77e9 * 0.0258 * (1 - tax) / 2.87e9
    chk(bool(j.loc["ONEOFF", "oneoff_capped"]) and abs(j.loc["ONEOFF", "trailing_pe"] - 2.5 / k) < 1e-6,
        "one-off: P/E restated on operating profit after tax")
    chk(not bool(j.loc["PLAIN", "oneoff_capped"]) and j.loc["PLAIN", "trailing_pe"] == 15.0,
        "an ordinary company is untouched")
    chk(not bool(j.loc["TRADER", "oneoff_capped"]), "a gap present in every filed year is structural, spared")
    chk(not bool(j.loc["BANK", "oneoff_capped"]), "financials exempt")
    return fails

def main() -> int:
    check_parsers()
    check_roster()
    check_market_cap()
    FAILURES.extend(check_cashflow_oneoff())
    check_oneoff_structural()
    check_pyramids()
    check_currency()
    cfg = ScreenConfig()
    df = make_universe()

    df["market_cap_usd"] = df["market_cap_local"] * USD_PER_EUR
    df = df[df["market_cap_usd"] >= cfg.min_market_cap_usd]
    df = FF.attach_sector(df)
    df, istats = FF.apply_sector_filters(df, cfg, {})
    res, stats = run_screen(df, USD_PER_EUR, cfg)
    res = FF.add_quality_context(res)
    res = FF.add_valueup_flags(res)
    res, _ = FF.apply_roe_gate(res, cfg)
    res, _ = FF.apply_absolute_screen(res, cfg)
    idx = res.set_index("symbol")

    print("\n=== universe hygiene ===")
    print(f"  funnel: {istats}")
    ok("CPI" not in idx.index, "listed landlord excluded (IAS 40 P/E)")
    ok("TINY" not in idx.index, "below the size floor")
    ok(bool(idx.loc["EVN", "is_holdco"]) and "Verbund" in idx.loc["EVN", "holdco_note"],
       "named holding company tagged with what it holds, not dropped")
    ok(not bool(idx.loc["SEM", "is_holdco"]), "Semperit AG Holding is not tagged a holdco")
    ok(bool(idx.loc["TKA", "is_state"]) and "OBAG" in idx.loc["TKA", "state_note"],
       "state holder named")
    ok("Russian" in idx.loc["RBI", "structural_note"], "structural note attached")
    ok(not bool(idx.loc["GOOD", "is_state"]) and idx.loc["GOOD", "structural_note"] == "",
       "no note on a company that has none")

    print("\n=== peers ===")
    ok(idx.loc["GOOD", "trailing_pe_peer_basis"] == "sector",
       "a populated sector benchmarks within itself")
    ok(idx.loc["TKA", "trailing_pe_peer_basis"] == "macro",
       f"a lone sector falls back to the market ({idx.loc['TKA', 'trailing_pe_peer_basis']!r})")
    ok(idx.loc["RBI", "price_to_book_peer_basis"] == "sector",
       "financials hold their own cohort at four peers")
    non_fin = res[~res["sector"].eq("Financial Services")]
    ok(idx.loc["TKA", "trailing_pe_peer_median"] > 12.0,
       "the fallback median excludes the banks' multiples")
    ok(len(non_fin) and non_fin["trailing_pe_peer_median"].notna().sum() >= len(non_fin) - 1,
       "no non-financial with a P/E is left unscored")

    print("\n=== screens ===")
    ok(bool(idx.loc["GOOD", "passes"]), "genuinely cheap name passes the peer screen")
    ok(pd.isna(idx.loc["LOSS", "trailing_pe"]), "P/E of 0 read as missing")
    ok(pd.isna(idx.loc["RBI", "ev_to_ebitda"]), "bank's EV/EBITDA suppressed")
    ok(bool(idx.loc["RBI", "abs_passes"]) and bool(idx.loc["RBI", "abs_via_carveout"]),
       "bank clears the absolute screen via the P/B + ROE carve-out")

    # One line per issuer: Gurktaler's preferred trades more than its ordinary.
    lines = pd.DataFrame([dict(ticker="GAGS.VI", name="Gurktaler AG St", adv_local=4e3,
                               is_class_line=False),
                          dict(ticker="GAGV.VI", name="Gurktaler AG Vz", adv_local=6e3,
                               is_class_line=True)])
    kept, lstats = FF.keep_one_line_per_issuer(lines)
    ok(kept["ticker"].tolist() == ["GAGV.VI"] and lstats["dropped_second_line"] == 1,
       "one line per issuer: the traded line kept, even if it is the preferred")

    check_statements()

    print("\n=== passing ===")
    hits = res[res["passes_any"]][["symbol", "name", "industry", "trailing_pe",
                                   "price_to_book", "roe_pct", "screen"]]
    print(hits.round(2).to_string(index=False) if not hits.empty else "  (none)")
    print("\n" + ("ALL CHECKS PASSED" if not FAILURES else f"FAILURES: {FAILURES}"))
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
