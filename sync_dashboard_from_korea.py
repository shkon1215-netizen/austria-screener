"""Re-derive the Austria dashboard from the Korea build's current dashboard.py.

    python sync_dashboard_from_korea.py ../Korea/dashboard.py

The Austria dashboard is not a fork that drifts: it is Korea's dashboard.py
with a fixed list of Austrian substitutions applied. Most are France's, which
are mostly Germany's (P/E and P/B labels, same-basis per_now/pbr_now for the
own-history screen, the reporting currency in growth tooltips, four filed
years instead of five, the undefined guard in cell(), one page rather than
one per board); the rest are Austrian (Vienna symbol, financials by Yahoo's
sector, state / vs market / structural-note tags, Austrian notes). When Korea
gains a feature, run this.

Every substitution must match exactly once. Anything that no longer matches is
printed and the exit code is 1 - Korea's text moved, and that substitution
needs updating by hand rather than being silently skipped. Afterwards, grep
the result for Korean text, KOSPI, PER/PBR and "ticker" to catch anything new
Korea added that this list does not know about yet, and re-check that the
browser's verdict matches the Python funnel at default thresholds.
"""
import io
import sys

if len(sys.argv) != 2:
    sys.exit("usage: python sync_dashboard_from_korea.py <path to Korea dashboard.py>")
SRC = sys.argv[1]
P = "dashboard.py"
s = io.open(SRC, encoding="utf-8").read()


PAIRS = [
    # ---- module docstring and imports --------------------------------------
    ("Reads the CSV that main_kr.py writes", "Reads the CSV that main_at.py writes"),
    ("re-run main_kr.py to refresh it in place.", "re-run main_at.py to refresh it in place."),
    ("import numpy as np\nimport pandas as pd\n",
     "import numpy as np\nimport pandas as pd\n\n"
     "# Financials by Yahoo's sector, the same test the screen used - the page's\n"
     "# carve-out must agree with Python's or its verdict drifts.\n"
     "from config_at import is_financial\n"),

    # Vienna symbols can lead with a digit (4X0); read them as text.
    ('dtype={"ticker": str})', 'dtype={"ticker": str, "symbol": str, "isin": str})'),

    # ---- funnel + table ----------------------------------------------------
    ('("listings", "Corporate lines", "ETFs, ETNs and funds already removed"),',
     '("listings", "Listed lines", "Wiener Börse company list"),'),
    ('("after_korea_filters", "After share-class hygiene", None),',
     '("after_austrian_filters", "After universe hygiene", None),'),
    ('("cleared_size_liquidity", "Cleared size gate", None),',
     '("cleared_size_liquidity", "Cleared size + liquidity", None),'),
    ('("ticker", "Code", "l"), ("name", "Name", "l"), ("industry", "업종 industry", "l"),',
     '("symbol", "Code", "l"), ("name", "Name", "l"), ("industry", "Industry", "l"),'),
    ('("mcap_musd", "Cap $m", ""), ("trailing_pe", "PER", ""), ("price_to_book", "PBR", ""),',
     '("mcap_musd", "Cap $m", ""), ("trailing_pe", "P/E", ""), ("price_to_book", "P/B", ""),'),
    ('("hist_avg_disc", "vs own 5y", ""),', '("hist_avg_disc", "vs own history", ""),'),
    ('("abs_pbr_ok", "PBR below {abs_max_pbr:g}"),', '("abs_pbr_ok", "P/B below {abs_max_pbr:g}"),'),
    ('("abs_pbr_vs_roe_ok", "PBR below fair value (ROE ÷ {abs_cost_of_equity_pct:g}% CoE)"),',
     '("abs_pbr_vs_roe_ok", "P/B below fair value (ROE ÷ {abs_cost_of_equity_pct:g}% CoE)"),'),

    # ---- row payload -------------------------------------------------------
    ('            "ticker": str(r.get("ticker", "")),\n',
     '            # The Vienna symbol, not the Yahoo one: ANDR is what a reader\n'
     '            # looks up, ANDR.VI is a vendor detail. This key must stay in step\n'
     '            # with TABLE_COLS - see the guard in cell().\n'
     '            "symbol": str(r.get("symbol", "") or r.get("ticker", "")),\n'),
    # The segments are the boards (prime, standard, direct, abroad), so Korea's
    # board field and filter are kept as they are.
    ('            "fin": bool(str(r.get("sector", "") or "").lower().find("financial") >= 0),',
     '            "fin": bool(is_financial(r.get("sector", "") or "", r.get("industry", "") or "")),\n'
     '            # Closely held: insiders and strategic holders own a majority\n'
     '            # (Yahoo\'s figure) - see at_filters.apply_control. A flag.\n'
     '            "ctrl": "" if pd.isna(r.get("ctrl_pct")) or r.get("is_controlled") != True else\n'
     '                    f"{float(r.get(\'ctrl_pct\')):.0f}%",\n'
     '            # What a named holding company holds - config_at.KNOWN_HOLDCOS.\n'
     '            "hold": "" if pd.isna(r.get("holdco_note")) else str(r.get("holdco_note") or ""),\n'
     '            # The public-sector holder, named - config_at.STATE_HOLDERS.\n'
     '            "state": "" if pd.isna(r.get("state_note")) else str(r.get("state_note") or ""),\n'
     '            # A standing discount no multiple shows - config_at.STRUCTURAL_NOTES.\n'
     '            "note": "" if pd.isna(r.get("structural_note")) else str(r.get("structural_note") or ""),\n'
     '            # Benchmarked against the rest of the market rather than its own\n'
     '            # sector, on at least one metric - see config_at.macro_of.\n'
     '            "vsmkt": any(r.get(f"{m}_peer_basis") == "macro" for m in\n'
     '                         ("trailing_pe", "price_to_book", "ev_to_ebitda", "price_to_fcf")),\n'
     '            # The listed parent that consolidates this company -\n'
     '            # at_filters.flag_pyramids.\n'
     '            "pyr": "" if pd.isna(r.get("pyramid_child_of")) else str(r.get("pyramid_child_of") or ""),\n'
     '            # What the currency repair did to this row, if anything - see\n'
     '            # at_filters.repair_foreign_reporters.\n'
     '            "fxn": "" if pd.isna(r.get("fx_note")) else str(r.get("fx_note") or ""),\n'
     '            # Trailing profit against a filed loss - see at_filters.flag_ttm_vs_filed.\n'
     '            "ttmx": bool(r.get("ttm_vs_filed_loss") == True),  # noqa: E712'),
    ('            "evx_now": _f(r.get("evx_now"), 6),\n',
     '            "evx_now": _f(r.get("evx_now"), 6),\n'
     '            # Today\'s P/E and P/B on the SAME basis as the history (market\n'
     '            # value over the latest filing), which is not the basis of the\n'
     '            # trailing_pe/price_to_book columns - see add_history_now.\n'
     '            # These are what the history screen thresholds against, so\n'
     '            # they carry full precision like the multiples above.\n'
     '            "per_now": _f(r.get("per_now"), 6),\n'
     '            "pbr_now": _f(r.get("pbr_now"), 6),\n'
     '            # The reporting currency the 3-year figures are in. Not the quote\n'
     '            # currency, which can differ from the quote currency.\n'
     '            "fin_ccy": str(r.get("fin_ccy", "") or ""),\n'),
    ('            # Three-year history, oldest first, in 억원. The yearly values',
     '            # Three-year history, oldest first, in millions of the REPORTING\n'
     '            # currency (fin_ccy). The yearly values'),
    ('            # Own five-year history. The medians and today\'s values let the',
     '            # Own filed history. The medians and today\'s values let the'),

    # ---- drop labels -------------------------------------------------------
    ('''    for key, label in [("dropped_preferred", "우선주 preferred"),
                       ("dropped_reit", "리츠 REIT"),
                       ("dropped_spac", "스팩 SPAC")]:''',
     '''    for key, label in [("dropped_global_market", "global-market foreign lines"),
                       ("dropped_fund_line", "fund lines"),
                       ("dropped_foreign_secondary", "foreign issuers on Vienna's segments"),
                       ("dropped_property", "listed landlords"),
                       ("dropped_second_line", "second share-class lines"),
                       ("dropped_pyramid_parent", "parents consolidating a listed subsidiary"),
                       ("dropped_state", "public-sector holders"),
                       ("dropped_controlled", "closely held")]:'''),

    # ---- boards: one page ----------------------------------------------------
    ('''BOARD_FILES = {"KOSPI": "kr_dashboard.html",
               "KOSDAQ": "kq_dashboard.html",
               "BOTH": "krkq_dashboard.html"}''',
     '''# Austria runs as ONE screen: about 25 names survive the gates, too few to
# split across segments.
BOARD_FILES = {"MAIN": "at_dashboard.html"}'''),
    ('''# its own. KOSPI keeps the original name - renaming a published artifact makes
# it unrecognisable to anyone who bookmarked it.
BOARD_TITLES = {"KOSDAQ": "KOSDAQ Discount Screen"}''',
     '''# its own. One page here, so nothing to retitle.
BOARD_TITLES = {}'''),

    # ---- FX field ----------------------------------------------------------
    ('"krw_per_usd": meta.get("krw_per_usd"),', '"usd_per_eur": meta.get("usd_per_eur"),\n'
     '            "roster_asof": meta.get("roster_asof", ""),'),

    # ---- titles ------------------------------------------------------------
    ('head.replace("<title>Korea Discount Screen</title>",',
     'head.replace("<title>Austria Discount Screen</title>",'),
    ('body.replace("<h1>Korea Discount Screen</h1>",', 'body.replace("<h1>Austria Discount Screen</h1>",'),
    ('_HEAD = """<title>Korea Discount Screen</title>', '_HEAD = """<title>Austria Discount Screen</title>'),
    ('<p class="eyebrow">KRX relative valuation</p>', '<p class="eyebrow">Wiener Börse relative valuation</p>'),
    ('<h1>Korea Discount Screen</h1>', '<h1>Austria Discount Screen</h1>'),

    # ---- fonts and line breaking -------------------------------------------
    # IBM Plex Sans covers Latin-1, so ö, ü, ß render in the face.
    ('family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans+KR:wght@300;400;500;600;700&display=swap',
     'family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@300;400;500;600;700&display=swap'),
    ('--sans:"IBM Plex Sans KR", system-ui, -apple-system, "Segoe UI", "Malgun Gothic", sans-serif;',
     '--sans:"IBM Plex Sans", system-ui, -apple-system, "Segoe UI", Helvetica, Arial, sans-serif;'),
    ('''/* Korean breaks at any character by default, so 현대지에프홀딩스 shatters across
   four lines in a narrow column. keep-all breaks at word boundaries instead. */''',
     '''/* Austrian names break at spaces first and mid-word only when a single word
   is wider than its column - keep-all would push it out of the table. */'''),
    ("  word-break:keep-all}", "  word-break:normal;overflow-wrap:anywhere}"),

    # ---- commands / search / filters ---------------------------------------
    ('<code id="cmd">python main_kr.py</code>', '<code id="cmd">python main_at.py</code>'),
    ('placeholder="name, code or 업종"', 'placeholder="name, code or industry"'),
    ('$("cmd").textContent = M.cmd || ("python main_kr.py --board "',
     '$("cmd").textContent = M.cmd || ("python main_at.py --board "'),
    ('    <label class="toggle"><input type="checkbox" id="nohold"> Hide holdcos</label>',
     '    <label class="toggle"><input type="checkbox" id="nohold"> Hide holdcos</label>\n'
     '    <label class="toggle"><input type="checkbox" id="nostate"> Hide closely held</label>'),
    ('  const onlyPass = $("onlypass").checked, noHold = $("nohold").checked;',
     '  const onlyPass = $("onlypass").checked, noHold = $("nohold").checked;\n'
     '  const noState = $("nostate").checked;'),
    ('    if (noHold && r.holdco) return false;',
     '    if (noHold && r.holdco) return false;\n'
     '    if (noState && r.ctrl) return false;'),
    ('["q","brd","scr","gmode","onlypass","nohold"].forEach(id =>',
     '["q","brd","scr","gmode","onlypass","nohold","nostate"].forEach(id =>'),

    # ---- history panel, selector and control labels ------------------------
    ('<h2>Cheap vs its own 5 years</h2>', '<h2>Cheap vs its own history</h2>'),
    ('<span class="hint">median of filed years</span>',
     '<span class="hint">median of 4 filed years</span>'),
    ('<option value="history">Cheap vs own 5y</option>',
     '<option value="history">Cheap vs own history</option>'),
    ('<div class="tg"><label for="t_hdisc">Below own 5y by at least %</label>',
     '<div class="tg"><label for="t_hdisc">Below own history by at least %</label>'),

    # ---- threshold controls ------------------------------------------------
    ('<div class="tg"><label for="t_pbr">PBR below</label>',
     '<div class="tg"><label for="t_pbr">P/B below</label>'),
    ('<div class="tg"><label for="t_per">PER below</label>',
     '<div class="tg"><label for="t_per">P/E below</label>'),
    ('id="t_fair"> Require PBR below fair value', 'id="t_fair"> Require P/B below fair value'),
    ('id="t_carve"> Financials qualify on PBR + ROE', 'id="t_carve"> Financials qualify on P/B + ROE'),
    ('tests.push(["PBR below " + T.pbr,', 'tests.push(["P/B below " + T.pbr,'),
    ('tests.push(["PER below " + T.per,', 'tests.push(["P/E below " + T.per,'),
    ('tests.push([`PBR below fair value (ROE ÷ ${T.coe}% CoE)`,',
     'tests.push([`P/B below fair value (ROE ÷ ${T.coe}% CoE)`,'),
    ('financials qualified on PBR and ROE ', 'financials qualified on P/B and ROE '),
    ('${hist.length} vs own 5y`},', '${hist.length} vs own history`},'),

    # ---- chips -------------------------------------------------------------
    ('["Source", M.source === "naver" ? "KIND + Naver" : "KRX"],',
     '["Source", "Wiener Börse + Yahoo"],\n  ["Roster as at", M.roster_asof || "?"],'),
    ('["USD/KRW", M.krw_per_usd],', '["USD per EUR", M.usd_per_eur],'),

    # ---- interpretation copy -----------------------------------------------
    ('''    <p><b>Cheap vs its own five years</b> compares today's PER, PBR and EV/EBITDA
    with the median of the company's last five filed years. It catches what the
    other two miss - a company that always traded at a premium and has just
    de-rated. Loss years drop out of the benchmark rather than dragging it, and
    fewer than three usable years means no benchmark at all. <b>One caution:</b>
    these are trailing multiples, so when earnings are surging the latest filing
    lags the price and a stock reads <i>expensive</i> against its history until
    the next filing catches up. A one-off gain does the opposite.</p>''',
     '''    <p><b>Cheap vs its own history</b> compares today's P/E, P/B and EV/EBITDA
    with the median of the company's last four filed years - four, not Korea's
    five, because that is all Yahoo holds for Austrian companies. It catches what
    the other two miss: a company that always traded at a premium and has just
    de-rated. Loss years drop out of the benchmark rather than dragging it, and
    fewer than three usable years means no benchmark at all.</p>
    <p><b>Today's multiples in that column are not the ones in the P/E and P/B
    columns.</b> Each past year is that year-end market value over that year's
    filed accounts, so today is measured the same way: today's market value over
    the latest filed year, on Yahoo's normalized earnings. The P/E column uses
    the last twelve months instead; comparing across the two would report the
    gap between two definitions as a discount. <b>One caution:</b> when earnings
    are rising, the latest filing lags the price and a stock reads
    <i>expensive</i> against its history until the next filing catches up.</p>'''),
    ('''    own 5 years</b> asks whether it is cheap against itself. Korea needs all
    three:''',
     '''    own history</b> asks whether it is cheap against itself. Austria needs all
    three:'''),
    ('''how far below book it traded. Those names clear the absolute screen on PBR and
    ROE alone and are marked <span class="tag">pbr+roe</span>.</p>''',
     '''how far below book it traded. Those names clear the absolute screen on P/B and
    ROE alone and are marked <span class="tag">pbr+roe</span>.</p>'''),
    ('''<p><b>Low PBR with low ROE is not a discount.</b> It is a company not earning
    its cost of capital, priced accordingly. Much of what gets called the Korea
    Discount is this.''',
     '''<p><b>Low P/B with low ROE is not a discount.</b> It is a company not earning
    its cost of capital, priced accordingly. Much of what trades below book in
    Vienna - Wienerberger, Lenzing, Mayr-Melnhof - is this.'''),
    ('''<p><b>업종 files holding companies under 기타 금융업.</b> That pools operating
    holdcos with bank holdcos in one peer group, and suppresses EV/EBITDA for
    both — enterprise value is meaningless for a bank, but not for an operating
    company. Holdcos are tagged so you can see which rows this touches.</p>''',
     '''<p><b>Vienna is a small market, and peers are the hard part.</b> About 25
    names survive the gates, across eight of Yahoo's sectors. Only Industrials
    and Financials hold enough for a sector median. Everyone else is compared
    with the rest of the market on its side of the financial line, and carries
    a <span class="tag">vs market</span> tag: OMV's benchmark there is not a
    set of oil companies, so read that discount as cheap against Vienna, not
    against its industry.</p>
    <p><b>Liquidity runs lower here than in any other market on this list.</b>
    The floor is USD 250k a day on Vienna's own order book, which sits in the
    gap between Vienna's traded names and its near-untraded ones. Telekom
    Austria, a USD 6bn company, trades about USD 500k. Below the floor go
    Flughafen Wien, Agrana, AMAG, Oberbank and BTV: real companies whose free
    float barely trades, so their prices are not much of a market's verdict.</p>
    <p><b>What is taken out first.</b> Foreign shares on the global market, fund
    lines, RHI Magnesita (home market London), and listed landlords (CA Immo,
    CPI Europe), whose IAS 40 revaluations make the P/E an appraisal. Kontron,
    Fabasoft and ams-OSRAM are Austrian companies with their real market abroad,
    so they stay and are measured there: the <i>ABROAD</i> board.</p>
    <p><b>Public shareholders are named.</b> A <span class="tag">state</span>
    tag marks a company with a federal, provincial or city holder, approximate
    and listed by hand; hover it. <span class="tag">close</span> means insiders
    and strategic holders own a majority by Yahoo's count, which says the free
    float is the minority, not who controls, and it misses Verbund.</p>
    <p><b>A <span class="tag">note</span> tag is a discount no multiple
    shows.</b> Raiffeisen's Russian subsidiary and the frozen Rasperia stake in
    Strabag are the two today. They are as last checked by hand, so confirm
    the current position before relying on one.</p>
    <p><b>EVN is tagged <span class="tag">holdco</span></b> because its Verbund
    stake is a large share of its market value. It is an operating utility, but
    its P/B says as much about Verbund's share price as about its own.</p>
    <p><b>A <span class="tag">ttm vs fy</span> tag means read the P/E twice.</b>
    The P/E and ROE columns are Yahoo's trailing twelve months, which sum the
    last four quarters one-offs and all. A tagged name was profitable on that
    basis but lost money in its last filed year.</p>'''),

    # ---- JS: history reads same-basis values -------------------------------
    ('  const cur = {per: r.trailing_pe, pbr: r.price_to_book, evx: r.evx_now};',
     '  const cur = {per: r.per_now, pbr: r.pbr_now, evx: r.evx_now};'),
    ('  const now = {per: r.trailing_pe, pbr: r.price_to_book, evx: r.evx_now};',
     '  const now = {per: r.per_now, pbr: r.pbr_now, evx: r.evx_now};'),
    ('''  const passTag = r.ev.hist ? ' <span class="tag">5y low</span>' : "";''',
     '''  const passTag = r.ev.hist ? ' <span class="tag">hist low</span>' : "";'''),
    # Yahoo has four filed years for Austrian names, so the fifth history slot is
    # null with no year label. Show only the years that exist.
    ('    const ser = (r.h_ser && r.h_ser[k] || []).map((v, i) =>',
     '    const ser = (r.h_ser && r.h_ser[k] || []).slice(0, yrs.length).map((v, i) =>'),
    ('  // Own five-year history. Mirrors korea_filters.apply_history_screen: the',
     '  // Own filed history. Mirrors at_filters.apply_history_screen: the'),
    ('/* Today\'s value against the five-year median, per metric.',
     '/* Today\'s value against the filed-year median, per metric.'),
    ('/* Average discount to the company\'s own five-year median, across every metric',
     '/* Average discount to the company\'s own filed-year median, across every metric'),

    # ---- JS: growth tooltip names the reporting currency -------------------
    ('  const tip = GROWTH_LABEL[key] + " (억원)\\\\n"',
     '  const tip = GROWTH_LABEL[key] + " (" + (r.fin_ccy || "reporting ccy") + " m)\\\\n"'),

    # ---- JS: symbol, tags, and the guard against one bad key ---------------
    ('''function cell(r, k) {
  const v = r[k];
  if (k === "ticker") return `<span style="color:var(--ink-3)">${esc(v)}</span>`;''',
     '''function cell(r, k) {
  const v = r[k];
  /* A key present in TABLE_COLS but absent from the row payload arrives as
     undefined, which slipped past the null guard and hit .toFixed() in the UK
     build - one renamed column left the whole table empty. Missing reads as
     missing. Computed columns read other fields and are exempt. */
  if (v === undefined && !(k in GROWTH) && k !== "hist_avg_disc"
      && k !== "screen" && k !== "name") return '<span class="na">—</span>';
  if (k === "symbol") return `<span style="color:var(--ink-3)">${esc(v)}</span>`;'''),
    ('''    const tags = (r.holdco ? '<span class="tag">holdco</span>' : "")''',
     '''    const tags = (r.state ? `<span class="tag" title="Public shareholder: ${esc(r.state)}">state</span>` : "")
               + (r.ctrl ? `<span class="tag" title="Closely held: insiders and strategic holders own ${esc(r.ctrl)} (Yahoo)">close</span>` : "")
               + (r.note ? `<span class="tag" title="${esc(r.note)}">note</span>` : "")
               + (r.vsmkt ? '<span class="tag" title="Too few peers in its Yahoo sector: benchmarked against the rest of the market on its side of the financial line">vs market</span>' : "")
               + (r.pyr ? `<span class="tag" title="Consolidated by a listed parent: ${esc(r.pyr)}">listed parent</span>` : "")
               + (r.fxn ? `<span class="tag" title="Reports in ${esc(r.fin_ccy)}, quotes in EUR: ${esc(r.fxn)}">fx</span>` : "")
               + (r.ttmx ? '<span class="tag" title="Profitable over the trailing twelve months, loss-making in the last filed year: the trailing P/E and ROE likely carry one-offs">ttm vs fy</span>' : "")
               + (r.holdco ? `<span class="tag" title="${esc(r.hold || 'Holding company')}">holdco</span>` : "")'''),
    ('r.name.toLowerCase().includes(q) || r.ticker.includes(q)',
     'r.name.toLowerCase().includes(q) || (r.symbol || "").toLowerCase().includes(q)'),

    # ---- storage key and comments ------------------------------------------
    ('const STORE = "kr-thresholds-" + (M.board || "x");',
     'const STORE = "at-thresholds-" + (M.board || "x");'),
    ('/* One row against the current thresholds. Mirrors korea_filters.apply_roe_gate',
     '/* One row against the current thresholds. Mirrors at_filters.apply_roe_gate'),
    ('''   Only serve.py can actually re-run the screen: it shells out to main_kr.py,
   which scrapes KIND and Naver. A page opened straight off disk, or published''',
     '''   Only serve.py can actually re-run the screen: it shells out to main_at.py,
   which reads Wiener Boerse's list and Yahoo. A page opened straight off
   disk, or published'''),
]

# Labels that appear more than once, replaced everywhere.
ALL = [
    ('const lab = {per: "PER", pbr: "PBR", evx: "EV/EBITDA"};',
     'const lab = {per: "P/E", pbr: "P/B", evx: "EV/EBITDA"};'),
]

missed = []
for old, new in PAIRS:
    if old in s:
        s = s.replace(old, new, 1)
    else:
        missed.append(old[:72])
for old, new in ALL:
    n = s.count(old)
    if not n:
        missed.append(old[:72])
    s = s.replace(old, new)

io.open(P, "w", encoding="utf-8").write(s)
print(f"applied {len(PAIRS) + len(ALL) - len(missed)}/{len(PAIRS) + len(ALL)}")
for m in missed:
    print("  MISS:", m)
sys.exit(1 if missed else 0)
