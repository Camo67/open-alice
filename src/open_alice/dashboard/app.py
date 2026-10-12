"""Flask web dashboard for Alice (lazy Flask import so CLI works without it)."""

from __future__ import annotations

from typing import Any

INDEX_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Alice Trading Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
  :root { --bg:#0d1117; --panel:#161b22; --line:#30363d; --txt:#e6edf3;
          --green:#3fb950; --red:#f85149; --blue:#58a6ff; --amber:#d29922; }
  * { box-sizing:border-box; }
  body { margin:0; background:var(--bg); color:var(--txt);
         font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif; }
  header { display:flex; align-items:center; gap:12px; padding:14px 20px;
           border-bottom:1px solid var(--line); }
  header h1 { font-size:18px; margin:0; }
  .badge { padding:3px 10px; border-radius:20px; font-size:12px; font-weight:600; }
  .off { background:#3a2a2a; color:var(--red); }
  .on { background:#1a3a25; color:var(--green); }
  main { max-width:1100px; margin:0 auto; padding:20px; display:grid; gap:16px; }
  .card { background:var(--panel); border:1px solid var(--line); border-radius:8px;
          padding:16px; }
  .card h2 { margin:0 0 12px; font-size:14px; text-transform:uppercase;
             letter-spacing:.06em; color:#8b949e; }
  .row { display:flex; gap:10px; flex-wrap:wrap; align-items:end; }
  label { font-size:12px; color:#8b949e; display:block; margin-bottom:4px; }
  input,select,button { background:#0d1117; color:var(--txt); border:1px solid var(--line);
                        border-radius:6px; padding:8px 10px; font-size:14px; }
  button { background:#1f6feb; border-color:#1f6feb; cursor:pointer; font-weight:600; }
  button:hover { background:#388bfd; }
  button.danger { background:#6e1515; border-color:#6e1515; }
  .metrics { display:grid; grid-template-columns:repeat(auto-fit,minmax(130px,1fr));
             gap:10px; margin-top:12px; }
  .metric { background:#0d1117; border:1px solid var(--line); border-radius:6px;
            padding:10px; }
  .metric .k { font-size:11px; color:#8b949e; }
  .metric .v { font-size:18px; font-weight:700; margin-top:2px; }
  .pos { color:var(--green); } .neg { color:var(--red); }
  table { width:100%; border-collapse:collapse; font-size:13px; }
  th,td { text-align:right; padding:6px 8px; border-bottom:1px solid var(--line); }
  th:first-child,td:first-child { text-align:left; }
  th { color:#8b949e; font-weight:600; }
  canvas { max-height:340px; }
  #msg { min-height:20px; font-size:13px; margin-top:8px; }
</style>
</head>
<body>
<header>
  <h1>Alice Trading Dashboard</h1>
  <span id="conn" class="badge off">disconnected</span>
  <span id="acct" style="font-size:13px;color:#8b949e"></span>
</header>
<main>
  <div class="card">
    <h2>Analysis</h2>
    <div class="row">
      <div><label>Symbol</label><input id="symbol" value="AAPL" size="10"></div>
      <div><label>Strategy</label><select id="strategy">
        <option value="sma_crossover">SMA Crossover</option>
        <option value="rsi">RSI</option>
        <option value="macd">MACD</option>
        <option value="bollinger">Bollinger</option>
      </select></div>
      <div><label>Source</label><select id="source">
        <option value="yahoo">Yahoo Finance</option>
        <option value="mt5">MT5 / Headway</option>
      </select></div>
      <div><label>Period</label><select id="period">
        <option value="6mo">6mo</option>
        <option value="1y" selected>1y</option>
        <option value="2y">2y</option>
      </select></div>
      <div><button onclick="loadAnalysis()">Run</button></div>
    </div>
    <div class="metrics" id="metrics"></div>
  </div>
  <div class="card"><h2>Price &amp; Signals</h2><canvas id="price"></canvas></div>
  <div class="card"><h2>Equity Curve</h2><canvas id="equity"></canvas></div>
  <div class="card">
    <h2>Headway Positions</h2>
    <table><thead><tr><th>Ticket</th><th>Symbol</th><th>Side</th><th>Vol</th>
    <th>Open</th><th>Now</th><th>P&amp;L</th></tr></thead>
    <tbody id="positions"><tr><td colspan="7">loading…</td></tr></tbody></table>
  </div>
  <div class="card">
    <h2>Order Ticket</h2>
    <div class="row">
      <div><label>Symbol</label><input id="oSym" value="EURUSD" size="10"></div>
      <div><label>Side</label><select id="oSide">
        <option value="buy">Buy</option><option value="sell">Sell</option>
      </select></div>
      <div><label>Lots</label><input id="oVol" type="number" value="0.01"
        step="0.01" min="0.01" style="width:90px"></div>
      <div><label>SL (opt)</label><input id="oSL" type="number" step="any"
        style="width:110px"></div>
      <div><label>TP (opt)</label><input id="oTP" type="number" step="any"
        style="width:110px"></div>
      <div><label>Real order?</label><select id="oLive">
        <option value="no">Dry run</option><option value="yes">LIVE</option>
      </select></div>
      <div><button class="danger" onclick="sendOrder()">Send</button></div>
    </div>
    <div id="msg"></div>
  </div>
</main>
<script>
let priceChart=null, equityChart=null;
const OVERLAY_COLORS=['#58a6ff','#d29922','#a371f7','#39c5cf'];
async function api(path, opts){
  const r = await fetch(path, opts);
  return r.json();
}
async function refreshAccount(){
  const a = await api('/api/account');
  const badge = document.getElementById('conn');
  if(a.connected){
    badge.textContent = 'connected #' + a.login;
    badge.className = 'badge on';
    document.getElementById('acct').textContent =
      a.server + '  Bal ' + Number(a.balance).toFixed(2) + ' ' + a.currency +
      '  Eq ' + Number(a.equity).toFixed(2);
  } else {
    badge.textContent = 'disconnected';
    badge.className = 'badge off';
    document.getElementById('acct').textContent = a.error || '';
  }
}
async function refreshPositions(){
  const rows = await api('/api/positions');
  const tb = document.getElementById('positions');
  if(!rows.length){ tb.innerHTML = '<tr><td colspan="7">no open positions</td></tr>'; return; }
  tb.innerHTML = rows.map(p => {
    const cls = p.profit >= 0 ? 'pos' : 'neg';
    return '<tr><td>'+p.ticket+'</td><td>'+p.symbol+'</td><td>'+p.side+'</td>' +
      '<td>'+p.volume+'</td><td>'+p.price_open+'</td><td>'+p.price_current+'</td>' +
      '<td class="'+cls+'">'+Number(p.profit).toFixed(2)+'</td></tr>';
  }).join('');
}
async function loadAnalysis(){
  const q = new URLSearchParams({ symbol: v('symbol'), strategy: v('strategy'),
    source: v('source'), period: v('period') });
  const d = await api('/api/analysis?' + q);
  if(d.error){ alert(d.error); return; }
  const m = d.metrics;
  const rc = m.total_return >= 0 ? 'pos' : 'neg';
  document.getElementById('metrics').innerHTML =
    metric('Total Return', (m.total_return*100).toFixed(2)+'%', rc) +
    metric('Sharpe', m.sharpe_ratio.toFixed(2), '') +
    metric('Max Drawdown', (m.max_drawdown*100).toFixed(2)+'%', 'neg') +
    metric('Trades', m.num_trades, '') +
    metric('Win Rate', (m.win_rate*100).toFixed(1)+'%', '');
  const ds = [{ label:'Close', data:d.close, borderColor:'#e6edf3',
    pointRadius:0, borderWidth:1.5 }];
  Object.keys(d.overlays).forEach((k,i) => ds.push({ label:k, data:d.overlays[k],
    borderColor:OVERLAY_COLORS[i%OVERLAY_COLORS.length], pointRadius:0, borderWidth:1 }));
  ds.push({ label:'Buy', data:d.markers.filter(x=>x.side==='buy').map(x=>({x:x.t,y:x.price})),
    backgroundColor:'#3fb950', pointStyle:'triangle', rotation:0, radius:6, type:'scatter' });
  ds.push({ label:'Sell', data:d.markers.filter(x=>x.side==='sell').map(x=>({x:x.t,y:x.price})),
    backgroundColor:'#f85149', pointStyle:'triangle', rotation:180, radius:6, type:'scatter' });
  if(priceChart) priceChart.destroy();
  priceChart = new Chart(document.getElementById('price'),
    { type:'line', data:{ labels:d.labels, datasets:ds },
      options:{ animation:false, scales:{ x:{ ticks:{ maxTicksLimit:8 } } } } });
  if(equityChart) equityChart.destroy();
  equityChart = new Chart(document.getElementById('equity'),
    { type:'line', data:{ labels:d.equity.labels,
      datasets:[{ label:'Equity', data:d.equity.values, borderColor:'#3fb950',
        pointRadius:0, borderWidth:1.5 }] },
      options:{ animation:false, scales:{ x:{ ticks:{ maxTicksLimit:8 } } } } });
}
function metric(k,val,cls){ return '<div class="metric"><div class="k">'+k+'</div>' +
  '<div class="v '+cls+'">'+val+'</div></div>'; }
function v(id){ return document.getElementById(id).value; }
async function sendOrder(){
  const body = { symbol:v('oSym'), side:v('oSide'), volume:parseFloat(v('oVol')),
    sl:parseFloat(v('oSL'))||0, tp:parseFloat(v('oTP'))||0, live:v('oLive')==='yes' };
  if(body.live && !confirm('Place REAL order: '+body.side+' '+body.volume+
    ' '+body.symbol+'?')) return;
  const r = await api('/api/order', { method:'POST',
    headers:{'Content-Type':'application/json'}, body:JSON.stringify(body) });
  const el = document.getElementById('msg');
  el.textContent = r.message;
  el.style.color = r.ok ? '#3fb950' : '#f85149';
  refreshPositions();
}
refreshAccount(); refreshPositions(); loadAnalysis();
setInterval(refreshAccount, 5000); setInterval(refreshPositions, 5000);
</script>
</body>
</html>
"""


def create_dashboard_app() -> Any:
    """Create the Flask dashboard app (Flask imported lazily)."""
    try:
        from flask import Flask, jsonify, request
    except ImportError as exc:
        raise RuntimeError(
            "Flask is not installed. Run: pip install -e '.[web]'"
        ) from exc

    app = Flask(__name__)

    @app.route("/")  # type: ignore[untyped-decorator]
    def index() -> Any:
        return INDEX_HTML

    @app.route("/api/account")  # type: ignore[untyped-decorator]
    def api_account() -> Any:
        from open_alice.broker import load_credentials
        from open_alice.broker.mt5 import MT5Broker

        saved = load_credentials()
        if saved is None:
            return jsonify({"connected": False, "error": "no saved login (alice broker login)"})
        broker = MT5Broker(
            login=int(saved["login"]), password=saved["password"], server=saved["server"]
        )
        try:
            if not broker.connect():
                return jsonify({"connected": False, "error": "MT5 connect failed"})
            info = broker.get_account_info()
            return jsonify(
                {
                    "connected": True,
                    "login": info.login,
                    "server": saved["server"],
                    "balance": info.balance,
                    "equity": info.equity,
                    "margin": info.margin,
                    "free_margin": info.free_margin,
                    "currency": info.currency,
                    "leverage": info.leverage,
                }
            )
        except RuntimeError as exc:
            return jsonify({"connected": False, "error": str(exc)})
        finally:
            if broker.connected:
                broker.disconnect()

    @app.route("/api/positions")  # type: ignore[untyped-decorator]
    def api_positions() -> Any:
        from open_alice.broker import load_credentials
        from open_alice.broker.mt5 import MT5Broker

        saved = load_credentials()
        if saved is None:
            return jsonify([])
        broker = MT5Broker(
            login=int(saved["login"]), password=saved["password"], server=saved["server"]
        )
        try:
            if not broker.connect():
                return jsonify([])
            return jsonify(
                [
                    {
                        "ticket": p.ticket,
                        "symbol": p.symbol,
                        "side": "BUY" if p.type == 0 else "SELL",
                        "volume": p.volume,
                        "price_open": p.price_open,
                        "price_current": p.price_current,
                        "profit": p.profit,
                    }
                    for p in broker.get_positions()
                ]
            )
        except RuntimeError:
            return jsonify([])
        finally:
            if broker.connected:
                broker.disconnect()

    @app.route("/api/analysis")  # type: ignore[untyped-decorator]
    def api_analysis() -> Any:
        from open_alice.dashboard.charts import chart_payload
        from open_alice.data import add_returns, fetch_ohlcv

        symbol = str(request.args.get("symbol", "AAPL"))
        strategy = str(request.args.get("strategy", "sma_crossover"))
        source = str(request.args.get("source", "yahoo"))
        period = str(request.args.get("period", "1y"))
        if strategy not in ("sma_crossover", "rsi", "macd", "bollinger"):
            return jsonify({"error": f"unknown strategy: {strategy}"}), 400
        try:
            df = _mt5_frame(symbol) if source == "mt5" else fetch_ohlcv(symbol, period=period)
            df = add_returns(df)
            return jsonify(chart_payload(df, strategy))
        except Exception as exc:
            return jsonify({"error": str(exc)}), 500

    @app.route("/api/order", methods=["POST"])  # type: ignore[untyped-decorator]
    def api_order() -> Any:
        from open_alice.broker import load_credentials
        from open_alice.broker.mt5 import MT5Broker

        data = request.get_json(force=True, silent=True) or {}
        symbol = str(data.get("symbol", "")).strip().upper()
        side = str(data.get("side", "")).strip().lower()
        try:
            volume = float(data.get("volume", 0))
        except (TypeError, ValueError):
            return jsonify({"ok": False, "message": "invalid volume"}), 400
        sl = float(data.get("sl") or 0.0)
        tp = float(data.get("tp") or 0.0)
        live = bool(data.get("live", False))
        if not symbol or side not in ("buy", "sell") or volume <= 0:
            return jsonify({"ok": False, "message": "need symbol, side buy/sell, volume > 0"}), 400
        if not live:
            return jsonify(
                {
                    "ok": True,
                    "message": f"DRY RUN: {side} {volume} {symbol} "
                    f"(SL={sl} TP={tp}). Tick LIVE to send.",
                }
            )
        saved = load_credentials()
        if saved is None:
            return jsonify({"ok": False, "message": "no saved MT5 login"}), 400
        broker = MT5Broker(
            login=int(saved["login"]), password=saved["password"], server=saved["server"]
        )
        try:
            if not broker.connect():
                return jsonify({"ok": False, "message": "MT5 connect failed"}), 500
            ok = broker.buy(symbol, volume, sl, tp) if side == "buy" else broker.sell(
                symbol, volume, sl, tp
            )
            msg = f"LIVE {side} {volume} {symbol} sent." if ok else "order rejected by MT5"
            return jsonify({"ok": ok, "message": msg})
        except RuntimeError as exc:
            return jsonify({"ok": False, "message": str(exc)}), 500
        finally:
            if broker.connected:
                broker.disconnect()

    return app


def _mt5_frame(symbol: str, count: int = 500) -> Any:
    """Fetch recent daily bars from MT5 using saved credentials."""
    from typing import Any as _Any

    mt5: _Any = __import__("MetaTrader5")
    from open_alice.broker import load_credentials
    from open_alice.broker.mt5 import MT5Broker
    from open_alice.data import add_returns

    saved = load_credentials()
    if saved is None:
        raise RuntimeError("no saved MT5 login (run: alice broker login)")
    broker = MT5Broker(
        login=int(saved["login"]), password=saved["password"], server=saved["server"]
    )
    try:
        if not broker.connect():
            raise RuntimeError("MT5 connect failed")
        return add_returns(broker.get_rates(symbol, mt5.TIMEFRAME_D1, count))
    finally:
        if broker.connected:
            broker.disconnect()
