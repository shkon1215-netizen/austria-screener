"""Configuration for the Austria (Wiener Boerse) valuation screener.

Ninth market after Korea, the UK, Japan, Germany, Poland, France, Hong Kong
and the US, built on France's copy: same currency, same vendor, and France had
already combined what the others learned. The quality floor, the discount
test and the history screen are the user's screening preferences and are
carried over unchanged. What is local:

  * the universe - 779 lines on the exchange's list, 685 of them on the
    "global market", the MTF for foreign shares. Austria is its 73 Austrian lines, of
    which three have their real market abroad (ABROAD_LINES)
  * thin cohorts - about 25 names survive the gates across eight Yahoo
    sectors, so a sector alone rarely reaches five peers. Peers are the
    sector, falling back to the rest of the market on the same side of the
    financial / non-financial line. See `macro_of`
  * liquidity - Vienna trades in a band Warsaw and Paris do not: Telekom
    Austria, a EUR 5.6bn company, does about EUR 0.4m a day. The gate is
    measured below, and Wiener Boerse's own turnover is double-counted
  * ownership - the state stakes are few and public, so a named list gives
    Austria the state flag France could not have
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# P/FCF is the fourth: market value over the last filed free cash flow
# (add_cashflow_metrics). The relative test is unchanged - 20% below
# peers on at least two of the metrics a company has.
VALUATION_METRICS = ("trailing_pe", "price_to_book", "ev_to_ebitda", "price_to_fcf")

METRIC_LABELS = {
    "trailing_pe": "P/E",
    "price_to_book": "P/B",
    "ev_to_ebitda": "EV/EBITDA",
    "price_to_fcf": "P/FCF",
}

# Same reasoning as Korea: a zero or negative multiple means "no earnings" or
# "negative equity", never "cheap". Agrana's trailing P/E reads 1,145 on an EPS
# rounded to 0.01 - the upper bound is what removes it.
METRIC_BOUNDS = {
    "trailing_pe": (1.0, 200.0),
    "price_to_book": (0.05, 30.0),
    "ev_to_ebitda": (0.5, 100.0),
    # P/E's bounds: a free cash flow is an earnings-like flow.
    "price_to_fcf": (1.0, 200.0),
}

# ---------------------------------------------------------------------------
# Wiener Boerse's market segments
# ---------------------------------------------------------------------------
# The exchange's company list names each line's segment. Prime, standard
# continuous and standard auction are the Official Market; direct market and
# direct market plus are the Vienna MTF; the global market is the MTF on which
# foreign shares are traded in Vienna (Siemens Energy, Novo Nordisk), never a
# home market. Their price pages carry the link to each stock's page (and so
# its symbol) and a market cap.
BOARDS = {
    "prime market": "PRIME",
    "standard market continuous": "STANDARD",
    "standard market auction": "STANDARD",
    "direct market plus": "DIRECT",
    "direct market": "DIRECT",
}
GLOBAL_SEGMENT = "global market"
SEGMENT_PAGES = ("stocks-prime-market", "stocks-standard-market",
                 "stocks-direct-market-plus", "stocks-direct-market")
HOME_COUNTRY = "Austria"
HOME_ISIN_PREFIX = "AT"
# Security types that are not a company's shares: two Robeco funds on the
# auction segment, the Guernsey and Maltese fund lines on the direct market.
FUND_TYPES = ("ucits share", "investment certificate", "trust certificate")

# Austrian companies whose market is elsewhere. Vienna has them on the global
# market, like any foreign share, and their Vienna volume is a rounding error
# (Kontron 1,400 shares a day against 56,000 in Frankfurt; ams-OSRAM 5,700
# against 470,000 in Zurich). They are Austrian companies, and leaving them out
# of an Austrian screen would lose two of about 25 names, so each is read on
# its real market: ISIN -> (symbol shown, Yahoo line for fundamentals, Yahoo
# line for liquidity, that line's currency, venue).
#
# ams-OSRAM's fundamentals stay on the Vienna line: it quotes in euros, like
# the company's accounts, where Zurich quotes in francs. Its volume is Zurich's.
ABROAD_LINES = {
    "AT0000A0E9W5": ("KTN", "KTN.DE", "KTN.DE", "EUR", "Frankfurt"),
    "AT0000785407": ("FAA", "FAA.DE", "FAA.DE", "EUR", "Frankfurt"),
    "AT0000A3EPA4": ("AMS", "AMS2.VI", "AMS.SW", "CHF", "Zurich"),
}
BOARD_ABROAD = "ABROAD"

# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------
# Wiener Boerse publishes a sector scheme (10 industries, 41 sectors) but not
# the per-company mapping outside its licensed index area, so peers are Yahoo's,
# as in the UK and Hong Kong.
#
# Yahoo's sector alone is too thin here: on 2026-10-30 the 25 survivors split
# into Industrials 7, Financials 5, Technology 4, Consumer Cyclical 3,
# Basic Materials 2, Utilities 2, Energy 1, Communication 1. Only Industrials
# reaches five peers. So a thin sector falls back to the market on its side of
# one line: financials against financials, everyone else against the other
# non-financials. A crude benchmark for OMV or Telekom Austria, and the page
# shows which basis each metric used - but Poland's way, leaving them unscored,
# would blank most of the market's largest names.
FINANCIAL_SECTORS = ("Financial Services",)
PROPERTY_SECTORS = ("Real Estate",)

# Listed landlords, the Germany rule: IAS 40 runs revaluations through
# earnings, so CPI Europe's P/E of 4.5 at 0.46x book is an appraiser's year.

# Share classes. Wiener Boerse's list has Gurktaler's ordinary and preferred
# lines and Austriacard's temporary "Verkauf" (sale) line under one issuer
# name. Germany's rule applies: one line per issuer, the most traded.
CLASS_SUBTYPES = ("preferred",)
# Words dropped from names before lines are grouped by issuer.
CLASS_WORDS = {"AG", "SE", "ST", "VZ", "KAT", "A", "NV", "N", "V", "VERKAUF"}

# ---------------------------------------------------------------------------
# Holding companies and structural notes - flags, never silent
# ---------------------------------------------------------------------------
# By ISIN, as in France and Hong Kong. NOT by name: Semperit AG Holding,
# Polytec Holding, Frauenthal Holding and Austriacard Holdings are all
# operating companies, so a name token would tag the wrong ones.
KNOWN_HOLDCOS = {
    "AT0000640552": "Burgenland Holding (stake in Burgenland Energie; Verbund group)",
    "AT0000741053": "EVN (operating utility, but its Verbund stake is a large share of "
                    "its market value)",
}

# Public-sector shareholders, named because no free feed carries them. The
# federal stakes are the Republic's, held through OBAG (Verbund's is managed
# by OBAG for the finance ministry); the percentages are from a parliamentary
# paper and were not re-confirmed for 2026, so they are shown as approximate.
STATE_HOLDERS = {
    "AT0000APOST4": "Republic of Austria via OBAG, ~53%",
    "AT0000743059": "Republic of Austria via OBAG, ~31.5%",
    "AT0000720008": "Republic of Austria via OBAG, ~28%",
    "AT0000746409": "Republic of Austria, ~51%",
    "AT0000741053": "Province of Lower Austria, ~51%",
    "AT00000VIE62": "Province of Lower Austria and City of Vienna, ~40% together",
}

# A standing discount no multiple shows. Dated on purpose: these are the state
# of play as last checked, and each one will eventually be stale.
STRUCTURAL_NOTES = {
    "AT0000606306": "Russian subsidiary still held as of the last check: part of group "
                    "profit and capital cannot be extracted",
    "AT000000STR1": "Rasperia's ~24% stake is frozen under EU sanctions; legal disputes "
                    "with Russian courts continue",
}

# A parent that consolidates a listed subsidiary - France's test, unchanged.
PYRAMID_REVENUE_TOL = 0.01
PYRAMID_OP_TOL = 0.05
PYRAMID_MIN_MI_SHARE = 0.25
PYRAMID_MI_GAP = 0.15

# Closely held: Yahoo's heldPercentInsiders at a majority. Yahoo counts every
# strategic holder in it, so this says the free float is the minority, not who
# controls. Coarse here too: OMV reads 56% (OBAG + ADNOC), while Verbund reads
# 30% although the Republic alone holds a majority.
CONTROL_MIN_INSIDERS = 0.50


@dataclass
class ScreenConfig:
    # --- Size / liquidity, specified in USD then converted at live FX ---
    min_market_cap_usd: float = 600_000_000
    # Measured, not inherited - see CLAUDE.md "The liquidity gate". Median
    # traded value on Vienna's order book (Yahoo's .VI volume, Cboe and
    # Turquoise not in it). The names fall into two groups with a gap between
    # them, and this sits in the gap.
    min_adv_usd: float = 250_000
    adv_lookback_days: int = 60                 # trading days

    # --- Valuation test ---
    discount_threshold: float = 0.20
    metrics: tuple[str, ...] = VALUATION_METRICS
    min_metrics_passing: int = 2
    min_valid_metrics: int = 2

    # --- Quality floor ---
    min_roe_pct: float = 5.0
    roe_good_pct: float = 10.0

    # --- Absolute value screen ---
    abs_max_pbr: float = 1.0
    abs_max_ev_ebitda: float = 8.0
    abs_require_roe: bool = True
    abs_financials_pbr_only: bool = True
    abs_require_pbr_vs_roe: bool = True
    abs_cost_of_equity_pct: float = 10.0
    # The user's 2% payout floor, now on the SHAREHOLDER yield (dividends +
    # buybacks - issuance); the dividend yield where no cash flow was filed.
    abs_min_div_yield: float = 2.0

    # --- One-off guard (apply_oneoff_guard) ---
    oneoff_guard: bool = True
    # Trailing net income above this multiple of after-tax operating profit
    # is treated as below-the-line. Ordinary companies measure 1.0-1.2.
    oneoff_ratio: float = 1.5
    # Korperschaftsteuer, 23% since 2024.
    oneoff_tax_pct: float = 23.0

    # --- Own-history screen ---
    hist_min_discount: float = 0.30
    hist_min_metrics: int = 2
    hist_min_years: int = 3
    hist_require_roe: bool = True

    # --- Peer groups ---
    # sector = Yahoo's sector; macro = financial / non-financial (macro_of).
    peer_keys: tuple[str, ...] = ("sector",)
    fallback_peer_keys: tuple[str, ...] = ("macro",)
    # Four, not five, and only because of the financials: five names pass the
    # gates (Erste, BAWAG, RBI, VIG, Uniqa), so each has four peers, and at
    # five the whole sector would go unscored. Nothing else changes - see
    # CLAUDE.md "Thin cohorts".
    min_peers: int = 4
    winsor_pct: float = 0.05

    # --- Austria-specific universe hygiene ---
    exclude_property: bool = True           # CA Immo, CPI Europe, UBM
    exclude_secondary: bool = True          # RHI Magnesita (London) and foreign lines
    exclude_pyramid_parents: bool = True
    flag_holdcos: bool = True
    exclude_holdcos: bool = False           # flagged by default, not dropped
    exclude_controlled: bool = False
    exclude_state: bool = False

    exclude_sectors: tuple[str, ...] = ()

    # --- Fetching ---
    max_workers: int = 2
    request_delay: float = 0.25
    cache_dir: str = ".at_cache"
    cache_ttl_hours: int = 20


# ---------------------------------------------------------------------------
# Detection helpers
# ---------------------------------------------------------------------------
def plain(s: str) -> str:
    """Upper-case, accents stripped, punctuation to spaces."""
    import unicodedata
    s = str(s or "").replace("ß", "ss").replace("ä", "ae").replace("ö", "oe") \
        .replace("ü", "ue").replace("Ä", "Ae").replace("Ö", "Oe").replace("Ü", "Ue")
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return " ".join(re.sub(r"[^A-Z0-9]+", " ", s.upper()).split())


def issuer_key(name: str) -> str:
    """Groups the listed lines of one issuer: 'Gurktaler AG St' and 'Gurktaler
    AG Vz', 'AUSTRIACARD HOLDINGS AG' and 'AUSTRIACARD HOLDINGS VERKAUF'.
    Punctuation goes before class words, Germany's Draegerwerk lesson."""
    toks = [t for t in plain(name).split() if t not in CLASS_WORDS]
    return " ".join(toks[:2])


def board_of(segment: str) -> str:
    """'PRIME' / 'STANDARD' / 'DIRECT' from the exchange's segment; '' for the
    global market and anything it adds later."""
    return BOARDS.get(str(segment or "").strip().lower(), "")


def is_fund(sec_type: str) -> bool:
    return str(sec_type or "").strip().lower() in FUND_TYPES


def is_class_line(sec_type: str) -> bool:
    st = str(sec_type or "").lower()
    return any(t in st for t in CLASS_SUBTYPES)


def is_financial(sector: str = "", industry: str = "", icb: str = "") -> bool:
    """Yahoo's sector. Real estate is its own sector, so it needs no carve-out.
    `industry` and `icb` keep the signature the dashboard and screener call."""
    return str(sector).strip() in FINANCIAL_SECTORS


def is_property(sector: str) -> bool:
    return str(sector).strip() in PROPERTY_SECTORS


def macro_of(sector: str) -> str:
    """The fallback peer group: one line through the market. '' for a company
    with no sector, which then has no cohort rather than a guessed one."""
    s = str(sector or "").strip()
    if not s or s.lower() == "nan":
        return ""
    return "Financials" if is_financial(s) else "Non-financials"


def is_holdco(name: str, isin: str = "") -> bool:
    return str(isin) in KNOWN_HOLDCOS
