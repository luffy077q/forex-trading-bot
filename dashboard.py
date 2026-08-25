"""
Local website showing everything the bot is doing: account status, trades,
every signal check (including why trades were skipped), and a balance chart.

Run alongside main.py:
    python dashboard.py
Then open: http://localhost:5000

This does NOT place trades itself -- it only reads the CSV logs main.py
writes, plus a live account snapshot from OANDA. Safe to leave open in a
browser tab all day.
"""

import csv
import os
from flask import Flask, jsonify, render_template_string

import config
import paper_broker

app = Flask(__name__)


def read_csv(path, limit=200):
    if not os.path.isfile(path):
        return []
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))
    return rows[-limit:][::-1]  # most recent first


@app.route("/api/data")
def api_data():
    state = paper_broker.load_state()
    account_info = {
        "balance": state["balance"],
        "currency": state["currency"],
        "open_trades": [
            {
                "instrument": p["instrument"],
                "units": p["units"],
                "side": p["side"],
                "price": p["entry_price"],
                "stop_loss": p["stop_loss"],
                "take_profit": p["take_profit"],
            }
            for p in state["open_positions"]
        ],
        "error": None,
    }

    return jsonify({
        "account": account_info,
        "trades": read_csv(config.TRADE_LOG_FILE),
        "closed_trades": read_csv("closed_trades.csv"),
        "signals": read_csv(config.SIGNAL_LOG_FILE, limit=100),
        "balance_history": read_csv(config.BALANCE_LOG_FILE, limit=500)[::-1],  # chronological for chart
    })


PAGE = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Forex Bot Dashboard</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js"></script>
<style>
  :root {
    --bg: #0f1117; --card: #171a23; --border: #262b3a; --text: #e6e8ef;
    --muted: #8a90a3; --green: #3ecf8e; --red: #f26d6d; --blue: #5b8def; --yellow: #e0c341;
  }
  * { box-sizing: border-box; }
  body { background: var(--bg); color: var(--text); font-family: -apple-system, Segoe UI, Roboto, sans-serif; margin: 0; padding: 24px; }
  h1 { font-size: 20px; font-weight: 600; margin: 0 0 4px; }
  .sub { color: var(--muted); font-size: 13px; margin-bottom: 24px; }
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-bottom: 24px; }
  .card { background: var(--card); border: 1px solid var(--border); border-radius: 10px; padding: 16px; }
  .card .label { color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 6px; }
  .card .value { font-size: 24px; font-weight: 600; }
  .section { background: var(--card); border: 1px solid var(--border); border-radius: 10px; padding: 16px; margin-bottom: 20px; }
  .section h2 { font-size: 14px; margin: 0 0 12px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.05em; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th, td { text-align: left; padding: 8px 10px; border-bottom: 1px solid var(--border); white-space: nowrap; }
  th { color: var(--muted); font-weight: 500; }
  tr:hover { background: rgba(255,255,255,0.02); }
  .buy { color: var(--green); font-weight: 600; }
  .sell { color: var(--red); font-weight: 600; }
  .none { color: var(--muted); }
  .pos { color: var(--green); }
  .neg { color: var(--red); }
  .scroll { max-height: 420px; overflow-y: auto; }
  .badge { display: inline-block; padding: 2px 8px; border-radius: 999px; font-size: 11px; font-weight: 600; }
  .badge.err { background: rgba(242,109,109,0.15); color: var(--red); }
  .badge.ok { background: rgba(62,207,142,0.15); color: var(--green); }
  canvas { max-height: 220px; }
</style>
</head>
<body>

<h1>Forex Bot Dashboard</h1>
<div class="sub">Auto-refreshes every """ + str(config.DASHBOARD_REFRESH_SECONDS) + """s &middot; <span id="status"></span></div>

<div class="grid">
  <div class="card"><div class="label">Balance</div><div class="value" id="balance">--</div></div>
  <div class="card"><div class="label">Open Positions</div><div class="value" id="openCount">--</div></div>
  <div class="card"><div class="label">Total Trades Logged</div><div class="value" id="tradeCount">--</div></div>
  <div class="card"><div class="label">Instruments</div><div class="value" id="instruments" style="font-size:16px;">""" + ", ".join(config.INSTRUMENTS) + """</div></div>
</div>

<div class="section">
  <h2>Balance Over Time</h2>
  <canvas id="balanceChart"></canvas>
</div>

<div class="section">
  <h2>Open Positions</h2>
  <div id="openPositions">No data yet.</div>
</div>

<div class="section">
  <h2>Closed Trades (realized P/L)</h2>
  <div class="scroll"><table id="closedTable">
    <thead><tr><th>Closed</th><th>Instrument</th><th>Side</th><th>Units</th><th>Entry</th><th>Exit</th><th>Reason</th><th>P/L</th></tr></thead>
    <tbody></tbody>
  </table></div>
</div>

<div class="section">
  <h2>Trade History (all opens)</h2>
  <div class="scroll"><table id="tradesTable">
    <thead><tr><th>Time</th><th>Instrument</th><th>Side</th><th>Units</th><th>Entry</th><th>Stop Loss</th><th>Take Profit</th></tr></thead>
    <tbody></tbody>
  </table></div>
</div>

<div class="section">
  <h2>Signal Log (every check the bot made, including why it did or didn't trade)</h2>
  <div class="scroll"><table id="signalsTable">
    <thead><tr><th>Time</th><th>Instrument</th><th>Technical</th><th>RSI</th><th>News (base/quote/net)</th><th>Decision</th><th>Reason</th></tr></thead>
    <tbody></tbody>
  </table></div>
</div>

<script>
let chart = null;

function fmt(n, d=5) {
  if (n === null || n === undefined || n === "") return "--";
  const num = parseFloat(n);
  return isNaN(num) ? n : num.toFixed(d);
}

function sideClass(side) {
  if (side === "BUY") return "buy";
  if (side === "SELL") return "sell";
  return "none";
}

async function refresh() {
  try {
    const res = await fetch("/api/data");
    const data = await res.json();

    document.getElementById("status").textContent =
      "Last updated " + new Date().toLocaleTimeString();

    const acct = data.account;
    document.getElementById("balance").textContent =
      (acct.balance !== null ? acct.balance.toFixed(2) + " " + acct.currency : "--");
    document.getElementById("openCount").textContent = acct.open_trades.length;

    if (acct.open_trades.length === 0) {
      document.getElementById("openPositions").innerHTML = '<span style="color:var(--muted)">No open positions.</span>';
    } else {
      let html = '<table><thead><tr><th>Instrument</th><th>Side</th><th>Units</th><th>Entry</th><th>Stop Loss</th><th>Take Profit</th></tr></thead><tbody>';
      for (const t of acct.open_trades) {
        html += `<tr><td>${t.instrument}</td><td class="${sideClass(t.side)}">${t.side}</td><td>${t.units}</td>
                 <td>${fmt(t.price)}</td><td>${fmt(t.stop_loss)}</td><td>${fmt(t.take_profit)}</td></tr>`;
      }
      html += '</tbody></table>';
      document.getElementById("openPositions").innerHTML = html;
    }

    document.getElementById("tradeCount").textContent = data.trades.length;

    const closedBody = document.querySelector("#closedTable tbody");
    closedBody.innerHTML = data.closed_trades.map(t => {
      const pnl = parseFloat(t.pnl);
      return `<tr>
        <td>${new Date(t.closed_at).toLocaleString()}</td>
        <td>${t.instrument}</td>
        <td class="${sideClass(t.side)}">${t.side}</td>
        <td>${t.units}</td>
        <td>${fmt(t.entry_price)}</td>
        <td>${fmt(t.exit_price)}</td>
        <td>${t.exit_reason}</td>
        <td class="${pnl >= 0 ? 'pos' : 'neg'}">${pnl >= 0 ? '+' : ''}${fmt(t.pnl, 2)}</td>
      </tr>`;
    }).join("") || '<tr><td colspan="8" style="color:var(--muted)">No closed trades yet.</td></tr>';

    const tradesBody = document.querySelector("#tradesTable tbody");
    tradesBody.innerHTML = data.trades.map(t => `
      <tr>
        <td>${new Date(t.timestamp).toLocaleString()}</td>
        <td>${t.instrument}</td>
        <td class="${sideClass(t.side)}">${t.side}</td>
        <td>${t.units}</td>
        <td>${fmt(t.entry_price)}</td>
        <td>${fmt(t.stop_loss)}</td>
        <td>${fmt(t.take_profit)}</td>
      </tr>`).join("") || '<tr><td colspan="7" style="color:var(--muted)">No trades yet.</td></tr>';

    const signalsBody = document.querySelector("#signalsTable tbody");
    signalsBody.innerHTML = data.signals.map(s => `
      <tr>
        <td>${new Date(s.timestamp).toLocaleString()}</td>
        <td>${s.instrument}</td>
        <td class="${sideClass(s.technical_signal)}">${s.technical_signal || '--'}</td>
        <td>${fmt(s.rsi, 1)}</td>
        <td>${fmt(s.news_base,2)} / ${fmt(s.news_quote,2)} / ${fmt(s.news_net,2)}</td>
        <td class="${sideClass(s.final_decision)}">${s.final_decision || 'NO TRADE'}</td>
        <td style="white-space:normal; color:var(--muted)">${s.reason || ''}</td>
      </tr>`).join("") || '<tr><td colspan="7" style="color:var(--muted)">No signals logged yet.</td></tr>';

    const bh = data.balance_history;
    const labels = bh.map(b => new Date(b.timestamp).toLocaleTimeString());
    const values = bh.map(b => parseFloat(b.balance));

    if (chart) {
      chart.data.labels = labels;
      chart.data.datasets[0].data = values;
      chart.update();
    } else {
      const ctx = document.getElementById("balanceChart").getContext("2d");
      chart = new Chart(ctx, {
        type: "line",
        data: { labels: labels, datasets: [{ label: "Balance", data: values,
          borderColor: "#5b8def", backgroundColor: "rgba(91,141,239,0.1)", fill: true, tension: 0.2 }] },
        options: { responsive: true, plugins: { legend: { display: false } },
          scales: { x: { ticks: { color: "#8a90a3" }, grid: { color: "#262b3a" } },
                    y: { ticks: { color: "#8a90a3" }, grid: { color: "#262b3a" } } } }
      });
    }
  } catch (e) {
    document.getElementById("status").textContent = "Error refreshing: " + e;
  }
}

refresh();
setInterval(refresh, """ + str(config.DASHBOARD_REFRESH_SECONDS * 1000) + """);
</script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(PAGE)


if __name__ == "__main__":
    print(f"Dashboard running at http://localhost:{config.DASHBOARD_PORT}")
    print("Leave main.py running separately -- this dashboard only reads its logs.")
    app.run(host="0.0.0.0", port=config.DASHBOARD_PORT, debug=False)
