#!/usr/bin/env python3
"""
UnifAI Governance Dashboard — World Physics primitive.

Single-file HTTPS server on localhost:7700 providing:
  /            — governance dashboard (status, kill switch, oil gauge)
  /credentials — encrypted credential entry → SecretVault
  /kill-switch — manual trip/reset controls

No nginx dependency. Python stdlib only (+ openssl for cert generation).
Never store secrets in plain text; never log secret values.

Usage:
    python3 webui.py [--port 7700] [--sv-cli path/to/cli.js]
"""

import os, ssl, json, subprocess, argparse, sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent

DEFAULT_PORT   = int(os.getenv("WEBUI_PORT", "7700"))
DEFAULT_SV_CLI = os.getenv("WEBUI_SV_CLI", str(_HERE / "supervisor-secretvault" / "src" / "cli.js"))
CERT_DIR       = Path(os.getenv("WEBUI_CERT_DIR", str(_HERE / "data" / "certs")))
AUDIT_LOG      = Path(os.getenv("WEBUI_AUDIT_LOG", str(_HERE / "logs" / "webui_audit.log")))
FUSE_STATE     = Path(os.getenv("FUSE_STATE_FILE", "/var/lib/little7/fuse_state.json"))
FUSE_TRIP_CMD  = _HERE / "bin" / "fuse-trip"
FUSE_RESET_CMD = _HERE / "bin" / "fuse-reset"

# ── Token gauge: read from token_gauge.py if available ──────────────────────

def _token_gauge_summary() -> dict:
    """Read from token_gauge.py if available. Disabled by default for alpha."""
    gauge_script = _HERE / "plugins" / "bill_guardian" / "token_gauge.py"
    if not gauge_script.is_file():
        return {"ok": False, "error": "Token gauge not configured for Alpha."}
    
    try:
        result = subprocess.run(
            [sys.executable, str(gauge_script)],
            capture_output=True, text=True, timeout=10,
        )
        lines = result.stdout.splitlines()
        # Extract key numbers from output
        billable = used_pct = remaining = 0
        for line in lines:
            if "Billable total" in line:
                parts = line.split()
                for p in parts:
                    try: billable = int(p.replace(",", "")); break
                    except: pass
            if "Window used" in line:
                parts = line.split()
                for p in parts:
                    if "%" in p:
                        try: used_pct = float(p.replace("%", "")); break
                        except: pass
            if "Est. remaining" in line:
                parts = line.split()
                for p in parts:
                    try: remaining = int(p.replace(",", "")); break
                    except: pass
        bar_len = 20
        filled = round(used_pct / 100 * bar_len)
        bar = "█" * filled + "░" * (bar_len - filled)
        return {
            "billable": billable,
            "used_pct": round(used_pct, 1),
            "remaining": remaining,
            "bar": bar,
            "ok": True,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ── Fuse/Kill Switch state ───────────────────────────────────────────────────

def _fuse_state() -> dict:
    try:
        if FUSE_STATE.is_file():
            data = json.loads(FUSE_STATE.read_text())
            return {"tripped": True, **data}
    except Exception:
        pass
    return {"tripped": False}


def _trip_fuse(duration: int, reason: str) -> tuple[bool, str]:
    if not FUSE_TRIP_CMD.is_file():
        return False, f"fuse-trip not found at {FUSE_TRIP_CMD}"
    try:
        r = subprocess.run(
            [str(FUSE_TRIP_CMD), str(duration), "WEBUI_MANUAL", reason[:80]],
            capture_output=True, text=True, timeout=10,
        )
        return r.returncode == 0, r.stdout + r.stderr
    except Exception as e:
        return False, str(e)


def _reset_fuse() -> tuple[bool, str]:
    if not FUSE_RESET_CMD.is_file():
        return False, f"fuse-reset not found at {FUSE_RESET_CMD}"
    try:
        r = subprocess.run(
            [str(FUSE_RESET_CMD)],
            capture_output=True, text=True, timeout=10,
        )
        return r.returncode == 0, r.stdout + r.stderr
    except Exception as e:
        return False, str(e)


# ── SecretVault operations ───────────────────────────────────────────────────

def _master_key() -> str:
    key = os.environ.get("SECRETVAULT_MASTER_KEY", "")
    if not key:
        p = Path("/etc/little7/secretvault_master.key")
        if p.is_file():
            key = p.read_text().strip()
    return key


def _seed_secret(alias: str, value: str, sv_cli: str) -> tuple[bool, str]:
    mk = _master_key()
    if not mk:
        return False, "SECRETVAULT_MASTER_KEY not set"
    env = {**os.environ, "SECRETVAULT_MASTER_KEY": mk}
    try:
        r = subprocess.run(
            ["node", sv_cli, "seed", "--alias", alias, "--value", value],
            capture_output=True, text=True, timeout=15, env=env,
        )
        out = r.stdout + r.stderr
        if '"ok":true' in out or r.returncode == 0:
            return True, "Secret stored."
        return False, f"SecretVault error: {out[:200]}"
    except FileNotFoundError:
        return False, f"SecretVault CLI not found: {sv_cli}"
    except subprocess.TimeoutExpired:
        return False, "SecretVault CLI timed out"
    except Exception as e:
        return False, str(e)


# ── Audit log ────────────────────────────────────────────────────────────────

def _audit(entry: dict) -> None:
    AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry["ts"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with AUDIT_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


# ── CSS shared ───────────────────────────────────────────────────────────────

_CSS = """
body{font-family:monospace;max-width:600px;margin:40px auto;padding:0 20px;
     background:#0a0a0a;color:#d4d4d4;}
h1{font-size:1.1rem;color:#7ec8e3;border-bottom:1px solid #333;padding-bottom:8px;}
h2{font-size:.95rem;color:#aaa;margin-top:28px;}
nav a{color:#7ec8e3;margin-right:18px;font-size:.85rem;text-decoration:none;}
nav a:hover{text-decoration:underline;}
.card{background:#111;border:1px solid #2a2a2a;padding:14px;margin-top:12px;}
.ok{color:#6bcb77;} .warn{color:#ffd166;} .err{color:#ff6b6b;}
.bar{font-size:.8rem;letter-spacing:1px;}
label{display:block;margin-top:14px;font-size:.85rem;color:#aaa;}
input[type=text],input[type=password],input[type=number]{
  width:100%;padding:7px;margin-top:4px;background:#1a1a1a;
  border:1px solid #333;color:#e0e0e0;font-family:monospace;
  font-size:.88rem;box-sizing:border-box;}
button{margin-top:16px;padding:8px 18px;background:#1e5f74;color:#fff;
       border:none;font-family:monospace;cursor:pointer;}
button:hover{background:#2a7a94;}
button.danger{background:#7a1e1e;}
button.danger:hover{background:#9a2a2a;}
.notice{font-size:.78rem;color:#666;line-height:1.6;}
.status{margin-top:12px;font-size:.85rem;}
"""

_NAV = '<nav><a href="/">Dashboard</a><a href="/credentials">Credentials</a><a href="/kill-switch">Kill Switch</a></nav>'


# ── Page builders ────────────────────────────────────────────────────────────

def _page(title: str, body: str) -> str:
    return f"""<!DOCTYPE html><html lang="en"><head>
<meta charset="utf-8"><title>{title} — UnifAI</title>
<style>{_CSS}</style></head><body>
<h1>UnifAI Governance Dashboard</h1>
{_NAV}
<hr style="border-color:#1e1e1e;margin:12px 0;">
{body}
</body></html>"""


def _dashboard_page() -> str:
    fuse = _fuse_state()
    gauge = _token_gauge_summary()

    # Fuse card
    if fuse["tripped"]:
        until = fuse.get("until_epoch", "?")
        reason = fuse.get("reason_code", "?")
        fuse_html = f'<div class="card"><span class="err">⛔ FUSE TRIPPED</span><br>reason: {reason}<br>until: epoch {until}</div>'
    else:
        fuse_html = '<div class="card"><span class="ok">✅ Kill switch: ARMED (not tripped)</span></div>'

    # Gauge card
    if gauge["ok"]:
        pct = gauge["used_pct"]
        cls = "ok" if pct < 70 else ("warn" if pct < 90 else "err")
        gauge_html = (
            f'<div class="card">'
            f'<span class="{cls}">{pct}% of 5h token window used</span><br>'
            f'<span class="bar">[{gauge["bar"]}]</span><br>'
            f'Billable: {gauge["billable"]:,} / 44,000 &nbsp; Remaining: ~{gauge["remaining"]:,}'
            f'</div>'
        )
    else:
        gauge_html = f'<div class="card"><span class="warn">⚠ Token gauge unavailable: {gauge.get("error","")}</span></div>'

    sv_cli_ok = Path(DEFAULT_SV_CLI).is_file()
    sv_html = (
        f'<div class="card"><span class="ok">✅ SecretVault CLI found</span></div>'
        if sv_cli_ok else
        f'<div class="card"><span class="warn">⚠ SecretVault CLI not found at default path</span></div>'
    )

    return _page("Dashboard", f"""
<h2>System Status</h2>
{fuse_html}
{gauge_html}
{sv_html}
<p class="notice" style="margin-top:20px;">
  This dashboard is served over HTTPS on localhost only.<br>
  Access is restricted to this machine. No authentication required for localhost access.<br>
  All credential operations are written to the audit log.
</p>
""")


def _credentials_page(status_html: str = "") -> str:
    return _page("Credentials", f"""
<h2>Store a Secret in SecretVault</h2>
<p class="notice">
  Credentials are written directly into SecretVault — never logged or stored in plain text.<br>
  <strong>Never send credentials via Telegram.</strong> Always use this page.
</p>
{status_html}
<form method="POST" action="/credentials">
  <label>Secret alias (e.g. <code>codex-oauth</code>, <code>telegram-bot-token</code>)</label>
  <input type="text" name="alias" required placeholder="codex-oauth" autocomplete="off">
  <label>Secret value</label>
  <input type="password" name="value" required placeholder="sk-ant-..." autocomplete="off">
  <button type="submit">Store in SecretVault</button>
</form>
""")


def _kill_switch_page(status_html: str = "") -> str:
    fuse = _fuse_state()
    if fuse["tripped"]:
        state_html = f'<div class="card"><span class="err">⛔ FUSE TRIPPED — reason: {fuse.get("reason_code","?")} / until: epoch {fuse.get("until_epoch","?")}</span></div>'
    else:
        state_html = '<div class="card"><span class="ok">✅ Kill switch: ARMED (not tripped)</span></div>'

    return _page("Kill Switch", f"""
<h2>Kill Switch Control</h2>
{state_html}
{status_html}
<hr style="border-color:#1e1e1e;margin:16px 0;">
<h2>Manual Trip</h2>
<p class="notice">Trips the fuse for all cloud activity. Agent tasks will be blocked until reset.</p>
<form method="POST" action="/kill-switch/trip">
  <label>Duration (seconds, default 600)</label>
  <input type="number" name="duration" value="600" min="10" max="86400">
  <label>Reason (optional)</label>
  <input type="text" name="reason" placeholder="manual test" autocomplete="off">
  <button class="danger" type="submit">⚡ Trip Kill Switch</button>
</form>
<hr style="border-color:#1e1e1e;margin:16px 0;">
<h2>Reset</h2>
<form method="POST" action="/kill-switch/reset">
  <button type="submit">↺ Reset Kill Switch</button>
</form>
""")


# ── HTTP handler ─────────────────────────────────────────────────────────────

def make_handler(sv_cli: str):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            pass  # suppress default; we use _audit

        def _html(self, code: int, body: str) -> None:
            b = body.encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(b)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Strict-Transport-Security", "max-age=31536000")
            self.end_headers()
            self.wfile.write(b)

        def _read_body(self) -> dict:
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length).decode("utf-8", errors="replace")
            return parse_qs(raw)

        def do_GET(self):
            if self.path in ("/", "/index.html"):
                self._html(200, _dashboard_page())
            elif self.path == "/credentials":
                self._html(200, _credentials_page())
            elif self.path == "/kill-switch":
                self._html(200, _kill_switch_page())
            else:
                self._html(404, _page("404", "<p>Not found.</p>"))

        def do_POST(self):
            params = self._read_body()

            if self.path == "/credentials":
                alias = (params.get("alias", [""])[0]).strip()
                value = (params.get("value", [""])[0]).strip()
                if not alias or not value:
                    self._html(400, _credentials_page('<p class="status err">⚠ Both alias and value required.</p>'))
                    return
                _audit({"event": "seed_attempt", "alias": alias, "ip": self.client_address[0]})
                ok, msg = _seed_secret(alias, value, sv_cli)
                cls = "ok" if ok else "err"
                status = f'<p class="status {cls}">{"✓" if ok else "✗"} {msg}</p>'
                _audit({"event": "seed_ok" if ok else "seed_fail", "alias": alias, "msg": msg})
                self._html(200 if ok else 500, _credentials_page(status))

            elif self.path == "/kill-switch/trip":
                duration = int((params.get("duration", ["600"])[0]).strip() or "600")
                reason = (params.get("reason", ["manual"])[0]).strip() or "manual"
                _audit({"event": "trip_attempt", "duration": duration, "reason": reason, "ip": self.client_address[0]})
                ok, msg = _trip_fuse(duration, reason)
                cls = "ok" if ok else "err"
                status = f'<p class="status {cls}">{"✓ Fuse tripped." if ok else "✗ " + msg}</p>'
                _audit({"event": "trip_ok" if ok else "trip_fail", "msg": msg})
                self._html(200 if ok else 500, _kill_switch_page(status))

            elif self.path == "/kill-switch/reset":
                _audit({"event": "reset_attempt", "ip": self.client_address[0]})
                ok, msg = _reset_fuse()
                cls = "ok" if ok else "err"
                status = f'<p class="status {cls}">{"✓ Fuse reset." if ok else "✗ " + msg}</p>'
                _audit({"event": "reset_ok" if ok else "reset_fail", "msg": msg})
                self._html(200 if ok else 500, _kill_switch_page(status))

            else:
                self._html(404, _page("404", "<p>Not found.</p>"))

    return Handler


# ── TLS cert generation ───────────────────────────────────────────────────────

def _ensure_cert() -> tuple[str, str]:
    CERT_DIR.mkdir(parents=True, exist_ok=True)
    cert = CERT_DIR / "webui.crt"
    key  = CERT_DIR / "webui.key"
    if not (cert.is_file() and key.is_file()):
        subprocess.run(
            ["openssl", "req", "-x509", "-newkey", "rsa:2048",
             "-keyout", str(key), "-out", str(cert),
             "-days", "3650", "-nodes",
             "-subj", "/CN=localhost/O=UnifAI/C=XX"],
            check=True, capture_output=True,
        )
    return str(cert), str(key)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="UnifAI Governance Dashboard")
    parser.add_argument("--port",   type=int, default=DEFAULT_PORT)
    parser.add_argument("--sv-cli", default=DEFAULT_SV_CLI)
    args = parser.parse_args()

    cert_path, key_path = _ensure_cert()

    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(certfile=cert_path, keyfile=key_path)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2

    server = HTTPServer(("127.0.0.1", args.port), make_handler(args.sv_cli))
    server.socket = ctx.wrap_socket(server.socket, server_side=True)

    _audit({"event": "webui_start", "port": args.port})
    print(f"[webui] https://localhost:{args.port}")
    print(f"[webui] Pages: / (dashboard)  /credentials  /kill-switch")
    print(f"[webui] Audit: {AUDIT_LOG}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[webui] Stopped.")
    finally:
        _audit({"event": "webui_stop"})


if __name__ == "__main__":
    main()
